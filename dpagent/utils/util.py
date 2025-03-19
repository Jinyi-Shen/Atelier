import json
import os
import tiktoken


def saveJson(jsonf, param):
    with open(jsonf, "w") as fp:
        json.dump(param, fp, indent=4)


def loadJson(jsonf):
    with open(jsonf, "r") as fp:
        param = json.load(fp)
    return param


def saveJsonAppend(jsonf, param):
    if os.path.exists(jsonf):
        origin_param = loadJson(jsonf)
    else:
        origin_param = []
    origin_param.append(param)
    with open(jsonf, "w") as fp:
        json.dump(origin_param, fp, indent=4)


def json2str(jsonin):
    return json.dumps(jsonin, indent=4)


def printJson(jsonin):
    print(json2str(jsonin))


def saveFile(file, content):
    with open(file, "w") as fp:
        fp.write(content)


def removeFiles(files):
    for file in files:
        if os.path.exists(file):
            os.remove(file)


def num_tokens(string: str, encoding_name="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


# Trash
"""
def list2NestDict(listin, dictkey='desc', dict_childrenkey='children'):
    if len(listin)==0:
        return None
    if len(listin)>1:
        child_dict = list2NestDict(listin[1:], dictkey=dictkey, dict_childrenkey=dict_childrenkey)
        return {dictkey:listin[0], dict_childrenkey:[child_dict]}
    else:
        return {dictkey:listin[0], dict_childrenkey:[]}

def getNestDictLeaf(nestDict):
    if len(nestDict['children'])>0:
        return getNestDictLeaf(nestDict['children'][0])
    else:
        return nestDict

def getNestDict2ndLeaf(nestDict):
    if len(nestDict['children'])==0:
        return None
    elif len(nestDict['children'])>0 and len(nestDict['children'][0]['children'])==0:
        return nestDict
    elif len(nestDict['children'])>0 and len(nestDict['children'][0]['children'])>0:
        return getNestDict2ndLeaf(nestDict['children'][0])
    else:
        raise Exception('getNestDict2ndLeaf error')

def printNestDict(nestDict, level=0):
    print('  '*level + '- ' + nestDict['desc'])
    for child in nestDict['children']:
        printNestDict(child, level=level+1)
"""


if __name__ == "__main__":
    development_plan_exp1 = [
        {
            "desc": "task1",
            "children": [
                {"desc": "task1.1", "children": []},
                {
                    "desc": "task1.2",
                    "children": [
                        {"desc": "task1.2.1", "children": []},
                        {"desc": "task1.2.2", "children": []},
                    ],
                },
                {"desc": "task1.3", "children": []},
            ],
        },
        {"desc": "task2", "children": []},
        {"desc": "task3", "children": [{"desc": "task3.1", "children": []}]},
    ]
    listin = ["1", "2", "3", "4"]
    # nestDict = list2NestDict(listin)
    # nestDictLeaf = getNestDictLeaf(nestDict)
    # nestDict2ndLeaf = getNestDict2ndLeaf(nestDict)
    pass
