from google.adk import Agent

from tools import build_rdbms_to_gcs_config


root_agent = Agent(
    name='config_agent',
    model='gemini-2.5-flash',
    description='Generates ingestion configuration details for RDBMS to GCS migration.',
    instruction=(
        'You are a data platform configuration specialist. Use the tool to produce'
        ' concrete config JSON for moving data from RDBMS to GCS. Ask for missing'
        ' required fields before calling the tool.'
    ),
    tools=[build_rdbms_to_gcs_config],
)
