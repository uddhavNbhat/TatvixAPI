from fastapi import APIRouter, Depends, Request, HTTPException
from app.utils.security import security
from typing import Annotated
from app.models.models import User, Chat, Message
from app.utils.db.sql import SQLSessionDep
from sqlmodel import select
from app.utils.logger import logger

router = APIRouter(prefix="/api")


@router.get("/folder/{folder_id}/chat-ids", status_code=200)
def get_chat_ids(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
    folder_id: str,
):
    """
    End-point to get all chat_ids under a folder.
    returns -> a list of chat_ids of the user making the request. (passed to get_current_user dependency with the help of request object)
    """
    try:
        chats = session.exec(
            select(Chat)
            .where(Chat.owner_id == current_user.id)
            .where(Chat.folder_id == folder_id)
            .order_by(Chat.created_at.desc())
        ).all()

        logger.info(f"All present chats: {chats}")

        if not chats:
            chats = []

    except Exception as e:
        logger.error(f"Error at get_chat_ids : {e}")
        raise HTTPException(
            500, {"code": "INTERNAL_SERVER_ERROR", "message": "No chats exist"}
        )

    payload = {
        "code": "CHAT_IDS_RETRIEVED",
        "message": "chat ids have been successfully retrieved",
        "chats": {x.id: x.header for x in chats},
    }

    logger.info(payload)

    return {
        "code": "CHAT_IDS_RETRIEVED",
        "message": "chat ids have been successfully retrieved",
        "chat_ids": [x.id for x in chats],
        "chat_headers": [x.header for x in chats],
    }


@router.get("/folder/{folder_id}/chat/{chat_id}", status_code=200)
def find_chat(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
    folder_id: str,  # Required
    chat_id: str,  # Required
):
    """
    End point to find chat.
    /chat/chat_id=<chat_id> -> Retrieves the chat_id to get.
    """
    try:
        # Get chat entity from the Chat table.
        current_chat = session.exec(
            select(Chat)
            .where(Chat.owner_id == current_user.id)
            .where(Chat.folder_id == folder_id)
            .where(Chat.id == chat_id)
        ).first()

        if not current_chat:
            return HTTPException(
                status_code=403,
                detail={
                    "code": "UNAUTHORIZED",
                    "message": "chat does not belong to the user",
                },
            )

        # Returns a list of instances of messages of human and ai ordered by time created
        messages = session.exec(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at)
        ).all()

        logger.info(
            f'Messages: {[{"id": f.id, "file_id": f.file_id} for m in messages for f in m.files]}'
        )

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Could not load record",
            },
        )

    return {
        "code": "CHAT_RETRIEVED",
        "message": "chat history found successfully",
        "messages": [
            {
                "id": m.id,
                "chat_id": m.chat_id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
                "files": [{"id": f.id, "file_id": f.file_id} for f in m.files],
            }
            for m in messages
        ],
        "chat_id": chat_id,
    }
