from langchain.messages import HumanMessage, RemoveMessage, SystemMessage
from typing import Literal
from app.internal.agent.utils.custom.agent_class import BaseAgentStructure
from app.internal.agent.utils.states.parent import ParentAgentSchema
from app.internal.agent.utils.custom.prompts import prompt_templates
from app.internal.agent.utils.custom.wrapper import make_node, make_async_node


@make_async_node
async def summarize_node(
    self: BaseAgentStructure, state: ParentAgentSchema
) -> ParentAgentSchema:
    """Node to summarize conversation for keeping track of each convo with enough reference to the past ones"""
    aggregation_output = state.get("aggregation_output", [])
    messages = state.get("messages", [])
    if not aggregation_output or not messages:
        return {"global_summary": ""}
    # Current aggregation
    current_aggregation = aggregation_output[-1]
    # Summary so far
    prev_global_summary = state.get("global_summary", "")
    # Goals met during the current conversation and user query
    current_messages = messages[
        -2:
    ]  # Get the latest two messages (user query and conclusion of tasks for curr convo)
    try:
        summary_template = prompt_templates.get_summarizer_template()

        model_input = [
            current_aggregation,
            *current_messages,
            SystemMessage(content=f"GLOBAL SUMMARY SO FAR: \n{prev_global_summary}"),
            summary_template,
        ]

        model_input = [m for m in model_input if m is not None]

        response = await self.llm.ainvoke(model_input)

        print(f"\n GLOBAL SUMMARY: \n {response.content}\n\n")

        # Remove all the messages except the latest two (current conversation)
        delete_messages = [RemoveMessage(id=m.id) for m in messages[:-2]]
        # Remove all aggregations except the latest one
        delete_aggregations = [RemoveMessage(id=m.id) for m in aggregation_output[:-1]]

        return {
            "global_summary": response.content,
            "messages": delete_messages,
            "aggregation_output": delete_aggregations,
        }

    except Exception as e:
        raise e


@make_node
def should_summarize(
    self: BaseAgentStructure, state: ParentAgentSchema
) -> Literal["summarizer_node", "END"]:
    """Conditional edge to see if the system needs a memory refresh on messages built so far"""
    messages = state.get("messages", [])

    human_messages = len([x for x in messages if isinstance(x, HumanMessage)])

    # If conversation has gone past 3 turns summarize
    if human_messages >= 3:
        return "summarizer_node"

    return "END"
