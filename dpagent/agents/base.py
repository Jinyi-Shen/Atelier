from typing import Any, Callable, List, Optional, TypedDict, Union, Dict
from enum import Enum
import json
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chains.openai_functions import create_structured_output_runnable
from langchain.chains.openai_functions import create_openai_fn_runnable
from langchain.prompts.chat import ChatPromptTemplate, ChatPromptValue
from langgraph.prebuilt import create_agent_executor
from langgraph.graph import END, StateGraph
from dpagent.utils import util
from dpagent.utils.llm import get_llm
from dpagent.utils.logger import logger, logger_add_query_prompt, logger_add_response, logger_add_midstep
from dpagent.utils.history import historyManager
from dpagent.config.config import agentMdlCfg


def create_agent_normal(llm, prompt, name='llm'):
    return AgentConv(name=name, llm=llm, prompt=prompt).create_agent_normal()

def parse_agent_normal_result(output) -> str:
    return AgentConv().parse_result(output, agentType=AgentType.NORMAL)


def create_agent_force_structured_output(llm, formatClass: BaseModel, prompt, name='llm'):
    return AgentConv(name=name, llm=llm, prompt=prompt).create_agent_force_structured_output(formatClass)


def create_agent_optional_structured_output(llm, formatClassList: List[BaseModel], prompt, name='llm'):
    return AgentConv(name=name, llm=llm, prompt=prompt).create_agent_optional_structured_output(formatClassList)


def create_agent_with_tools(llm, tools: List, prompt, name='llm'):
    return AgentConv(name=name, llm=llm, prompt=prompt).create_agent_with_tools(tools)

def parse_agent_with_tools_result(output) -> str:
    return AgentConv().parse_result(output, agentType=AgentType.TOOLING)

def parse_agent_with_tools_midstep(output) -> List[Dict]:
    agt =  AgentConv()
    agt.agentType == AgentType.TOOLING
    return agt.parse_agent_with_tools_midstep(output)


def bind_llm_by_func_dict(llm, function_dict):
    return llm.bind_functions(functions=[function_dict], function_call=function_dict["name"])

def create_agent_force_structured_output_by_funcdict(llm, function_dict, prompt, name='llm'):
    return AgentConv(name=name, llm=llm, prompt=prompt).create_agent_force_structured_output_by_funcdict(function_dict)


def print_ChatPromptTemplate(obj: ChatPromptTemplate):
    obj.pretty_print()

def print_ChatPromptValue(obj: ChatPromptValue):
    for msg in obj.to_json()['kwargs']['messages']:
        print(msg.content)
        print(">>>>>>>>>>>>>>>>>>")

def instantiate_ChatPrompt(obj: ChatPromptTemplate, input: Dict):
    wrapped_input = {**input, **{'agent_scratchpad': []}} if 'agent_scratchpad' not in input else input
    objval = obj.invoke(wrapped_input)
    msglist = []
    for msg in objval.to_json()['kwargs']['messages']:
        msglist.append({msg.type: msg.content})
    return msglist

def sep_sys_human_prompt(msglist):
    sys_prompts = [list(mi.values())[0] for mi in msglist if 'system' in mi]
    human_prompts = [list(mi.values())[0] for mi in msglist if 'human' in mi]
    return sys_prompts, human_prompts


class AgentType(Enum):
    NORMAL = 1
    FORCE_STRUCTOUT = 2
    OPTIONAL_STRUCTOUT = 3
    TOOLING = 4


class AgentConv:
    def __init__(self, name='llm', llm=None, prompt=None, agent=None):
        self.name = name
        self.llm = llm
        self.prompt = prompt
        self.agent = agent
        self.agentType = None
    
    def set_or_use_llm_prompt(self, llm, prompt):
        if llm is None:
            llm = self.llm
        else:
            self.llm = llm
        if prompt is None:
            prompt = self.prompt
        else:
            self.prompt = prompt
        return llm, prompt

    def create_agent_normal(self, llm=None, prompt=None):
        llm, prompt = self.set_or_use_llm_prompt(llm, prompt)
        self.agent = (prompt | llm)
        self.agentType = AgentType.NORMAL
        return self

    def create_agent_force_structured_output(self, formatClass: BaseModel, llm=None, prompt=None):
        llm, prompt = self.set_or_use_llm_prompt(llm, prompt)
        self.agent = create_structured_output_runnable(
            formatClass, 
            llm,
            prompt
        ) # ChatPromptTemplate | RunnableBinding | PydanticAttrOutputFunctionsParser
        self.agentType = AgentType.FORCE_STRUCTOUT
        return self

    def create_agent_force_structured_output_by_funcdict(self, function_dict, llm=None, prompt=None):
        llm, prompt = self.set_or_use_llm_prompt(llm, prompt)
        self.agent = (
            prompt
            | bind_llm_by_func_dict(llm, function_dict)
            | JsonOutputFunctionsParser()
        )
        self.agentType = AgentType.FORCE_STRUCTOUT
        return self

    def create_agent_optional_structured_output(self, formatClassList: List[BaseModel], llm=None, prompt=None):
        llm, prompt = self.set_or_use_llm_prompt(llm, prompt)
        self.agent = create_openai_fn_runnable(
            formatClassList,
            llm,
            prompt,
        )
        self.agentType = AgentType.OPTIONAL_STRUCTOUT
        return self
    
    def create_agent_with_tools(self, tools: List, llm=None, prompt=None):
        llm, prompt = self.set_or_use_llm_prompt(llm, prompt)
        agent_runnable = create_openai_functions_agent(llm, tools, prompt)
        self.agent = AgentExecutor(agent=agent_runnable, tools=tools, return_intermediate_steps=True) # AgentExecutor
        # self.agent = create_agent_executor(agent_runnable, tools) # create_agent_executor
        self.agentType = AgentType.TOOLING
        return self
    
    def parse_agent_with_tools_midstep(self, res) -> List[Dict]:
        if not self.agentType == AgentType.TOOLING:
            return []
        midsteps = res["intermediate_steps"]
        mid_json_list = []
        for step in midsteps:
            mid_json_list.append({
                'tool': step[0].tool, 
                'tool_input': step[0].tool_input,
                'result': step[1]
            })
        return mid_json_list

    
    def invoke(self, input: Dict):
        # get prompt value
        query_prompt = instantiate_ChatPrompt(self.prompt, input)
        sys_prompts, human_prompts = sep_sys_human_prompt(query_prompt)
        logger_add_query_prompt(AgentName=self.name, sys_prompt=sys_prompts[0], human_prompts=human_prompts)
        # invoke
        raw_ret = self.agent.invoke(input)
        ret = self.parse_result(raw_ret)
        # post
        if self.agentType == AgentType.NORMAL:
            logger_add_response(AgentName=self.name, response=ret)
            historyManager.add_message({'name':self.name, 'query': query_prompt, 'response': [{'assistant': ret}]})
            return raw_ret
        if self.agentType == AgentType.TOOLING:
            # process middle step
            mid_json_list = self.parse_agent_with_tools_midstep(raw_ret)
            mid_str_list = []
            mid_query_str_list = []
            for mid in mid_json_list:
                new_mid = {key: value for key, value in mid.items() if key != 'result'}
                mid_str_list.append({'assistant': util.json2str(mid)})
                mid_query_str_list.append(util.json2str(new_mid))
            logger_add_midstep(AgentName=self.name, mid_steps=mid_query_str_list)
            # process response
            logger_add_response(AgentName=self.name, response=ret)
            historyManager.add_message({'name':self.name, 'query': query_prompt, 'response': [{'assistant': ret}]}, middle=mid_str_list)
            return raw_ret
        elif self.agentType in [AgentType.FORCE_STRUCTOUT, AgentType.OPTIONAL_STRUCTOUT]:
            response_str = util.json2str(ret.dict())
            logger_add_response(AgentName=self.name, response=response_str)
            historyManager.add_message({'name':self.name, 'query': query_prompt, 'response': [{'assistant': response_str}]})
            return raw_ret
        else:
            raise Exception("Unknown Agent type:", self.agentType)
    
    def parse_result(self, res, agentType=None):
        if agentType is None:
            agentType = self.agentType
        if agentType == AgentType.NORMAL:
            #  output: str
            return res.content
        elif agentType == AgentType.FORCE_STRUCTOUT:
            return res
        elif agentType == AgentType.OPTIONAL_STRUCTOUT:
            return res
        elif agentType == AgentType.TOOLING:
            #  output: str
            return res["output"] # AgentExecutor
            # return res["agent_outcome"].return_values["output"] # create_agent_executor
        else:
            raise Exception("Unknown Agent type:", agentType)
    
    def with_retry(self):
        self.agent = self.agent.with_retry()
        return self



if __name__ == '__main__':
    from dpagent.agents.Tooling.base import ToolSuiteLists
    from dpagent.agents.Tooling.WebSearch.WebSearch import webSearchChainSuite
    toolSuiteList = ToolSuiteLists([webSearchChainSuite])
    if False:
        from dpagent.agents.Planning.dfs.PlanMaker.PlanMaker import PlanMaker
        from dpagent.agents.Planning.dfs.PlanMaker.prompt import executor_cap_list_to_str
        executor_cap_list = [
            'Search the Internet',
            'Retrieve the information from the document',
        ]
        planMaker = PlanMaker(toolSuiteList)
        plan_input = {
            'objective': 'what is the hometown of the 2024 Australia open winner?',
            'executor_cap': executor_cap_list_to_str(executor_cap_list),
        }
        planMaker_plan_out = planMaker.planMaker_plan.invoke(plan_input)
    if False:
        from dpagent.agents.Tooling.WebSearch.WebSearch import webSearch_agent, webSearch_chain
        # search_agent_out = webSearch_agent.invoke({"query": "when is Taylor Swift's next tour?"})
        query1 = "when is Taylor Swift's next tour?"
        query = "What does this url presented: https://lamport.azurewebsites.net/tla/tla.html"
        result = webSearch_chain.invoke(query)
    if False:
        from dpagent.agents.Planning.dfs.ActionSeqMaker.ActionSeqMaker import ActionSeqMaker
        development_plan_exp1 = [{
                "desc": "Research the winner's hometown",
                "children": [
                    {
                        "desc": "Look up the winner's biographical information through:",
                        "children": [{
                                "desc": "Official ATP or WTA player profiles",
                                "children": []
                            },
                            {
                                "desc": "Sports news articles profiling the winner",
                                "children": []
                            }
                        ]
                    },
                ]
            },
        ]
        action_executors = ['retrieve_db', 'retrieve_docs', 'retrieve_codes', 'explain_codes']
        action_seq = """- action: retrieve_docs
        description: Search for recent sports news articles profiling the 2024 Australian Open winner.
        parameters:
            keywords: "2024 Australian Open winner profile"
            source_type: "sports news"
            date_range: "last month"

        - action: explain_codes
        description: Extract information regarding the winner's hometown from the retrieved sports news articles.
        parameters:
            data_type: "text"
            operation: "information extraction"
            information: "hometown" """
        input = {
            'objective': 'what is the hometown of the 2024 Australia open winner?',
            'development_plan': development_plan_exp1,
            'node_task': 'Sports news articles profiling the winner',
            'Action_Executors': ', '.join(action_executors),
            'action_seq': action_seq,
            'refine_reason': "The action sequence is not in the correct YAML format. There is an indentation issue with the second action block which should be at the same level as the first action. Additionally, the second action 'explain_codes' requires the output from the first action as an input, but this is not specified in the parameters.",
            # 'feedback': 'execution failed due to network error',
        }
        actionSeqMaker = ActionSeqMaker(toolSuiteList)
        actionSeqMaker_check_actionseq_yaml_out = actionSeqMaker.actionSeqMaker_check_actionseq.invoke(input)
    
    pass

