from langchain.messages import HumanMessage
from app.internal.agent.utils.states.objective import (
    ObjectiveSchema,
    ObjectiveAgentSchema,
)
from app.internal.agent.utils.custom.prompts import prompt_templates
from app.internal.agent.utils.custom.wrapper import make_async_node
from app.internal.agent.utils.custom.agent_class import ObjectiveAgentStructure


@make_async_node
async def build_objective(self: ObjectiveAgentStructure, state: ObjectiveAgentSchema):
    """Builds user objective from user query"""
    try:
        user_query = state.get("user_query", "")
        prompt_template = prompt_templates.get_objective_template()
        message = [
            prompt_template,
            HumanMessage(content=f"The user query is: {user_query}"),
        ]

        # Retry for llm level retry for schema enforcement.
        for _ in range(0, self.retries):
            response = await self.objective_llm.ainvoke(message)
            if isinstance(response, ObjectiveSchema) and response.objective:
                return {"objective": response.objective}
        else:
            raise Exception("Model generation failed! Please retry!")

    except Exception as e:
        raise e
