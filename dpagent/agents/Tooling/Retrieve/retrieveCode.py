from typing import Annotated, List, Tuple, Union
from typing_extensions import TypedDict
import functools, operator
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.tools import tool
from dpagent.utils.llm import get_llm
from dpagent.agents.base import (
    create_agent_with_tools,
    bind_llm_by_func_dict,
    parse_agent_with_tools_result,
)
from dpagent.agents.Tooling.base import fake_human_input
from dpagent.agents.Tooling.Retrieve.prompt import (
    retrieve_codes_agent_prompt,
    explain_codes_agent_prompt,
)
from dpagent.config.config import agentMdlCfg
from dpagent.agents.Knowledge.code.graph.udb_graph import UdbGraph
from dpagent.agents.Knowledge.code.service.code_service import CodeService


# @tool
# def retrieve_codes(
#     query: Annotated[str, "Search query to look up the related code"],
# ) -> str:
#     """Retrieve the code repositories to get the related code."""
#     returnval = fake_human_input(
#         "retrieve_codes query:" + query, "retrieve_codes_input"
#     )
#     return returnval

# @tool
# def explain_codes(
#     query: Annotated[str, "The code snippet to explain"],
# ) -> str:
#     """Explain the given code snippet."""
#     returnval = fake_human_input("explain_codes query:" + query, "explain_codes_input")
#     return returnval


# def gen_agent():
#     llm = get_llm(
#         inc=agentMdlCfg.Retrieve["inc"], model_name=agentMdlCfg.Retrieve["model_name"]
#     )

#     retrieve_codes_agent = create_agent_with_tools(
#         llm, [retrieve_codes], retrieve_codes_agent_prompt, name="retrieve_codes_agent"
#     )
#     explain_codes_agent = create_agent_with_tools(
#         llm, [explain_codes], explain_codes_agent_prompt, name="explain_codes_agent"
#     )
#     # node = functools.partial(agent_node, agent=retrieve_codes_agent, name="Retrieve_codes")
#     return retrieve_codes_agent, explain_codes_agent

srv_dict = {
    "/home/jlhuang/turbox-hjl/sourcecode/turbox-c6490p-lu1.0-dev.release.FC.r001002/apps_proc/src/kernel/msm-5.4/techpack/camera": CodeService(
        proj_path="/home/jlhuang/turbox-hjl/sourcecode/turbox-c6490p-lu1.0-dev.release.FC.r001002/apps_proc/src/kernel/msm-5.4/techpack/camera",
        languages="c++",
        analyze=False,
    )
}


def retrieve_codes_wrapper(
    proj_path: str,
    languages: str,
    analyze: bool = False,
):
    @tool(return_direct=True)
    def retrieve_codes(
        query: Annotated[str, "Search query to look up the related code"],
    ) -> str:
        """Retrieve the code repositories to get the related code."""
        if proj_path not in srv_dict:
            srv_dict[proj_path] = CodeService(
                proj_path=proj_path, languages=languages, analyze=analyze
            )
        srv = srv_dict[proj_path]
        res = srv.retrieve_code_by_log(query)
        res = "\n\n".join([node.get_code_with_annotations() for node in res])
        return res

    return retrieve_codes


def get_code_retrieval_agent(proj_path, languages="c++", analyze=False):
    llm = get_llm(
        inc=agentMdlCfg.Retrieve["inc"], model_name=agentMdlCfg.Retrieve["model_name"]
    )
    retrieve_codes_agent = create_agent_with_tools(
        llm,
        [
            retrieve_codes_wrapper(
                proj_path=proj_path, languages=languages, analyze=analyze
            )
        ],
        retrieve_codes_agent_prompt,
        name="retrieve_codes_agent",
    )
    return retrieve_codes_agent


if __name__ == "__main__":
    proj_path = "/home/jlhuang/turbox-hjl/sourcecode/turbox-c6490p-lu1.0-dev.release.FC.r001002/apps_proc/src/kernel/msm-5.4/techpack/camera"
    languages = "c++"
    retrieve_codes_agent = get_code_retrieval_agent(
        proj_path=proj_path, languages=languages
    )
    retrieve_codes_agent_out = retrieve_codes_agent.invoke(
        {"user_requirement": ["How to match the camera sensor id?"]}
    )
    print(parse_agent_with_tools_result(retrieve_codes_agent_out))

    # retrieve_codes_agent, explain_codes_agent = gen_agent()
    # retrieve_codes_agent_out = retrieve_codes_agent.invoke(
    #     {"user_requirement": ["How to match the camera sensor id?"]}
    # )
    # fakeanswer: It is in the file project_config.py
    # print(parse_agent_with_tools_result(retrieve_codes_agent_out))
    # explain_codes_agent_out = explain_codes_agent.invoke(
    #     {"user_requirement": ["What does the function router.get_dfs mean?"]}
    # )
    # # fakeanswer: It means to get the dfs from the router
    # print(parse_agent_with_tools_result(explain_codes_agent_out))
    pass
