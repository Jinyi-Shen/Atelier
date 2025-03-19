import os, time, copy
from typing import List, Dict
import random
from dpagent.utils import util
from dpagent.config.config import SequentialHistoryFile, HierarchicalHistoryFile



def rename_file(filename):
    dirname, basename = os.path.split(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    file_name, file_extension = os.path.splitext(basename)
    max_num = -1
    if os.path.exists(filename):
        max_num = 0
    for file in os.listdir(dirname):
        if file.startswith(file_name + '-'):
            try:
                num_ext = file.split('-')[-1]
                num = int(num_ext[:-len(file_extension)])
                max_num = max(max_num, num)
            except ValueError:
                continue
    if max_num>-1 and os.path.exists(filename):
        new_filename = os.path.join(dirname, f"{file_name}-{max_num + 1}{file_extension}")
        os.rename(filename, new_filename)

def gen_id():
    rounded_sample = round(random.uniform(0, 1), 5)
    return int((float(time.time()) + rounded_sample) * 1e5)


class SequentialHistory:
    def __init__(self, file):
        self.file = file
        self.history = []
        self.file_inited = False

    def save(self):
        if not self.file_inited:
            rename_file(self.file)
            self.file_inited = True
        util.saveJson(self.file, self.history)
    
    def add_message(self, message: Dict, id: int=None, save: bool=True):
        full_message = {**{'id': id if id is not None else gen_id()}, **message}
        self.history.append(full_message)
        if save:
            self.save()


class HierarchicalHistory:
    def __init__(self, file):
        self.file = file
        self.history = []
        self.file_inited = False
        self.cursur = self.history
        self.cursur_stack = []
    
    def save(self):
        if not self.file_inited:
            rename_file(self.file)
            self.file_inited = True
        util.saveJson(self.file, self.history)

    def add_message(self, message: Dict, id: int=None, save: bool=True):
        full_message = {**{'id': id if id is not None else gen_id()}, **message}
        self.cursur.append(full_message)
        if save:
            self.save()
    
    def inner(self):
        if len(self.cursur)>0:
            if 'middle' not in self.cursur[-1]:
                self.cursur[-1]['middle'] = []
            self.cursur_stack.append(self.cursur)
            self.cursur = self.cursur[-1]['middle']
        return self.cursur
    
    def outer(self):
        if len(self.cursur_stack)>0:
            self.cursur = self.cursur_stack[-1]
            self.cursur_stack.pop()
        return self.cursur


class HistoryManager:
    def __init__(self, seqFile=SequentialHistoryFile, hierFile=HierarchicalHistoryFile):
        self.sequentialHistory = SequentialHistory(seqFile)
        self.hierarchicalHistory = HierarchicalHistory(hierFile)

    def set_file(self, seqFile, hierFile):
        self.sequentialHistory.file = seqFile
        self.hierarchicalHistory.file = hierFile

    def add_message(self, message: Dict, middle: List[Dict]=[]):
        # sequential
        seqmsg = copy.copy(message)
        if len(middle)>0:
            seqmsg['response'] = copy.copy(middle) + seqmsg['response']
        self.sequentialHistory.add_message(seqmsg)
        # hierarchical
        hiermsg = copy.copy(message)
        self.hierarchicalHistory.add_message(hiermsg)
        if len(middle)>0:
            self.hierarchicalHistory.inner()
            submsg = {'response': copy.copy(middle)}
            if 'name' in message:
                submsg = {'name': message['name'], 'response': copy.copy(middle)}
            self.hierarchicalHistory.add_message(submsg)
            self.hierarchicalHistory.outer()

    def inner(self):
        self.hierarchicalHistory.inner()
    
    def outer(self):
        self.hierarchicalHistory.outer()


historyManager = HistoryManager()


if __name__ == '__main__':
    gen_id()
    msg = {
        "name": "llm1",
        "query": [
            {
                "system": "sys1"
            },
            {
                "human": "human1"
            }
        ],
        "response": [
            {
                "assistant": "assistant1"
            }
        ]
    }
    middle = [{'assistant': 'mid1'}, {'assistant': 'mid2'}]
    historyManager.add_message(msg)
    historyManager.add_message(msg, middle=middle)
    historyManager.add_message(msg)
    historyManager.inner()
    historyManager.add_message(msg)
    historyManager.add_message(msg)
    historyManager.add_message(msg, middle=middle)
    historyManager.add_message(msg, middle=middle)
    historyManager.outer()
    historyManager.add_message(msg)
    historyManager.add_message(msg, middle=middle)
    historyManager.inner()
    historyManager.inner()
    historyManager.inner()
    historyManager.add_message(msg)
    historyManager.outer()
    historyManager.outer()
    historyManager.outer()
    historyManager.add_message(msg)
    pass



