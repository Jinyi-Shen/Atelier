from dpagent.utils import util
import copy


class NestDict(dict):
    def __init__(self, descKey, childrenKey, indict=None):
        self.descKey = descKey
        self.childrenKey = childrenKey
        if indict is not None:
            self = self.from_dict(indict)
    
    def isValid(self, indict=None):
        if indict is not None:
            if self.descKey in indict and self.childrenKey in indict:
                return True
            else:
                return False
        else:
            return self.isValid(indict=self)
    
    def from_dict(self, indict):
        if not self.isValid(indict=indict):
            return self
        childNestDictList = []
        if len(indict[self.childrenKey])>0:
            for child in indict[self.childrenKey]:
                childNestDict = NestDict(self.descKey, self.childrenKey, indict=child)
                childNestDictList.append(childNestDict)
        self[self.descKey] = copy.copy(indict[self.descKey])
        self[self.childrenKey] = copy.copy(childNestDictList)
        return self
    
    def from_str(self, instr):
        self[self.descKey] = instr
        self[self.childrenKey] = []
        return self

    def from_vertical_list(self, listin):
        if len(listin)==0:
            return self
        if len(listin)>1:
            child_dict = NestDict(self.descKey, self.childrenKey).from_vertical_list(listin[1:])
            self[self.descKey] = copy.copy(listin[0])
            self[self.childrenKey] = [child_dict]
            return self
        else:
            return self.from_str(listin[0])

    def getLeaf(self, leafList=[]):
        if not self.isValid():
            return []
        newLeafList = copy.copy(leafList)
        if len(self[self.childrenKey])==0:
            newLeafList.append(self)
        else:
            for child in self[self.childrenKey]:
                newLeafList += child.getLeaf(leafList)
        return newLeafList


class PlanTreeDict(NestDict):
    def __init__(self, indict=None):
        NestDict.__init__(self, 'desc', 'children', indict=indict)
    
    def add_conclusion(self):
        pass



if __name__ == '__main__':
    tasks_exp1 = [{
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
    plan_exp1 = {'desc': 'obj', 'children': tasks_exp1}
    plan_exp2 = {'desc': 'obj', 'children': []}
    plan_tree_exp1 = PlanTreeDict(plan_exp1)
    util.printJson(plan_tree_exp1)
    plan_tree_exp2 = PlanTreeDict(plan_exp2)
    util.printJson(plan_tree_exp2)
    list_exp1 = ['1', '2', '3', '4', '5']
    list_exp2 = ['1']
    plan_list_exp1 = PlanTreeDict().from_vertical_list(list_exp1)
    util.printJson(plan_list_exp1)
    plan_list_exp2 = PlanTreeDict().from_vertical_list(list_exp2)
    util.printJson(plan_list_exp2)
    getLeaf_exp1 = plan_tree_exp1.getLeaf()
    getLeaf_exp1[2]['children'].append(PlanTreeDict({'desc': 'conclusion', 'children': []}))
    util.printJson(plan_tree_exp1)
    getLeaf_exp2 = plan_tree_exp2.getLeaf()
    getLeaf_exp2[0]['desc'] = 'pp'
    util.printJson(plan_tree_exp2)
    pass

