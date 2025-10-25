from google.adk.agents.llm_agent import Agent

state_management = Agent(
    model='gemini-2.5-flash',
    name='state_manager',
    description='Checks for any missing data',
    instruction='Answer user questions to the best of your knowledge',
)

record_wrangler = Agent(
    model='gemini-2.5-flash',
    name='record_wrangler',
    description='Gets client data per section and identify what is missing',
    instruction='Answer user questions to the best of your knowledge',
)

client_communication = Agent(
    model='gemini-2.5-flash',
    name='client_communication',
    description='Drafts email for clients',
    instruction='Answer user questions to the best of your knowledge',
)

legal_researcher = Agent(
    model='gemini-2.5-flash',
    name='legal_researcher',
    description='Finds supporting cases for recommender summary',
    instruction='Answer user questions to the best of your knowledge',
)

voice_bot_scheduler = Agent(
    model='gemini-2.5-flash',
    name='voice_bot_scheduler',
    description='schedules client meetings',
    instruction='Answer user questions to the best of your knowledge',
)

evidence_sorter = Agent(
    model='gemini-2.5-flash',
    name='evidence_sorter',
    description='Takes all client data and sorts into 3 sections',
    instruction='Answer user questions to the best of your knowledge',
)

agent_coordinator = Agent(
    model='gemini-2.5-flash',
    name='agent_coordinator',
    description='The main agent that oversees sub_agents.',
    instruction='Answer user questions to the best of your knowledge',

    sub_agents=[state_management, record_wrangler, client_communication,
                legal_researcher, voice_bot_scheduler, evidence_sorter]
)

root_agent = agent_coordinator