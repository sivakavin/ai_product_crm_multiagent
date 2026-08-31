import asyncio
from fastmcp import Client
import logging 

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self,server,name:str="mcp"):
        self.server = server
        self.name = name
        self._direct_tools = {}

        #Cache direct tools for in-memory (avoid redis issue)
        if not isinstance(server,str):
            for tool_name,tool in server._tool_manager._tool.items():
                self._direct_tools[tool_name] = tool.fn

    def call(self,tool_name:str,args:dict={})->str:
        return asyncio.run(self._call(tool_name,args))

    async def _call(self,tool_name:str,args:dict) -> str:
        async with Client(self.server) as client:
            result = await client.call_tool(tool_name,args)
            return str(result.data)

# class MCPRegistry:
#     """ One place to manage all mcp server"""

#     def __init__(self):
#         self._clients = {}

#     def register(self,name:str,server):
#         self._clients = MCPClient(server,name=name)
    