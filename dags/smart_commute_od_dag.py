from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 11, 5),
    "retries": 1
}

with DAG(
    dag_id="smart_commute_od_dag",
    default_args=default_args,
    schedule_interval="@monthly",
    catchup=False,
    tags=["od", "bus", "rail"]
) as dag:

    fetch_od = BashOperator(
        task_id="fetch_od",
        bash_command="python /opt/airflow/src/fetch_od_bus_rail.py"
    )

    transform_od = BashOperator(
        task_id="transform_od",
        bash_command="python /opt/airflow/src/transform_od_bus_rail.py"
    )

    load_od = BashOperator(
        task_id="load_od",
        bash_command="python /opt/airflow/src/load_od_to_db.py"
    )

    fetch_od >> transform_od >> load_od
