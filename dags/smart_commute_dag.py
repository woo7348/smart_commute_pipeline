"""
Legacy Smart Commute Pipeline DAG (Deprecated)
Use `smart_commute_unified_dag.py` instead for better structure and monitoring.

This DAG is kept for backward compatibility.
Scheduled to run every 30 minutes during morning commute (06:00-10:00).
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
    "start_date": datetime(2025, 11, 4),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def run_python_script(script_name: str, **context) -> None:
    """Execute a Python script from src/ directory"""
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


with DAG(
    dag_id="smart_commute_pipeline",
    default_args=default_args,
    description="[DEPRECATED] Legacy unified pipeline - use smart_commute_unified_pipeline instead",
    schedule_interval="*/30 6-10 * * *",
    catchup=False,
    tags=["smartcommute", "legacy"],
    max_active_runs=1,
    doc_md=__doc__,
) as dag:

    fetch_weather = PythonOperator(
        task_id="fetch_weather",
        python_callable=run_python_script,
        op_kwargs={"script_name": "fetch_weather.py"},
    )

    fetch_bus = PythonOperator(
        task_id="fetch_bus",
        python_callable=run_python_script,
        op_kwargs={"script_name": "fetch_bus_seoul.py"},
    )

    transform_merge = PythonOperator(
        task_id="transform_merge",
        python_callable=run_python_script,
        op_kwargs={"script_name": "transform_merge.py"},
    )

    load_to_db = PythonOperator(
        task_id="load_to_db",
        python_callable=run_python_script,
        op_kwargs={"script_name": "load_to_db.py"},
    )

    fetch_weather >> fetch_bus >> transform_merge >> load_to_db
 
