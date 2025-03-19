from typing import Annotated, List, Tuple, Union, Dict
from typing_extensions import TypedDict
import functools, operator
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langchain_core.pydantic_v1 import BaseModel, Field
from dpagent.utils import util
from dpagent.utils.llm import get_llm
from dpagent.utils.history import historyManager
from dpagent.agents.base import (
    create_agent_normal,
    parse_agent_normal_result,
    create_agent_with_tools,
    create_agent_force_structured_output,
    create_agent_optional_structured_output,
    parse_agent_with_tools_result
)
from dpagent.config.config import agentMdlCfg
from dpagent.agents.Planning.dfs.ActionSeqMaker.prompt import (
    ActionSeqMaker_make_actionseq_prompt,
    ActionSeqMaker_update_actionseq_prompt,
    ActionSeqMaker_check_actionseq_prompt,
    ActionSeqMaker_run_actionseq_prompt,
    ActionSeqMaker_conclude_actionseq_run_prompt,
    ActionSeqMaker_decide_actionseq_call_finish_prompt,
)
from dpagent.agents.Tooling.base import ToolSuiteLists


class ActionSeqPass(BaseModel):
    """Decide whether the action sequence is executable and in right YAML format"""
    ispass: bool = Field(
        description="action sequence pass or not"
    )
    needinfo: bool = Field(
        description="need more information or not"
    )
    description: str = Field(
        description="description of the decision"
    )

class NeedInfo(BaseModel):
    """Decide whether need more information to make the action sequence executable"""
    need: bool = Field(
        description="need or not"
    )

class ActionSeqComplete(BaseModel):
    """Decide whether the execution of action sequence is complete"""
    complete: bool = Field(
        description="complete or not"
    )


# ===================== graph state =====================

class ActionSeqState(TypedDict):
    action_executors: List[str]
    objective: str
    development_plan: List
    node_task: str
    action_seq: str
    refine_reason: str
    feedback: str
    conclusion: str
    check_actionseq_out: ActionSeqPass
    decide_actionseq_call_finish_out: ActionSeqComplete
    end_refine: bool
    end_finish: bool
    # past_steps: Annotated[List[Tuple], operator.add]


class ActionSeqMaker:
    def __init__(self, toolSuiteList: ToolSuiteLists):
        self.toolSuiteList = toolSuiteList
        self.toolfuncs = toolSuiteList.get_toolfuncs()
        self.toolNames = toolSuiteList.get_names()
        self.gen_agents()
        self.gen_graph()

    def gen_agents(self):
        llm = get_llm()

        self.actionSeqMaker_make_actionseq = create_agent_normal(llm, ActionSeqMaker_make_actionseq_prompt, name='actionSeqMaker_make_actionseq')
        self.actionSeqMaker_update_actionseq = create_agent_normal(llm, ActionSeqMaker_update_actionseq_prompt, name='actionSeqMaker_update_actionseq')
        self.actionSeqMaker_conclude_actionseq = create_agent_normal(llm, ActionSeqMaker_conclude_actionseq_run_prompt, name='actionSeqMaker_conclude_actionseq')

        self.actionSeqMaker_check_actionseq = create_agent_force_structured_output(llm, ActionSeqPass, ActionSeqMaker_check_actionseq_prompt, name='actionSeqMaker_check_actionseq')
        # self.actionSeqMaker_check_need_moreinfo = create_agent_force_structured_output(llm, NeedInfo, ActionSeqMaker_check_need_moreinfo_prompt, name='actionSeqMaker_check_need_moreinfo')
        self.actionSeqMaker_decide_actionseq_call_finish = create_agent_force_structured_output(llm, ActionSeqComplete, ActionSeqMaker_decide_actionseq_call_finish_prompt, name='actionSeqMaker_decide_actionseq_call_finish')

        self.actionSeqMaker_run_actionseq = create_agent_with_tools(
            get_llm(inc=agentMdlCfg.Retrieve['inc'], model_name=agentMdlCfg.Retrieve['model_name']), 
            self.toolfuncs, ActionSeqMaker_run_actionseq_prompt, name='actionSeqMaker_run_actionseq'
        )

    # ===================== nodes =====================

    def make_actionseq(self, state: ActionSeqState):
        inputDict = {
            'Action_Executors': ', '.join(state['action_executors']),
            'objective': state["objective"],
            'development_plan': state["development_plan"],
            'node_task': state["node_task"],
        }
        out = self.actionSeqMaker_make_actionseq.invoke(inputDict)
        return {'action_seq': parse_agent_normal_result(out)}

    def update_actionseq(self, state: ActionSeqState):
        inputDict = {
            'Action_Executors': ', '.join(state['action_executors']),
            'objective': state["objective"],
            'node_task': state["node_task"],
            'action_seq': state["action_seq"],
            'refine_reason': state["refine_reason"],
        }
        out = self.actionSeqMaker_update_actionseq.invoke(inputDict)
        return {'action_seq': parse_agent_normal_result(out)}

    def conclude_actionseq(self, state: ActionSeqState):
        inputDict = {
            'Action_Executors': ', '.join(state['action_executors']),
            'objective': state["objective"],
            'node_task': state["node_task"],
            'action_seq': state["action_seq"],
            'feedback': state["feedback"],
        }
        out = self.actionSeqMaker_conclude_actionseq.invoke(inputDict)
        return {'conclusion': parse_agent_normal_result(out)}

    def check_actionseq(self, state: ActionSeqState):
        inputDict = {
            'Action_Executors': ', '.join(state['action_executors']),
            'objective': state["objective"],
            'node_task': state["node_task"],
            'action_seq': state["action_seq"],
        }
        out = self.actionSeqMaker_check_actionseq.invoke(inputDict)
        # end logic
        ret = {'check_actionseq_out': out, 'refine_reason': out.description}
        if not out.ispass and out.needinfo:
            ret['end_refine'] = True
        return ret

    def decide_actionseq_call_finish(self, state: ActionSeqState):
        inputDict = {
            'Action_Executors': ', '.join(state['action_executors']),
            'objective': state["objective"],
            'node_task': state["node_task"],
            'action_seq': state["action_seq"],
            'conclusion': state["conclusion"],
        }
        out = self.actionSeqMaker_decide_actionseq_call_finish.invoke(inputDict)
        # end logic
        ret = {'decide_actionseq_call_finish_out': out}
        if out.complete:
            ret['end_finish'] = True
        return ret

    def run_actionseq(self, state: ActionSeqState):
        inputDict = {
            'Action_Executors': ', '.join(state['action_executors']),
            'objective': state["objective"],
            'node_task': state["node_task"],
            'action_seq': state["action_seq"],
        }
        out = self.actionSeqMaker_run_actionseq.invoke(inputDict)
        return {'feedback': parse_agent_with_tools_result(out)}

    # ===================== graph =====================

    def postProcNode_check_actionseq(self, state: ActionSeqState):
        nodeout = state['check_actionseq_out']
        if nodeout.ispass:
            return 'run_actionseq'
        else:
            if nodeout.needinfo:
                return 'end'
            else:
                return 'update_actionseq'

    def enter_chain(self, chain_in):
        init_state = {
            "action_executors": self.toolNames,
            "objective": chain_in['objective'],
            "development_plan": chain_in['development_plan'],
            "node_task": chain_in['node_task'],
            "end_refine": False,
            "end_finish": False
        }
        return init_state

    def gen_graph(self):
        actionSeqMakerGraph = StateGraph(ActionSeqState)
        actionSeqMakerGraph.add_node("make_actionseq", self.make_actionseq)
        actionSeqMakerGraph.add_node("update_actionseq", self.update_actionseq)
        actionSeqMakerGraph.add_node("conclude_actionseq", self.conclude_actionseq)
        actionSeqMakerGraph.add_node("check_actionseq", self.check_actionseq)
        actionSeqMakerGraph.add_node("decide_actionseq_call_finish", self.decide_actionseq_call_finish)
        actionSeqMakerGraph.add_node("run_actionseq", self.run_actionseq)

        actionSeqMakerGraph.add_edge("make_actionseq", "check_actionseq")
        actionSeqMakerGraph.add_edge("run_actionseq", "conclude_actionseq")
        actionSeqMakerGraph.add_edge("conclude_actionseq", "decide_actionseq_call_finish")
        actionSeqMakerGraph.add_edge("update_actionseq", "check_actionseq")

        actionSeqMakerGraph.add_conditional_edges(
            "check_actionseq",
            self.postProcNode_check_actionseq,
            {'run_actionseq': 'run_actionseq', 'update_actionseq': 'update_actionseq', 'end':END},
        )

        actionSeqMakerGraph.add_conditional_edges(
            "decide_actionseq_call_finish",
            lambda state: state['decide_actionseq_call_finish_out'].complete,
            {False: 'check_actionseq', True:END},
        )

        actionSeqMakerGraph.set_entry_point("make_actionseq")
        actionSeqMakerChain = self.enter_chain | actionSeqMakerGraph.compile()
        self.actionSeqMakerGraph = actionSeqMakerGraph
        self.actionSeqMakerChain = actionSeqMakerChain


    # human in loop for debug
    def fake_invoke_actionSeqMakerChain(self, chain_in):
        from dpagent.agents.base import instantiate_ChatPrompt, sep_sys_human_prompt
        from dpagent.agents.Tooling.base import fake_human_input
        from dpagent.utils.logger import logger_add_query_prompt, logger_add_response
        fake_chain_name = 'fake actionSeqMakerChain'
        chain_state = self.enter_chain(chain_in)
        chain_state['Action_Executors'] = ', '.join(chain_state['action_executors'])
        query_prompt = instantiate_ChatPrompt(ActionSeqMaker_make_actionseq_prompt, chain_state)
        sys_prompts, human_prompts = sep_sys_human_prompt(query_prompt)
        logger_add_query_prompt(AgentName=fake_chain_name, sys_prompt=sys_prompts[0], human_prompts=human_prompts)
        # fake input
        print('\n=== fake_invoke_actionSeqMakerChain ===\n\n')
        instruction = """fake_invoke_actionSeqMakerChain\n\
        Make sure the first line as [end_refine: bool]
        The second line as [end_finish: bool]
        The third line as [refine_reason or conclusion: str]\n"""
        humanin = fake_human_input(instruction, 'fake_invoke_actionSeqMakerChain.txt', overwrite=False)
        parts = humanin.split('\n', 2)
        chain_out = {
            'end_refine': True if parts[0]=="True" else False,
            'end_finish': True if parts[1]=="True" else False,
            'refine_reason': parts[2],
            'conclusion': parts[2],
        }
        # log and history
        ret_str = util.json2str(chain_out)
        logger_add_response(AgentName=fake_chain_name, response=ret_str)
        historyManager.add_message({'name':fake_chain_name, 'query': query_prompt, 'response': [{'assistant': ret_str}]})
        return chain_out



if __name__ == '__main__':
    from dpagent.agents.Tooling.WebSearch.WebSearch import webSearchChainSuite
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
    toolSuiteList = ToolSuiteLists([webSearchChainSuite])
    action_executors = toolSuiteList.get_names()
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
    if True:
        actionSeqMaker_make_actionseq_out = actionSeqMaker.actionSeqMaker_make_actionseq.invoke(input)
        print(parse_agent_normal_result(actionSeqMaker_make_actionseq_out))
    if False:
        actionSeqMaker_check_actionseq_yaml_out = actionSeqMaker.actionSeqMaker_check_actionseq.invoke(input)
        print(actionSeqMaker_check_actionseq_yaml_out.ispass)
        print(actionSeqMaker_check_actionseq_yaml_out.description)
    if False:
        actionSeqMaker_run_actionseq_out = actionSeqMaker.actionSeqMaker_run_actionseq.invoke(input)
        print(parse_agent_with_tools_result(actionSeqMaker_run_actionseq_out))
    if False:
        chain_out = actionSeqMaker.actionSeqMakerChain.invoke(input)
        if chain_out['end_refine']:
            print('end_refine with refine_reason:', chain_out['refine_reason'])
        if chain_out['end_finish']:
            print('end_finish with conclusion:', chain_out['conclusion'])
    pass



