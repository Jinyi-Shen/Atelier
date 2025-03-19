from typing import Annotated, List, Tuple, Union
from typing_extensions import TypedDict
import functools, operator
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.tools import tool
from dpagent.utils.llm import get_llm
from dpagent.agents.base import create_agent_with_tools, bind_llm_by_func_dict, parse_agent_with_tools_result
from dpagent.agents.Tooling.base import fake_human_input
from dpagent.agents.Tooling.Retrieve.prompt import retrieve_db_agent_prompt
from dpagent.config.config import agentMdlCfg


@tool
def retrieve_db(
    query: Annotated[str, "Search query to look up in the knowledge database"],
) -> str:
    """Retrieve the knowledge database to get the related information."""
    returnval = fake_human_input('retrieve_db query:'+query, 'retrieve_db_input')
    return returnval


def gen_agent():
    llm = get_llm(inc=agentMdlCfg.Retrieve['inc'], model_name=agentMdlCfg.Retrieve['model_name'])

    retrieve_db_agent = create_agent_with_tools(llm, [retrieve_db], retrieve_db_agent_prompt, name='retrieve_db_agent')
    # node = functools.partial(agent_node, agent=retrieve_db_agent, name="Retrieve_db")
    return retrieve_db_agent


if __name__ == '__main__':
    retrieve_db_agent = gen_agent()
    retrieve_db_agent_out = retrieve_db_agent.invoke({'user_requirement': ['How to configure the WLAN module?']})
    # fakeanswer: No information found in the database
    print(parse_agent_with_tools_result(retrieve_db_agent_out))
    pass


