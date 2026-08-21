from nodes.rag_agent import rag_agent_node

result = rag_agent_node({"question":"Tell me replacement option?"})
print(result["rag_result"])