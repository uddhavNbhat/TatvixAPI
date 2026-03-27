from typing import Literal
from langchain.messages import HumanMessage, SystemMessage
from app.internal.agent.utils.custom.prompts import prompt_templates
from app.internal.agent.utils.states.executor import (
    ExecutorAgentSchema,
    ShouldPlanSchema,
    PlannerOutputSchema,
)
from app.internal.agent.utils.custom.wrapper import make_async_node
from app.internal.agent.utils.custom.agent_class import ExecutorAgentStructure


@make_async_node
async def should_plan(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> Literal["irrelvant_query", "planner_node"]:
    """Node to decide if planning is really needed for the task"""
    try:
        user_query = state.get("user_query", "")
        base_messages = state.get("messages", [])

        user_query_reference = [x for x in base_messages if isinstance(x, HumanMessage)]

        user_queries = {
            index: m.content for index, m in enumerate(user_query_reference)
        }

        lines = [
            f"Q{idx + 1}: {query}" for idx, query in enumerate(user_queries.values())
        ]
        context_block = "\n".join(lines)

        should_plan_template = prompt_templates.get_should_plan_template(
            context_block=context_block
        )
        messages = [
            should_plan_template,
            SystemMessage(
                content=f"Previous User queries to check continuity: {str(user_queries)}"
            ),
            HumanMessage(content=f"My current question: {user_query}"),
        ]
        for _ in range(0, self.retries):
            response = await self.should_plan_llm.ainvoke(messages)
            if isinstance(response, ShouldPlanSchema):
                if response.plan:
                    return "planner_node"
                else:
                    return "irrelvant_query"
        else:
            raise Exception("Model generation failed! Please retry!")
    except Exception as e:
        raise e


@make_async_node
async def planner_node(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> ExecutorAgentSchema:
    """planner node to build a task list"""
    try:
        user_query = state.get("user_query", "")
        summary = state.get("global_summary", "")
        base_messages = state.get("messages", [])

        user_query_reference = [x for x in base_messages if isinstance(x, HumanMessage)]

        user_queries = {
            index: m.content for index, m in enumerate(user_query_reference)
        }

        lines = [
            f"Q{idx + 1}: {query}" for idx, query in enumerate(user_queries.values())
        ]
        context_block = "\n".join(lines)

        planner_prompt = prompt_templates.get_planner_template(summary=summary)

        messages = [
            planner_prompt,
            HumanMessage(
                content=f"""
                    Conversation Context So Far:
                    {context_block}

                    Current User Query:
                    {user_query}
                """
            ),
        ]

        for _ in range(0, self.retries):
            response = await self.planner_llm.ainvoke(messages)
            if isinstance(response, PlannerOutputSchema):
                return {
                    "tasks": response.tasks,
                    "document_output": [],
                    "executor_output": [],
                }
        else:
            raise Exception("Model generation failed! Please retry!")
    except Exception as e:
        raise e
