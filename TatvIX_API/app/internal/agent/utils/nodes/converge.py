from langchain.messages import AIMessage
from app.internal.agent.utils.custom.agent_class import BaseAgentStructure
from app.internal.agent.utils.states.parent import ParentAgentSchema
from app.internal.agent.utils.custom.wrapper import make_node
from app.utils.logger import logger


@make_node
def should_build_objective(self: BaseAgentStructure, state: ParentAgentSchema):
    """conditional node to check if objective must be build or not"""
    objective = state.get("objective")
    if not objective:
        return "build_objective"
    return "END"


@make_node
def build_state(
    self: BaseAgentStructure, state: ParentAgentSchema
) -> ParentAgentSchema:
    """Node to return built state in the above sub agents"""
    try:
        messages = state.get("messages", [])
        aggregation_output = state.get("aggregation_output", [])
        document_output = state.get("document_output", [])

        # If aggregation output does not exist directly return chat state reducer
        if not aggregation_output:
            return {
                "llm_output": "",
            }

        print(messages)
        print(
            f"\n\n CONCLUDED TASKS SO FAR: \n {[x for x in messages if isinstance(x, AIMessage)]} \n\n"
        )
        print(f"\n\n AGGREGATION OUTPUT: \n {aggregation_output} \n\n")
        print(
            f"\n\n LLM OUTPUT CONTENT FOR CURRENT ITERATION: \n {aggregation_output[-1].content} \n\n"
        )
        print(f"\n\n DOCUMENT OUTPUT: \n {document_output} \n\n")
        return {
            "llm_output": aggregation_output[-1].content,
        }
    except Exception as e:
        logger.error(f"Error at converge.build_state: {e}")
        raise e
