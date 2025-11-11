from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
import sys

# 경로 등록 (src 폴더 인식)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# 각 단계의 Python 함수 가져오기
from fetch_weather import fetch_weather
from transform_weather import transform_weather
from load_to_db import load_weather_to_db

# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# DAG 정의
with DAG(
    dag_id='smart_commute_pipeline',
    default_args=default_args,
    description='Smart Commute Weather ETL Pipeline',
    schedule_interval=timedelta(hours=1),   # 매시간 실행
    start_date=datetime(2025, 11, 5),
    catchup=False,
    tags=['weather', 'etl', 'smart_commute']
) as dag:

    task_fetch = PythonOperator(
        task_id='fetch_weather_data',
        python_callable=fetch_weather
    )

    task_transform = PythonOperator(
        task_id='transform_weather_data',
        python_callable=transform_weather
    )

    task_load = PythonOperator(
        task_id='load_weather_to_db',
        python_callable=load_weather_to_db
    )

    # 실행 순서 정의
    task_fetch >> task_transform >> task_load
