from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)


yaml2json_sys_prompt = """You will be given a tree-structured developmemt plan in YAML format, and you should convert it into a nested JSON tree format.
In each level of the json dict, it contains two keys: 'desc' and 'children'. \
The 'desc' key is a string that describes the subtask of the node. \
The 'children' key is a list of subtasks that are the children of the current node. \
Note that the depth of the tree is not limited, it should be the same with the developmemt plan tree.

For example, given the YAML-formatted development plan:
---
- task1
    - task1.1
    - task1.2
        - task1.2.1
        - task1.2.2
    - task1.3
- task2
---
It will be convert to:
```
[
    {
        "desc": "task1",
        "children": [
            {
                "desc": "task1.1",
                "children": []
            },
            {
                "desc": "task1.2",
                "children": [
                    {
                        "desc": "task1.2.1",
                        "children": []
                    }
                ]
            },
        ]
    },
    {
        "desc": "task2",
        "children": []
    }
]
```"""

yaml2json_human_prompt = """Now the developmemt plan is:
{development_plan_yaml}"""


yaml2json_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(yaml2json_sys_prompt, template_format="jinja2"),
        HumanMessagePromptTemplate.from_template(yaml2json_human_prompt),
    ]
)


