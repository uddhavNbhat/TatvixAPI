from fastapi import APIRouter, Depends, Request, HTTPException
from app.utils.security import security
from typing import Annotated
from app.models.models import User, Chat
from app.internal.agent.graph import LegalAgent
from app.utils.db.sql import SQLSessionDep
from sqlmodel import select
from app.utils.logger import logger
from app.utils.dependency import get_legal_agent

router = APIRouter(prefix="/api")


@router.delete("/folder/{folder_id}/chat/{chat_id}", status_code=200)
def delete_chat(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
    legal_agent: Annotated[LegalAgent, Depends(get_legal_agent)],
    folder_id: str,
    chat_id: str,
):
    """
    Method to delete specified chat from user chat history and lang-graph mongodb checkpointer.
    args -> chat_id:str -> query params
    """

    current_chat = session.exec(
        select(Chat)
        .where(Chat.owner_id == current_user.id)
        .where(Chat.folder_id == folder_id)
        .where(Chat.id == chat_id)
    ).first()
    if not current_chat:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "chat could not be found"},
        )
    try:
        response = legal_agent.clear_chat(
            session_id=chat_id
        )  # Clear chat from mongoDB checkpointer
        logger.error(response)  # LOG
        try:
            session.delete(current_chat)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(e)  # LOG
            raise HTTPException(
                500, {"code": "DB_ERROR", "message": "Failed to delete messages"}
            )

        return {
            "code": "CHAT_DELETE_SUCCESS",
            "message": "Chat has been successfully been deleted",
        }

    except Exception as e:
        logger.error(f"Error at delete chat: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Could not delete record",
            },
        )
