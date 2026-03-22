from pydantic import BaseModel
from langgraph.graph import MessagesState
from langchain.messages import AIMessage
from langgraph.graph.message import add_messages
from typing import Annotated, List
from operator import add
from app.internal.agent.utils.custom.reducer import append_or_clear

# Schemas for model output and agent states


class DocumentOutputSchema(BaseModel):
    file_id: str
    page_no: str


# Agent State Schemas


class ParentAgentSchema(MessagesState):
    user_query: str
    objective: str
    global_summary: str  # Incrementally tracks all the conversation goals met so far
    document_output: Annotated[
        List[DocumentOutputSchema], append_or_clear
    ]  # To store document meta data
    aggregation_output: Annotated[List[AIMessage], add_messages]
    llm_output: str
