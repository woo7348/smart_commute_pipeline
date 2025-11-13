"""
fetch_weather.py
-----------------
기상청 ASOS(종관기상관측) 일별 데이터를 수집하는 스크립트.
- 매달 1일 오후 2시에 자동 호출되어 지난달 1일~말일까지의 데이터를 가져옴.
- 각 주간 데이터를 raw 폴더에 개별 JSON으로 저장한 뒤, 최종적으로 한 달치 데이터를 병합.

Author : MinWoo Kang
Project: Smart Commute Pipeline
"""

import os
import requests
import json
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta

# --------------------------------------------------------------------
# ✅ 환경 변수 및 API 기본 설정
# --------------------------------------------------------------------
load_dotenv()
SERVICE_KEY = os.getenv("WEATHER_API_KEY")
if not SERVICE_KEY:
    raise ValueError("❌ WEATHER_API_KEY not found in .env file")

BASE_URL = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"

# --------------------------------------------------------------------
# ✅ 1️⃣ 안전한 요청 함수 (재시도 + 지연 포함)
# --------------------------------------------------------------------
def safe_request(params, max_retries=3, delay=5):
    """요청 실패 시 자동 재시도 + 지연"""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(BASE_URL, params=params, timeout=(5, 60))
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            print(f"⏳ Timeout on attempt {attempt}/{max_retries}. Retrying in {delay}s...")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed on attempt {attempt}/{max_retries}: {e}")
        time.sleep(delay)
    print("❌ All retry attempts failed.")
    return None

# --------------------------------------------------------------------
# ✅ 2️⃣ 단일 구간 데이터 요청 함수
# --------------------------------------------------------------------
def fetch_asos_daily(start_date, end_date, stn_id="108"):
    """기상청 ASOS 일별 데이터 수집 및 저장 (주간 단위)"""
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

    print(f"📡 Requesting ASOS Daily data ({start_date} ~ {end_date}, stn={stn_id})")
    response = safe_request(params)

    if not response:
        print(f"❌ Skipping period ({start_date} ~ {end_date}) due to repeated failures.")
        return None

    data = response.json()
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

    if not items:
        print("⚠️ No data found for given date range or station ID.")
        return None

    os.makedirs("raw", exist_ok=True)
    filepath = f"raw/{filename}"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved ASOS daily data → {filepath}")
    return items

# --------------------------------------------------------------------
# ✅ 3️⃣ 월 단위 데이터 병합 함수 (주 단위 분할 호출)
# --------------------------------------------------------------------
def fetch_asos_month_chunked(year, month, stn_id="108"):
    """한 달 데이터를 주 단위로 분할 요청 후 병합 저장 + 중간 파일 자동 삭제"""
    start = datetime(year, month, 1)
    end = (start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    all_items = []             # 전체 데이터를 담을 리스트
    saved_files = []           # ✅ 여기서 반드시 초기화 (중간파일 경로 저장용)
    delta = timedelta(days=7)  # 7일 간격

    while start <= end:
        chunk_start = start.strftime("%Y%m%d")
        chunk_end = min(start + delta - timedelta(days=1), end).strftime("%Y%m%d")

        print(f"📅 Fetching chunk: {chunk_start} ~ {chunk_end}")
        items = fetch_asos_daily(chunk_start, chunk_end, stn_id)

        if items:
            all_items.extend(items)
            filename = f"raw/asos_daily_{stn_id}_{chunk_start}_{chunk_end}.json"
            saved_files.append(filename)  # ✅ 파일 경로 누적 저장

        time.sleep(2)
        start += delta

    # ✅ 병합 및 중간파일 삭제
    if all_items:
        os.makedirs("raw", exist_ok=True)
        merged_path = f"raw/asos_daily_{stn_id}_{year}{month:02d}_full.json"

        with open(merged_path, "w", encoding="utf-8") as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)

        print(f"✅ Merged {len(all_items)} records → {merged_path}")

        # 🧹 주간 파일 자동 삭제
        for fpath in saved_files:
            if os.path.exists(fpath):
                os.remove(fpath)
                print(f"🗑️ Removed intermediate file → {fpath}")
            else:
                print(f"⚠️ Skipped (not found): {fpath}")
    else:
        print("⚠️ No data collected for the month.")

# --------------------------------------------------------------------
# ✅ 4️⃣ 실행부
# --------------------------------------------------------------------
if __name__ == "__main__":
    stn_id = "108"
    start_year = 2025
    start_month = 4

    # 현재 날짜 기준으로 데이터 확인
    today = datetime.now()
    current_year = today.year
    current_month = today.month

    # 비어있는 달 확인 및 사용자 입력
for year in range(start_year, current_year + 1):
    # 현재 연도인지에 따라 '최대 월'을 다르게 설정
    if year < current_year:
        max_month = 12                 # 과거 연도는 12월까지 다 확인
    else:
        max_month = current_month - 1  # 현재 연도는 '지난달'까지만 확인

    for month in range(start_month, max_month + 1):
        # 📌 year == current_year일 때 month는 1 ~ (current_month-1) 만 포함됨
        last_month_file = f"raw/asos_daily_{stn_id}_{year}{month:02d}_full.json"

        if not os.path.exists(last_month_file):
            print(f"⚠️ {year}-{month:02d} 데이터가 없습니다.")
            user_input = input(
                f"{year}-{month:02d}의 데이터를 호출하시겠습니까? (Y/N): "
            ).strip().upper()
            if user_input == 'Y':
                fetch_asos_month_chunked(year=year, month=month, stn_id=stn_id)
        else:
            print(f"✅ {year}-{month:02d} 데이터가 이미 존재합니다.")

    # 마지막으로 지난달 데이터 호출
    last_month = today.month - 1 if today.month > 1 else 12
    last_year = today.year if today.month > 1 else today.year - 1
    last_month_file = f"raw/asos_daily_{stn_id}_{last_year}{last_month:02d}_full.json"

    if os.path.exists(last_month_file):
        print(f"📅 지난달 데이터가 이미 존재합니다: {last_year}-{last_month:02d}.")
    else:
        print(f"📅 지난달 데이터 호출 중: {last_year}-{last_month:02d}.")
        fetch_asos_month_chunked(year=last_year, month=last_month, stn_id=stn_id)