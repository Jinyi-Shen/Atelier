from typing import Any, Callable, List, Optional, TypedDict, Union
from langchain_core.pydantic_v1 import BaseModel, Field
from dpagent.agents.Utils.yaml2json.prompt import yaml2json_prompt
from dpagent.utils.llm import get_llm
from dpagent.config.config import agentMdlCfg
from dpagent.utils.treeDict import PlanTreeDict
from dpagent.agents.base import create_agent_force_structured_output_by_funcdict, create_agent_force_structured_output


yaml2json_llm = get_llm(inc=agentMdlCfg.yaml2json['inc'], model_name=agentMdlCfg.yaml2json['model_name'])


yaml2json_funcdict = {
    "name": "yaml2json",
    "description": "Generate json-formatted development plan tree.",
    "parameters": {
        "type": "object",
        "properties": {
            "tree": {
                "type": "array",
                "description": "Json-formatted development plan tree, representing the tree with a nested structure.",
                "items": {
                    "properties": {
                        "desc": {
                            "type": "string",
                            "description": "Description of the node of the development plan tree.",
                        },
                        "children": {
                            "type": "array",
                            "description": "The list of child nodes of the node in the development plan tree.",
                            "properties": {
                                "desc": {
                                    "type": "string",
                                    "description": "Description of child node of the node of the development plan tree.",
                                },
                                "children": {
                                    "type": "array",
                                    "description": "The list of child nodes of the node in the development plan tree.",
                                },
                            },
                            "required": ["desc", "children"],
                        },
                    },
                    "required": ["desc", "children"],
                },
            },
        },
        "required": ["tree"],
    },
}


class JsonTree(BaseModel):
    """Generate json-formatted development plan tree"""
    desc: str = Field(
        description="Description of the node of the development plan tree"
    )
    children: list = Field(
        description="The list of child nodes of the node in the development plan tree"
    )

class JsonTreeList(BaseModel):
    """Generate list of json-formatted development plan tree"""
    tree: List[JsonTree] = Field(
        description="Json-formatted development plan tree, representing the tree with a nested structure."
    )


yaml2json_agent_funcdict = create_agent_force_structured_output_by_funcdict(yaml2json_llm, yaml2json_funcdict, yaml2json_prompt, name='yaml2json_agent_funcdict')
yaml2json_agent_force = create_agent_force_structured_output(yaml2json_llm, JsonTreeList, yaml2json_prompt, name='yaml2json_agent_force')
yaml2json_agent = yaml2json_agent_force


def run_yaml2json(yamlin, retryNum=5) -> List[PlanTreeDict]:
    for i in range(retryNum):
        try:
            yaml2json_agent_out = yaml2json_agent.invoke({'development_plan_yaml': yamlin})
            list_dict = parse_agent_out_to_list_dict(yaml2json_agent_out)
            valid, _ = check_json_key(list_dict)
            if valid:
                return [PlanTreeDict(dicti) for dicti in list_dict]
        except Exception as e:
            continue
    return [PlanTreeDict({'desc': yamlin, 'children': []})]

def parse_agent_out_to_list_dict(output: JsonTreeList) -> List[dict]:
    outlist = []
    for subplan in output.tree:
        outlist.append(subplan.dict())
    return outlist

def check_json_key(jsonin):
    try:
        ret = check_json_list(jsonin)
        if ret[0] == True:
            return (True, jsonin)
        else:
            return ret
    except Exception as e:
        return (False, e)

def check_json_list(listin):
    if not isinstance(listin, list):
        return (False, "{listin} is not a list".format(listin=listin))
    for dicti in listin:
        reti = check_json_dict(dicti)
        if reti[0] == False:
            return reti
    return (True, None)

def check_json_dict(dictin):
    if not isinstance(dictin, dict):
        return (False, "{dictin} is not a dict".format(dictin=dictin))
    if not 'desc' in dictin:
        return (False, "KeyError: 'desc' in {dictin}\n No such key: 'desc'".format(dictin=dictin))
    if not 'children' in dictin:
        return (False, "KeyError: 'children' in {dictin}\n No such key: 'children'".format(dictin=dictin))
    if not isinstance(dictin['desc'], str):
        return (False, "TypeError: 'desc' in {dictin} is not a string".format(dictin=dictin))
    if not isinstance(dictin['children'], list):
        return (False, "TypeError: 'children' in {dictin} is not a list".format(dictin=dictin))
    ret = check_json_list(dictin['children'])
    if ret[0] == False:
        return ret
    return (True, None)



if __name__ == '__main__':
    development_plan_yaml = """\
- task1
    - task1.1
    - task1.2
        - task1.2.1
        - task1.2.2
    - task1.3
- task2"""
    if False:
        yaml2json_agent_out = yaml2json_agent.invoke({"development_plan_yaml": development_plan_yaml})
        print(yaml2json_agent_out['tree'])
    right_json = [
        {
            "desc": "Main Task 1: Identify the 2024 Australia Open winner",
            "children": [
                {
                    "desc": "Subtask 1.1: Monitor the Australia Open tournament",
                    "children": [
                        {
                            "desc": "Subtask 1.1.1: Set up alerts for match results using sports news apps and websites",
                            "children": []
                        },
                        {
                            "desc": "Subtask 1.1.2: Watch the matches or follow live updates",
                            "children": []
                        }
                    ]
                },
                {
                    "desc": "Subtask 1.2: Confirm the winner once the tournament concludes",
                    "children": [
                        {
                            "desc": "Subtask 1.2.1: Check official Australia Open website for the final results",
                            "children": []
                        },
                        {
                            "desc": "Subtask 1.2.2: Verify through multiple trusted sports news sources",
                            "children": []
                        }
                    ]
                },
                {
                    "desc": "Main Task 2: Research the winner's personal details",
                    "children": [
                        {
                            "desc": "Subtask 2.1: Search for the winner's biographical data online",
                            "children": [
                                {
                                    "desc": "Subtask 2.1.1: Use search engines with queries like \"2024 Australia Open winner biography\"",
                                    "children": []
                                },
                                {
                                    "desc": "Subtask 2.1.2: Visit sports analytics and statistics websites",
                                    "children": []
                                }
                            ]
                        },
                        {
                            "desc": "Subtask 2.2: Access interviews and personal profiles",
                            "children": [
                                {
                                    "desc": "Subtask 2.2.1: Look for interviews on sports networks like ESPN, BBC Sports, etc.",
                                    "children": []
                                },
                                {
                                    "desc": "Subtask 2.2.2: Explore profiles in sports magazines and websites",
                                    "children": []
                                }
                            ]
                        },
                        {
                            "desc": "Main Task 3: Determine the winner's hometown",
                            "children": [
                                {
                                    "desc": "Subtask 3.1: Extract hometown information from the researched data",
                                    "children": [
                                        {
                                            "desc": "Subtask 3.1.1: Review biographical details found online for mentions of hometown",
                                            "children": []
                                        },
                                        {
                                            "desc": "Subtask 3.1.2: Check for any direct mentions in interviews or profiles",
                                            "children": []
                                        }
                                    ]
                                },
                                {
                                    "desc": "Subtask 3.2: Confirm the information",
                                    "children": [
                                        {
                                            "desc": "Subtask 3.2.1: Cross-verify with other reputable sources",
                                            "children": []
                                        },
                                        {
                                            "desc": "Subtask 3.2.2: Check for consistency in the information across various platforms",
                                            "children": []
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    wrong_json = [
        {
            "Main Task 1: Monitor and identify the winner of the 2024 Australian Open": [
                {
                    "Subtask 1.1: Follow the Australian Open through reliable sports news sources and broadcasts": []
                },
                {
                    "Subtask 1.2: Set alerts for match results and final winner announcements": []
                },
                {
                    "Subtask 1.3: Verify the winner's name once the tournament concludes": []
                }
            ]
        },
        {
            "Main Task 2: Research the winner's background": [
                {
                    "Subtask 2.1: Use search engines to find detailed biographies and interviews": []
                },
                {
                    "Subtask 2.2: Check sports databases and the official Australian Open website for player profiles": []
                },
                {
                    "Subtask 2.3: Visit social media profiles and official athlete pages to gather personal information": []
                }
            ]
        },
        {
            "Main Task 3: Determine the hometown of the winner": [
                {
                    "Subtask 3.1: Extract hometown information from the collected data in Task 2": []
                },
                {
                    "Subtask 3.2: Verify the hometown by cross-referencing multiple sources for accuracy": []
                }
            ]
        },
        {
            "Main Task 4: Compile and report the information": [
                {
                    "Subtask 4.1: Summarize the findings in a concise report": []
                },
                {
                    "Subtask 4.2: Prepare to present or publish the information as required by the context or requester": []
                }
            ]
        }
    ]
    if False:
        ret1 = check_json_key(right_json)
        ret2 = check_json_key(wrong_json)
    if False:
        yaml2json_agent_out2 = run_yaml2json(development_plan_yaml, retryNum=5)
    pass

