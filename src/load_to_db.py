import psycopg2
import pandas as pd
import os

def load_to_db():
    conn = psycopg2.connect(
        host="localhost",
        dbname="airflow",
        user="airflow",
        password="airflow"
    )
    cur = conn.cursor()
    df = pd.read_csv("output/joined_sample.csv")

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO joined_analysis (route_id, station_id, temperature, rainfall, delay_rate)
            VALUES (%s, %s, %s, %s, %s)
        """, (row.route_id, row.station_id, row.temperature, row.rainfall, row.delay_rate))

    conn.commit()
    conn.close()
    print("✅ Data loaded to Postgres")

if __name__ == "__main__":
    load_to_db()
