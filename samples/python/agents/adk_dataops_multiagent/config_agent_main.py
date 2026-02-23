import click

from common_server import serve_agent
from config_agent import root_agent


@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=10101)
def main(host: str, port: int):
    serve_agent(
        root_agent,
        host=host,
        port=port,
        skill_id='config-rdbms-gcs',
        skill_name='RDBMS to GCS Config',
        skill_description='Prepares migration configuration for RDBMS to GCS ingestion.',
    )


if __name__ == '__main__':
    main()
