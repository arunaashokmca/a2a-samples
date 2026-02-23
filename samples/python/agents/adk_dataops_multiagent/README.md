# ADK DataOps Multi-Agent (A2A)

This sample provides a **Google ADK + A2A** multi-agent design for your scenario:

1. **Main orchestrator agent** greets users and asks how to help.
2. **Config agent** prepares RDBMS ➜ GCS movement configuration.
3. **DAG agent** generates Airflow DAG code from a **Jinja template**.
4. **Audit agent** performs basic movement + data quality checks.

It demonstrates:
- ADK `Runner` + in-memory `SessionService` usage.
- Human-in-the-loop approval using escalation (`request_human_approval`).
- Agent-to-agent delegation over A2A protocol (`send_message`).
- MCP integration ideas exposed as a tool (`list_mcp_tooling_ideas`).

## Architecture

- `orchestrator_main.py` starts the customer-facing A2A agent (`dataops_orchestrator_agent`).
- Sub-agents run on their own A2A endpoints:
  - `config_agent_main.py` on port `10101`
  - `dag_agent_main.py` on port `10102`
  - `audit_agent_main.py` on port `10103`
- The orchestrator resolves agent cards and delegates via A2A clients.

## Run

```bash
cd samples/python/agents/adk_dataops_multiagent
uv run config_agent_main.py
uv run dag_agent_main.py
uv run audit_agent_main.py
uv run orchestrator_main.py
```

Then send A2A requests to `http://localhost:10100`.

## Deploy (Cloud Run pattern)

Deploy each agent as an independent Cloud Run service:

1. Build each service image with its respective entrypoint.
2. Deploy 4 services (`orchestrator`, `config`, `dag`, `audit`).
3. Start orchestrator with:
   - `--remote-agent=https://<config-service-url>`
   - `--remote-agent=https://<dag-service-url>`
   - `--remote-agent=https://<audit-service-url>`
4. Set `LITELLM_MODEL` and model credentials as environment variables/secrets.

## Notes

This is a sample skeleton for platform design. Extend with:
- real JDBC/db connectors,
- secure secret manager retrieval,
- production DQ suites (e.g., Great Expectations/BigQuery validations),
- persistent session/memory stores,
- authenticated A2A + MCP tool servers.
