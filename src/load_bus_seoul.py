import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "airflow")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASS = os.getenv("DB_PASS", "airflow")
DB_PORT = os.getenv("DB_PORT", "5432")

def load_bus_to_db():
    df = pd.read_csv("output/bus_seoul_processed.csv")
    print(f"📊 Loaded {len(df)} rows from output/bus_seoul_processed.csv")

    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bus_seoul_data (
            id SERIAL PRIMARY KEY,
            route_name VARCHAR(100),
            bus_type VARCHAR(50),
            station_name VARCHAR(100),
            arrmsg1 VARCHAR(100),
            arrmsg2 VARCHAR(100),
            plain_no VARCHAR(50),
            veh_id VARCHAR(50)
        );
    """)

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO bus_seoul_data (route_name, bus_type, station_name, arrmsg1, arrmsg2, plain_no, veh_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (row.route_name, row.bus_type, row.station_name, row.arrmsg1, row.arrmsg2, row.plain_no, row.veh_id))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Bus data successfully loaded into PostgreSQL.")

if __name__ == "__main__":
    load_bus_to_db()
