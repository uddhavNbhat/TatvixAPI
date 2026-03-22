from typing import ClassVar, Optional, List
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph.state import CompiledStateGraph
from app.internal.agent.utils.nodes.summarize import (
    should_summarize,
    summarize_node,
)
from app.internal.agent.utils.nodes.converge import (
    should_build_objective,
    build_state,
)
from app.internal.agent.utils.custom.agent_tools import AgentTools
from app.internal.agent.utils.states.parent import ParentAgentSchema
from app.internal.agent.utils.custom.mcp_client import McpClient
from app.utils.logger import logger
from app.internal.agent.utils.custom.model_factory import ModelFactory
from app.internal.agent.sub_agents.executor_agent import ExecutionAgent
from app.internal.agent.sub_agents.objective_agent import ObjectiveAgent
import certifi
import os

# Force Python to use certifi's CA bundle so TLS/HTTPS validation works
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


class LegalAgent:
    _cahced_tools: ClassVar[Optional[List]] = None  # Global class cache for MCP tools.

    def __init__(self):
        self.retries = None
        self.llm: ChatGroq | ChatOllama | ChatGoogleGenerativeAI | ChatOpenAI = None
        self.family = None
        self.name = None
        self.tool_caller = None
        self.tools = None
        self._checkpointer: MongoDBSaver = None
        self.objective_agent: CompiledStateGraph = None
        self.execution_agent: CompiledStateGraph = None
        self.agent_graph: CompiledStateGraph = None

    @classmethod
    async def init_agent(
        cls, model_family: str, model_name: str, checkpointer: MongoDBSaver
    ):
        """Decoupled async instance variable initializer for class"""
        self = cls()  # Class object

        async def _populate_agent_attributes(self: LegalAgent):
            try:
                self.retries = 3
                self.family = model_family
                self.name = model_name
                self.llm = (
                    ModelFactory()
                    .initialize_model(model_family=self.family, model_name=self.name)
                    .model
                )
                if cls._cahced_tools is None:
                    cls._cahced_tools = await self._get_mcp_tools()
                self.tool_caller = await AgentTools.init_agent_tools(cls._cahced_tools)
                self._checkpointer = checkpointer
                self.objective_agent = ObjectiveAgent(llm=self.llm).agent_graph
                self.execution_agent = ExecutionAgent(
                    llm=self.llm, tool_caller=self.tool_caller
                ).agent_graph
            except Exception as e:
                raise e

        await _populate_agent_attributes(self=self)
        # Build the agent after the required agent attributes are populated.
        self.agent_graph = self._build_agent()
        return self

    async def _get_mcp_tools(self):
        """Method to get mcp tools from mcp server."""
        client = McpClient()
        return await client._init_tools()

    def _build_agent(self) -> CompiledStateGraph:
        """Builds Legal Agent graph and returns built graph object"""
        try:
            if not (
                self.family
                and self.name
                and self.llm
                and self.execution_agent
                and self.objective_agent
            ):
                raise Exception("Agent initialization Incomplete!")
            # Builder initialization
            builder = StateGraph(ParentAgentSchema)
            # Nodes
            builder.add_node("build_objective", self.objective_agent)
            builder.add_node("execution_agent", self.execution_agent)
            builder.add_node("summarizer_node", summarize_node(self))
            builder.add_node("state_node", build_state(self))
            # Edges
            builder.add_edge(START, "execution_agent")
            builder.add_conditional_edges(
                START,
                should_build_objective(self),
                {"build_objective": "build_objective", "END": END},
            )
            builder.add_edge("build_objective", "state_node")
            builder.add_edge("execution_agent", "state_node")
            builder.add_conditional_edges(
                "state_node",
                should_summarize(self),
                {"summarizer_node": "summarizer_node", "END": END},
            )
            builder.add_edge("summarizer_node", END)
            # Compiled State Graph
            graph = builder.compile(checkpointer=self._checkpointer)

            return graph
        except Exception as e:
            raise e

    async def invoke(self, session_id: str, query: str):
        """Method to invoke the compiled agent graph"""
        try:
            if not self.agent_graph:
                raise Exception("Can only Invoke Agent after it is built!")

            config = {"configurable": {"thread_id": session_id}}

            agent_input = {"user_query": query}

            response = await self.agent_graph.ainvoke(config=config, input=agent_input)

            messages = response["messages"]
            objective = response["objective"]
            document_data = response["document_output"]
            content = response["llm_output"]

            if not content:
                content = messages[-1].content
                if isinstance(self.llm, ChatGoogleGenerativeAI):
                    return {"content": content[0]["text"]}
                return {"content": content}

            if isinstance(content, list) and isinstance(
                self.llm, ChatGoogleGenerativeAI
            ):
                content = response["llm_output"][0]["text"]

            return {
                "objective": objective,
                "document_data": document_data,
                "content": content,
            }

        except Exception as e:
            logger.error(f"Error at {LegalAgent.__name__}: {e}")
            raise e

    def clear_chat(self, session_id: str):
        """Clear current session from lang graph checkpointer"""
        try:
            response = self._checkpointer.delete_thread(session_id)
            return response
        except Exception as e:
            raise e
