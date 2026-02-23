from google.adk import Agent

from tools import audit_data_movement


root_agent = Agent(
    name='audit_agent',
    model='gemini-2.5-flash',
    description='Audits data movement and runs basic DQ checks.',
    instruction=(
        'You are a data quality auditor. Use audit_data_movement to evaluate'
        ' movement integrity and report concise pass/fail outcomes.'
    ),
    tools=[audit_data_movement],
)
