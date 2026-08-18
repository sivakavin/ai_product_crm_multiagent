from graph.state import AgentState
from utils.llm import call_llm
from utils.prompt_loader import build_prompt
from utils.db import get_all_schemas,run_sql



def sql_agent_node(state:AgentState)-> dict:
    schemas = get_all_schemas()
    prompt = build_prompt("sql_agent",schemas=schemas,question=state["question"])
    query = call_llm(prompt,tier="sql_model").strip()
    print("Query :",query)
    result = run_sql(query)

    return {"sql_result":result}