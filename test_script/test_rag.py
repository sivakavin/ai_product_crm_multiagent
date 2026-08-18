from nodes.rag_agent import rag_agent_node

result = rag_agent_node({"question":"when can i expect my order?"})
print(result["rag_result"])