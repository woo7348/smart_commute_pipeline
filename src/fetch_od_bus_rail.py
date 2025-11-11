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
    # 예시: 2025년 11월 데이터 전부 수집 후 월 전체 병합 JSON만 남김
    fetch_od_monthly_final(year=2025, month=4)
