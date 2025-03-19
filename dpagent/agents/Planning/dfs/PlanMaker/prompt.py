from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from dpagent.agents.Planning.prompt import development_plan, child_err_node_info

# consider adding a brief introduction about what kinds of objectives the assistant can help plan for
# it might be beneficial to include an example of an objective and how the assistant would approach it, followed by the YAML format explanation
# define what is the actionable tasks

PlanMaker_sys_prompt = """You are an assistant tasked with creating a detailed plan to achieve a specified objective. You will collaborate closely with the Executor. Your role is to decompose the main objective into a series of smaller, actionable tasks. The Executor will execute these tasks and provide feedback on their outcomes. Based on this feedback, you will refine the plan as needed to ensure the objective is achieved."""

PlanMaker_executor_info_prompt = """The Executor is equipped with the following capabilities, remember the plan you make should not exceed the capability of the Executor:
{executor_cap}"""

"""You are an assistant who can help create a plan for a given objective. \
You will break down the objective into smaller tasks that can be executed to achieve the final goal. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps.
The plan should be nested List of subtasks, and in YAML format. For example:
```
- subtask 1
  - subtask 1.1
  - subtask 1.2
    - subtask 1.2.1
    - subtask 1.2.2
  - subtask 1.3
- subtask2
- subtask3
  - subtask 3.1
```
"""


PlanMaker_plan_sys_prompt = PlanMaker_sys_prompt + "\n\n" + PlanMaker_executor_info_prompt + "\n\n" + """When breaking down the objective into tasks, ensure that each step is essential and directly contributes to the objective, avoid including unnecessary actions.
Structure the plan as a nested list, where each major task can contain subtasks. Subtasks may further contain their own subtasks, creating a hierarchical outline of what needs to be done. Use YAML format for clear and structured representation. 

For instance, the plan should look something like this:
```
- Main Task 1:
  - Subtask 1.1
  - Subtask 1.2:
    - Subtask 1.2.1
    - Subtask 1.2.2
  - Subtask 1.3
- Main Task 2
- Main Task 3:
  - Subtask 3.1
```
This format ensures that the plan is organized and each task's relation to the overall objective is clear."""

PlanMaker_plan_human_prompt = """Given the objective as follows:
---
{objective}
---

Create a plan for the objective"""

PlanMaker_replan_sys_prompt = PlanMaker_sys_prompt + "\n\n" + PlanMaker_executor_info_prompt + "\n\n" + """Your current task is to update a structured project plan based on feedback from the Executor. You'll be provided with a hierarchical plan in YAML format, detailing the tasks and subtasks necessary to achieve the main objective.
For instance, the initial plan [init_plan] might look like this:
```
- Main Task 1:
  - Subtask 1.1
  - [curr_subtask]:
    - Subtask 1.2.1
    - Subtask 1.2.2
  - Subtask 1.3
- Main Task 2
```
where Subtask 1.2 is the [curr_subtask].

Your task is to focus on the specific subtask the Executor is currently working on, indicated by [curr_subtask]. Based on the feedback related to [curr_subtask], you need to propose an updated subtask plan [new_subplan] to replace [curr_subtask]. 

The [new_subplan] will be YAML-formatted, it can either be a simple sentence replacing the [curr_subtask], or a detailed, nested Dict structure including only ONE key.
Examples for [curr_subtask] are:
1. Simple sentence:
```
- <New Subtask>
```
2. Nested Dict structure:
```
<New Subtask>:
  - <item 1>
  - <item 2>
  - <item 3>
```

Note that the [new_subplan] should strictly replace [curr_subtask] without introducing any other tasks in [init_plan] and must be formatted correctly as either a sentence or a YAML dictionary with only one key.
"""

PlanMaker_replan_human_prompt = """Given the objective as follows:
---
{{objective}}
---

We made a plan to break down the objective into subtasks:
--- [init_plan] ---
""" + development_plan + \
"""---

During executing the current subtask:
--- [curr_subtask] ---
{{node_task}}
---

{% if child_err_node_info|length > 0 %}
We execute it with the following step, and get the feedback:
---
""" + child_err_node_info + \
"""---
{% else %}
We get the following feedback:
---
{{feedback}}
---
{% endif %}

The suggestion of Executor is as follows:
---
{{suggestion}}
---

Now you should write the [new_subplan] to replace the [curr_subtask], remember not to include any other tasks in [init_plan] and not to perform the same operation as other parts of [init_plan]."""

PlanMaker_replan_critic_sys_prompt = """
You are an assistant collaborating with a PlanMaker to update a structured project plan based on feedback from an Executor. The plan is in YAML format and consists of tasks and subtasks necessary to achieve a specific objective.

Current Plan Example:
```
- Main Task 1:
  - Subtask 1.1
  - [curr_subtask]:
    - Subtask 1.2.1
    - Subtask 1.2.2
  - Subtask 1.3
- Main Task 2
```

Where [curr_subtask] is the specific subtask the Executor is currently working on. The PlanMaker will provide you with an updated subtask plan ([new_subplan]) to replace the [curr_subtask], based on the Executor's feedback. The [new_subplan] will be YAML-formatted, it can either be a simple sentence replacing the [curr_subtask], or a detailed, nested Dict structure.

Example replacements for [curr_subtask] ('Subtask 1.2'):
1. Simple sentence:
```
- <New Subtask>
```
2. Nested Dict structure:
```
<New Subtask>:
  - <item 1>
  - <item 2>
  - <item 3>
```

The [new_subplan] should strictly replace [curr_subtask] without introducing unrelated tasks and must be formatted correctly as a YAML dictionary.

Your task is to verify and potentially adjust the [new_subplan] provided by the PlanMaker to ensure the following [Requirements] are met:
1. It exclusively replaces [curr_subtask] and includes no unrelated tasks.
2. It does not duplicate any operations from other parts of the original plan.
3. It maintains the correct YAML dictionary format. Note that list structure is not allowed

If the [new_subplan] meets these requirements, reiterate it for confirmation. If not, adjust it accordingly. DO NOT merge it with the original plan.
"""

PlanMaker_replan_critic_human_prompt = """Given the objective as follows:
---
{{objective}}
---

The PlanMaker made a plan to break down the objective into subtasks:
--- [init_plan] ---
""" + development_plan + \
"""---

During executing the current subtask:
--- [curr_subtask] ---
{{node_task}}
---

After obtaining the feedback of the current task, the PlanMaker has proposed the following updated subtask plan [new_subplan] to replace [curr_subtask]:
---
{{new_subplan}}
---

Now you should verify and potentially adjust the [new_subplan] to meet the [Requirements]:
"""

PlanMaker_findwhere_update_sys_prompt = PlanMaker_sys_prompt + "\n\n" + """You are tasked with updating a structured project plan based on feedback provided by the Executor, who is responsible for implementing the plan. The plan is presented in hierarchical YAML format, detailing the tasks and subtasks necessary to achieve the main objective.
For instance, the initial plan might look like this:
```
- Main Task 1:
  - Subtask 1.1
  - Subtask 1.2:
    - Subtask 1.2.1
    - Subtask 1.2.2
  - Subtask 1.3
- Main Task 2
```

You need to identify and focus on the specific subtask the Executor is currently working on, indicated by [curr_subtask]. Based on the feedback related to [curr_subtask], you need to decide whether to modify just the [curr_subtask] or its parent task.

If modifying the [curr_subtask] is sufficient, your answer will be True, then we will replace the [curr_subtask] with an updated subtask plan [new_subplan]. For example:
```
- Main Task 1:
  - Subtask 1.1
  - [new_subplan]   # This replaces Subtask 1.2
  - Subtask 1.3
- Main Task 2
```

If a broader modification is needed, your answer will be False, then we will replace the entire parent task of [curr_subtask]. For instance:
```
- [new_subplan]    # This replaces all of Main Task 1
- Main Task 2
```"""

PlanMaker_findwhere_update_human_prompt = """Given the objective as follows:
---
{{objective}}
---

We made a plan to break down the objective into subtasks, and currently we are focusing on the subtask of:
---
""" + development_plan + \
"""---

During executing the current subtask:
--- [curr_subtask] ---
{{node_task}}
---

{% if child_err_node_info|length > 0 %}
We execute it with the following step, and get the feedback:
---
""" + child_err_node_info + \
"""---
{% else %}
We get the following feedback:
---
{{feedback}}
---
{% endif %}

The Executor gives the following suggestions:
---
{{suggestion}}
---

Now we want to modify the plan. According to the feedback, you should decide whether to modify just the [curr_subtask] or its parent task. If modifying the [curr_subtask] is sufficient, your answer will be True. If a broader modification is needed, your answer will be False."""

PlanMaker_conclude_human_prompt = """Given the objective as follows:
---
{{objective}}
---
We made a plan to break down the objective into subtasks, and currently we are focusing on the subtask of:
---
""" + development_plan + \
"""---

During executing the current subtask:
--- [curr_subtask] ---
{{node_task}}
---
We get the following feedback:
---
{{feedback}}
---

Now you should conclude the execution of the [curr_subtask] according to the task itself and the feedback. \
If the execution is successful, then you should conclude the information gain from the execution. \
If the execution fails, then you should conclude the reason of failure. \
If the subtask requires more information to be executable, then you should conclude what kind of information is required.
Keep your conclusion brief and clear, ensuring it includes both the task description and the outcomes of the [curr_subtask] execution.
The conclusion should be in plain text, DO NOT include any structured elements."""

PlanMaker_decide_update_human_prompt = """Given the objective as follows:
---
{{objective}}
---
We made a plan to break down the objective into subtasks, and currently we are focusing on the subtask of:
---
""" + development_plan + \
"""---

We just executed the subtask:
--- [curr_subtask] ---
{{node_task}}
---
The conclusion of the execution of [curr_subtask] is:
---
{{conclusion}}
---

According to the conclusion, now you should decide whether should we update the whole plan."""

PlanMaker_howto_update_human_prompt = """Given the objective as follows:
---
{{objective}}
---
We made a plan to break down the objective into subtasks, and currently we are focusing on the subtask of:
---
""" + development_plan + \
"""---

We just executed the subtask:
--- [curr_subtask] ---
{{node_task}}
---
The conclusion of the execution of [curr_subtask] is:
---
{{conclusion}}
---

According to the conclusion, now you should provide a concise suggestion on how to update the whole plan, keep it brief and clear. The suggestion should be in plain text, DO NOT include any structured elements."""

PlanMaker_plan_conclude_human_prompt = """Given the objective as follows:
---
{{objective}}
---

We made a plan to break down the objective into subtasks, the execution of subtasks are all finished. The plan and the conclusion of the subtasks are as follows:
---
""" + development_plan + \
"""---

Now you should determine whether the objective has been solved, and provide the reason in brief for your decision.
"""

PlanMaker_whole_replan_sys_prompt = PlanMaker_sys_prompt + "\n\n" + PlanMaker_executor_info_prompt + "\n\n" + """Your current task is to update a structured project plan based on suggestion from the Executor. 
When making the new, ensure that each step is essential and directly contributes to the objective, avoid including unnecessary actions.
Structure the plan as a nested list, where each major task can contain subtasks. Subtasks may further contain their own subtasks, creating a hierarchical outline of what needs to be done. Use YAML format for clear and structured representation. 

For instance, the plan should look something like this:
```
- Main Task 1:
  - Subtask 1.1
  - Subtask 1.2:
    - Subtask 1.2.1
    - Subtask 1.2.2
  - Subtask 1.3
- Main Task 2
- Main Task 3:
  - Subtask 3.1
```"""

PlanMaker_whole_replan_human_prompt = """Given the objective as follows:
---
{{objective}}
---

We made a plan to break down the objective into subtasks, the execution of subtasks are all finished. The plan and the conclusion of the subtasks are as follows:
---
""" + development_plan + \
"""---

The plan failed to solve the objective due to the following reason:
---
{{suggestion}}
---

Now you should refine the plan to solve the objective:"""


# In: executor_cap objective 
# Out: development_plan
PlanMaker_plan_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_plan_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_plan_human_prompt),
    ]
)

# In: executor_cap objective development_plan node_task child_err_node_info/feedback suggestion
# Out: development_plan
PlanMaker_replan_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_replan_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_replan_human_prompt, template_format="jinja2"),
    ]
)

# In: objective development_plan node_task new_subplan
# Out: development_plan
PlanMaker_replan_critic_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_replan_critic_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_replan_critic_human_prompt, template_format="jinja2"),
    ]
)

# In: objective development_plan node_task child_err_node_info/feedback suggestion
# Out: bool
PlanMaker_findwhere_update_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_findwhere_update_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_findwhere_update_human_prompt, template_format="jinja2"),
    ]
)

# In: objective development_plan node_task feedback
# Out: conclusion
PlanMaker_conclude_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_conclude_human_prompt, template_format="jinja2"),
    ]
)

# In: objective development_plan node_task conclusion
# Out: bool
PlanMaker_decide_update_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_decide_update_human_prompt, template_format="jinja2"),
    ]
)

# In: objective development_plan node_task conclusion
# Out: suggestion
PlanMaker_howto_update_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_howto_update_human_prompt, template_format="jinja2"),
    ]
)

# In: objective development_plan
# Out: bool+suggestion
PlanMaker_plan_conclude_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_plan_conclude_human_prompt, template_format="jinja2"),
    ]
)

# In: executor_cap objective development_plan suggestion
# Out: development_plan
PlanMaker_whole_replan_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(PlanMaker_whole_replan_sys_prompt),
        HumanMessagePromptTemplate.from_template(PlanMaker_whole_replan_human_prompt, template_format="jinja2"),
    ]
)


def executor_cap_list_to_str(executor_cap_list):
    out = ''
    for i in range(len(executor_cap_list)):
        out += str(i+1) + '. ' + executor_cap_list[i] + '\n'
    return out


if __name__ == '__main__':
    from dpagent.agents.base import print_ChatPromptValue
    executor_cap_list = [
        'Search the Internet',
        'Retrieve the information from the document',
    ]
    plan_input = {
        'executor_cap': executor_cap_list_to_str(executor_cap_list),
        'objective': 'the objective',
    }
    print('==== PlanMaker_plan_prompt ====\n\n')
    print_ChatPromptValue(PlanMaker_plan_prompt.invoke(plan_input))
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
    development_plan_exp1_child = [{
        "desc": "task1.2.1",
        "children": [
            {
                "desc": "task1.2.1.1",
                "children": [{
                        "desc": "task1.2.1.1.1",
                        "children": []
                    },
                    {
                        "desc": "task1.2.1.1.2",
                        "children": []
                    }
                ]
            },
        ]
    },
    ]
    replan_input = {
        'executor_cap': executor_cap_list_to_str(executor_cap_list),
        'objective': 'the objective',
        'development_plan': development_plan_exp1,
        'node_task': 'task1.2.1',
        # 'child_err_node_info': development_plan_exp1_child,
        'child_err_node_info': [],
        'feedback': 'out of bound',
        'suggestion': 'Be more specific',
    }
    print('==== PlanMaker_replan_prompt ====\n\n')
    print_ChatPromptValue(PlanMaker_replan_prompt.invoke(replan_input))
    print('==== PlanMaker_findwhere_update_prompt ====\n\n')
    print_ChatPromptValue(PlanMaker_findwhere_update_prompt.invoke(replan_input))
    print('==== PlanMaker_conclude_prompt ====\n\n')
    print_ChatPromptValue(PlanMaker_conclude_prompt.invoke(replan_input))
    decideupdate_input = {**replan_input, **{'conclusion': 'the var out of bound'}}
    print('==== PlanMaker_decide_update_prompt ====\n\n')
    print_ChatPromptValue(PlanMaker_decide_update_prompt.invoke(decideupdate_input))
    print('==== PlanMaker_howto_update_prompt ====\n\n')
    print_ChatPromptValue(PlanMaker_howto_update_prompt.invoke(decideupdate_input))
    print('==== PlanMaker_plan_conclude_prompt ====\n\n')
    print_ChatPromptValue(PlanMaker_plan_conclude_prompt.invoke(replan_input))
    print('==== PlanMaker_whole_replan_prompt ====\n\n')
    print_ChatPromptValue(PlanMaker_whole_replan_prompt.invoke(replan_input))
