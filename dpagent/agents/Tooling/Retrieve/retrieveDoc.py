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
from dpagent.agents.Tooling.Retrieve.prompt import retrieve_docs_agent_prompt
from dpagent.config.config import agentMdlCfg


@tool
def retrieve_docs(
    query: Annotated[str, "Search query to look up the related documents"],
) -> str:
    """Retrieve the documents to get the related information."""
    returnval = fake_human_input('retrieve_docs query:'+query, 'retrieve_docs_input')
    return returnval


def gen_agent():
    llm = get_llm(inc=agentMdlCfg.Retrieve['inc'], model_name=agentMdlCfg.Retrieve['model_name'])

    retrieve_docs_agent = create_agent_with_tools(llm, [retrieve_docs], retrieve_docs_agent_prompt, name='retrieve_docs_agent')
    # node = functools.partial(agent_node, agent=retrieve_docs_agent, name="Retrieve_docs")
    return retrieve_docs_agent


if __name__ == '__main__':
    retrieve_docs_agent = gen_agent()
    retrieve_docs_agent_out = retrieve_docs_agent.invoke({'user_requirement': ['How to configure the WLAN module?']})
    # fakeanswer: Set the WLAN configuration in yupik.dtsi
    print(parse_agent_with_tools_result(retrieve_docs_agent_out))
    pass

