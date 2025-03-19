'''
Project      : 
FilePath     : /DevelopPlatform-v2/dpagent/utils/tester/testDebugLocation.py
Descripttion : 
Author       : GDDG08
Date         : 2024-04-16 15:14:54
LastEditors  : GDDG08
LastEditTime : 2024-04-17 16:51:11
'''

"""
usage:
from dpagent.utils.tester.testDebugLocation import TEST_LOG

# Add 
@TEST_LOG
# to all the functions you want to test
"""

import functools
import json
import datetime

logfile = f'./testDebugLocation.log'


def TEST_LOG(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # function_name = f"{func.__name__!r}"
        function_name = func.__name__
        # args_repr = [repr(a) for a in args]
        args_repr = list(args)
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]

        # signature = ", ".join(args_repr + kwargs_repr)\
        # print(f"Calling {function_name}({signature})")

        ret = func(*args, **kwargs)

        # print(f"{function_name} returned {ret!r}")
        T_Node(function_name, args_repr+kwargs_repr, ret)
        return ret
    return wrapper


nodeInput = {
    "make_actionseq": ['action_executors', 'objective', 'development_plan', 'node_task'],
    "update_actionseq": ['action_executors', 'objective', 'node_task', 'action_seq', 'refine_reason'],
    "conclude_actionseq": ['action_executors', 'objective', 'node_task', 'action_seq', 'feedback'],
    "check_actionseq": ['action_executors', 'objective', 'node_task', 'action_seq'],
    "decide_actionseq_call_finish": ['action_executors', 'objective', 'node_task', 'action_seq', 'conclusion'],
    "run_actionseq": ['action_executors', 'objective', 'node_task', 'action_seq'],
}


def cropInput(node, input):
    return {key: input[key] for key in nodeInput[node]}


def T_Node(node, inputs, outputs):
    # [2024-04-15 15:14:54][nodeName] in blue bold
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\033[1;34m[{time}][{node}]{'='*30}\033[0m")

    if len(inputs) == 1 and node in nodeInput.keys():
        inputs = inputs[0]
        inputs = cropInput(node, inputs)
    print(f"\033[1;31mINPUT:\033[0m\n{inputs}")
    print(f"\033[1;32mOUTPUT:\033[0m\n{outputs}")
    print("="*50)

    if logfile:
        with open(logfile, 'a+') as f:
            f.write(f"[{time}][{node}]\n")
            f.write(f"INPUT:\n{inputs}\n")
            f.write(f"OUTPUT:\n{outputs}\n")
            f.write("="*50 + "\n")


# def load_test_input():
#     development_plan_exp1 = [{
#         "desc": "Research the winner's hometown",
#         "children": [
#                 {
#                     "desc": "Look up the winner's biographical information through:",
#                     "children": [{
#                             "desc": "Official ATP or WTA player profiles",
#                             "children": []
#                     },
#                         {
#                             "desc": "Sports news articles profiling the winner",
#                             "children": []
#                     }
#                     ]
#                 },
#         ]
#     },
#     ]
#     action_executors = ['retrieve_db', 'retrieve_docs', 'retrieve_codes', 'explain_codes']
#     action_seq = """- action: retrieve_docs
#     description: Search for recent sports news articles profiling the 2024 Australian Open winner.
#     parameters:
#         keywords: "2024 Australian Open winner profile"
#         source_type: "sports news"
#         date_range: "last month"

#     - action: explain_codes
#     description: Extract information regarding the winner's hometown from the retrieved sports news articles.
#     parameters:
#         data_type: "text"
#         operation: "information extraction"
#         information: "hometown" """
#     test_input = {
#         'objective': 'what is the hometown of the 2024 Australia open winner?',
#         'development_plan': development_plan_exp1,
#         'node_task': 'Sports news articles profiling the winner',
#         'Action_Executors': ', '.join(action_executors),
#         'action_seq': action_seq,
#         'refine_reason': "The action sequence is not in the correct YAML format. There is an indentation issue with the second action block which should be at the same level as the first action. Additionally, the second action 'explain_codes' requires the output from the first action as an input, but this is not specified in the parameters.",
#         # 'feedback': 'execution failed due to network error',
#     }
#     return test_input


# def main():
#     from dpagent.agents.Planning.dfs.ActionSeqMaker.ActionSeqMaker import actionSeqMakerChain
#     test_input = load_test_input()
#     actionSeqMakerChain.invoke(test_input)


# if __name__ == '__main__':
#     time = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
#     # logfile = f'./testActionSeqMaker-{time}.log'
#     open(logfile,'a+').write("#"*50 + "\n"+time + "\n" + "#"*50 + "\n")
#     main()
    pass
