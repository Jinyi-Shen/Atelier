# Atelier: An Automated Analog Circuit Design Framework via Multiple Large Language Model-based Agents

This is the code repository for our proposed method Atelier that accompanys our paper Atelier: An Automated Analog Circuit Design Framework via Multiple Large Language Model-based Agents, which has been accepted by IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems 2025.

## Prerequisites and Dependencies

1. Install the prerequisite packages in ```./requirements.txt``` via ```pip``` or ```conda```. We used Anaconda Python 3.10 for our experiments.

2. Add your own ZhiPu API key at line 20 in ```/dpagent/utils/llm.py``` to enable LLM functionality.

## Running Experiments

The code related to opamp design is under ```./atelier/```. Start the optimization for spec1 with ```./run.sh```.
