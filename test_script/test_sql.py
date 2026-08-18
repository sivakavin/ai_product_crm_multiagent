from nodes.sql_agent import sql_agent_node

result = sql_agent_node({"question":"Show me bengaluru based customer name?"})
print(result["sql_result"])