import pandas as pd
import json, glob, os

def merge_data():
    weather_files = sorted(glob.glob("raw/weather_*.json"))
    bus_files = sorted(glob.glob("raw/bus_*.json"))

    if not weather_files or not bus_files:
        raise FileNotFoundError("No raw files found")

    weather = pd.read_json(weather_files[-1])
    bus = pd.read_json(bus_files[-1])

    # 간단한 병합 로직 (실제 API 스펙에 맞게 수정 필요)
    merged = pd.DataFrame({
        "route_id": bus["route_id"],
        "station_id": bus["station_id"],
        "temperature": weather["current"]["temp_c"],
        "rainfall": weather["current"]["precip_mm"],
        "delay_rate": bus["delay_seconds"].mean() / 60
    }, index=[0])

    os.makedirs("output", exist_ok=True)
    merged.to_csv("output/joined_sample.csv", index=False)
    print("✅ merged data saved to output/joined_sample.csv")

if __name__ == "__main__":
    merge_data()
