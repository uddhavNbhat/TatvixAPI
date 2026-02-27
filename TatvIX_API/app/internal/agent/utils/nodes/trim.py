from app.internal.agent.utils.custom.baseagentclass import BaseAgentStructure
from app.internal.agent.utils.states import ChatState
from app.internal.agent.utils.custom.wrapper import make_node
from langchain.messages import (
    HumanMessage,
    ToolMessage,
    AIMessage,
    SystemMessage,
    trim_messages,
)
from langchain_core.messages.utils import count_tokens_approximately


@make_node
def trim_tool_output(agent: BaseAgentStructure, state: ChatState) -> ChatState:
    """Node to explicitly trim tool message length"""
    default_messages = state.get("messages")
    history_to_trim = default_messages[
        -2:
    ]  # The last 2 messages is always AI message followed by tool call output, hence trimming pipeline is deterministically made.
    to_trim = [
        x for x in history_to_trim if type(x) is ToolMessage or AIMessage
    ]  # Tool output messages to trim.
    try:
        trimmed_tool_output = trim_messages(
            to_trim,
            strategy="last",
            token_counter=count_tokens_approximately,  # Passes an estimated token count of the base message input.
            max_tokens=7000,
            start_on="ai",
            end_on=("tool"),
        )

        trimmed = []  # Make sure sequence of trimmedoutput is in the correct sequence our LLM expects the input in. (Human/System Message followed by AI/Tool Message)
        for msg in default_messages:
            if isinstance(msg, (HumanMessage, SystemMessage)):
                trimmed.append(msg)
            elif isinstance(msg, (AIMessage, ToolMessage)):
                if msg in trimmed_tool_output:
                    trimmed.append(msg)

    except Exception as e:
        raise e

    return {"messages": trimmed}


@make_node
def trim_input_context(agent: BaseAgentStructure, state: ChatState) -> ChatState:
    """Node to trim input context to make sure context window size is not exceeded by the token length of the input for the large language model input"""
    try:
        trimmed_messages = trim_messages(
            state.get("messages"),
            strategy="last",
            token_counter=count_tokens_approximately,  # Passes an estimated token count of the base message input.
            max_tokens=3000,
            start_on="human",
            end_on=("human", "tool"),
        )

    except Exception as e:
        raise e

    return {"messages": trimmed_messages}
