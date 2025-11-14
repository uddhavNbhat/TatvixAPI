from langchain_mcp_adapters.client import MultiServerMCPClient
from app.settings import settings

class McpClient():
    def __init__(self):
        self.mcp_client = self._get_mcp_client()
        self.tools = self._get_tools()

    def _get_mcp_client(self):
        """ Method to get mcp client object """
        client = MultiServerMCPClient(
            {
                #Retrieval client
                "retrieval": {
                    "transport": "streamable_http",
                    "url": settings.MCP_SERVER, #http endpoint of mcp server.
                }
            }
        )
        return client
    
    async def _get_tools(self):
        tools = await self.mcp_client.get_tools()
        return tools


mcp = McpClient()

