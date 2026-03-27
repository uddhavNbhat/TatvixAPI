from fastapi import Request
from app.internal.agent.graph import LegalAgent


async def get_legal_agent(
    request: Request,
    model_family: str | None = "groq",
    model_name: str | None = "openai/gpt-oss-20b",
):
    """Dependency to inject agent instance with correctly initialized global checkpointer."""

    agent = await LegalAgent.init_agent(
        model_family=model_family,
        model_name=model_name,
        checkpointer=request.app.state.checkpointer,
    )
    return agent
