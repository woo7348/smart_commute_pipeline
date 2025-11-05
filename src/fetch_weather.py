import os
import requests
import json
import datetime
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 환경 변수에서 API 키 로드
SERVICE_KEY = os.getenv("WEATHER_API_KEY")

if not SERVICE_KEY:
    raise ValueError("❌ WEATHER_API_KEY not found in .env file")

BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"


def fetch_weather(nx=60, ny=127):
    """기상청 단기예보 API에서 날씨 데이터를 가져와 JSON 파일로 저장"""

    now = datetime.datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = "0500"  # 새벽 기준 예보 시간 (테스트용)

    params = {
        "serviceKey": SERVICE_KEY,  # 인코딩하지 않고 원본 그대로 사용
        "numOfRows": 1000,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    print(f"📡 Requesting weather data for {base_date} {base_time} (nx={nx}, ny={ny})")
    response = requests.get(BASE_URL, params=params)
    print("📡 Request URL:", response.url)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to fetch weather data: {e}")
        print(f"Response text: {response.text[:500]}")  # 일부만 출력
        raise

    data = response.json()

    # raw 폴더 생성 (Airflow 컨테이너에서도 작동)
    os.makedirs("/opt/airflow/raw", exist_ok=True)
    filepath = f"/opt/airflow/raw/weather_{base_date}_{base_time}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved weather data to {filepath}")
    return data


if __name__ == "__main__":
    fetch_weather()
