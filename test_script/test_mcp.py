from mcp_servers.sql_server import mcp as sql_server
from utils.mcp_client import MCPClient

# sql_mcp = MCPClient("mcp_servers/sql_server.py")
client = MCPClient(sql_server)
print(client.call("get_all_schemas"))
