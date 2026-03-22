from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain.messages import AIMessage
from typing import Annotated, List, Literal, Optional
from operator import add
from app.internal.agent.utils.custom.reducer import append_or_clear

# Schemas for model output and agent states


class TaskSchema(BaseModel):
    task_id: str
    objective: str
    tool_call: Literal["document_search", "search_engine"]
    enhanced_query: str
    completion_criteria: str
    task_conclusion: str


class ShouldPlanSchema(BaseModel):
    plan: bool


class PlannerOutputSchema(BaseModel):
    tasks: List[TaskSchema]


class ToolOutput(BaseModel):
    tool_name: str
    data: str | List[str]


class ToolOutputSchema(BaseModel):
    enhanced_user_query: str
    tool_output: ToolOutput


class DocumentOutputSchema(BaseModel):
    file_id: str
    page_no: str


class TaskCompleteSchema(BaseModel):
    task_id: str
    task_objective: str
    task_conclusion: str


class TaskListSchema(BaseModel):
    completed_tasks: List[TaskCompleteSchema]


class ExecutorOutputSchema(BaseModel):

    reasoning: str = Field(
        description="Reasoning of the model to decide and point out all the goals the current context can meet and should meet."
    )

    content: str = Field(
        description="Main content that is explained from from the context provided."
    )

    reference_links: Optional[List[str]] = Field(
        default=None,
        description="External URLs or citation links pointing to the referenced authorities.",
    )


# Agent State Schemas


class ExecutorAgentSchema(MessagesState):
    user_query: str
    tasks: List[TaskSchema]  # Fixed tasks per workflow invoke, not accumilated.
    completed_tasks: TaskListSchema  # Keeps track of complete tasks at every step (Gets input incomplete tasks at every step).
    tool_outputs: List[ToolOutputSchema]  # Tool output
    context: str  # Current context being passed
    index: int  # Index of execution of context
    document_output: Annotated[
        List[DocumentOutputSchema], append_or_clear
    ]  # To store document meta data
    local_summary: Annotated[
        List[str], add
    ]  # Incrementally keeps track of all the goals met per iteration.
    global_summary: (
        str  # Incrementally tracks all the conversation goals met so far.agg
    )
    executor_output: List[
        ExecutorOutputSchema
    ]  # Incrementally tracks all the executor outputs
    aggregation_output: Annotated[List[AIMessage], add_messages]


class ExecutorAgentOutputSchema(MessagesState):
    tool_outputs: List[ToolOutputSchema]  # Tool output
    document_output: Annotated[
        List[DocumentOutputSchema], append_or_clear
    ]  # To store document meta data
    global_summary: str  # Incrementally tracks all the conversation goals met so far.
    executor_output: List[
        ExecutorOutputSchema
    ]  # Incrementally tracks all the executor outputs.
    aggregation_output: Annotated[List[AIMessage], add_messages]
