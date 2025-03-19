from typing import Annotated, List, Tuple, Union
from typing_extensions import TypedDict
import functools, operator
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langchain_core.pydantic_v1 import BaseModel, Field
from dpagent.utils.llm import get_llm
from dpagent.utils.history import historyManager
from dpagent.agents.base import (
    create_agent_normal,
    parse_agent_normal_result,
    create_agent_with_tools,
    create_agent_force_structured_output,
    create_agent_optional_structured_output,
    parse_agent_with_tools_result,
)
from dpagent.agents.Utils.yaml2json.yaml2json import run_yaml2json
from dpagent.config.config import agentMdlCfg
from dpagent.agents.Planning.dfs.PlanMaker.prompt import (
    PlanMaker_plan_prompt,
    PlanMaker_replan_prompt,
    PlanMaker_findwhere_update_prompt,
    PlanMaker_conclude_prompt,
    PlanMaker_decide_update_prompt,
    PlanMaker_howto_update_prompt,
    PlanMaker_plan_conclude_prompt,
    PlanMaker_whole_replan_prompt,
    executor_cap_list_to_str,
)
from dpagent.agents.Tooling.base import ToolSuiteLists



class ToUpdate(BaseModel):
    """Decide whether to update the current subtask"""
    update: bool = Field(
        description="update or not"
    )

class ToUpdatePlan(BaseModel):
    """Decide whether to update the plan"""
    update: bool = Field(
        description="update or not"
    )

class PlanConclusion(BaseModel):
    """Determine whether the objective has been solved"""
    solved: bool = Field(
        description="solved or not"
    )
    description: str = Field(
        description="description of the decision"
    )

# ===================== graph state =====================

class PlanMakeState(TypedDict):
    executor_cap: str
    objective: str
    development_plan: List
    node_task: str
    child_err_node_info: List
    feedback: str
    suggestion: str
    new_subplan: List
    conclusion: str
    updateHere: bool
    needUpdate: bool
    end_conclusion: bool
    end_update_parent: bool
    end_new_subplan: bool
    # past_steps: Annotated[List[Tuple], operator.add]


class PlanMaker:
    def __init__(self, toolSuiteList: ToolSuiteLists=None):
        if toolSuiteList is None:
            self.toolSuiteList = ToolSuiteLists([])
            self.capabilities = ['']
        else:
            self.toolSuiteList = toolSuiteList
            self.capabilities = self.toolSuiteList.get_capabilities()
        self.executor_cap = executor_cap_list_to_str(self.capabilities)
        self.gen_agents()
        self.gen_planMakerGraph()
        self.gen_replanGraph()

    def gen_agents(self):
        llm = get_llm()
        self.planMaker_plan = create_agent_normal(llm, PlanMaker_plan_prompt, name="planMaker_plan")
        self.planMaker_replan = create_agent_normal(
            get_llm(inc=agentMdlCfg.PlanMaker_replan['inc'], model_name=agentMdlCfg.PlanMaker_replan['model_name']), 
            PlanMaker_replan_prompt, name="planMaker_replan"
        )
        self.planMaker_conclude = create_agent_normal(llm, PlanMaker_conclude_prompt, name="planMaker_conclude")
        self.planMaker_howto_update = create_agent_normal(llm, PlanMaker_howto_update_prompt, name="planMaker_howto_update")
        self.planMaker_whole_replan = create_agent_normal(llm, PlanMaker_whole_replan_prompt, name="planMaker_whole_replan")

        self.planMaker_findwhere_update = create_agent_force_structured_output(llm, ToUpdate, PlanMaker_findwhere_update_prompt, name="planMaker_findwhere_update")
        self.planMaker_decide_update = create_agent_force_structured_output(llm, ToUpdatePlan, PlanMaker_decide_update_prompt, name="planMaker_decide_update")
        self.planMaker_plan_conclude = create_agent_force_structured_output(llm, PlanConclusion, PlanMaker_plan_conclude_prompt, name="planMaker_plan_conclude")

    # ===================== nodes =====================

    def run_plan(self, query: str, executor_cap: str=None) -> List:
        if executor_cap is None:
            executor_cap = self.executor_cap
        inputDict = {
            'executor_cap': executor_cap,
            'objective': query,
        }
        out = self.planMaker_plan.invoke(inputDict)
        historyManager.inner()
        json_out = run_yaml2json(parse_agent_normal_result(out))
        historyManager.outer()
        return json_out

    def replan(self, state: PlanMakeState):
        inputDict = {
            'executor_cap': state["executor_cap"],
            'objective': state["objective"],
            'development_plan': state["development_plan"],
            'node_task': state["node_task"],
            'child_err_node_info': state["child_err_node_info"],
            'feedback': state["feedback"],
            'suggestion': state["suggestion"],
        }
        out = self.planMaker_replan.invoke(inputDict)
        historyManager.inner()
        json_out = run_yaml2json(parse_agent_normal_result(out))
        historyManager.outer()
        return {'new_subplan': json_out, 'end_new_subplan': True}

    def run_replan(self, queryDict, executor_cap: str=None):
        if executor_cap is None:
            executor_cap = self.executor_cap
        inputDict = {
            'executor_cap': executor_cap,
            'objective': queryDict['objective'],
            'development_plan': queryDict['development_plan'],
            'node_task': queryDict['node_task'],
            'child_err_node_info': queryDict['child_err_node_info'],
            'feedback': queryDict['feedback'],
            'suggestion': queryDict['suggestion'],
        }
        out = self.planMaker_replan.invoke(inputDict)
        historyManager.inner()
        json_out = run_yaml2json(parse_agent_normal_result(out))
        historyManager.outer()
        return json_out

    def conclude(self, state: PlanMakeState):
        inputDict = {
            'objective': state["objective"],
            'development_plan': state["development_plan"],
            'node_task': state["node_task"],
            'feedback': state["feedback"],
        }
        out = self.planMaker_conclude.invoke(inputDict)
        return {'conclusion': parse_agent_normal_result(out)}

    def howto_update(self, state: PlanMakeState):
        inputDict = {
            'objective': state["objective"],
            'development_plan': state["development_plan"],
            'node_task': state["node_task"],
            'conclusion': state["conclusion"],
        }
        out = self.planMaker_howto_update.invoke(inputDict)
        return {'suggestion': parse_agent_normal_result(out)}

    def findwhere_update(self, state: PlanMakeState):
        inputDict = {
            'objective': state["objective"],
            'development_plan': state["development_plan"],
            'node_task': state["node_task"],
            'child_err_node_info': state["child_err_node_info"],
            'feedback': state["feedback"],
            'suggestion': state["suggestion"],
        }
        out = self.planMaker_findwhere_update.invoke(inputDict)
        ret = {'updateHere': out.update}
        if not out.update:
            ret['end_update_parent'] = True
        return ret

    def decide_update(self, state: PlanMakeState):
        inputDict = {
            'objective': state["objective"],
            'development_plan': state["development_plan"],
            'node_task': state["node_task"],
            'conclusion': state["conclusion"],
        }
        out = self.planMaker_decide_update.invoke(inputDict)
        ret = {'needUpdate': out.update}
        if not out.update:
            ret['end_conclusion'] = True
        return ret

    def run_plan_conclude(self, queryDict):
        inputDict = {
            'objective': queryDict['objective'],
            'development_plan': queryDict['development_plan'],
        }
        out = self.planMaker_plan_conclude.invoke(inputDict)
        return out

    def run_whole_replan(self, queryDict, executor_cap: str=None):
        if executor_cap is None:
            executor_cap = self.executor_cap
        inputDict = {
            'executor_cap': executor_cap,
            'objective': queryDict['objective'],
            'development_plan': queryDict['development_plan'],
            'suggestion': queryDict['suggestion'],
        }
        out = self.planMaker_whole_replan.invoke(inputDict)
        historyManager.inner()
        json_out = run_yaml2json(parse_agent_normal_result(out))
        historyManager.outer()
        return json_out

    # ===================== planMakerGraph =====================

    def enter_chain(self, chain_in):
        init_state = {
            "executor_cap": self.executor_cap,
            "objective": chain_in['objective'],
            "development_plan": chain_in['development_plan'],
            "node_task": chain_in['node_task'],
            'feedback': chain_in["feedback"],
            'child_err_node_info': chain_in["child_err_node_info"],
            "end_conclusion": False,
            "end_update_parent": False,
            "end_new_subplan": False
        }
        return init_state

    def gen_planMakerGraph(self):
        planMakerGraph = StateGraph(PlanMakeState)
        planMakerGraph.add_node("replan", self.replan)
        planMakerGraph.add_node("conclude", self.conclude)
        planMakerGraph.add_node("howto_update", self.howto_update)
        planMakerGraph.add_node("findwhere_update", self.findwhere_update)
        planMakerGraph.add_node("decide_update", self.decide_update)

        planMakerGraph.add_edge("conclude", "decide_update")
        planMakerGraph.add_edge("howto_update", "findwhere_update")
        planMakerGraph.add_edge("replan", END)

        planMakerGraph.add_conditional_edges(
            "decide_update",
            lambda state: state['needUpdate'],
            {False: END, True: 'howto_update'},
        )

        planMakerGraph.add_conditional_edges(
            "findwhere_update",
            lambda state: state['updateHere'],
            {False: END, True: 'replan'},
        )

        planMakerGraph.set_entry_point("conclude")
        planMakerChain = self.enter_chain | planMakerGraph.compile()
        self.planMakerGraph = planMakerGraph
        self.planMakerChain = planMakerChain

# ===================== replanGraph =====================

    def gen_replanGraph(self):
        replanGraph = StateGraph(PlanMakeState)
        replanGraph.add_node("replan", self.replan)
        replanGraph.add_node("findwhere_update", self.findwhere_update)

        replanGraph.add_edge("replan", END)

        replanGraph.add_conditional_edges(
            "findwhere_update",
            lambda state: state['updateHere'],
            {False: END, True: 'replan'},
        )

        replanGraph.set_entry_point("findwhere_update")
        replanChain = self.enter_chain | replanGraph.compile()
        self.replanGraph = replanGraph
        self.replanChain = replanChain



if __name__ == '__main__':
    from dpagent.agents.Tooling.WebSearch.WebSearch import webSearchChainSuite
    toolSuiteList = ToolSuiteLists([webSearchChainSuite])
    executor_cap_list = [
        'Search the Internet',
        'Retrieve the information from the document',
    ]
    planMaker = PlanMaker(toolSuiteList)
    plan_input = {
        'executor_cap': executor_cap_list_to_str(executor_cap_list),
        'objective': 'what is the hometown of the 2024 Australia open winner?',
    }
    if False:
        planMaker_plan_out = planMaker.planMaker_plan.invoke(plan_input)
        print(parse_agent_normal_result(planMaker_plan_out))
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
    decide_update_input = {
        'executor_cap': executor_cap_list_to_str(executor_cap_list),
        'objective': 'what is the hometown of the 2024 Australia open winner?',
        'development_plan': development_plan_exp1,
        'node_task': 'Sports news articles profiling the winner',
        'conclusion': 'No news about the winner',
    }
    if False:
        planMaker_decide_update_out = planMaker.planMaker_decide_update.invoke(decide_update_input)
        print(planMaker_decide_update_out.update)
    if True:
        development_plan_exp2 = planMaker.run_plan(query='what is the hometown of the 2024 Australia open winner?')
    development_plan_exp3 = [
        {
            'desc': 'Identify the 2024 Australian Open winner',
            'children': [{
                'desc': "Check the official Australian Open website for the winner's name",
                'children': []
            }, {
                'desc': 'Look for recent news articles or press releases about the 2024 Australian Open',
                'children': []
            }, {
                'desc': 'Check reputable sports news websites for information on the tournament results',
                'children': []
            }, {
                'desc': 'Use social media platforms for any official announcements from the Australian Open accounts',
                'children': []
            }]
        }, {
            'desc': "Research the winner's hometown",
            'children': [{
                'desc': 'Use search engines with the winner\'s name and terms like "biography," "profile," or "hometown"',
                'children': []
            }, {
                'desc': "Visit the winner's official website or social media profiles if available",
                'children': []
            }, {
                'desc': "Look for the winner's profile on the official Australian Open website or ATP/WTA profiles",
                'children': []
            }, {
                'desc': 'Check sports databases and encyclopedias that may contain personal information about athletes',
                'children': []
            }]
        }, {
            'desc': 'Verify the information',
            'children': [{
                'desc': 'Cross-reference the found hometown with multiple reliable sources',
                'children': []
            }, {
                'desc': 'Ensure the information is up-to-date and pertains to the correct individual',
                'children': []
            }]
        }
    ]
    chain_input = {
        'executor_cap': executor_cap_list_to_str(executor_cap_list),
        'objective': 'what is the hometown of the 2024 Australia open winner?',
        'development_plan': development_plan_exp3,
        'node_task': 'Look for recent news articles or press releases about the 2024 Australian Open',
        'feedback': 'New York Times reports that the winner is from New York',
        'child_err_node_info': []
    }
    if False:
        new_subtask_exp1 = planMaker.run_replan({**chain_input, **{'suggestion': 'Be more specific'}})
    if False:
        plan_conclude_out = planMaker.run_plan_conclude(chain_input)
    if False:
        whole_replan_out = planMaker.run_whole_replan({**chain_input, **{'suggestion': 'Be more specific'}})
    if False:
        planMakerChain_out = planMaker.planMakerChain.invoke(chain_input)
        if planMakerChain_out['end_conclusion']:
            print('end_conclusion with conclusion:', planMakerChain_out['conclusion'])
        if planMakerChain_out['end_update_parent']:
            print('end_update_parent with conclusion:', planMakerChain_out['conclusion'], '\n and suggestion:', planMakerChain_out['suggestion'])
        if planMakerChain_out['end_new_subplan']:
            print('end_new_subplan with new_subplan:', planMakerChain_out['new_subplan'])
    pass



