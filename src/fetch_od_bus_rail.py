import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
SERVICE_KEY = os.getenv("OD_API_KEY")

BASE_URL = "https://apis.data.go.kr/1613000/ODUsageforGeneralBusesandUrbanRailways/getDailyODUsageforGeneralBusesandUrbanRailways"


def fetch_od_daily(opr_ymd, dptre_ctpv_cd="11", dptre_sgg_cd="11110", arvl_ctpv_cd="11", arvl_sgg_cd="11680"):
    """일자별 API 호출"""
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": "1",
        "numOfRows": "100",
        "opr_ymd": opr_ymd,
        "dptre_ctpv_cd": dptre_ctpv_cd,
        "dptre_sgg_cd": dptre_sgg_cd,
        "arvl_ctpv_cd": arvl_ctpv_cd,
        "arvl_sgg_cd": arvl_sgg_cd,
        "dataType": "JSON"
    }

    response = requests.get(BASE_URL, params=params)
    os.makedirs("raw/tmp", exist_ok=True)

    try:
        data = response.json()
        if "Response" in data and "body" in data["Response"]:
            items = data["Response"]["body"].get("items", {}).get("item", [])
            filename = f"raw/tmp/od_{opr_ymd}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False)
            print(f"✅ {opr_ymd}: {len(items)} records")
            return filename
        else:
            print(f"⚠️ {opr_ymd}: Unexpected response structure")
            return None
    except Exception as e:
        print(f"❌ {opr_ymd}: Error parsing JSON - {e}")
        return None


def merge_json_files(file_list, output_path):
    """여러 JSON 파일 병합"""
    all_items = []
    for file in file_list:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_items.extend(data)
        except Exception as e:
            print(f"⚠️ Skipped {file}: {e}")

    if not all_items:
        print(f"⚠️ No data to save for {output_path}")
        return None

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print(f"💾 Merged {len(all_items)} records → {output_path}")
    return output_path


def fetch_od_monthly_final(year=2025, month=4, chunk_size=10, **kwargs):
    """10일 단위로 임시 병합 후 마지막에 월 전체 병합"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    current_date = start_date
    tmp_files = []
    chunk_files = []
    chunk_start = current_date.strftime("%Y%m%d")

    while current_date <= end_date:
        opr_ymd = current_date.strftime("%Y%m%d")
        f = fetch_od_daily(opr_ymd, **kwargs)
        if f:
            tmp_files.append(f)

        # 10일 단위 또는 마지막 날짜 도달 시 병합
        if len(tmp_files) == chunk_size or current_date == end_date:
            chunk_end = opr_ymd
            os.makedirs("raw", exist_ok=True)
            chunk_path = f"raw/od_{chunk_start}_to_{chunk_end}.json"
            merge_json_files(tmp_files, chunk_path)
            chunk_files.append(chunk_path)

            # 임시 개별 파일 삭제
            for tf in tmp_files:
                try:
                    os.remove(tf)
                except Exception:
                    pass
            tmp_files = []

            if current_date + timedelta(days=1) <= end_date:
                chunk_start = (current_date + timedelta(days=1)).strftime("%Y%m%d")

        current_date += timedelta(days=1)

    # ✅ 마지막: 월 전체 병합
    final_path = f"raw/od_{year}{month:02d}_all.json"
    merge_json_files(chunk_files, final_path)

    # 중간 병합 파일 삭제
    for cf in chunk_files:
        try:
            os.remove(cf)
        except Exception:
            pass

    print(f"🌕 Final monthly JSON created: {final_path}")
    print("🧹 Cleaned up intermediate chunk files.")


if __name__ == "__main__":
    # 데이터가 이미 존재하는지 확인
    start_year = 2025
    start_month = 4

    # 현재 날짜 기준으로 데이터 확인
    today = datetime.now()
    current_year = today.year
    current_month = today.month

    empty_months = []

    # ------------------------------------------------------------------
    # 🔍 1) 비어있는 달 확인 (백필용)
    #
    #  - start_year/start_month 부터 "완료된 달(지난달)"까지 확인
    #  - 현재 연도는 current_month - 1(지난달)까지만 검사
    # ------------------------------------------------------------------
    for year in range(start_year, current_year + 1):

        # 해당 연도에서 시작 월 결정
        if year == start_year:
            start_m = start_month      # 첫 해는 지정한 start_month부터
        else:
            start_m = 1                # 이후 연도는 1월부터

        # 해당 연도에서 검사할 마지막 월 결정
        if year < current_year:
            max_month = 12             # 과거 연도는 12월까지
        else:
            max_month = current_month - 1  # 올해는 "지난달"까지만

        # 올해가 1월인 경우 current_month - 1 == 0 이 될 수 있음 → 스킵
        if max_month < 1:
            continue

        for month in range(start_m, max_month + 1):
            last_month_file = f"raw/od_{year}{month:02d}_all.json"
            if not os.path.exists(last_month_file):
                print(f"⚠️ {year}-{month:02d} 데이터가 없습니다.")
                empty_months.append((year, month))

    # 비어있는 달에 대한 사용자 입력
    if empty_months:
        print("다음 달의 데이터가 비어 있습니다:")
        for year, month in empty_months:
            print(f"- {year}-{month:02d}")

        user_input = input("이 달들의 데이터를 호출하시겠습니까? (Y/N): ").strip().upper()
        if user_input == 'Y':
            for year, month in empty_months:
                fetch_od_monthly_final(year=year, month=month)
    else:
        print("모든 데이터가 존재합니다.")


    # ------------------------------------------------------------------
    # 📅 3) 마지막으로 '지난달' 데이터 자동 호출 (운영/배치용)
    #
    #  - 오늘이 2025-11-13 이면 → last_month = 10 (10월)
    #  - 오늘이 2025-01-10 이면 → last_month = 12, last_year = 2024
    # ------------------------------------------------------------------
    if today.month > 1:
        last_month = today.month - 1
        last_year = today.year
    else:
        last_month = 12
        last_year = today.year - 1

    last_month_file = f"raw/od_{last_year}{last_month:02d}_all.json"

    if os.path.exists(last_month_file):
        print(f"📅 지난달 데이터가 이미 존재합니다: {last_year}-{last_month:02d}.")
    else:
        print(f"📅 지난달 데이터 호출 중: {last_year}-{last_month:02d}.")
        fetch_od_monthly_final(year=last_year, month=last_month)