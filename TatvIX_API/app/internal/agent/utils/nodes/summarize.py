from app.internal.agent.utils.custom.baseagentclass import BaseAgentStructure
from app.internal.agent.utils.states import ChatState
from app.internal.agent.utils.custom.wrapper import make_node
from langchain.messages import HumanMessage, RemoveMessage


@make_node
def summary_node(agent: BaseAgentStructure, state: ChatState) -> ChatState:
    """Node to build summaries of accumilated messages in message state reducer to improve checkpointer performance/Model performance"""
    summary = state.get("summary", "")
    if summary:
        summary_message = (
            f"This is the summary of the conversation to date: {summary}\n"
            "Extend the summary by taking into account the new messages above:\n"
            "Make sure the summary is no more than 100 tokens in length please"
        )
    else:
        summary_message = "Create a summary of the conversation above:"
    # Add the summary to the state reducer and invoke the model for summarized input
    messages = state.get("messages") + [HumanMessage(content=summary_message)]
    try:
        response = agent.model.invoke(messages)
        print(response.content)
        # Remove everything but the last 2 messages as a summary already exists now
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
        return {"summary": response.content, "messages": delete_messages}

    except Exception as e:
        print(f"Exception -> {e}")
        raise e
