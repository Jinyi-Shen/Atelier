import functools
# from langchain_openai.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from dpagent.config.config import apiConfig, agentMdlCfg
from zhipuai import ZhipuAI


def get_llm(inc=agentMdlCfg.default['inc'], model_name=agentMdlCfg.default['model_name']):
    if inc == "openai":
        llm = ChatOpenAI(
            openai_api_base=apiConfig.OPENAI_API_BASE,
            openai_api_key=apiConfig.OPENAI_API_KEY,
            model_name=model_name,
        )
        return llm
    elif inc == "zhipu":
        llm = ChatOpenAI(
            temperature=0.95,
            model="glm-4-0520",
            openai_api_key="",#replace with your ZhipuAI key
            openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
            max_tokens=10000
        )
        return llm
    else:
        raise ValueError(f"Unknown model Incorporation: {inc}")


if __name__ == "__main__":
    llm = get_llm(inc="zhipu", model_name="gpt-3.5-turbo-1106")
    print(llm.invoke("Who are you"))