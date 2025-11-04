from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="smart_commute_pipeline",
    default_args=default_args,
    schedule_interval="*/30 6-10 * * *",
    start_date=datetime(2025, 11, 4),
    catchup=False,
    tags=["smartcommute"]
) as dag:

    fetch_weather = BashOperator(
        task_id="fetch_weather",
        bash_command="python /opt/airflow/src/fetch_weather.py"
    )

    fetch_bus = BashOperator(
        task_id="fetch_bus",
        bash_command="python /opt/airflow/src/fetch_bus.py"
    )

    transform_merge = BashOperator(
        task_id="transform_merge",
        bash_command="python /opt/airflow/src/transform_merge.py"
    )

    load_to_db = BashOperator(
        task_id="load_to_db",
        bash_command="python /opt/airflow/src/load_to_db.py"
    )

    fetch_weather >> fetch_bus >> transform_merge >> load_to_db
 