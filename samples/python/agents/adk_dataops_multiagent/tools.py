DAG_TEMPLATE = """from airflow import DAG
from airflow.providers.google.cloud.transfers.sql_to_gcs import SQLToGCSOperator
from datetime import datetime

with DAG(
    dag_id="{{ dag_id }}",
    start_date=datetime(2024, 1, 1),
    schedule="{{ schedule }}",
    catchup=False,
    tags=["data-movement", "rdbms", "gcs"],
) as dag:
    export_task = SQLToGCSOperator(
        task_id="extract_{{ source_table }}",
        sql_conn_id="{{ sql_conn_id }}",
        sql="SELECT * FROM {{ source_table }}",
        bucket="{{ gcs_bucket }}",
        filename="{{ destination_path }}/{{ source_table }}_{{ ds_nodash }}.parquet",
        export_format="parquet",
    )
"""


NULL_RATIO_THRESHOLD = 0.05
DUPLICATE_RATIO_THRESHOLD = 0.01
FRESHNESS_SLA_MINUTES = 90


def build_rdbms_to_gcs_config(
    source_rdbms: str,
    source_table: str,
    gcs_bucket: str,
    destination_path: str,
    load_mode: str = 'incremental',
    watermark_column: str = 'updated_at',
) -> dict:
    return {
        'source': {
            'type': 'rdbms',
            'connection_secret': f'projects/<project>/secrets/{source_rdbms}-conn',
            'table': source_table,
            'watermark_column': watermark_column,
        },
        'sink': {
            'type': 'gcs',
            'bucket': gcs_bucket,
            'path': destination_path,
            'format': 'parquet',
        },
        'pipeline': {
            'load_mode': load_mode,
            'retry_count': 3,
            'max_batch_rows': 250000,
        },
    }


def create_airflow_dag(
    dag_id: str,
    source_table: str,
    sql_conn_id: str,
    gcs_bucket: str,
    destination_path: str,
    schedule: str = '@daily',
) -> str:
    rendered = DAG_TEMPLATE
    replacements = {
        "{{ dag_id }}": dag_id,
        "{{ source_table }}": source_table,
        "{{ sql_conn_id }}": sql_conn_id,
        "{{ gcs_bucket }}": gcs_bucket,
        "{{ destination_path }}": destination_path,
        "{{ schedule }}": schedule,
    }
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    return rendered


def audit_data_movement(
    extracted_rows: int,
    loaded_rows: int,
    null_ratio: float,
    duplicate_ratio: float,
    freshness_minutes: int,
) -> dict:
    row_match = extracted_rows == loaded_rows
    quality_pass = (
        null_ratio < NULL_RATIO_THRESHOLD
        and duplicate_ratio < DUPLICATE_RATIO_THRESHOLD
    )
    freshness_pass = freshness_minutes <= FRESHNESS_SLA_MINUTES
    overall = row_match and quality_pass and freshness_pass

    return {
        'status': 'pass' if overall else 'fail',
        'checks': {
            'row_count_match': row_match,
            'quality_thresholds': quality_pass,
            'freshness_sla': freshness_pass,
        },
        'recommendation': (
            'Pipeline healthy. Proceed to downstream consumption.'
            if overall
            else 'Hold release and investigate failed checks before downstream publish.'
        ),
    }
