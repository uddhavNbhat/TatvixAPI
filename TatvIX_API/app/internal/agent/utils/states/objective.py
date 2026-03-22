from pydantic import BaseModel
from typing import TypedDict

# Schemas for model output and agent states


class ObjectiveSchema(BaseModel):
    objective: str


# Agent State Schemas


class ObjectiveAgentSchema(TypedDict):
    user_query: str


class ObjectiveAgentOutputSchema(TypedDict):
    objective: str
