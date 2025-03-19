.subckt opamp NodeInput NodeOutput NodeGround
*main amplification stages and associated parasitics
G_in_1 Node1 NodeGround NodeInput NodeGround G_in_1
Rprs_in_1 Node1 NodeGround 'Rprs_in_1/G_in_1'
G_1_2 Node2 NodeGround Node1 NodeGround '-1*G_1_2'
Rprs_1_2 Node2 NodeGround 'Rprs_1_2/G_1_2'
Cprsin_1_2 Node1 NodeGround 'G_1_2/6.28*5n'
G_2_out NodeOutput NodeGround Node2 NodeGround G_2_out
Rprs_2_out NodeOutput NodeGround 'Rprs_2_out/G_2_out'
Cprsin_2_out Node2 NodeGround 'G_2_out/6.28*5n'
*loads
C_L NodeOutput NodeGround 1n
R_L NodeOutput NodeGround 1000000
*compensation structure
C_Node1_NodeOutput Node1 NodeOutput C_Node1_NodeOutput
G_Node1_NodeOutput NodeOutput NodeGround Node1 NodeGround G_Node1_NodeOutput
Rprs_Node1_NodeOutput NodeOutput NodeGround 'Rprs_Node1_NodeOutput/G_Node1_NodeOutput'
Cprsin_Node1_NodeOutput Node1 NodeGround 'G_Node1_NodeOutput/6.28*5n'
R_Node2_Node2_NodeGround Node2 Node2_NodeGround R_Node2_Node2_NodeGround
C_Node2_NodeGround Node2_NodeGround NodeGround C_Node2_NodeGround
C_Node2_NodeOutput Node2 NodeOutput C_Node2_NodeOutput
C_Node2_NodeOutput_2 Node2 NodeOutput C_Node2_NodeOutput_2
.ends