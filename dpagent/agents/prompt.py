from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)


nested_json_tree_define = """\
{%- macro render_tasks(tasks, level=1, start=True) -%}
{% if start %}
{% endif %}
{%- for task in tasks -%}
{%- set index = loop.index -%}
{%- set prefix = '-' -%}
{{'  ' * (level - 1)}}{{prefix}} {{ task['desc'] }}
{% if task['children'] and task['children']|length > 0 %}\
{{ render_tasks(task['children'], level + 1, False) }}\
{% endif %}
{%- endfor -%}
{%- endmacro -%}
"""

