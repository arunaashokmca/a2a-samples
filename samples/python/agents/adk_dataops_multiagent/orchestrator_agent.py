import json
import os
import uuid

import httpx

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import (
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TextPart,
    TransportProtocol,
)
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext


class DataOpsOrchestrator:
    """Main ADK agent that greets users and delegates task work through A2A."""

    def __init__(self, remote_agent_addresses: list[str]):
        self.httpx_client = httpx.AsyncClient(timeout=30)
        config = ClientConfig(
            httpx_client=self.httpx_client,
            supported_transports=[TransportProtocol.jsonrpc, TransportProtocol.http_json],
        )
        self.client_factory = ClientFactory(config)
        self.cards = {}
        self.connections = {}
        self.remote_agent_addresses = remote_agent_addresses

    async def startup(self):
        for address in self.remote_agent_addresses:
            resolver = A2ACardResolver(self.httpx_client, address)
            card = await resolver.get_agent_card()
            self.cards[card.name] = card
            self.connections[card.name] = self.client_factory.create(card)

    def create_agent(self):
        model_name = os.getenv('LITELLM_MODEL', 'gemini/gemini-2.0-flash-001')
        return Agent(
            model=LiteLlm(model=model_name),
            name='dataops_orchestrator_agent',
            description='Greets user, clarifies needs, and orchestrates data movement sub-agents.',
            instruction=(
                'You are the main customer-facing coordinator. Greet users first, ask'
                ' clarifying questions, then delegate implementation to sub-agents via'
                ' tools. Before execution, call request_human_approval.'
                ' Use config_agent for ingestion config, dag_generator_agent for DAG code,'
                ' and audit_agent for audit checks.'
            ),
            tools=[
                self.list_remote_agents,
                self.request_human_approval,
                self.send_message,
                self.list_mcp_tooling_ideas,
            ],
        )

    def list_remote_agents(self):
        """Lists available sub-agents registered over A2A."""
        return [
            {'name': c.name, 'description': c.description, 'url': c.url}
            for c in self.cards.values()
        ]

    def list_mcp_tooling_ideas(self):
        """Returns MCP tool integration ideas for this platform."""
        return {
            'suggestions': [
                'Add an MCP BigQuery schema server for source/target contract checks.',
                'Add an MCP Airflow server to trigger DAG validation and dry-runs.',
                'Add an MCP Data Catalog server for policy-tag lineage verification.',
            ]
        }

    def request_human_approval(self, action: str, details: str, tool_context: ToolContext) -> str:
        """Pauses execution and asks for human approval (HITL)."""
        tool_context.actions.skip_summarization = True
        tool_context.actions.escalate = True
        form = {
            'type': 'approval',
            'question': f"Approve action '{action}'?",
            'details': details,
            'allowed_values': ['approve', 'reject'],
        }
        return json.dumps(form)

    async def send_message(self, agent_name: str, message: str, tool_context: ToolContext):
        """Delegates the request to a named remote agent over A2A."""
        if agent_name not in self.connections:
            raise ValueError(f'Unknown agent: {agent_name}')

        state = tool_context.state
        msg = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=message))],
            message_id=str(uuid.uuid4()),
            context_id=state.get('context_id'),
            task_id=state.get('task_id'),
        )
        response = await self.connections[agent_name].send_message(msg)
        if isinstance(response, Message):
            return [p.root.text for p in response.parts if p.root.kind == 'text']

        task: Task = response
        state['context_id'] = task.context_id
        state['task_id'] = task.id
        if task.status.state == TaskState.input_required:
            tool_context.actions.skip_summarization = True
            tool_context.actions.escalate = True
        if task.status.state in [TaskState.failed, TaskState.canceled]:
            raise ValueError(f'Remote agent {agent_name} returned {task.status.state}')

        output = []
        if task.status.message:
            output.extend([p.root.text for p in task.status.message.parts if p.root.kind == 'text'])
        for artifact in task.artifacts or []:
            output.extend([p.root.text for p in artifact.parts if p.root.kind == 'text'])
        return output
