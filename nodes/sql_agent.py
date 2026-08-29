from graph.state import AgentState
from utils.llm import call_llm
from utils.prompt_loader import build_prompt
from utils.logger import get_logger
from utils.mcp_client import call_mcp_tool

log = get_logger(__name__)


def sql_agent_node(state: AgentState) -> dict:
    log.info("SQL agent: generating query")
    schemas = call_mcp_tool("sql", "get_all_schemas")
    prompt = build_prompt("sql_agent", schemas=schemas, question=state["question"])
    query = call_llm(prompt, tier="sql_model").strip()
    log.info("SQL agent: generated query -> %s", query)
    result = call_mcp_tool("sql", "run_sql", {"query": query})
    log.debug("SQL agent: result -> %s", result)

    return {"sql_result": result}
