from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)


retrieve_db_agent_sys_prompt = """You are an assistant for software or embedded system development. \
Your responsibility is to retrieve information from the knowledge database using the retrieve_db function. \
Please generate the query message according to the user requirement, and then call the retrieve_db function. 
"""

retrieve_docs_agent_sys_prompt = """You are an assistant for software or embedded system development. \
Your responsibility is to retrieve information from the given documents using the retrieve_docs function. \
Please generate the query message according to the user requirement, and then call the retrieve_docs function. 
"""

retrieve_codes_agent_sys_prompt = """You are an assistant for software or embedded system development. \
Your responsibility is to retrieve related code from the code repository using the retrieve_codes function. \
Please generate the query message according to the user requirement, and then call the retrieve_codes function.
"""

explain_codes_agent_sys_prompt = """You are an assistant for software or embedded system development. \
Your responsibility is to get the explanation of the given code snippet using the explain_codes function. \
Please generate the query message according to the user requirement, and then call the explain_codes function. 
"""

retrieve_db_agent_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(retrieve_db_agent_sys_prompt),
        MessagesPlaceholder(variable_name="user_requirement"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

retrieve_docs_agent_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(retrieve_docs_agent_sys_prompt),
        MessagesPlaceholder(variable_name="user_requirement"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

retrieve_codes_agent_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(retrieve_codes_agent_sys_prompt),
        MessagesPlaceholder(variable_name="user_requirement"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

explain_codes_agent_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(explain_codes_agent_sys_prompt),
        MessagesPlaceholder(variable_name="user_requirement"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
