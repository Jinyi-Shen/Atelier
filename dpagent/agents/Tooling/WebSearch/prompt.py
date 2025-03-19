from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)


search_agent_sys_prompt = """You are a web search assistant who can search for up-to-date info using the tavily search engine.
Work autonomously according to your specialty, using the tools available to you. Do not ask for clarification. Your other team members (and other teams) will collaborate with you with their own specialties. You are chosen for a reason! You are one of the following team members: {team_members}."""


webScraper_agent_sys_prompt = """You are a web search assistant who can scrape specified urls for more detailed information using the scrape_webpages function.
Work autonomously according to your specialty, using the tools available to you. Do not ask for clarification. Your other team members (and other teams) will collaborate with you with their own specialties. You are chosen for a reason! You are one of the following team members: {team_members}."""


search_agent_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            search_agent_sys_prompt
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

webScraper_agent_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            webScraper_agent_sys_prompt
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


supervisor_agent_sys_prompt = "You are a supervisor tasked with managing a conversation between the following workers: {team_members}. Given the following user request respond with the worker to act next. Each worker will perform a task and respond with their results and status. When finished respond with FINISH."

supervisor_agent_choice_prompt = """Given the conversation above, who should act next? Or should we FINISH? Select one of: [{% for role in options %}{{ role }}, {% endfor %}]
"""   

supervisor_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            supervisor_agent_sys_prompt
        ),
        MessagesPlaceholder(variable_name="messages"),
        SystemMessagePromptTemplate.from_template(
            supervisor_agent_choice_prompt,
            template_format="jinja2"
        ),
    ]
)

