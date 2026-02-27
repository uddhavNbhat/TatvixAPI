from typing import Protocol, Optional, List
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import Runnable


# Base instance level attributes of the class for the nodes to use.
class BaseAgentStructure(Protocol):
    model_family: Optional[str]
    model_name: Optional[str]
    tools: Optional[List]
    model: Optional[Runnable]
    fallback_model: Optional[Runnable]
    checkpointer: Optional[MongoDBSaver]
    _graph: Optional[CompiledStateGraph]
