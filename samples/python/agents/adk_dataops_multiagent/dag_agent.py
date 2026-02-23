from google.adk import Agent

from tools import create_airflow_dag


root_agent = Agent(
    name='dag_generator_agent',
    model='gemini-2.5-flash',
    description='Builds Airflow DAG files (via Jinja templates) for RDBMS to GCS pipelines.',
    instruction=(
        'You generate Airflow DAG code by calling create_airflow_dag.'
        ' Confirm the required DAG metadata first, then return the generated code.'
    ),
    tools=[create_airflow_dag],
)
