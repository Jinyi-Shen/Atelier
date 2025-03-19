from typing import Annotated, List, Tuple, Union
from typing_extensions import TypedDict
import functools, operator
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.tools import tool
from dpagent.utils.llm import get_llm
from dpagent.agents.base import create_agent_with_tools, bind_llm_by_func_dict, parse_agent_with_tools_result
from dpagent.agents.Tooling.WebSearch.tool import tavily_tool, scrape_webpages
from dpagent.agents.Tooling.WebSearch.prompt import search_agent_prompt, webScraper_agent_prompt, supervisor_prompt
from dpagent.agents.Tooling.base import ToolSuite
from dpagent.config.config import agentMdlCfg


# ===================== graph state =====================

# WebSearch team graph state
class WebSearchTeamState(TypedDict):
    # A message is added after each team member finishes
    messages: Annotated[List[BaseMessage], operator.add]
    # The team members are tracked so they are aware of the others' skill-sets
    team_members: List[str]
    # Used to route work. The supervisor calls a function that will update this every time it makes a decision
    next: str


# ===================== nodes =====================

def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=parse_agent_with_tools_result(result), name=name)]}


def get_agent_nodes(llm):
    webSearch_agent = create_agent_with_tools(llm, [tavily_tool], search_agent_prompt, name='webSearch_agent')
    webSearch_node = functools.partial(agent_node, agent=webSearch_agent, name="Web_Search")

    webScraper_agent = create_agent_with_tools(llm, [scrape_webpages], webScraper_agent_prompt, name='webScraper_agent')
    webScraper_node = functools.partial(agent_node, agent=webScraper_agent, name="Web_Scraper")

    options = ["FINISH"] + ["Web_Search", "Web_Scraper"]
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                },
            },
            "required": ["next"],
        },
    }
    
    supervisor_agent = (
        # supervisor_prompt
        # supervisor_prompt.partial(options=options, team_members=", ".join(["Web_Search", "Web_Scraper"]))
        supervisor_prompt.partial(options=options)
        | bind_llm_by_func_dict(llm, function_def)
        | JsonOutputFunctionsParser()
    )
    return webSearch_agent, webSearch_node, webScraper_agent, webScraper_node, supervisor_agent


# ===================== graph =====================

def gen_graph(webSearch_node, webScraper_node, supervisor_agent):
    webSearch_graph = StateGraph(WebSearchTeamState)
    webSearch_graph.add_node("Web_Search", webSearch_node)
    webSearch_graph.add_node("Web_Scraper", webScraper_node)
    webSearch_graph.add_node("supervisor", supervisor_agent)

    # Define the control flow
    webSearch_graph.add_edge("Web_Search", "supervisor")
    webSearch_graph.add_edge("Web_Scraper", "supervisor")
    webSearch_graph.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {"Web_Search": "Web_Search", "Web_Scraper": "Web_Scraper", "FINISH": END},
    )

    webSearch_graph.set_entry_point("supervisor")
    chain = webSearch_graph.compile()

    webSearch_chain = enter_chain | chain
    return webSearch_chain

# The following functions interoperate between the top level graph state and the state of the webSearch sub-graph this makes it so that the states of each graph don't get intermixed
def enter_chain(message: str):
    results = {
        "messages": [HumanMessage(content=message)],
        "team_members": ", ".join(["Web_Search", "Web_Scraper"])
    }
    return results


llm = get_llm(inc=agentMdlCfg.WebSearch['inc'], model_name=agentMdlCfg.WebSearch['model_name'])
webSearch_agent, webSearch_node, webScraper_agent, webScraper_node, supervisor_agent = get_agent_nodes(llm)
webSearch_chain = gen_graph(webSearch_node, webScraper_node, supervisor_agent)

tavilyWebSearchSuite = ToolSuite("WebSearch", "Search the Internet", toolfunc=tavily_tool, toolAgent=webSearch_agent)

@tool
def search_internet(query: str) -> str:
    """Search the Internet, or scrape the provided web pages for detailed information."""
    res = webSearch_chain.invoke(query)
    answer = res['messages'][-1].content
    return answer

webSearchChainSuite = ToolSuite(
    "SearchInternet", 
    "Search the Internet, or scrape the provided web pages for detailed information.", 
    toolfunc=search_internet, 
    toolAgent=webSearch_chain
)


if __name__ == '__main__':
    query1 = "when is Taylor Swift's next tour?"
    query2 = """I got an error message:
    Error code: 400 - {'error': {'message': "'Note Taker' does not match '^[a-zA-Z0-9_-]{1,64}$' - 'messages.2.name'", 'type': 'invalid_request_error', 'param': None, 'code': None}
    How to fix it?
    """
    query = "What does this url presented: https://lamport.azurewebsites.net/tla/tla.html"
    # invoke
    if False:
        ret = webSearch_agent.invoke({"messages": [HumanMessage(content=query1, name='human1')], "team_members": "Web_Search"})
    if False:
        result = webSearch_chain.invoke(query)
        for m in result['messages']:
            print(m.content)
            print("---")
        answer = result['messages'][-1].content
        exit()
        # stream
        ss = webSearch_chain.stream(
            query, {"recursion_limit": 20}
        )
        for s in ss:
            if "__end__" not in s:
                print(s)
                print("---")
    if False:
        print(search_internet(query1))
