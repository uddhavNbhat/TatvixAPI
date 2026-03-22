from typing import ClassVar, List, Dict
from langgraph.graph.state import Runnable
from langchain_core.tools import BaseTool

class AgentTools:
    current_tools: ClassVar[List[str]] = [
        "document_search",
        "search_engine"
    ]
    def __init__(self):
        self.tool_map: Dict[str, Runnable] | None = None
    
    @classmethod
    async def init_agent_tools(cls, tools: List[BaseTool]):
        """ Class method to instantiate agent tool class by passing a list of base tool dependency """
        self = cls()
        self.tool_map = {
            "document_search" : next(x.coroutine for x in tools if x.name == "document_search"),
            "search_engine" : next(x.coroutine for x in tools if x.name == "search_engine")
        }
        return self
    
    async def call_tool(self, tool_name: str, **kwargs):
        """
        Call the mappable tool from agent intent \n
        Args:
            tool_name: str -> pass tool name from supported list (["document_search", "search_engine"]), \n
            **kwargs
        """
        try:
            if tool_name not in self.current_tools:
                raise ValueError("No such tool exists!")
            tool = self.tool_map[tool_name]
            if tool_name == "document_search" or tool_name == "search_engine":
                query = kwargs["query"]
                response = await tool(query=query)
                return response
        except Exception as e:
            raise e

