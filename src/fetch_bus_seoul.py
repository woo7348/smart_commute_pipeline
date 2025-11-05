import os
import requests
import xml.etree.ElementTree as ET
import json
from dotenv import load_dotenv

load_dotenv()
SERVICE_KEY = os.getenv("SEOUL_BUS_API_KEY")

BASE_URL = "http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute"

# 테스트용 정류소 ID (예: 서울역 버스정류소)
STOP_ID = "115000112"

def fetch_bus_data():
    if not SERVICE_KEY:
        raise ValueError("❌ SEOUL_BUS_API_KEY not found in .env file")

    params = {
        "serviceKey": SERVICE_KEY,
        "stId": STOP_ID
    }

    response = requests.get(BASE_URL, params=params)
    print("📡 Request URL:", response.url)
    response.raise_for_status()

    # XML → 파싱
    root = ET.fromstring(response.text)
    items = root.findall(".//itemList")

    records = []
    for item in items:
        record = {
            "route_name": item.findtext("rtNm"),
            "bus_type": item.findtext("busType1"),
            "station_name": item.findtext("stNm"),
            "arrmsg1": item.findtext("arrmsg1"),
            "arrmsg2": item.findtext("arrmsg2"),
            "plain_no": item.findtext("plainNo1"),
            "veh_id": item.findtext("vehId1")
        }
        records.append(record)

    os.makedirs("raw", exist_ok=True)
    filepath = "raw/bus_seoul_raw.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(records)} records to {filepath}")
    return records


if __name__ == "__main__":
    fetch_bus_data()