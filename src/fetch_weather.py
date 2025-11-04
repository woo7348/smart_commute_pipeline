import requests, json, os, datetime, logging

API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.weatherapi.com/v1/current.json"

def fetch_weather(city="Seoul"):
    params = {"key": API_KEY, "q": city}
    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()
    data = r.json()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    os.makedirs("raw", exist_ok=True)
    with open(f"raw/weather_{ts}.json", "w") as f:
        json.dump(data, f)
    logging.info(f"Weather data saved: {ts}")
    return data

if __name__ == "__main__":
    logging.basicConfig(filename="logs/data_ingestion.log", level=logging.INFO)
    fetch_weather()
