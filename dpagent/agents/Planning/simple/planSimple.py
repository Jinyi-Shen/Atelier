from typing import Annotated, List, Tuple, Union
from typing_extensions import TypedDict
import functools, operator
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langchain_core.pydantic_v1 import BaseModel, Field
from dpagent.utils.llm import get_llm
from dpagent.agents.base import create_agent_with_tools, create_agent_force_structured_output, create_agent_optional_structured_output, parse_agent_with_tools_result
from dpagent.agents.Tooling.WebSearch.tool import tavily_tool
from dpagent.config.config import agentMdlCfg
from dpagent.agents.Planning.simple.prompt import executor_prompt, planner_prompt, replanner_prompt


# ===================== graph state =====================

class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str


# ===================== nodes =====================

llm = get_llm()

executor = create_agent_with_tools(llm, [tavily_tool], executor_prompt, name='executor')


class Plan(BaseModel):
    """Plan to follow in future"""
    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )

class Response(BaseModel):
    """Response to user."""
    response: str

planner = create_agent_force_structured_output(llm, Plan, planner_prompt, name='planner')

replanner = create_agent_optional_structured_output(llm, [Plan, Response], replanner_prompt, name='replanner')


def execute_step(state: PlanExecute):
    task = state["plan"][0]
    agent_response = executor.invoke({"input": task, "chat_history": []})
    return {
        "past_steps": (task, parse_agent_with_tools_result(agent_response))
    }


def plan_step(state: PlanExecute):
    plan = planner.invoke({"objective": state["input"]})
    return {"plan": plan.steps}


def replan_step(state: PlanExecute):
    output = replanner.invoke(state)
    if isinstance(output, Response):
        return {"response": output.response}
    else:
        return {"plan": output.steps}


def should_end(state: PlanExecute):
    # if state["response"]:
    if "response" in state:
        return True
    else:
        return False


# ===================== graph =====================

def gen_graph():
    workflow = StateGraph(PlanExecute)
    # Add the plan node
    workflow.add_node("planner", plan_step)
    # Add the execution step
    workflow.add_node("agent", execute_step)
    # Add a replan node
    workflow.add_node("replan", replan_step)
    # From plan we go to agent
    workflow.add_edge("planner", "agent")
    # From agent, we replan
    workflow.add_edge("agent", "replan")
    workflow.add_conditional_edges(
        "replan",
        # Next, we pass in the function that will determine which node is called next.
        should_end,
        {
            # If `tools`, then we call the tool node.
            True: END,
            False: "agent",
        },
    )
    workflow.set_entry_point("planner")
    # Finally, we compile it! This compiles it into a LangChain Runnable, meaning you can use it as you would any other runnable
    chain = workflow.compile()
    return chain

def enter_chain(input: str):
    return {"input": input}


plan_simple_chain = enter_chain | gen_graph()


if __name__ == '__main__':
    config = {"recursion_limit": 50}
    inputs = "what is the hometown of the 2024 Australia open winner?"
    for event in plan_simple_chain.stream(inputs, config=config):
        for k, v in event.items():
            if k != "__end__":
                print(v)
