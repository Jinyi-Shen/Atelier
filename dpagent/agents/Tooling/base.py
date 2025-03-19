import os
from typing import Annotated, List, Tuple, Union, Dict


def fake_human_input(instruction, file, overwrite=True):
    if overwrite or not os.path.exists(file):
        with open(file, "w") as f:
            f.write('')
    response = input(f"{instruction}. Please write the return content in {file}, and then press [y/n]: ")
    if response == "n":
        return ""
    with open(file, "r") as f:
        returnval = f.read()
    print('\nfake_human_input input:\n', returnval, '\n\n')
    return returnval


class ToolSuite:
    def __init__(self, name: str, capability: str, toolfunc=None, toolAgent=None):
        self.name = name
        self.capability = capability
        self.toolfunc = toolfunc
        self.toolAgent = toolAgent
    
    def get_name(self):
        return self.name
    
    def get_capability(self):
        return self.capability
    
    def get_toolfunc(self):
        return self.toolfunc
    
    def get_toolAgent(self):
        return self.toolAgent


class ToolSuiteLists:
    def __init__(self, toolSuiteList: List[ToolSuite]):
        self.toolSuiteList = toolSuiteList
    
    def add_toolSuite(self, toolSuite: ToolSuite):
        self.toolSuiteList.append(toolSuite)
    
    def get_toolSuiteList(self):
        return self.toolSuiteList

    def get_names(self):
        return [toolSuite.get_name() for toolSuite in self.toolSuiteList]
    
    def get_capabilities(self):
        return [toolSuite.get_capability() for toolSuite in self.toolSuiteList]
    
    def get_toolfuncs(self):
        return [toolSuite.get_toolfunc() for toolSuite in self.toolSuiteList]
    
    def get_toolAgents(self):
        return [toolSuite.get_toolAgent() for toolSuite in self.toolSuiteList]
