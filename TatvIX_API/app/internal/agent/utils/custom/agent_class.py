from typing import Protocol, Optional, List
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from app.internal.agent.utils.custom.weaviate import WeaviateStore
from app.internal.agent.utils.custom.agent_tools import AgentTools

# Set to optional for testing, types will established in the future.


# Base instance level attributes of the class for the nodes to use.
class BaseAgentStructure(Protocol):
    retries: Optional[int]
    llm: Optional[ChatOpenAI | ChatGroq | ChatOllama | ChatGoogleGenerativeAI]
    family: Optional[str]
    name: Optional[str]
    tools: Optional[List[BaseTool]]
    tool_caller: Optional[AgentTools]
    _checkpointer: Optional[MongoDBSaver]
    _store: Optional[WeaviateStore]
    objective_agent: Optional[CompiledStateGraph]
    execution_agent: Optional[CompiledStateGraph]
    agent_graph: Optional[CompiledStateGraph]


# Objective Agent instance Protocol for type ref
class ObjectiveAgentStructure(Protocol):
    retries: Optional[int]
    objective_llm: Optional[Runnable]
    agent_graph: Optional[CompiledStateGraph]


# Executor Agent instance Protocl for type ref
class ExecutorAgentStructure(Protocol):
    retries: Optional[int]
    tool_caller: Optional[AgentTools]
    should_plan_llm: Optional[Runnable]
    planner_llm: Optional[Runnable]
    execution_llm: Optional[Runnable]
    task_list_llm: Optional[Runnable]
    aggregator_llm: Optional[Runnable]
    agent_graph: CompiledStateGraph
    _store: Optional[WeaviateStore]
