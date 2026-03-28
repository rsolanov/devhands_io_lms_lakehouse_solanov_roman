"""
Вспомогательный DAG для проверки состояния инфраструктуры платформы.
"""
from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "platform-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 0,
}

with DAG(
    dag_id="platform_healthcheck",
    default_args=default_args,
    description="Проверка доступности Trino и MinIO",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    tags=["platform", "healthcheck"],
) as dag:

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    check_trino = BashOperator(
        task_id="check_trino",
        bash_command=(
            'curl -sf -H "X-Trino-User: admin" http://trino-coordinator:8080/v1/info '
            '| python3 -c "'
            'import sys,json; '
            'd=json.load(sys.stdin); '
            'print(\'Trino OK, starting:\', d.get(\'starting\')); '
            'exit(0 if not d.get(\'starting\') else 1)'
            '"'
        ),
    )

    check_minio = BashOperator(
        task_id="check_minio",
        bash_command="curl -sf http://minio:9000/minio/health/live && echo 'MinIO OK'",
    )

    start >> [check_trino, check_minio] >> end