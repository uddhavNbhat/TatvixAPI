from app.internal.agent.utils.custom.baseagentclass import BaseAgentStructure
from app.internal.agent.utils.states import ChatState
from app.internal.agent.utils.custom.wrapper import make_node
from langchain.messages import HumanMessage


@make_node
def append_query(agent: BaseAgentStructure, state: ChatState) -> ChatState:
    """Node to append user query to messages reducer"""
    query = state.get("user_query")  # Get user query
    messages = state.get("messages")  # Get overall message state
    messages.append(
        HumanMessage(content=query)
    )  # Append user query to message state reducer
    return {"messages": messages}  # Return message state object as the node output
