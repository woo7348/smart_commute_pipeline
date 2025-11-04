import os
import requests
import json
import datetime
from dotenv import load_dotenv

load_dotenv()
SERVICE_KEY = os.getenv("WEATHER_API_KEY")

BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

def fetch_weather(nx=60, ny=127):
    now = datetime.datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = "0500"  # 새벽 예보 기준 (테스트용)

    params = {
        "serviceKey": SERVICE_KEY,  # 인코딩 없이 원본 값 사용
        "numOfRows": 1000,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny
    }

    response = requests.get(BASE_URL, params=params)
    print("📡 Request URL:", response.url)
    response.raise_for_status()
    data = response.json()

    os.makedirs("raw", exist_ok=True)
    filepath = f"raw/weather_{base_date}_{base_time}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved weather data to {filepath}")
    return data

if __name__ == "__main__":
    fetch_weather()