"""
fetch_od_bus_rail.py
---------------------
일일 OD(버스/도시철도) 데이터를 수집하는 스크립트.
NiFi 자동화에 맞게 디렉토리 구조 및 처리 방식 리팩토링.

변경 사항:
1. data/raw/od/YYYY/MM 구조로 저장 (NiFi가 모니터링하기 최적)
2. Safe Request 도입 (재시도/지연)
3. 사용자 입력 제거 (자동화 환경에 맞춤)
4. 여러 JSON → 월 단위 병합 → 중간파일 삭제
5. 절대경로 기반으로 경로 안전하게 처리

Author : MinWoo Kang
Project : Smart Commute Pipeline
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv


# --------------------------------------------------------------------
# 🌐 환경 변수 로드
# --------------------------------------------------------------------
load_dotenv()
SERVICE_KEY = os.getenv("OD_API_KEY")
if not SERVICE_KEY:
    raise ValueError("❌ OD_API_KEY not found in .env file")

BASE_URL = (
    "https://apis.data.go.kr/1613000/"
    "ODUsageforGeneralBusesandUrbanRailways/getDailyODUsageforGeneralBusesandUrbanRailways"
)

# 절대 경로 구성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_OD_DIR = os.path.join(BASE_DIR, "../data/raw/od")


# --------------------------------------------------------------------
# 📁 JSON 저장 함수 (NiFi Friendly)
# --------------------------------------------------------------------
def save_json(year, month, filename, data):
    """
    data/raw/od/YYYY/MM/filename.json 형식으로 저장
    """
    year_dir = os.path.join(RAW_OD_DIR, str(year))
    month_dir = os.path.join(year_dir, f"{month:02d}")

    os.makedirs(month_dir, exist_ok=True)

    filepath = os.path.join(month_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Saved → {filepath}")
    return filepath


# --------------------------------------------------------------------
# 🔁 Safe Request (재시도 포함)
# --------------------------------------------------------------------
def safe_request(params, max_retries=3, delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(BASE_URL, params=params, timeout=(5, 60))
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"⚠️ Attempt {attempt}/{max_retries} failed: {e}")
            time.sleep(delay)

    print("❌ All retry attempts failed.")
    return None


# --------------------------------------------------------------------
# 📥 일자별 API 호출
# --------------------------------------------------------------------
def fetch_od_daily(opr_ymd, year, month,
                   dptre_ctpv_cd="11", dptre_sgg_cd="11110",
                   arvl_ctpv_cd="11", arvl_sgg_cd="11680"):
    """
    일자별 OD 데이터 호출 후 JSON 저장
    """

    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": "1",
        "numOfRows": "100",
        "opr_ymd": opr_ymd,
        "dptre_ctpv_cd": dptre_ctpv_cd,
        "dptre_sgg_cd": dptre_sgg_cd,
        "arvl_ctpv_cd": arvl_ctpv_cd,
        "arvl_sgg_cd": arvl_sgg_cd,
        "dataType": "JSON",
    }

    print(f"📡 Requesting OD: {opr_ymd}")

    response = safe_request(params)
    if not response:
        return None

    try:
        data = response.json()
    except Exception:
        print(f"❌ JSON Parse Error on {opr_ymd}")
        return None

    # 내부 구조 탐색
    items = data.get("Response", {}).get("body", {}).get("items", {}).get("item", [])

    filename = f"od_{opr_ymd}.json"
    return save_json(year, month, filename, items)


# --------------------------------------------------------------------
# 🧩 여러 JSON 병합
# --------------------------------------------------------------------
def merge_json_files(file_list, year, month, output_filename):
    """여러 JSON 파일 병합"""

    all_items = []

    for file_path in file_list:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_items.extend(data)
        except Exception as e:
            print(f"⚠️ Skipped {file_path}: {e}")

    # 저장
    return save_json(year, month, output_filename, all_items)


# --------------------------------------------------------------------
# 🌕 월 전체 수집 (일별 요청 → 병합 → 중간삭제)
# --------------------------------------------------------------------
def fetch_od_monthly(year, month, chunk_size=10, **kwargs):
    """
    1. 하루 단위로 API 요청
    2. chunk_size(10일) 단위로 병합
    3. 마지막에 full 파일 생성
    """

    print(f"📅 Fetching OD Monthly → {year}-{month:02d}")

    start_date = datetime(year, month, 1)
    end_date = (
        datetime(year + (month // 12), (month % 12) + 1, 1)
        - timedelta(days=1)
    )

    current = start_date
    temp_files = []
    chunk_files = []

    chunk_start_date = current.strftime("%Y%m%d")

    while current <= end_date:
        opr_ymd = current.strftime("%Y%m%d")

        file_path = fetch_od_daily(opr_ymd, year, month, **kwargs)
        if file_path:
            temp_files.append(file_path)

        # 10일 단위 병합
        if len(temp_files) == chunk_size or current == end_date:
            chunk_end_date = opr_ymd
            chunk_filename = f"od_{chunk_start_date}_to_{chunk_end_date}.json"

            merged_path = merge_json_files(temp_files, year, month, chunk_filename)
            chunk_files.append(merged_path)

            # temp 파일 삭제
            for tmp in temp_files:
                try:
                    os.remove(tmp)
                except:
                    pass
            temp_files = []

            # 다음 chunk 시작점 갱신
            if current < end_date:
                chunk_start_date = (current + timedelta(days=1)).strftime("%Y%m%d")

        current += timedelta(days=1)
        time.sleep(1)

    # 월 전체 병합
    final_filename = f"od_{year}{month:02d}_all.json"
    final_path = merge_json_files(chunk_files, year, month, final_filename)

    # 중간 chunk 삭제
    for c in chunk_files:
        try:
            os.remove(c)
        except:
            pass

    print(f"🌕 Final merged file: {final_path}")
    return final_path


# --------------------------------------------------------------------
# 🚀 실행부 (자동화 + 누락 월 백필)
# --------------------------------------------------------------------
if __name__ == "__main__":
    start_year = 2025
    start_month = 4

    today = datetime.now()
    current_year = today.year
    current_month = today.month

    # 누락 월 자동 수집
    for year in range(start_year, current_year + 1):

        # 시작 월 설정
        if year == start_year:
            m_start = start_month
        else:
            m_start = 1

        # 검사할 마지막 월
        if year < current_year:
            m_end = 12
        else:
            m_end = current_month - 1

        if m_end < 1:
            continue

        for month in range(m_start, m_end + 1):
            expected = os.path.join(
                RAW_OD_DIR,
                f"{year}/{month:02d}/od_{year}{month:02d}_all.json"
            )

            if not os.path.exists(expected):
                print(f"📡 Missing → Fetching {year}-{month:02d}")
                fetch_od_monthly(year, month)
            else:
                print(f"✅ Exists: {expected}")

    print("🎉 OD Extract Completed Successfully")
