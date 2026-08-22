from graph.state import AgentState
from utils.llm import call_llm
from utils.prompt_loader import build_prompt
from utils.db import get_all_schemas,run_sql
from utils.logger import get_logger
import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


log = get_logger(__name__)
SQL_SERVER = StdioTransport(
    command="python",
    args=["mcp_servers/sql_server.py"],
)
# SQL_SERVER = "mcp_servers/sql_server.py"

async def _call_mcp(tool_name:str,args:dict)->str:
    async with Client(SQL_SERVER) as client:
        result = await client.call_tool(tool_name,args)
        return result[0].text

def sql_agent_node(state:AgentState)-> dict:
    log.info("SQL agent: generating query")
    # schemas = get_all_schemas()
    schemas = asyncio.run(_call_mcp("get_all_schemas",{}))
    prompt = build_prompt("sql_agent",schemas=schemas,question=state["question"])
    query = call_llm(prompt,tier="sql_model").strip()
    log.info("SQL agent: generated query -> %s", query)
    # result = run_sql(query)
    result = asyncio.run(_call_mcp("run_sql",{"query":query}))
    log.debug("SQL agent: result -> %s", result)

    return {"sql_result":result}