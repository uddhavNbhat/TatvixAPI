from app.internal.agent.utils.custom.baseagentclass import BaseAgentStructure
from app.internal.agent.utils.states import ChatState
from app.internal.agent.utils.custom.wrapper import make_node
from langgraph.prebuilt import ToolNode


@make_node
def tool_node(agent: BaseAgentStructure, state: ChatState) -> ToolNode:
    """Node to wrap retrieved tool list with a prebuilt ToolNode class for an appropriate Tool function in the compilable graph"""
    return ToolNode(tools=agent.tools)
