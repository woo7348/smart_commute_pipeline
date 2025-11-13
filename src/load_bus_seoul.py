import os
import sys
import json
import argparse
import logging
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# 환경설정
load_dotenv()

# 로깅 설정 (NiFi에서 추적 가능하도록)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# DB 연결정보
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "airflow")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASS = os.getenv("DB_PASS", "airflow")
DB_PORT = os.getenv("DB_PORT", "5432")

def load_bus_to_db(csv_path: str = "output/bus_seoul_processed.csv") -> dict:
    """
    버스 데이터를 PostgreSQL에 적재
    
    Args:
        csv_path: 입력 CSV 파일 경로
        
    Returns:
        dict: 실행 결과 (status, message, row_count, errors)
    """
    try:
        # 1️⃣ 파일 존재 여부 확인
        if not os.path.exists(csv_path):
            error_msg = f"File not found: {csv_path}"
            logger.error(error_msg)
            return {
                "status": "ERROR",
                "message": error_msg,
                "row_count": 0,
                "errors": [error_msg]
            }
        
        # 2️⃣ CSV 읽기
        logger.info(f"📂 Reading CSV from: {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"📊 Loaded {len(df)} rows")
        
        if len(df) == 0:
            warn_msg = "CSV file is empty"
            logger.warning(warn_msg)
            return {
                "status": "WARNING",
                "message": warn_msg,
                "row_count": 0,
                "errors": []
            }
        
        # 3️⃣ DB 연결
        logger.info(f"🔗 Connecting to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        logger.info("✅ Database connection established")
        
        # 4️⃣ 테이블 생성
        logger.info("📋 Creating table if not exists...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bus_seoul_data (
                id SERIAL PRIMARY KEY,
                route_name VARCHAR(100),
                bus_type VARCHAR(50),
                station_name VARCHAR(100),
                arrmsg1 VARCHAR(100),
                arrmsg2 VARCHAR(100),
                plain_no VARCHAR(50),
                veh_id VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        logger.info("✅ Table ready")
        
        # 5️⃣ 데이터 적재
        logger.info(f"📥 Inserting {len(df)} rows...")
        inserted_count = 0
        errors = []
        
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            try:
                cur.execute("""
                    INSERT INTO bus_seoul_data (route_name, bus_type, station_name, arrmsg1, arrmsg2, plain_no, veh_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(row.get("route_name", "")),
                    str(row.get("bus_type", "")),
                    str(row.get("station_name", "")),
                    str(row.get("arrmsg1", "")),
                    str(row.get("arrmsg2", "")),
                    str(row.get("plain_no", "")),
                    str(row.get("veh_id", ""))
                ))
                inserted_count += 1
                
                if idx % 100 == 0:
                    logger.info(f"  Progress: {idx}/{len(df)} rows inserted")
                    
            except Exception as e:
                error_msg = f"Row {idx} error: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Successfully inserted {inserted_count} rows")
        
        return {
            "status": "SUCCESS" if len(errors) == 0 else "PARTIAL_SUCCESS",
            "message": f"Loaded {inserted_count}/{len(df)} rows",
            "row_count": inserted_count,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Critical error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "ERROR",
            "message": error_msg,
            "row_count": 0,
            "errors": [error_msg],
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load bus data to PostgreSQL")
    parser.add_argument(
        "--input",
        type=str,
        default="output/bus_seoul_processed.csv",
        help="Input CSV file path"
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output result as JSON (for NiFi integration)"
    )
    
    args = parser.parse_args()
    
    result = load_bus_to_db(csv_path=args.input)
    
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    sys.exit(0 if result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"] else 1)
