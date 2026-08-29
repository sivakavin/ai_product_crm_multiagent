import asyncio
from utils.mcp_client import MCPClient

sql_mcp = MCPClient("mcp_servers/sql_server.py")

print("Schema:")
print(sql_mcp.call("get_all_schemas"))
# async def main():
#     async with Client(_build_transport("sql")) as client:
#         tools = await client.list_tools()
#         print("Available Tools:")
#         for tool in tools:
#             print(f"- {tool.name}: {tool.description}")

# asyncio.run(main())