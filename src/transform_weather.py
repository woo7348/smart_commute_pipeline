import json
import glob
import pandas as pd
import os

def transform_latest_weather():
    os.makedirs("output", exist_ok=True)

    # 1️⃣ 최신 raw 파일 선택
    files = sorted(glob.glob("raw/weather_*.json"))
    if not files:
        raise FileNotFoundError("No weather JSON files found in raw/")
    latest_file = files[-1]
    print(f"📂 Using latest file: {latest_file}")

    # 2️⃣ JSON 로드
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["response"]["body"]["items"]["item"]
    df = pd.DataFrame(items)

    # 3️⃣ 관심 변수만 선택
    df = df[["category", "fcstDate", "fcstTime", "fcstValue"]]

    # 4️⃣ pivot 변환 (행: 날짜/시간, 열: category)
    pivoted = df.pivot_table(
        index=["fcstDate", "fcstTime"],
        columns="category",
        values="fcstValue",
        aggfunc="first"
    ).reset_index()

    # 5️⃣ CSV 저장
    output_path = "output/weather_processed.csv"
    pivoted.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"✅ Transformed data saved: {output_path}")
    return pivoted


if __name__ == "__main__":
    df = transform_latest_weather()
    print(df.tail(5))  # 마지막 5행 출력
