from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from dpagent.agents.Planning.prompt import development_plan


ActionSeqMaker_sys_prompt = """
You are an assistant specializing in software or embedded system development projects. 
Your goal is to bridge the gap between high-level planning and practical implementation, ensuring that the Plan Maker's vision is realized through precise, executable steps.

Your primary responsibility is to decompose tasks provided by the Planer Maker into clearly defined and logically ordered action sequences to facilitate efficient execution by the Action Executors.
The actions can be executed by Action Executors are listed as follows:
[{Action_Executors}]

Specifically, your task includes:
1. Analyzing subtasks produced by the Plan Maker.
2. Developing a step-by-step action plan that outlines exactly what needs to be done to execute each subtask identified in the Plan Maker's output. 
This involves specifying the sequence of actions in a clear, logical order to ensure they can be executed by Action Executors.

"""

"""You are an assistant in software or embedded system development.\
Given an objective, a Plan Maker will break down it into subtasks, and your duty is to create a sequence of actions to execute the tasks.\
You will cooperate with a the following Action Executors: [{Action_Executors}], they will do the execution."""

ActionSeqMaker_make_actionseq_human_prompt = """The development objective is as follows:
---
{{objective}}
---

Plan Maker made a plan to break down the objective into subtasks, and currently we are focusing on the subtask of:
---
""" + development_plan + \
"""---

The ongoing subtask is:
--- [curr_subtask] ---
{{node_task}}
---

You should break down the [curr_subtask] into a sequence of actions, and call the corresponding Action Executor to execute the action.
The action sequence should be in YAML format. For example:
- action 1
- action 2
- action 3

If you think the subtask is not detailed enough or the information is not adequate to generate a executable action sequence, say NOT EXECUTABLE and explain the reason:
"""


ActionSeqMaker_update_actionseq_human_prompt = """The development objective is as follows:
---
{{objective}}
---

Plan Maker made a plan to break down the objective into subtasks, the ongoing subtask is:
--- [curr_subtask] ---
{{node_task}}
---

We plan to break down the [curr_subtask] into a sequence of actions as follows:
--- [curr_actionseq] ---
{{action_seq}}
---

However, the [curr_actionseq] is not executable due to the following reason:
---
{{refine_reason}}
---

Now you should refine the [curr_actionseq] to make it executable. Remember to keep the action sequence in YAML format.

If you think the subtask is not detailed enough or the information is not adequate to generate a executable action sequence, say NOT EXECUTABLE and explain the reason:"""


ActionSeqMaker_check_actionseq_human_prompt = """The development objective is as follows:
---
{{objective}}
---

Plan Maker made a plan to break down the objective into subtasks, the ongoing subtask is:
--- [curr_subtask] ---
{{node_task}}
---

We tried to break down the [curr_subtask] into a sequence of actions:
--- [curr_actionseq] ---
{{action_seq}}
---

The requirements for the action sequence are that it should be executable and in the correct YAML format. You need to make two decisions: 
1. Determine whether the [curr_actionseq] meets the requirements.
2. Decide if you require more information to make the action sequence executable if it does not meet the requirements. 
Additionally, please provide reasons or suggestions to support your decisions.
"""


# Not used
ActionSeqMaker_check_need_moreinfo_human_prompt = """The development objective is as follows:
---
{{objective}}
---

Plan Maker made a plan to break down the objective into subtasks, the ongoing subtask is:
--- [curr_subtask] ---
{{node_task}}
---

We tried to break down the [curr_subtask] into a sequence of actions:
--- [curr_actionseq] ---
{{action_seq}}
---

Now you should decide whether you need more information to make the action sequence executable."""


ActionSeqMaker_run_actionseq_human_prompt = """The development objective is as follows:
---
{{objective}}
---

Plan Maker made a plan to break down the objective into subtasks, the ongoing subtask is:
--- [curr_subtask] ---
{{node_task}}
---

We break down the [curr_subtask] into a sequence of actions as follows:
--- [curr_actionseq] ---
{{action_seq}}
---

Now you should call the Action Executors to execute the [curr_actionseq] one by one.
"""


ActionSeqMaker_conclude_actionseq_run_human_prompt = """Plan Maker made a plan to break down the objective into subtasks, the ongoing subtask is:
--- [curr_subtask] ---
{{node_task}}
---

We break down the [curr_subtask] into a sequence of actions as follows:
--- [curr_actionseq] ---
{{action_seq}}
---

The execution of the [curr_actionseq] obtains the following feedback:
--- [curr_feedback] ---
{{feedback}}
---

Now you should conclude the execution of the [curr_actionseq] according to [curr_feedback]. If the execution is successful, give a brief summary of the execution result. If the execution is failed, conclude the reason and suggestions."""


ActionSeqMaker_decide_actionseq_call_finish_human_prompt = """Plan Maker made a plan to break down the objective into subtasks, the ongoing subtask is:
--- [curr_subtask] ---
{{node_task}}
---

We break down the [curr_subtask] into a sequence of actions as follows:
--- [curr_actionseq] ---
{{action_seq}}
---

Here is the conclusion of the execution of the [curr_actionseq]:
---
{{conclusion}}
---

Now you should determine whether the execution of the [curr_actionseq] is complete. If you think the execution is successful or it failed but a retry is not necessary, then the answer is Yes. If you think the execution is failed and there is a chance of success upon retrying, the answer is No."""


ActionSeqMaker_make_actionseq_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(ActionSeqMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(ActionSeqMaker_make_actionseq_human_prompt, template_format="jinja2"),
    ]
)

ActionSeqMaker_update_actionseq_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(ActionSeqMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(ActionSeqMaker_update_actionseq_human_prompt, template_format="jinja2"),
    ]
)

ActionSeqMaker_check_actionseq_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(ActionSeqMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(ActionSeqMaker_check_actionseq_human_prompt, template_format="jinja2"),
    ]
)

ActionSeqMaker_check_need_moreinfo_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(ActionSeqMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(ActionSeqMaker_check_need_moreinfo_human_prompt, template_format="jinja2"),
    ]
)

ActionSeqMaker_run_actionseq_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(ActionSeqMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(ActionSeqMaker_run_actionseq_human_prompt, template_format="jinja2"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

ActionSeqMaker_conclude_actionseq_run_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(ActionSeqMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(ActionSeqMaker_conclude_actionseq_run_human_prompt, template_format="jinja2"),
    ]
)

ActionSeqMaker_decide_actionseq_call_finish_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(ActionSeqMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(ActionSeqMaker_decide_actionseq_call_finish_human_prompt, template_format="jinja2"),
    ]
)



if __name__ == '__main__':
    from dpagent.agents.base import print_ChatPromptValue
    development_plan_exp1 = [{
            "desc": "task1",
            "children": [
                {
                    "desc": "task1.2",
                    "children": [{
                            "desc": "task1.2.1",
                            "children": []
                        },
                        {
                            "desc": "task1.2.2",
                            "children": []
                        }
                    ]
                },
            ]
        },
    ]
    action_executors = ['retrieve_db', 'retrieve_docs', 'retrieve_codes', 'explain_codes']
    input = {
        'objective': 'the objective',
        'development_plan': development_plan_exp1,
        'node_task': 'task1.2.1',
        'Action_Executors': ', '.join(action_executors),
        'action_seq': '- action 1\n- action 2\n- action 3',
        'refine_reason': 'not detailed enough',
        'feedback': 'execution failed due to network error',
        'conclusion': 'The execution failed due to network error, need to try again',
    }
    print('==== ActionSeqMaker_make_actionseq_prompt ====\n\n')
    print_ChatPromptValue(ActionSeqMaker_make_actionseq_prompt.invoke(input))
    print('==== ActionSeqMaker_update_actionseq_prompt ====\n\n')
    print_ChatPromptValue(ActionSeqMaker_update_actionseq_prompt.invoke(input))
    print('==== ActionSeqMaker_check_actionseq_prompt ====\n\n')
    print_ChatPromptValue(ActionSeqMaker_check_actionseq_prompt.invoke(input))
    print('==== ActionSeqMaker_check_need_moreinfo_prompt ====\n\n')
    print_ChatPromptValue(ActionSeqMaker_check_need_moreinfo_prompt.invoke(input))
    print('==== ActionSeqMaker_run_actionseq_prompt ====\n\n')
    print_ChatPromptValue(ActionSeqMaker_run_actionseq_prompt.invoke({**input, **{'agent_scratchpad': []}}))
    print('==== ActionSeqMaker_conclude_actionseq_run_prompt ====\n\n')
    print_ChatPromptValue(ActionSeqMaker_conclude_actionseq_run_prompt.invoke(input))
    print('==== ActionSeqMaker_decide_actionseq_call_finish_prompt ====\n\n')
    print_ChatPromptValue(ActionSeqMaker_decide_actionseq_call_finish_prompt.invoke(input))

