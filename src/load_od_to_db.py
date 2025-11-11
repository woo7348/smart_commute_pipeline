import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ✅ 환경변수 불러오기 (.env에서)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "commute_db")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASS = os.getenv("DB_PASS", "airflow")
DB_PORT = os.getenv("DB_PORT", "5432")

OUTPUT_DIR = "output"

def load_od_to_db(opr_ym="202404"):
    csv_path = os.path.join(OUTPUT_DIR, f"od_monthly_{opr_ym}_processed.csv")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"❌ File not found: {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} rows from {csv_path}")

    # ✅ DB 연결
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cur = conn.cursor()

    # ✅ 테이블 생성
    cur.execute("""
        CREATE TABLE IF NOT EXISTS od_bus_rail (
            id SERIAL PRIMARY KEY,
            opr_ym VARCHAR(6),
            dptre_ctpv_nm VARCHAR(50),
            dptre_sgg_nm VARCHAR(50),
            dptre_emd_nm VARCHAR(50),
            arvl_ctpv_nm VARCHAR(50),
            arvl_sgg_nm VARCHAR(50),
            arvl_emd_nm VARCHAR(50),
            trfvlm INT,
            pasg_hr_sum INT,
            pasg_dstnc_sum INT
        );
    """)
    conn.commit()

    # ✅ 데이터 삽입
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO od_bus_rail (
                opr_ym, dptre_ctpv_nm, dptre_sgg_nm, dptre_emd_nm,
                arvl_ctpv_nm, arvl_sgg_nm, arvl_emd_nm,
                trfvlm, pasg_hr_sum, pasg_dstnc_sum
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """, (
            row.get("opr_ym"),
            row.get("dptre_ctpv_nm"),
            row.get("dptre_sgg_nm"),
            row.get("dptre_emd_nm"),
            row.get("arvl_ctpv_nm"),
            row.get("arvl_sgg_nm"),
            row.get("arvl_emd_nm"),
            int(row.get("trfvlm", 0)),
            int(row.get("pasg_hr_sum", 0)),
            int(row.get("pasg_dstnc_sum", 0))
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ od_bus_rail table successfully updated.")

if __name__ == "__main__":
    load_od_to_db()
