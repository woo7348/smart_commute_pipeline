"""
fetch_weather.py
-----------------
기상청 ASOS(종관기상관측) 일별 데이터를 수집하는 스크립트.
NiFi 자동화를 위해 아래 원칙으로 리팩토링됨:

1. 모든 Raw 파일을 프로젝트 절대경로 기준의 구조적 폴더에 저장
   data/raw/weather/YYYY/MM/

2. 사용자 입력 제거 (cron + NiFi 자동화 환경에서는 input 사용 불가)

3. Airflow → NiFi 전환을 위한 분리 구조
   - Python: Extract(데이터 수집)만 담당
   - NiFi: Transform + Load 담당

4. 주 단위 chunk 요청 후, 월 단위 full 파일 생성
   → NiFi는 full 파일만 읽으면 됨

Author : MinWoo Kang
Project: Smart Commute Pipeline
"""

import os
import json
import time
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# --------------------------------------------------------------------
# 🌐 환경 변수 및 기본 설정
# --------------------------------------------------------------------
load_dotenv()

SERVICE_KEY = os.getenv("WEATHER_API_KEY")
if not SERVICE_KEY:
    raise ValueError("❌ WEATHER_API_KEY not found in .env file")

BASE_URL = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"

# 프로젝트 절대 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# NiFi가 읽을 Raw 데이터 저장 경로
RAW_WEATHER_DIR = os.path.join(BASE_DIR, "../data/raw/weather")


# --------------------------------------------------------------------
# 🧩 공통 함수: JSON 저장 (NiFi Friendly Directory)
# --------------------------------------------------------------------
def save_json(year, month, stn_id, filename, data):
    """
    JSON 파일을 아래 구조로 저장:
    data/raw/weather/YYYY/MM/filename.json
    """
    year_dir = os.path.join(RAW_WEATHER_DIR, str(year))
    month_dir = os.path.join(year_dir, f"{month:02d}")

    os.makedirs(month_dir, exist_ok=True)

    filepath = os.path.join(month_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Saved → {filepath}")
    return filepath


# --------------------------------------------------------------------
# 🔁 안전한 요청 함수 (재시도)
# --------------------------------------------------------------------
def safe_request(params, max_retries=3, delay=5):
    """API 요청 실패 시 자동 재시도"""
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
# 📥 단일 기간 데이터 수집 (주 단위)
# --------------------------------------------------------------------
def fetch_asos_daily(start_date, end_date, year, month, stn_id="108"):
    """
    주 단위 데이터 수집 후 raw 폴더에 저장.
    """
    filename = f"asos_daily_{stn_id}_{start_date}_{end_date}.json"

    params = {
        "serviceKey": SERVICE_KEY,
        "dataCd": "ASOS",
        "dateCd": "DAY",
        "startDt": start_date,
        "endDt": end_date,
        "stnIds": stn_id,
        "dataType": "JSON",
        "numOfRows": 100,
        "pageNo": 1,
    }

    print(f"📡 Requesting ASOS Daily ({start_date} ~ {end_date})")

    response = safe_request(params)
    if not response:
        return None

    data = response.json()
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

    if not items:
        print("⚠️ No data returned.")
        return None

    # 저장
    save_json(year, month, stn_id, filename, items)
    return items


# --------------------------------------------------------------------
# 📅 전체 월 데이터를 주 단위로 fetch 후 병합
# --------------------------------------------------------------------
def fetch_asos_month_chunked(year, month, stn_id="108"):
    """
    1. 한 달 데이터를 7일 단위로 분할 요청
    2. 주간 파일 저장
    3. 월 단위 full JSON 생성
    4. 중간 주간 파일 삭제
    """
    print(f"📅 Fetching ASOS Monthly → {year}-{month:02d}")

    start = datetime(year, month, 1)
    end = (start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    all_items = []
    weekly_files = []
    delta = timedelta(days=7)

    while start <= end:
        chunk_start = start.strftime("%Y%m%d")
        chunk_end = min(start + delta - timedelta(days=1), end).strftime("%Y%m%d")

        items = fetch_asos_daily(chunk_start, chunk_end, year, month, stn_id)

        if items:
            all_items.extend(items)
            weekly_files.append(
                os.path.join(
                    RAW_WEATHER_DIR, f"{year}/{month:02d}/asos_daily_{stn_id}_{chunk_start}_{chunk_end}.json"
                )
            )

        start += delta
        time.sleep(1)

    # 월 단위 full 파일 저장
    full_filename = f"asos_daily_{stn_id}_{year}{month:02d}_full.json"
    save_json(year, month, stn_id, full_filename, all_items)

    # 중간 weekly 파일 삭제
    for path in weekly_files:
        if os.path.exists(path):
            os.remove(path)
            print(f"🗑 Removed weekly → {path}")

    print(f"✅ Completed Monthly Fetch: {year}-{month:02d}")


# --------------------------------------------------------------------
# 🚀 실행부 (크론에서 실행 가능)
# --------------------------------------------------------------------
if __name__ == "__main__":
    stn_id = "108"
    start_year = 2025
    start_month = 4

    today = datetime.now()
    current_year = today.year
    current_month = today.month

    # 과거 ~ 지난달까지 자동 확인 및 누락분 수집
    for year in range(start_year, current_year + 1):
        # 현재 연도는 지난달까지만
        max_month = 12 if year < current_year else current_month - 1

        for month in range(start_month, max_month + 1):
            # 월 단위 Full 파일 존재 여부 확인
            expected_full_file = os.path.join(
                RAW_WEATHER_DIR,
                f"{year}/{month:02d}/asos_daily_{stn_id}_{year}{month:02d}_full.json"
            )

            if not os.path.exists(expected_full_file):
                print(f"📡 Missing month → Fetching {year}-{month:02d}")
                fetch_asos_month_chunked(year, month, stn_id)
            else:
                print(f"✅ Exists: {expected_full_file}")

    print("🎉 Weather Extract Completed Successfully")
