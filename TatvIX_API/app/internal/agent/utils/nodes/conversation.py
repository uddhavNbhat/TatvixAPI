from app.internal.agent.utils.custom.baseagentclass import BaseAgentStructure
from app.internal.agent.utils.states import ChatState
from app.internal.agent.utils.prompts import prompt_templates
from app.internal.agent.utils.custom.wrapper import make_node
from langchain.messages import SystemMessage


@make_node
def generate_header(agent: BaseAgentStructure, state: ChatState) -> ChatState:
    """Node to generate thread header for the on-going conversation"""
    user_query = state.get("user_query")
    template = prompt_templates.header_template
    try:
        if user_query:
            query_template = template.invoke({"user_query": user_query})
            response = agent.model.invoke(query_template)
            print(response.text)  # LOG
        else:
            raise Exception("No user query passed!!!")

    except Exception as e:
        raise e

    return {"heading": response.text}


@make_node
def chat_node(agent: BaseAgentStructure, state: ChatState) -> ChatState:
    """Node to initiate conversation with the chat model"""

    error_codes = [400, 404, 413, 429]

    default_messages = state.get("messages")
    final_message = [
        SystemMessage(content=prompt_templates.system_template)
    ] + default_messages
    summary = state.get("summary")
    if summary:
        print(f"Summary so far: {summary}")
        system_message = f"Summary of previous conversation is : {summary}"
        messages = [SystemMessage(content=system_message), *final_message]
    else:
        messages = [*final_message]

    try:
        response = agent.model.invoke(messages)

    except Exception as e:
        if getattr(e, "status_code", None) in error_codes:
            print("\n Using Fallback model.....\n")
            response = agent.fallback_model.invoke(messages)
            return {"messages": [response]}
        raise e

    return {"messages": [response]}
