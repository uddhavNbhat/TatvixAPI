from fastapi import Request
from app.internal.agent.graph import LegalAgent

async def get_legal_agent(
    request: Request,
    model_family: str | None = "router",
    model_name: str | None = "openai/gpt-oss-20b:free",
):
    """Dependency to inject agent instance with correctly initialized global checkpointer."""
    agent = await LegalAgent.init_legal_agent(
        model_family=model_family,
        model_name=model_name,
        checkpointer=request.app.state.checkpointer,
    )
    return agent
