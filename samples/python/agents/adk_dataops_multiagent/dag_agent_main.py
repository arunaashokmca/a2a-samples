import click

from common_server import serve_agent
from dag_agent import root_agent


@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=10102)
def main(host: str, port: int):
    serve_agent(
        root_agent,
        host=host,
        port=port,
        skill_id='dag-jinja-generator',
        skill_name='Airflow DAG Generator',
        skill_description='Creates DAG files from Jinja templates for ingestion jobs.',
    )


if __name__ == '__main__':
    main()
