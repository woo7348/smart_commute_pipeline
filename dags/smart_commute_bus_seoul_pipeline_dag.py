"""
Smart Commute Seoul Bus Pipeline DAG
- Fetches real-time bus arrival information from Seoul Open Data API
- Transforms and loads into PostgreSQL database
- Scheduled to run during peak commute hours (06:00-10:00)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
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
    "retry_delay": timedelta(minutes=3),
}

# ============= Helper Functions =============
def run_python_script(script_name: str, **context) -> None:
    """
    Execute a Python script from src/ directory
    
    Args:
        script_name: Name of the script (e.g., 'fetch_bus_seoul.py')
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
    dag_id="smart_commute_bus_seoul_pipeline",
    default_args=default_args,
    description="Fetch, transform, and load Seoul bus data into PostgreSQL",
    schedule_interval="*/15 6-10 * * MON-FRI",  # Every 15 mins, 6-10 AM, weekdays only
    catchup=False,
    tags=["smartcommute", "bus_seoul", "production"],
    max_active_runs=1,
    doc_md=__doc__,
) as dag:

    with TaskGroup("bus_data_pipeline") as bus_data_pipeline:
        """
        Stage 1: Fetch Seoul bus data and transform
        """
        fetch_bus_task = PythonOperator(
            task_id="fetch_bus_seoul",
            python_callable=run_python_script,
            op_kwargs={"script_name": "fetch_bus_seoul.py"},
            pool="default_pool",
            pool_slots=1,
        )

        transform_bus_task = PythonOperator(
            task_id="transform_bus_seoul",
            python_callable=run_python_script,
            op_kwargs={"script_name": "transform_bus_seoul.py"},
            pool="default_pool",
            pool_slots=1,
        )

        load_bus_task = PythonOperator(
            task_id="load_bus_seoul",
            python_callable=run_python_script,
            op_kwargs={"script_name": "load_bus_seoul.py"},
            pool="default_pool",
            pool_slots=1,
        )

        fetch_bus_task >> transform_bus_task >> load_bus_task

    # ============= Task Dependencies =============
    bus_data_pipeline
