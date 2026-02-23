import asyncio

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import ADKRunnerAgentExecutor
from orchestrator_agent import DataOpsOrchestrator


@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=10100)
@click.option(
    '--remote-agent',
    'remote_agents',
    multiple=True,
    help='Remote A2A agent URLs; pass multiple times.',
)
def main(host: str, port: int, remote_agents: tuple[str, ...]):
    remote_list = list(remote_agents) or [
        'http://localhost:10101',
        'http://localhost:10102',
        'http://localhost:10103',
    ]
    orchestrator = DataOpsOrchestrator(remote_list)
    asyncio.run(orchestrator.startup())
    root_agent = orchestrator.create_agent()

    card = AgentCard(
        name='dataops_orchestrator_agent',
        description=root_agent.description,
        url=f'http://{host}:{port}',
        version='1.0.0',
        defaultInputModes=['text', 'text/plain'],
        defaultOutputModes=['text', 'text/plain'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id='dataops-coordinator',
                name='DataOps Coordinator',
                description=(
                    'Greets customers, delegates work to config/dag/audit sub-agents'
                    ' using A2A, and supports HITL approvals.'
                ),
                tags=['orchestration', 'hitl', 'a2a'],
            )
        ],
    )

    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=DefaultRequestHandler(
            agent_executor=ADKRunnerAgentExecutor(root_agent),
            task_store=InMemoryTaskStore(),
        ),
    )
    uvicorn.run(app.build(), host=host, port=port)


if __name__ == '__main__':
    main()
