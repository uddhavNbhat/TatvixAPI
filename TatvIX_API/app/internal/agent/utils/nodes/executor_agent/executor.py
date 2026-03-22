from typing import Literal
from langchain.messages import HumanMessage
from app.internal.agent.utils.custom.prompts import prompt_templates
from app.internal.agent.utils.states.executor import (
    ExecutorAgentSchema,
    ExecutorOutputSchema,
    TaskListSchema,
)
from app.internal.agent.utils.custom.wrapper import make_async_node, make_node
from app.internal.agent.utils.custom.agent_class import ExecutorAgentStructure


@make_async_node
async def executor(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> ExecutorAgentSchema:
    """Node to execute llm with derived context"""
    user_query = state.get("user_query", "")
    # Get context, complete task list and completed tasks
    context = state.get("context", "")
    tasks = state.get("tasks", [])
    completed_tasks_state = state.get("completed_tasks")
    executor_output = state.get("executor_output", [])

    if completed_tasks_state:
        completed_tasks = completed_tasks_state.completed_tasks
    else:
        completed_tasks = []

    # If context does not exist or tasks don't exist simply return
    if not context or not tasks:
        return {}

    # Extract all the complete task ids
    tasks_ids = [x.task_id for x in completed_tasks]

    # Extract all incomplete tasks from original task list
    incomplete_tasks = [
        (x.task_id, x.objective) for x in tasks if x.task_id not in tasks_ids
    ]

    try:
        # Parse overall task list and incomplete tasks to meet
        executor_template = prompt_templates.get_executor_template(
            tasks="\n".join([f"{task_id}: {obj}" for task_id, obj in incomplete_tasks]),
            completed_tasks="\n".join(
                [f"{t.task_id}: {t.task_conclusion}" for t in completed_tasks]
            ),
        )

        messages = [
            executor_template,
            HumanMessage(content=f"Context to refer to: {context}"),
            HumanMessage(content=f"User Query: {user_query}"),
        ]

        print(f"\n\n PER STEP INPUT: \n {messages} \n\n")

        for _ in range(0, self.retries):
            response = await self.execution_llm.ainvoke(input=messages)
            print(f"\n\n PER STEP OUTPUT: \n {response} \n\n")
            if isinstance(response, ExecutorOutputSchema):
                merged_executor_output = executor_output + [response]
                return {"executor_output": merged_executor_output}
        else:
            raise Exception("Model generation failed! Please retry!")

    except Exception as e:
        raise e


@make_async_node
async def task_tracker(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> ExecutorAgentSchema:
    """Node to track tasks completed from previous execution node"""
    executor_data_list = state.get("executor_output", [])

    if not executor_data_list:  # If no output was found simply return
        return {}

    executor_data = executor_data_list[-1].content  # Get latest executor output
    tasks = state.get("tasks", [])
    completed_tasks_state = state.get("completed_tasks")

    if completed_tasks_state:
        completed_tasks = completed_tasks_state.completed_tasks
    else:
        completed_tasks = []

    # If tasks don't exist simply return
    if not tasks:
        return {}

    # Extract all the complete task ids
    tasks_ids = [x.task_id for x in completed_tasks]

    # Extract all incomplete tasks from original task list
    incomplete_tasks = [
        (x.task_id, x.objective, x.task_conclusion)
        for x in tasks
        if x.task_id not in tasks_ids
    ]

    print(f"\n\n INCOMPLETE TASKS: \n {incomplete_tasks} \n\n")

    try:
        task_template = prompt_templates.get_goals_met_template(
            tasks="\n".join(
                [
                    f"{task_id}: \n objective: {obj}\n conclusion: {conclusion}"
                    for task_id, obj, conclusion in incomplete_tasks
                ]
            ),
            previous_content=executor_data,
        )

        messages = [task_template]

        for _ in range(0, self.retries):
            response = await self.task_list_llm.ainvoke(input=messages)
            if isinstance(response, TaskListSchema):
                new_completed = response.completed_tasks

                existing = {t.task_id: t for t in completed_tasks}

                for t in new_completed:
                    existing[t.task_id] = t  # overwrite same id, keep new

                merged = list(existing.values())

                print(f"\n\n TASK TRACK OUTPUT: \n {merged} \n\n")

                return {"completed_tasks": TaskListSchema(completed_tasks=merged)}
        else:
            raise Exception("Model generation failed! Please retry!")

    except Exception as e:
        raise e


@make_node
def should_continue(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> Literal["aggregate", "structure_tool_context"]:
    """conditional edge node to check if execution must continue"""
    tool_outputs = state.get("tool_outputs", [])
    index = state.get("index", 0)
    tasks = state.get("tasks", [])
    completed_tasks_state = state.get("completed_tasks")

    print(f"\n\n COMPLETED TASKS: \n {completed_tasks_state} \n\n")

    print(f"\n\n INDEX: \n {index} \n\n")

    if completed_tasks_state:
        completed_tasks = completed_tasks_state.completed_tasks
    else:
        completed_tasks = []

    # All tasks have been completed
    if len(completed_tasks) >= len(tasks):
        return "aggregate"

    # Full context has been gone through
    if index >= len(tool_outputs):
        return "aggregate"

    return "structure_tool_context"
