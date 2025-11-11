"""
Smart Commute Weather Pipeline DAG
- Fetches weather data from Korea Meteorological Administration API
- Transforms and loads into PostgreSQL database
- Scheduled to run every 3 hours from 06:00 to 22:00
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
import subprocess
import sys
import os

# ============= Configuration =============
REPO_ROOT = "/opt/airflow"
SCRIPT_PATH = os.path.join(REPO_ROOT, "src")

default_args = {
    "owner": "smartcommute_team",
    "depends_on_past": False,
    "start_date": datetime(2025, 11, 1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ============= Helper Functions =============
def run_python_script(script_name: str, **context) -> None:
    """
    Execute a Python script from src/ directory
    
    Args:
        script_name: Name of the script (e.g., 'fetch_weather.py')
    """
    script_path = os.path.join(SCRIPT_PATH, script_name)
    
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    print(f"🚀 Executing: {script_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False,
            cwd=REPO_ROOT,
        )
        print(f"✅ {script_name} completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with exit code {e.returncode}")
        raise Exception(f"Task failed: {script_name}") from e


# ============= DAG Definition =============
with DAG(
    dag_id="smart_commute_weather_pipeline",
    default_args=default_args,
    description="Fetch, transform, and load weather data into PostgreSQL",
    schedule_interval="0 */3 6-22 * * *",  # Every 3 hours from 6 AM to 10 PM
    catchup=False,
    tags=["smartcommute", "weather", "production"],
    max_active_runs=1,  # Only one run at a time
    doc_md=__doc__,
) as dag:

    with TaskGroup("fetch_and_transform") as fetch_and_transform:
        """
        Stage 1: Fetch weather data from API and validate
        """
        fetch_weather_task = PythonOperator(
            task_id="fetch_weather",
            python_callable=run_python_script,
            op_kwargs={"script_name": "fetch_weather.py"},
            pool="default_pool",
            pool_slots=1,
        )

        transform_weather_task = PythonOperator(
            task_id="transform_weather",
            python_callable=run_python_script,
            op_kwargs={"script_name": "transform_weather.py"},
            pool="default_pool",
            pool_slots=1,
        )

        fetch_weather_task >> transform_weather_task

    load_to_db_task = PythonOperator(
        task_id="load_weather_to_db",
        python_callable=run_python_script,
        op_kwargs={"script_name": "load_to_db.py"},
        pool="default_pool",
        pool_slots=1,
    )

    # ============= Task Dependencies =============
    fetch_and_transform >> load_to_db_task
