from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from app.internal.agent.utils.custom.prompts import prompt_templates
from app.internal.agent.utils.states.executor import (
    ExecutorAgentSchema,
    ExecutorAgentOutputSchema,
    DocumentOutputSchema,
)
from app.internal.agent.utils.custom.wrapper import make_async_node
from app.internal.agent.utils.custom.agent_class import ExecutorAgentStructure
from app.utils.logger import logger


@make_async_node
async def aggregate(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> ExecutorAgentOutputSchema:
    """Node to aggregate final output"""
    base_messages = state.get("messages", [])
    user_query = state.get("user_query", "")
    document_data = state.get("document_output", [])
    executor_data_list = state.get("executor_output", [])
    global_summary = state.get(
        "global_summary", ""
    )  # Extract global summary to see the gist of conversations so far.

    if not executor_data_list:  # If no output was found simply return
        return {
            "aggregation_output": [
                AIMessage(
                    "No Goals were met, the question asked does not exist in the system as of now!"
                )
            ]
        }

    # Extract all the accumilated content in the research iterations
    pre_trim_contents = [
        AIMessage(content=data.content.strip())
        for data in executor_data_list
        if data.content
    ]

    # Trim context if too long (6000 tokens limit)
    all_contents = trim_messages(
        pre_trim_contents,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=6000,
        start_on="ai",
        end_on="ai",
    )

    # All extracted links in research iteration
    all_links: set[str] = set()
    for data in executor_data_list:
        if data.reference_links:
            all_links.update(data.reference_links)

    links_text = "\n".join(sorted(all_links))

    print(f"\n\n REFERENCE LINKS: \n {links_text} \n\n")

    # All document ids and pages retrieved
    final_docs = [
        DocumentOutputSchema(file_id=file_id, page_no=page_no)
        for file_id, page_no in {
            (data.file_id, data.page_no) for data in document_data if data.file_id
        }
    ]

    completed_tasks_state = state.get("completed_tasks")
    # Only to see if ANY task was completed, if it wasn't across the entire context, simply return a error message.
    if completed_tasks_state:
        completed_tasks = completed_tasks_state.completed_tasks
    else:
        completed_tasks = []

    if not completed_tasks:
        return {
            "aggregation_output": [
                AIMessage(
                    "No Goals were met, the question asked does not exist in the system as of now!"
                )
            ]
        }

    task_track = ";\n".join(
        [
            f"[Task {x.task_id}] {x.task_objective} : {x.task_conclusion}"
            for x in completed_tasks
        ]
    )

    try:
        new_messages = []
        new_messages.append(HumanMessage(content=user_query))
        new_messages.append(AIMessage(content=f"TASKS COMPLETED SO FAR : {task_track}"))

        conversation_track = {}

        for m in base_messages:
            if isinstance(m, HumanMessage):
                conversation_track["user_query"] = m.content
            elif isinstance(m, AIMessage):
                conversation_track["tasks_completed"] = m.content

        aggregation_template = prompt_templates.get_aggregator_template()
        messages = [
            SystemMessage(
                content=f"GLOBAL CONVERSATION SUMMARY: {global_summary}\n USER QUERIES AND GOALS MET SO FAR:\n {str(conversation_track)}"
            ),
            SystemMessage(content="EXTRACTED LEGAL INSIGHTS BELOW:"),
            *all_contents,
            SystemMessage(content=f"REFERENCE LINKS BELOW: {links_text}"),
            SystemMessage(content="TASK PROGRESS CONTEXT BELOW:"),
            *new_messages,
            aggregation_template,
        ]
        messages = [m for m in messages if m is not None]
        response = await self.aggregator_llm.ainvoke(input=messages)
        logger.info(f"\n AGGREGATOR RESPONSE: {response} \n")
        return {
            "aggregation_output": [response],
            "messages": new_messages,
            "document_output": ["clear", *final_docs],
        }

    except Exception as e:
        raise e


@make_async_node
async def irrelvant_query(
    self: ExecutorAgentStructure, state: ExecutorAgentSchema
) -> ExecutorAgentOutputSchema:
    """Node to handle irrelevant queries"""
    user_query = state.get("user_query", "")
    base_messages = state.get("messages", [])
    try:
        # Add current query
        base_messages.append(HumanMessage(content=user_query))
        irrelevant_query_template = prompt_templates.get_irrelevant_query_template()
        model_input = [
            irrelevant_query_template,
            *base_messages,
        ]

        response = await self.aggregator_llm.ainvoke(model_input)

        # Store response in new list
        updated_messages = base_messages + [response]

        return {"messages": updated_messages}

    except Exception as e:
        raise e
