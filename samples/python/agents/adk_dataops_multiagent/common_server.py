import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import ADKRunnerAgentExecutor


def serve_agent(agent, *, host: str, port: int, skill_id: str, skill_name: str, skill_description: str):
    card = AgentCard(
        name=agent.name,
        description=agent.description,
        url=f'http://{host}:{port}',
        version='1.0.0',
        defaultInputModes=['text', 'text/plain'],
        defaultOutputModes=['text', 'text/plain'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id=skill_id,
                name=skill_name,
                description=skill_description,
                tags=['data-engineering', 'a2a', 'adk'],
            )
        ],
    )

    handler = DefaultRequestHandler(
        agent_executor=ADKRunnerAgentExecutor(agent=agent),
        task_store=InMemoryTaskStore(),
    )
    app = A2AStarletteApplication(agent_card=card, http_handler=handler)
    uvicorn.run(app.build(), host=host, port=port)
