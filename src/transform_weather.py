import json
import pandas as pd
import numpy as np
import os

input_path = "raw/asos_daily_108_202506_full.json"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# JSON 로드
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# ✅ 필요한 컬럼만 선택
cols = ["tm", "avgTa", "maxTa", "minTa", "sumRn", "avgWs", "maxWs", "avgRhm", "ssDur"]
df = df[cols]

# ✅ 컬럼명 변경
df.rename(columns={
    "tm": "date",
    "avgTa": "avg_temp",
    "maxTa": "max_temp",
    "minTa": "min_temp",
    "sumRn": "rainfall",
    "avgWs": "avg_wind",
    "maxWs": "max_wind",
    "avgRhm": "humidity",
    "ssDur": "sunshine"
}, inplace=True)

# ✅ 문자열 → 숫자 변환
numeric_cols = ["avg_temp", "max_temp", "min_temp", "rainfall", "avg_wind", "max_wind", "humidity", "sunshine"]
df[numeric_cols] = df[numeric_cols].replace("", np.nan).astype(float)

# ✅ 날짜형 변환
df["date"] = pd.to_datetime(df["date"])

# ✅ CSV 저장
output_path = os.path.join(output_dir, "asos_seoul_202506_clean.csv")
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"✅ Clean CSV saved → {output_path}")
print(df.head())
