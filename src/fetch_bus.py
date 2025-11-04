import requests, json, os, datetime, logging

API_KEY = os.getenv("BUS_API_KEY")
BASE_URL = "https://api.data.go.kr/bus/arrivalInfo"  # 예시용 엔드포인트

def fetch_bus(route_id="100"):
    params = {"serviceKey": API_KEY, "routeId": route_id}
    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()
    data = r.json()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    os.makedirs("raw", exist_ok=True)
    with open(f"raw/bus_{ts}.json", "w") as f:
        json.dump(data, f)
    logging.info(f"Bus data saved: {ts}")
    return data

if __name__ == "__main__":
    logging.basicConfig(filename="logs/data_ingestion.log", level=logging.INFO)
    fetch_bus()
