from typing import Annotated, List, Tuple, Union, Dict
import copy
import random, json
from dpagent.utils import util
from dpagent.utils.history import historyManager
from dpagent.utils.logger import logger, logger_add_query_prompt, logger_add_response
from dpagent.utils.treeDict import PlanTreeDict
from dpagent.agents.Planning.dfs.PlanMaker.PlanMaker import PlanMaker
from dpagent.agents.Planning.dfs.ActionSeqMaker.ActionSeqMaker import ActionSeqMaker
from dpagent.agents.Tooling.base import ToolSuiteLists



class DFSReport:
    def __init__(self, status, infos, node):
        self.status = status # ['conclusion', 'update_parent', 'update', 'visited']
        self.infos = infos
        self.node = node
    
    def to_str(self):
        tojson = {
            'status': self.status,
            'infos': self.infos,
        }
        return util.json2str(tojson)
    
    def stop_dfs(self):
        if self.status == 'update':
            return True
        else:
            return False
    
    def should_update_parent(self):
        if self.status == 'update_parent':
            return True
        else:
            return False
    
    def is_valid(self):
        if self.status in ['conclusion', 'update', 'visited']:
            return True
        else:
            return False


class TaskNode:
    def __init__(self, desc, objective, planMaker, actionSeqMaker, isLeafNode=True, isRootNode=False, parent=None, children=[]):
        self.desc = desc
        self.objective = objective
        self.planMaker = planMaker
        self.actionSeqMaker = actionSeqMaker
        self.parent = parent
        self.children = children
        self.returnInfo = None
        self.conclusion = None
        self.isLeafNode = isLeafNode
        self.isRootNode = isRootNode
        self.visited = False
        self.id = random.randint(1000, 9999)
    
    def __repr__(self):
        return f"TaskNode(desc={self.desc}, children={len(self.children)}, isLeafNode={self.isLeafNode}, isRootNode={self.isRootNode}, objective={self.objective}, id={self.id})"

    def __eq__(self, other):
        if isinstance(other, TaskNode):
            return self.id==other.id and self.desc==other.desc
        return False
    
    def __deepcopy__(self, memo):
        new_instance = TaskNode(self.desc, self.objective, None, None)
        new_instance.desc = copy.deepcopy(self.desc, memo)
        new_instance.objective = copy.deepcopy(self.objective, memo)
        # new_instance.planMaker = copy.deepcopy(self.planMaker, memo)
        # new_instance.actionSeqMaker = copy.deepcopy(self.actionSeqMaker, memo)
        new_instance.parent = copy.deepcopy(self.parent, memo)
        new_instance.children = copy.deepcopy(self.children, memo)
        new_instance.returnInfo = copy.deepcopy(self.returnInfo, memo)
        new_instance.conclusion = copy.deepcopy(self.conclusion, memo)
        new_instance.isLeafNode = copy.deepcopy(self.isLeafNode, memo)
        new_instance.isRootNode = copy.deepcopy(self.isRootNode, memo)
        new_instance.visited = copy.deepcopy(self.visited, memo)
        new_instance.id = copy.deepcopy(self.id, memo)
        return new_instance

    def print_subtree(self, level=0, allinfo=False):
        if allinfo:
            print('  '*level + '- ' + self.desc, 'conclusion:', self.conclusion, 'isLeaf:', self.isLeafNode, 'isRoot:', self.isRootNode)
        else:
            print('  '*level + '- ' + self.desc)
        for child in self.children:
            child.print_subtree(level=level+1, allinfo=allinfo)
    
    def subtree_to_json(self, use_conclusion=False, limit_level=None) -> Dict:
        desc = self.get_desc_con_info() if use_conclusion else self.desc
        children_json = []
        if limit_level is None:
            for child in self.children:
                children_json += [child.subtree_to_json(use_conclusion=use_conclusion, limit_level=limit_level)]
        elif limit_level is not None and limit_level>=1:
            for child in self.children:
                children_json += [child.subtree_to_json(use_conclusion=use_conclusion, limit_level=limit_level-1)]
        return PlanTreeDict({'desc':desc, 'children': children_json})
    
    def set_children(self, children):
        self.children = children
    
    def set_parent(self, parent):
        self.parent = parent
    
    def children_set_parent(self):
        for child in self.children:
            child.set_parent(self)
    
    def get_brothers(self, includeSelf=False):
        if self.isRootNode:
            if includeSelf:
                return [self]
            else:
                return []
        else:
            if includeSelf:
                return self.parent.children
            brothers = []
            for child in self.parent.children:
                if child!=self:
                    brothers.append(child)
            return brothers
    
    def get_rootNode(self):
        if self.isRootNode:
            return self
        else:
            return self.parent.get_rootNode()
    
    def update_leaf(self):
        if len(self.children)>0:
            self.isLeafNode = False
        else:
            self.isLeafNode = True

    def get_desc_con_info(self):
        if self.conclusion is None:
            return self.desc
        else:
            return self.conclusion
    
    def have_grandchild(self, node):
        if self==node:
            return True
        have_grandchild = False
        for child in self.children:
            if child.have_grandchild(node):
                have_grandchild = True
        return have_grandchild
    
    def bfs_cut(self, criterion_func):
        '''BFS seach, cut the subtree if the node not meet the criterion_func'''
        new_children = []
        for child in self.children:
            if criterion_func(child):
                new_children.append(child)
        self.children = new_children
        for child in self.children:
            child.bfs_cut(criterion_func)
    
    def get_root_to_self_planTreeDict(self, use_conclusion=False) -> PlanTreeDict:
        if self.isRootNode:
            desc = self.get_desc_con_info() if use_conclusion else self.desc
            return PlanTreeDict({'desc':desc, 'children':[]})
        parent_planTreeDict = self.parent.get_root_to_self_planTreeDict(use_conclusion=use_conclusion)
        parent_planTreeDict.getLeaf()[0]['children'].append(PlanTreeDict({'desc':self.get_desc_con_info(), 'children':[]}))
        return parent_planTreeDict
    
    def get_nearby_nodes_info(self, need_parent_level_info=False) -> List[PlanTreeDict]:
        brothers = self.get_brothers(includeSelf=True)
        if need_parent_level_info:
            if self.isRootNode:
                parent_brothers = []
            else:
                parent_brothers = self.parent.get_brothers(includeSelf=True)
        rootNode = self.get_rootNode()
        refRootNode = copy.deepcopy(rootNode)
        def root_to_self_plus_self_brother(node):
            if node.have_grandchild(self):
                return True
            if node in brothers:
                return True
            return False
        def root_to_self_plus_self_brother_plus_parent_brother(node):
            if node.have_grandchild(self):
                return True
            if node in parent_brothers:
                return True
            if node in brothers:
                return True
            return False
        criterion_func = root_to_self_plus_self_brother_plus_parent_brother if need_parent_level_info else root_to_self_plus_self_brother
        refRootNode.bfs_cut(criterion_func)
        refRootNode_json = refRootNode.subtree_to_json(use_conclusion=True)
        return refRootNode_json['children']
    
    def get_child_err_node_info(self, errNode) -> List[PlanTreeDict]:
        err_brothers = errNode.get_brothers(includeSelf=True)
        refSelfNode = copy.deepcopy(self)
        def self_to_err_plus_err_brothers(node):
            if node.have_grandchild(errNode):
                return True
            if node in err_brothers:
                return True
            return False
        refSelfNode.bfs_cut(self_to_err_plus_err_brothers)
        refSelfNode_json = refSelfNode.subtree_to_json(use_conclusion=True)
        # errNode use desc and conclusion
        leafs = refSelfNode_json.getLeaf()
        if errNode.conclusion is not None:
            for leaf in leafs:
                if leaf['desc']==errNode.conclusion:
                    leaf['desc'] = errNode.desc
                    leaf['children'].append({'desc':'Conclusion: '+str(errNode.conclusion), 'children':[]})
                    break
        return [refSelfNode_json]
    
    def gen_subtask_feedback(self):
        feedback = ''
        for child in self.children:
            feedback += '- subtask: ' + child.desc + '\n'
            if child.conclusion is not None:
                feedback += '  - conclusion: ' + child.conclusion + '\n'
        return feedback
    
    def exec(self):
        # prepare for actionSeqMakerChain call
        nearby_nodes_info = self.get_nearby_nodes_info(need_parent_level_info=False)
        exec_input = {
            "objective": self.objective,
            "development_plan": nearby_nodes_info,
            "node_task": self.desc,
        }
        logger_add_query_prompt(AgentName='actionSeqMakerChain', sys_prompt=util.json2str(exec_input))
        historyManager.add_message({'name':'actionSeqMakerChain', 'query': [{'system': util.json2str(exec_input)}]})
        historyManager.inner()
        # chain_out = self.actionSeqMaker.actionSeqMakerChain.invoke(exec_input)
        chain_out = self.actionSeqMaker.fake_invoke_actionSeqMakerChain(exec_input) # human in loop for debug
        historyManager.outer()
        logger_add_response(AgentName='actionSeqMakerChain', response=util.json2str(chain_out))
        historyManager.add_message({'name':'actionSeqMakerChain', 'response': [{'assistant': util.json2str(chain_out)}]})
        if chain_out['end_refine']:
            self.returnInfo = chain_out['refine_reason']
        if chain_out['end_finish']:
            self.returnInfo = chain_out['conclusion']

    def traverse(self):
        if self.visited:
            return DFSReport(status='visited', infos=None, node=self)
        if self.isLeafNode:
            self.exec()
        
        # traverse children
        for child in self.children:
            dfsreport = child.traverse()
            if not dfsreport.is_valid():
                raise ValueError('should not reach here: TaskNode.traverse child dfsreport.status=', dfsreport.status)
            if dfsreport.stop_dfs():
                return dfsreport
        
        # prepare for planMakerChain
        nearby_nodes_info = self.get_nearby_nodes_info(need_parent_level_info=True)
        feedback = self.returnInfo if self.isLeafNode else self.gen_subtask_feedback()
        chain_input = {
            'objective': self.objective,
            'development_plan': nearby_nodes_info,
            'node_task': self.desc,
            'feedback': feedback,
            'child_err_node_info': []
        }

        # run planMakerChain
        planMakerChain_out = self.planMaker.planMakerChain.invoke(chain_input)
        if planMakerChain_out['end_conclusion']:
            # traverse successfully
            self.conclusion = planMakerChain_out['conclusion']
            self.visited = True
            return DFSReport(status='conclusion', infos=planMakerChain_out['conclusion'], node=self)
        if planMakerChain_out['end_update_parent']:
            # need to find a parent to update
            self.conclusion = planMakerChain_out['conclusion']
            self.visited = True
            return self.find_where_update_plan(errNode=self, suggestion=planMakerChain_out['suggestion'], init_node=True)
        if planMakerChain_out['end_new_subplan']:
            # need to update the current node
            return DFSReport(status='update', infos=planMakerChain_out['new_subplan'], node=self)

    def find_where_update_plan(self, errNode, suggestion, init_node=False):
        # if the node is the initial node occurs error, skip
        if init_node:
            return self.parent.find_where_update_plan(errNode, suggestion)
        
        # prepare for invoke
        nearby_nodes_info = self.get_nearby_nodes_info(need_parent_level_info=True)
        child_err_node_info = self.get_child_err_node_info(errNode)
        chain_input = {
            'objective': self.objective,
            'development_plan': nearby_nodes_info,
            'node_task': self.desc,
            'feedback': None,
            'child_err_node_info': child_err_node_info,
            'suggestion': suggestion
        }

        # if the parent is root, then force to replan
        if self.parent.isRootNode:
            new_subplan = self.planMaker.run_replan(chain_input)
            return DFSReport(status='update', infos=new_subplan, node=self)

        # for normal node, use replanChain to decide
        replanChain_out = self.planMaker.replanChain.invoke(chain_input)
        if replanChain_out['end_update_parent']:
            return self.parent.find_where_update_plan(errNode, suggestion)
        elif replanChain_out['end_new_subplan']:
            return DFSReport(status='update', infos=replanChain_out['new_subplan'], node=self)
        else:
            raise ValueError('should not reach here: TaskNode.find_where_update_plan replanChain_out=', replanChain_out)

    # Trash
    '''
    def get_all_parents_info_list(self) -> List[str]:
        if self.isRootNode:
            return []
        info = self.get_desc_con_info()
        parents_infos = self.parent.get_all_parents_info_list()
        parents_infos.append(info)
        return parents_infos
    
    def get_to_grandchild_parents_info_list(self, childNode) -> List[str]:
        parents_infos_list = [childNode.desc]
        currNode = childNode.parent
        while True:
            parents_infos_list.insert(0, currNode.desc)
            if currNode==self:
                break
            else:
                currNode = currNode.parent
        parents_infos = util.list2NestDict(parents_infos_list)
        return parents_infos

    def get_nearby_nodes_info1(self, need_parent_level_info=False) -> List[Dict]:
        all_parents_info_list = self.parent.get_all_parents_info_list()
        rootNode = self.get_rootNode()
        if len(all_parents_info_list)==0:
            return rootNode.subtree_to_json(use_conclusion=True, limit_level=1)['children']
        elif len(all_parents_info_list)==1:
            if need_parent_level_info:
                return rootNode.subtree_to_json(use_conclusion=True, limit_level=2)['children']
            else:
                return [{'desc': self.parent.get_desc_con_info(), 'children': self.parent.subtree_to_json(use_conclusion=True, limit_level=1)['children']}]
        nearby_nodes_info = util.list2NestDict(all_parents_info_list)
        leaf_node_info = util.getNestDictLeaf(nearby_nodes_info)
        leaf_parent_node_info = util.getNestDict2ndLeaf(nearby_nodes_info)
        
        # same level nodes desc or conclusion
        same_level_info = []
        assert self.parent is not None
        for child in self.parent.children:
            info = child.get_desc_con_info()
            same_level_info.append({'desc':info, 'children':[]})
        leaf_node_info['children'] = same_level_info

        # parent level nodes desc or conclusion
        parent_level_info = []
        if need_parent_level_info and self.parent.parent is not None:
            for child in self.parent.parent.children:
                info = child.get_desc_con_info()
                parent_level_info.append({'desc':info, 'children':[]})
            if leaf_parent_node_info is not None:
                passleaf = False
                for info in parent_level_info:
                    if info['desc']==leaf_node_info['desc']:
                        passleaf = True
                    else:
                        if passleaf:
                            leaf_parent_node_info['children'].append(info)
                        else:
                            leaf_parent_node_info['children'].insert(-2, info)
        return [nearby_nodes_info]

    def get_child_err_node_info1(self, errNode):
        to_err_parents_infos = self.get_to_grandchild_parents_info_list(errNode)
        # err brothers
        err_parent = util.getNestDict2ndLeaf(to_err_parents_infos)
        before_err = True
        for child in errNode.parent.children:
            if child!=errNode:
                if before_err:
                    err_parent['children'].insert(-2, {'desc':child.desc, 'children':[]})
                else:
                    err_parent['children'].append({'desc':child.desc, 'children':[]})
            else:
                before_err = False
                err_parent['children'][-1]['children'].append({'desc':'Conclusion: '+str(errNode.conclusion), 'children':[]})
        return to_err_parents_infos
    '''


class RootTaskNode(TaskNode):
    def __init__(self, objective, planMaker, actionSeqMaker, children=[]):
        TaskNode.__init__(self, objective, objective, planMaker, actionSeqMaker, isLeafNode=False, isRootNode=True, parent=None, children=children)
    
    def __repr__(self):
        return f"RootTaskNode(objective={self.objective}, children={len(self.children)}, id={self.id})"
    
    def __deepcopy__(self, memo):
        new_instance = RootTaskNode(self.objective, None, None)
        new_instance.desc = copy.deepcopy(self.desc, memo)
        new_instance.objective = copy.deepcopy(self.objective, memo)
        # new_instance.planMaker = copy.deepcopy(self.planMaker, memo)
        # new_instance.actionSeqMaker = copy.deepcopy(self.actionSeqMaker, memo)
        new_instance.parent = copy.deepcopy(self.parent, memo)
        new_instance.children = copy.deepcopy(self.children, memo)
        new_instance.returnInfo = copy.deepcopy(self.returnInfo, memo)
        new_instance.conclusion = copy.deepcopy(self.conclusion, memo)
        new_instance.isLeafNode = copy.deepcopy(self.isLeafNode, memo)
        new_instance.isRootNode = copy.deepcopy(self.isRootNode, memo)
        new_instance.visited = copy.deepcopy(self.visited, memo)
        new_instance.id = copy.deepcopy(self.id, memo)
        return new_instance
    
    def traverse(self):
        # traverse children
        for child in self.children:
            dfsreport = child.traverse()
            if not dfsreport.is_valid():
                raise ValueError('should not reach here: TaskNode.traverse child dfsreport.status=', dfsreport.status)
            if dfsreport.stop_dfs():
                return dfsreport
            
        queryDict = {
            "objective": self.objective,
            "development_plan": self.subtree_to_json(use_conclusion=True, limit_level=1)['children'],
        }
        conclude_out = self.planMaker.run_plan_conclude(queryDict)
        if conclude_out.solved:
            return DFSReport(status='conclusion', infos=conclude_out.description, node=self)
        else:
            whole_replan_out = self.planMaker.run_whole_replan({**queryDict, **{'suggestion':conclude_out.description}})
            return DFSReport(status='update', infos=whole_replan_out.subPlans, node=self)


class TaskTree:
    def __init__(self, objective: str, toolSuiteList: ToolSuiteLists):
        self.objective = objective
        self.toolSuiteList = toolSuiteList
        self.planMaker = PlanMaker(self.toolSuiteList)
        self.actionSeqMaker = ActionSeqMaker(self.toolSuiteList)
        self.rootNode = RootTaskNode(objective, self.planMaker, self.actionSeqMaker)
    
    def genSubTree(self, node=None, subPlans=None):
        if node is None:
            node = self.rootNode
        if subPlans is None:
            subPlans = self.planMaker.run_plan(query=self.objective)
        root_nodes = self.plan2Tree(subPlans, parentNode=node)
        node.set_children(root_nodes)
        node.update_leaf()
    
    def updateSubTree(self, node, subPlans: List[Dict]):
        if node.isRootNode:
            self.genSubTree(self, node=self.rootNode, subPlans=subPlans)
        else:
            if len(subPlans)==0:
                return
            elif len(subPlans)==1:
                root_nodes = self.plan2Tree(subPlans[0]['children'], parentNode=node)
                node.desc = subPlans[0]['desc']
                node.set_children(root_nodes)
                node.update_leaf()
            else:
                root_nodes = self.plan2Tree(subPlans, parentNode=node)
                node.desc = subPlans[0]['desc']
                node.set_children(root_nodes)
                node.update_leaf()

    
    def DFS_traverse(self):
        while True:
            # log query
            dfs_info_str = util.json2str({'objective': self.objective, 'development_plan': self.rootNode.subtree_to_json()})
            logger_add_query_prompt(AgentName='Planning DFS', sys_prompt=dfs_info_str)
            historyManager.add_message({'name':'Planning DFS', 'query': [{'system': dfs_info_str}]})
            historyManager.inner()

            dfsreport = self.rootNode.traverse()

            # log result
            historyManager.outer()
            logger_add_response(AgentName='Planning DFS', response=util.json2str(dfsreport.to_str()))
            historyManager.add_message({'name':'Planning DFS', 'response': [{'assistant': util.json2str(dfsreport.to_str())}]})

            if dfsreport.status == 'conclusion':
                return dfsreport.infos
            elif dfsreport.status == 'update':
                self.updateSubTree(dfsreport.node, dfsreport.infos)
            else:
                raise ValueError('should not reach here: DFS_traverse dfsreport.status=', dfsreport.status)
    
    def plan2Tree(self, subPlanList, parentNode=None):
        root_nodes = []
        for subPlanDict in subPlanList:
            node_desc = subPlanDict['desc']
            node_children = self.plan2Tree(subPlanDict['children'])
            isLeafNode = True if len(node_children)==0 else False
            node = TaskNode(node_desc, self.objective, self.planMaker, self.actionSeqMaker, isLeafNode=isLeafNode, parent=parentNode, children=node_children)
            node.children_set_parent()
            root_nodes.append(node)
        return root_nodes

    def print_tree(self, allinfo=False):
        self.rootNode.print_subtree(allinfo=allinfo)



if __name__ == '__main__':
    from dpagent.agents.Tooling.WebSearch.WebSearch import webSearchChainSuite
    toolSuiteList = ToolSuiteLists([webSearchChainSuite])
    development_plan_exp1 = [
        {
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
    objective = 'what is the hometown of the 2024 Australia open winner?'
    tree = TaskTree(objective, toolSuiteList)
    tree.genSubTree(subPlans=development_plan_exp1)
    if False:
        tree.print_tree(allinfo=True)
    if False:
        json1 = tree.rootNode.subtree_to_json(use_conclusion=False, limit_level=None)
        util.printJson(json1)
        json2 = tree.rootNode.children[0].children[1].children[1].subtree_to_json(use_conclusion=False, limit_level=None)
        util.printJson(json2)
    if False:
        print(tree.rootNode.children[0].have_grandchild(tree.rootNode.children[0].children[1].children[1]))
        print(tree.rootNode.children[0].children[0].have_grandchild(tree.rootNode.children[0].children[1].children[1]))
        print(tree.rootNode.have_grandchild(tree.rootNode.children[0].children[1].children[1]))
    if False:
        util.printJson(tree.rootNode.get_root_to_self_planTreeDict(use_conclusion=True))
        util.printJson(tree.rootNode.children[0].children[1].children[1].get_root_to_self_planTreeDict(use_conclusion=True))
    if False:
        # all_parents_info_list1 = tree.rootNode.children[0].children[1].children[1].get_all_parents_info_list()
        nearby_nodes_info1_1 = tree.rootNode.children[0].children[1].children[1].get_nearby_nodes_info(need_parent_level_info=False)
        util.printJson(nearby_nodes_info1_1)
        nearby_nodes_info1_2 = tree.rootNode.children[0].children[1].children[1].get_nearby_nodes_info(need_parent_level_info=True)
        util.printJson(nearby_nodes_info1_2)
        nearby_nodes_info2_1 = tree.rootNode.children[0].children[1].get_nearby_nodes_info(need_parent_level_info=False)
        util.printJson(nearby_nodes_info2_1)
        nearby_nodes_info2_2 = tree.rootNode.children[0].children[1].get_nearby_nodes_info(need_parent_level_info=True)
        util.printJson(nearby_nodes_info2_2)
        nearby_nodes_info3_1 = tree.rootNode.children[0].get_nearby_nodes_info(need_parent_level_info=True)
        util.printJson(nearby_nodes_info3_1)
        nearby_nodes_info3_2 = tree.rootNode.children[0].get_nearby_nodes_info(need_parent_level_info=True)
        util.printJson(nearby_nodes_info3_2)
    if False:
        tree.rootNode.children[0].children[1].children[1].conclusion = 'task1.2.2 conclusion'
        # to_grandchild_parents_info = tree.rootNode.children[0].get_to_grandchild_parents_info_list(tree.rootNode.children[0].children[1].children[1])
        to_err_parents_infos_1 = tree.rootNode.children[0].get_child_err_node_info(tree.rootNode.children[0].children[1].children[1])
        util.printJson(to_err_parents_infos_1)
        to_err_parents_infos_2 = tree.rootNode.children[0].get_child_err_node_info(tree.rootNode.children[0].children[1])
        util.printJson(to_err_parents_infos_2)
        to_err_parents_infos_3 = tree.rootNode.children[0].get_child_err_node_info(tree.rootNode.children[0])
        util.printJson(to_err_parents_infos_3)
        to_err_parents_infos_4 = tree.rootNode.get_child_err_node_info(tree.rootNode)
        util.printJson(to_err_parents_infos_4)
        to_err_parents_infos_5 = tree.rootNode.children[0].get_child_err_node_info(tree.rootNode)
        util.printJson(to_err_parents_infos_5)
    pass

