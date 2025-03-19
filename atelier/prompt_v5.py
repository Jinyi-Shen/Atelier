from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from dpagent.agents.Planning.prompt import development_plan

CircuitAnalysis_sys_prompt = """
You are an assistant to analog circuit design engineers.
Your mission is to help analog circuit designers design a three-stage opamp.
"""

InitialSelection_human_prompt = """
---[info]---
[Required Performance Metrics]:{{desired_metrics}}
[Initial Designs]:{{initial_designs}}
[Initial Selection Supplementary Knowledge]:{{initial_selection_supplementary_knowledge}}
---

---[info explanation]---
The op-amp refers to operational amplifier.
The [Required Performance Metrics] are the performance requirements for the op-amp design.
The [Initial Designs] is the set of initial topologies from which you should select the most suitable topology for the [Required Performance Metrics].
The [Initial Selection Supplementary Knowledge] is provided by the user to help you make your answer.
---

---[request]---
With the [info] and [info explanation] provided, you need to select the most suitable topology from the [Initial Designs] for the [Required Performance Metrics]. Your response should be in JSON with two keys: "selected_topology" and "reasons_for_selection".
---
"""

CircuitAnalysis_human_prompt = """
---[info]---
[Required Performance Metrics]:{{desired_metrics}}
[Current Netlist Description]:{{current_netlist_description}}
[Circuit Analysis Supplementary Knowledge]:{{circuit_analysis_supplementary_knowledge}}
---

---[info explanation]---
The op-amp refers to operational amplifier.
The [Required Performance Metrics] are the performance requirements for the op-amp design.
The [Current Netlist Description] is the description of the compensation structure of the current op-amp using natural language.
The [Circuit Analysis Supplementary Knowledge] is provided by the user to help you make your answer.
---

---[request]---
With the [info] and [info explanation] provided, you need to do the following tasks:
1. For each sentence in the [Current Netlist Description], list the sentence and generate the corresponding SPICE netlist lines according to the [Circuit Analysis Supplementary Knowledge]. 
2. Concatenate all netlist lines generated in the previous task to get the SPICE netlist of the part of "compensation structure".
3. Generate the complete SPICE netlist of the op-amp.
4. Provide all tunable parameters in the netlist.
Please execute these tasks one by one and provide your response in JSON with three keys: "output_of_task1", "netlist", and "tunable_parameters". The value of "tunable_parameters" is a list, in which each element is a string that is the parameter name.
---
"""

DebugSchemeSelection_human_prompt = """
---[info]---
[Current Scheme]:{{current_scheme}}
[Scheme Selection Supplementary Knowledge]:{{scheme_selection_supplementary_knowledge}}
[Number of Topology Modification]:{{number_of_topology_modification}}
---

---[info explanation]---
The [Current Scheme] is the previous operation in op-amp design.
The [Circuit Analysis Supplementary Knowledge] is provided by the user to help you make your answer.
The [Number of Topology Modification] is the number of "Topology Modification" that have been tried in op-amp design.
---

---[request]---
You are a circuit design decision maker.
According to the [info] and [info explanation] provided, you need to select exactly one operation from the following four options:
1. circuit analysis
2. parameter tuning
3. topology modification
4. end
You should only output the name of the selected operation.
---
"""

ParameterTuning_human_prompt = """
---[info]---
[Current Parameters]:{{current_parameters}}
[Parameter Tuning Supplementary Knowledge]:{{parameter_tuning_supplementary_knowledge}}
---

---[info explanation]---
The [Current Parameters] is a list that contains all tunable parameters in the current op-amp.
The [Parameter Tuning Supplementary Knowledge] is provided by the user to help you make your answer.
---

---[request]---
With the [info] and [info explanation] provided, you need to do determine the ranges of all tunable parameters:
Your response should only be a single list, in which each element is a list whose first element is the lower bound and the second element is the upper bound of the parameter. You should not add any comments to your response. You should not write a code to generate the response.
---
"""

TopologyModification_human_prompt = """
---[info]---
[Required Performance Metrics]:{{desired_metrics}}
[Current Performance Metrics]:{{current_metrics}}
[Current Netlist Description]:{{current_netlist_description}}
[Options]:{{options}}
[Topology Modification Supplementary Knowledge]:{{topology_modification_supplementary_knowledge}}
---

---[explain info]---
The op-amp refers to operational amplifier.
The [Required Performance Metrics] are the performance requirements for the op-amp design.
The [Current Performance Metrics] are the performance metrics for the current op-amp.
The [Current Netlist Description] is the description of the compensation structure of the current op-amp using natural language.
The [Options] lists all available modification options to the current op-amp.
The [Topology Modification Supplementary Knowledge] is to provide guidance on how to modify the topology.
---

---[request]---
With the [info] and [info explanation] provided, you need to do the following tasks:
1. Compare the current [Current Performance Metrics] with the [Required Performance Metrics] to find out the metrics that do not meet the requirements.
2. Select one modification from the {{options}} based on metric analysis of task1 according to the [Topology Modification Supplementary Knowledge].
Please execute these tasks one by one and provide your response in a single JSON with keys: "performance_comparison", "selected_modification_name", and "reasons_for_selection". The value of "selected_modification_name" should be a string that only contains the name of the selected modification. You should not add any comments to your response. 
---
"""


Conclusion_human_prompt = """
---[info]---
[Circuit_name]: {{circuit_name}}
[Required Performance Metrics]:{{desired_metrics}}
[Initial Performance Metrics]:{{initial_metrics}}
[Initial Netlist]:{{initial_netlist}}
[Current Performance Metrics]:{{current_metrics}}
[Current Netlist]:{{current_netlist}}
[Historical Debugging Schemes]:{{historical_debugging_schemes}}
---

---[explain info]---
The [Circuit_name] [Required Performance Metrics] [Initial Performance Metrics] [Initial Netlist] are the basic information of the initial analog circuit.
The [Historical Debugging Schemes] are the debugging schemes that have been tried before, which contains the debugging methods and the corresponding performance metrics and netlists.
---

---[request]---
You are a summarizer.
With the [info] [explain info] provided, you need to do two thinks
1. Conclusion.
2. Comparison.
---
"""
InitialSelection_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(CircuitAnalysis_sys_prompt),
        HumanMessagePromptTemplate.from_template(InitialSelection_human_prompt,template_format="jinja2"),
    ]
)

CircuitAnalysis_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(CircuitAnalysis_sys_prompt),
        HumanMessagePromptTemplate.from_template(CircuitAnalysis_human_prompt,template_format="jinja2"),
    ]
)

DebugSchemeSelection_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(CircuitAnalysis_sys_prompt),
        HumanMessagePromptTemplate.from_template(DebugSchemeSelection_human_prompt,template_format="jinja2"),
    ]
)

ParameterTuning_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(CircuitAnalysis_sys_prompt),
        HumanMessagePromptTemplate.from_template(ParameterTuning_human_prompt,template_format="jinja2"),
    ]
)

TopologyModification_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(CircuitAnalysis_sys_prompt),
        HumanMessagePromptTemplate.from_template(TopologyModification_human_prompt,template_format="jinja2"),
    ]
)

Conclusion_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(CircuitAnalysis_sys_prompt),
        HumanMessagePromptTemplate.from_template(Conclusion_human_prompt,template_format="jinja2"),
    ]
)




