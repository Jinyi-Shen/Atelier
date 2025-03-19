from dpagent.agents.prompt import nested_json_tree_define


development_plan = nested_json_tree_define + """{{- render_tasks(development_plan) -}}"""

child_err_node_info = nested_json_tree_define + """{{- render_tasks(child_err_node_info) -}}"""


if __name__ == '__main__':
    from jinja2 import Environment
    development_plan_exp1 = [{
            "desc": "task1",
            "children": [{
                    "desc": "task1.1",
                    "children": []
                },
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
                {
                    "desc": "task1.3",
                    "children": []
                }
            ]
        },
        {
            "desc": "task2",
            "children": []
        },
        {
            "desc": "task3",
            "children": [{
                "desc": "task3.1",
                "children": []
            }]
        }
    ]
    data = {"development_plan": development_plan_exp1}
    output = Environment().from_string(development_plan).render(data)
    print(output)
    print('--end--')
