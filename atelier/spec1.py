import os
cpu_lim = 1
os.environ['OMP_NUM_THREADS'] = str(cpu_lim)
os.environ['OPENBLAS_NUM_THREADS'] = str(cpu_lim)
os.environ['MKL_NUM_THREADS'] = str(cpu_lim)
os.environ['VECLIB_MAXIMUM_THREADS'] = str(cpu_lim)
os.environ['NUMEXPR_NUM_THREADS'] = str(cpu_lim)
import sys
import argparse
sys.path.insert(0, '..')
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph
from dpagent.utils.llm import get_llm
from dpagent.agents.base import (
    create_agent_normal
)
from prompt_v5 import (
    InitialSelection_prompt,
    CircuitAnalysis_prompt,
    DebugSchemeSelection_prompt,
    ParameterTuning_prompt,
    TopologyModification_prompt
)

from dpagent.agents.Planning.dfs.Debugger.utils.parser import (
    parse_input_file
)
from atelier.sizing.sizing_spec1 import *
import json
import re
import pickle
import time


# ===================== graph state =====================
class DesignerState(TypedDict):
    desired_metrics: str
    current_netlist_description: str
    best_netlist_description: str
    number_of_topology_modification: int
    current_scheme: str
    current_metrics: str
    current_netlist: str
    selected_scheme: str
    current_parameters: list
    parameter_ranges: list
    parameter_names: list
    modification_history: list
    circuit_dir: str
    best_fom: float
    best_cons: float
    options: list
    best_sizing: list
    best_perf: list
    best_netlist_description: str
    best_netlist: str
    time: float

class Designer:
    def __init__(self):
        self.gen_agents()
        self.gen_graph()
        self.knowledge_file = 'circuit_analysis1.txt'
    def gen_agents(self):
        llm = get_llm(inc="zhipu")
        self.InitialSelection = create_agent_normal(llm=llm, prompt=InitialSelection_prompt, name="InitialSelection")
        self.CircuitAnalysis = create_agent_normal(llm=llm, prompt=CircuitAnalysis_prompt, name="CircuitAnalysis")
        self.DebugSchemeSelection = create_agent_normal(llm=llm, prompt=DebugSchemeSelection_prompt, name="DebugSchemeSelection")
        self.ParameterTuning = create_agent_normal(llm=llm, prompt=ParameterTuning_prompt, name="ParameterTuning")
        self.TopologyModification = create_agent_normal(llm=llm, prompt=TopologyModification_prompt, name="TopologyModification")
        
    def convert_to_json(self, s: str):
        match = re.search(r"```json\n(.*?)\n```", s, re.DOTALL)
        if match:
            cleaned_string = match.group(1)
        else:
            cleaned_string = s

        netlist_match = re.search(r'"netlist":\s*"(.*?)"', cleaned_string, re.DOTALL)
        if netlist_match:
            netlist_value = netlist_match.group(1)
            cleaned_string = cleaned_string.replace("\n", "")
            netlist_value_cleaned = re.sub(r'\\(?!n)', '', netlist_value)
            cleaned_string = cleaned_string.replace(netlist_value, netlist_value_cleaned)    
        try:
            json_object = json.loads(cleaned_string)
            print('object', json_object)
        except json.JSONDecodeError as e:
            print("Failed to parse JSON:", e)
        return json_object
    
    def convert_to_list(self, s: str):
        start_index = s.find('[')
        end_index = s.rfind(']')
        if start_index == -1 or end_index == -1:
            return None
        print(s[start_index+1:end_index].replace("\n", ""))
        l = eval(s[start_index+1:end_index].replace("\n", ""))
        return l
    
    def revise(self, netlist, new_statement):
        conflict_rules = [(re.compile(r"A capacitor connected between Node1 and NodeOutput", re.IGNORECASE), re.compile(r"A SRC block connected between Node1 and NodeOutput", re.IGNORECASE)), (re.compile(r"A capacitor connected between Node2 and NodeOutput", re.IGNORECASE), re.compile(r"A SRC block connected between Node2 and NodeOutput", re.IGNORECASE)), (re.compile(r"A SRC block connected between Node2 and NodeGround", re.IGNORECASE), re.compile(r"A DFC block connected at Node2", re.IGNORECASE))]

        conflict_found = False
        for rule in conflict_rules:
            pattern1, pattern2 = rule
            for stmt in netlist:
                if re.match(pattern1, stmt) and re.match(pattern2, new_statement):
                    netlist.remove(stmt)
                    conflict_found = True
                    break
                elif re.match(pattern2, stmt) and re.match(pattern1, new_statement):
                    netlist.remove(stmt)
                    conflict_found = True
                    break
            if conflict_found:
                break
        netlist.append(new_statement)
        return '.'.join(netlist)


    def initial_selection(self, state: DesignerState):
        with open('initial_designs_spec1.json', 'r') as file:
            initial_designs = json.load(file)
        inputDict = {
            "desired_metrics": state["desired_metrics"],
            "initial_designs": initial_designs,
            "initial_selection_supplementary_knowledge": parse_input_file(self.knowledge_file).get("initial_selection_supplementary_knowledge", "")
        }
        out = self.InitialSelection.invoke(inputDict)
        js = self.convert_to_json(out.content)
        netlist_description = initial_designs[js["selected_topology"]]

        return {"current_netlist_description": netlist_description,
                "current_scheme": "topology selection",
                "best_netlist_description": netlist_description
                }

    # ===================== nodes =====================
    def circuit_analysis(self, state: DesignerState):
        inputDict = {
            "desired_metrics": state["desired_metrics"],
            "current_netlist_description": state["current_netlist_description"],
            "circuit_analysis_supplementary_knowledge": parse_input_file(self.knowledge_file).get("circuit_analysis_supplementary_knowledge", "")
        }
        print("current_netlist_description", state["current_netlist_description"])
        out = self.CircuitAnalysis.invoke(inputDict)
        js = self.convert_to_json(out.content)
        params = [item for item in js["tunable_parameters"] if not item.startswith("Cprs")]
        return {"current_netlist": js["netlist"],
                "current_parameters": params,
                "current_scheme": "circuit analysis"
                }

    def parameter_tuning(self, state: DesignerState):
        inputDict = {
            "current_netlist": state["current_netlist"],
            "current_parameters": state["current_parameters"],
            "parameter_tuning_supplementary_knowledge": parse_input_file(self.knowledge_file).get("parameter_tuning_supplementary_knowledge", "")
        }

        out = self.ParameterTuning.invoke(inputDict)
        parameter_ranges = np.array(self.convert_to_list(out.content)).T
        circuit_dir = os.path.join("./sizing/spec1/", "circuit_behavior_"+state["circuit_dir"])
        with open(os.path.join(circuit_dir, "opamp.sp"), "w") as f:
            f.write(state["current_netlist"])
        best_x, obj, cons = sizing(circuit_dir, state["current_parameters"], parameter_ranges)
        d = opt_summary(best_x, obj, cons, state["current_parameters"], parameter_ranges)
        print("current cons", d['current_cons'])
        print("current fom", d['current_fom'])
        print("best cons", state['best_cons'])
        print("best fom", state['best_fom'])
        if d['current_cons'] < state["best_cons"] or (d['current_cons'] == state["best_cons"] and d['current_fom'] < state["best_fom"]):
            d["best_cons"] = d['current_cons']
            d['best_fom'] = d['current_fom']
            d['best_sizing'] = d['current_sizing']
            d['best_perf'] = d['current_perf']
            d["best_netlist_description"] = state["current_netlist_description"]
            d['best_netlist'] = state["current_netlist"]
            d["parameter_ranges"] = parameter_ranges
            d["parameter_names"] = state["current_parameters"]
            d['time'] = time.time() - start
            with open('res_'+state["circuit_dir"]+'.pkl', 'wb') as f:
                pickle.dump(d, f)
        else:
            d["best_cons"] = state['best_cons']
            d['best_fom'] = state['best_fom']
            d['best_sizing'] = state['best_sizing']
            d['best_perf'] = state['best_perf']
            d["best_netlist_description"] = state["best_netlist_description"]
            d['best_netlist'] = state["best_netlist"]
            d['current_cons'] = d["best_cons"]
            d['current_fom'] = d['best_fom']
            d['current_sizing'] = d['best_sizing']
            d['current_perf'] = d['best_perf']
            d["current_netlist_description"] = state["best_netlist_description"]
            d["parameter_names"] = state["parameter_names"]
            d["parameter_ranges"] = state["parameter_ranges"]
            d['time'] = state['time']
        if state["number_of_topology_modification"] == 1:
            with open('res1_'+state["circuit_dir"]+'.pkl', 'wb') as f:
                pickle.dump(d, f)
        return d
    
    def topology_modification(self, state: DesignerState):
        options = state["options"]
        current_paths = state["current_netlist_description"].split('.')
        for path in current_paths:
            if path in options:
                options.remove(path)
        for path in state["modification_history"]:
            if path in options:
                options.remove(path)
        print("options", options)
        inputDict = {
            "desired_metrics": state["desired_metrics"],
            "current_metrics": state["current_metrics"],
            "current_netlist_description": state["current_netlist_description"],
            "options": options,
            "topology_modification_supplementary_knowledge": parse_input_file(self.knowledge_file).get("topology_modification_supplementary_knowledge", "")
        }
        print("current_netlist_description", state["current_netlist_description"])
        print("state[modification_history]", state["modification_history"])
        out = self.TopologyModification.invoke(inputDict)
        
        js = self.convert_to_json(out.content)
        operation = js["selected_modification_name"]
        modified_description = self.revise(current_paths, operation)
        if operation not in state["modification_history"]:
            state["modification_history"].append(operation)
        else:
            print('repeated selection')
        for path in current_paths:
            if path not in state["modification_history"]:
                state["modification_history"].append(path)
        return {"modification_history": state["modification_history"], "current_netlist_description": modified_description, "current_scheme": "topology modification", "number_of_topology_modification": state["number_of_topology_modification"]+1}


    def selected_scheme(self, state: DesignerState):
        return state["number_of_topology_modification"] >= 3


    # ===================== graph =====================
    def enter_chain(self, chain_in):
        init_state = {
            "desired_metrics": chain_in["desired_metrics"],
            "current_netlist_description": "",
            "options": eval(chain_in["options"]),
            "current_netlist_description": "",
            "current_parameters": [],
            "best_cons": 1000,
            "best_fom": 1000,
            "circuit_dir": chain_in["circuit_dir"],
            "best_netlist_description": "",
            "current_scheme": "",
            'number_of_topology_modification': 0,
            'modification_history': [],
            "current_netlist": "",
            "best_sizing": [],
            "best_perf": [],
            "best_netlist_description": "",
            "best_netlist": ""
        }
        return init_state

    def gen_graph(self):
        designerGraph = StateGraph(DesignerState)

        # add nodes
        designerGraph.add_node("InitialSelection", self.initial_selection)
        designerGraph.add_node("CircuitAnalysis", self.circuit_analysis)
        designerGraph.add_node("ParameterTuning", self.parameter_tuning)
        designerGraph.add_node("TopologyModification", self.topology_modification)
        designerGraph.add_edge("InitialSelection", "CircuitAnalysis")
        designerGraph.add_edge("TopologyModification", "CircuitAnalysis")
        designerGraph.add_edge("CircuitAnalysis", "ParameterTuning")
        designerGraph.add_conditional_edges("ParameterTuning", self.selected_scheme, {True: END, False:"TopologyModification"})
        designerGraph.set_entry_point("InitialSelection")
        designerChain = self.enter_chain | designerGraph.compile()
        self.designerChain = designerChain
        self.designerGraph = designerGraph




if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser(description="Op-amp design")
    parser.add_argument('run', default=1, type=int, help="the id of run")
    args = parser.parse_args()
 
    designer = Designer()
    print("Start debugging the circuit...")
    inputs = parse_input_file('./case/case_spec1.txt')
    inputs["circuit_dir"] = str(args.run)
    
    chain_out = designer.designerChain.invoke(inputs)