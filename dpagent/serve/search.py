from langchain.schema.runnable import RunnableLambda
from dpagent.agents.Tooling.Retrieve.retrieveCode import (
    get_code_retrieval_agent,
)
from dpagent.agents.base import (
    parse_agent_with_tools_result,
)
from dpagent.utils.logger import logger


def search_code(json_data):
    proj_path = json_data.get("proj_path")
    languages = json_data.get("language")
    query = json_data.get("query")
    retrieve_codes_agent = get_code_retrieval_agent(
        proj_path=proj_path, languages=languages
    )
    retrieve_codes_agent_out = retrieve_codes_agent.invoke(
        {"user_requirement": [query]}
    )
    retrieve_codes_agent_out = parse_agent_with_tools_result(retrieve_codes_agent_out)
    logger.info(
        f"proj_path: {proj_path} languages:{languages} query: {query} retrieve_codes_agent_out: {retrieve_codes_agent_out}"
    )
    return {"result": retrieve_codes_agent_out}
    # return {"result": "This is a placeholder for the code search functionality."}


def search_doc(json_data):
    return {"result": "This is a placeholder for the doc search functionality."}


search_code_runnable = RunnableLambda(search_code)

search_doc_runnable = RunnableLambda(search_doc)

if __name__ == "__main__":
    search_code_runnable.invoke(
        {
            "proj_path": "/home/jlhuang/turbox-hjl/sourcecode/turbox-c6490p-lu1.0-dev.release.FC.r001002/apps_proc/src/kernel/msm-5.4/techpack/camera",
            "language": "c++",
            "query": "How to initilize camera sensor?",
        }
    )
