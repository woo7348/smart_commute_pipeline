import json
import pandas as pd
import os

def transform_bus_data():
    with open("raw/bus_seoul_raw.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("ServiceResult", {}).get("msgBody", {}).get("itemList", [])
    records = []

    for item in items:
        records.append({
            "route_name": item.get("rtNm"),
            "bus_type": item.get("busType"),
            "station_name": item.get("stNm"),
            "arrmsg1": item.get("arrmsg1"),
            "arrmsg2": item.get("arrmsg2"),
            "plain_no": item.get("plainNo1"),
            "veh_id": item.get("vehId1")
        })

    df = pd.DataFrame(records)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/bus_seoul_processed.csv", index=False)
    print("✅ Saved transformed data to output/bus_seoul_processed.csv")

if __name__ == "__main__":
    transform_bus_data()
