import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# .env에서 DB 접속정보 불러오기
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "commute_db")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASS = os.getenv("DB_PASS", "airflow")
DB_PORT = os.getenv("DB_PORT", "5432")

def load_weather_to_db(csv_path="output/asos_seoul_202505_clean.csv"):
    # 1️⃣ CSV 읽기
    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} rows from {csv_path}")

    # 2️⃣ DB 연결
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cur = conn.cursor()

    # 3️⃣ 테이블 생성 (없을 경우)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            fcstDate VARCHAR(8),
            fcstTime VARCHAR(4),
            TMP FLOAT,
            POP FLOAT,
            WSD FLOAT,
            REH FLOAT,
            SKY FLOAT
        )
    """)
    conn.commit()

    # 4️⃣ CSV → DB 적재
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO weather_data (fcstDate, fcstTime, TMP, POP, WSD, REH, SKY)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            str(row.get("fcstDate")),
            str(row.get("fcstTime")),
            float(row.get("TMP", 0)),
            float(row.get("POP", 0)),
            float(row.get("WSD", 0)),
            float(row.get("REH", 0)),
            float(row.get("SKY", 0)),
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Weather data successfully loaded into PostgreSQL.")

if __name__ == "__main__":
    load_weather_to_db()
