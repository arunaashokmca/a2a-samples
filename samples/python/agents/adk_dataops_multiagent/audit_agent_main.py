import click

from audit_agent import root_agent
from common_server import serve_agent


@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=10103)
def main(host: str, port: int):
    serve_agent(
        root_agent,
        host=host,
        port=port,
        skill_id='movement-audit',
        skill_name='Data Movement Audit',
        skill_description='Runs row count and basic data quality audits after movement.',
    )


if __name__ == '__main__':
    main()
