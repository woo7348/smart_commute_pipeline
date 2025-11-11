"""
Smart Commute Unified Pipeline DAG
- Combines weather and bus data
- Runs merge transformation and final load
- Orchestrates multi-source data pipeline
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.operators.bash import BashOperator
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
    dag_id="smart_commute_unified_pipeline",
    default_args=default_args,
    description="Unified weather + bus data pipeline with merge and analysis",
    schedule_interval="0 11 * * *",  # Daily at 11:00 AM (after morning commute)
    catchup=False,
    tags=["smartcommute", "unified", "analysis"],
    max_active_runs=1,
    doc_md=__doc__,
) as dag:

    with TaskGroup("data_ingestion") as data_ingestion:
        """
        Stage 1: Parallel fetch of weather and bus data
        """
        fetch_weather = PythonOperator(
            task_id="fetch_weather",
            python_callable=run_python_script,
            op_kwargs={"script_name": "fetch_weather.py"},
        )

        fetch_bus_seoul = PythonOperator(
            task_id="fetch_bus_seoul",
            python_callable=run_python_script,
            op_kwargs={"script_name": "fetch_bus_seoul.py"},
        )

        # Both can run in parallel
        [fetch_weather, fetch_bus_seoul]

    with TaskGroup("data_transformation") as data_transformation:
        """
        Stage 2: Transform individual datasets
        """
        transform_weather = PythonOperator(
            task_id="transform_weather",
            python_callable=run_python_script,
            op_kwargs={"script_name": "transform_weather.py"},
        )

        transform_bus = PythonOperator(
            task_id="transform_bus_seoul",
            python_callable=run_python_script,
            op_kwargs={"script_name": "transform_bus_seoul.py"},
        )

        # Both can run in parallel
        [transform_weather, transform_bus]

    with TaskGroup("data_merge_and_load") as data_merge_and_load:
        """
        Stage 3: Merge datasets and load to database
        """
        merge_data = PythonOperator(
            task_id="transform_merge",
            python_callable=run_python_script,
            op_kwargs={"script_name": "transform_merge.py"},
        )

        load_to_database = PythonOperator(
            task_id="load_to_db",
            python_callable=run_python_script,
            op_kwargs={"script_name": "load_to_db.py"},
        )

        merge_data >> load_to_database

    # ============= Task Dependencies =============
    data_ingestion >> data_transformation >> data_merge_and_load
