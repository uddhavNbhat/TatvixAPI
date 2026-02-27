from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.mongodb import MongoDBSaver
from typing import Literal, Optional, List
import certifi
import os
from langgraph.prebuilt import tools_condition
from app.internal.agent.utils.states import ChatState
from app.internal.agent.utils.mcp_client import McpClient
from app.internal.agent.utils.nodes import (
    trim_tool_output,
    append_query,
    chat_node,
    generate_header,
    summary_node,
    tool_node,
    trim_input_context,
)
from app.utils.logger import logger
from langgraph.graph.state import CompiledStateGraph
from app.internal.agent.utils.model_factory import ModelFactory
from typing import ClassVar

# Force Python to use certifi's CA bundle so TLS/HTTPS validation works
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


class LegalAgent:
    _cahced_tools: ClassVar[Optional[List]] = (
        None  # Global class cache for MCP tools only accesible through class.
    )

    def __init__(self):
        self.model_family = None
        self.model_name = None
        self.tools = None
        self.model = None
        self.fallback_model = None
        self.checkpointer: Optional[MongoDBSaver] = None
        self._graph: Optional[CompiledStateGraph] = None

    @classmethod
    async def init_legal_agent(cls, model_family, model_name, checkpointer):
        """Method to get mcp tools while creating class instance consistently."""
        self = cls()
        if cls._cahced_tools is None:
            cls._cahced_tools = await self._get_mcp_tools()
        self.model_family = model_family
        self.model_name = model_name
        self.tools = cls._cahced_tools
        self.model = self._get_llm()
        self.fallback_model = self._initialize_fallback_model()
        self.checkpointer = checkpointer
        # Build graph on intialization
        self._build_graph()

        return self

    async def _get_mcp_tools(self):
        """Method to get mcp tools from mcp server."""
        client = McpClient()
        return await client._init_tools()

    def _get_llm(self):
        """Method to initialize chat model"""
        factory = ModelFactory.initialize_model(
            model_family=self.model_family, model_name=self.model_name
        )
        model = factory.model.bind_tools(self.tools)
        return model

    def _initialize_fallback_model(self):
        """Method to intialize fallback model"""
        fallback_model = ChatOllama(model="qwen3:4b").bind_tools(self.tools)
        return fallback_model

    def _should_summarize(
        self, state: ChatState
    ) -> Literal["summary_node", "chat_node"]:
        """conditional edge to make sure if more than n messages have accumilated, summarize chat history"""
        user_msg = [
            m for m in state.get("messages") if isinstance(m, HumanMessage)
        ]  # Count only the number of pormpts asked by the user.
        if len(user_msg) > 3:  # Set to 3 for test purposes.
            return "summary_node"
        return "trim_input_context"

    def _should_generate_header(
        self, state: ChatState
    ) -> Literal["generate_header", "chat_node"]:
        """conditional edge to generate section header for the UI"""
        header = state.get("heading", "")
        if header:
            return "chat_node"
        return "generate_header"

    def _build_graph(self):
        """Create langgraph agent workflow and complie it"""
        if self._graph is None:
            try:
                # Nodes
                builder = StateGraph(ChatState)
                builder.add_node("append_query", append_query(self))
                builder.add_node("tools", tool_node(self))
                builder.add_node("generate_header", generate_header(self))
                builder.add_node("trim_input_context", trim_input_context(self))
                builder.add_node("trim_tool_output", trim_tool_output(self))
                builder.add_node("summary_node", summary_node(self))
                builder.add_node("chat_node", chat_node(self))

                builder.add_edge(START, "append_query")
                builder.add_conditional_edges(
                    "append_query",
                    self._should_summarize,
                    {
                        "trim_input_context": "trim_input_context",
                        "summary_node": "summary_node",
                    },
                )
                builder.add_edge("summary_node", "trim_input_context")
                builder.add_conditional_edges(
                    "trim_input_context",
                    self._should_generate_header,
                    {"chat_node": "chat_node", "generate_header": "generate_header"},
                )
                builder.add_edge("generate_header", "chat_node")
                builder.add_edge("trim_input_context", "chat_node")
                builder.add_conditional_edges("chat_node", tools_condition)
                builder.add_edge("tools", "trim_tool_output")
                builder.add_edge("trim_tool_output", "chat_node")

                if self.checkpointer is None:
                    raise RuntimeError(
                        "checkpointer not initialized! Use app.state.legal_agent.checkpointer"
                    )

                self._graph = builder.compile(checkpointer=self.checkpointer)

            except Exception as e:
                print(f"Exception -> {e}")  # Log
                raise e

        return self._graph

    async def get_response(self, message: str, session_id: str):
        """Get response from the LLM for user question"""
        if self.checkpointer is None:
            raise RuntimeError(
                "No Memory for the agent to go with, make sure checkpointer is set!"
            )

        config = {"configurable": {"thread_id": session_id}}

        try:
            response = await self._graph.ainvoke({"user_query": message}, config)
            print(response["messages"])  # LOG
            data = response.get("messages", "")
            header = response.get("heading", "")
            content = None
            for msg in reversed(data):
                if isinstance(msg, AIMessage):
                    content = msg.content

                    if isinstance(content, str):
                        response_data = {"content": content}
                        break
                    elif isinstance(content, list):
                        # Extract text from the list of content blocks
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block["text"])
                        response_data = {"content": "\n".join(text_parts)}
                        break

            if "heading" in response:
                response_data["header"] = header

            """tool_messages = [
                m for m in response["messages"]
                if isinstance(m, ToolMessage)
            ] #Extract all the tool messages from the messages list from graph state.
            print(tool_messages)
            """
        except Exception as e:
            logger.error(f"Error at get_response: {e}")
            raise e

        return response_data

    def clear_chat(self, session_id: str):
        """Clear current session from lang graph checkpointer"""
        try:
            response = self.checkpointer.delete_thread(session_id)
            return response
        except Exception as e:
            raise e
