from fastapi import APIRouter, Depends, Request, HTTPException, Body
from app.utils.security import security
from typing import Annotated
from app.models.models import User, Chat, Message, MessageFiles
from app.internal.agent.graph import LegalAgent
from app.utils.db.sql import SQLSessionDep
from sqlmodel import select
from app.validators.chat import ChatPayload
from app.utils.logger import logger
from app.utils.dependency import get_legal_agent

router = APIRouter(prefix="/api")


@router.post("/chat", status_code=201)
async def create_chat(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
):
    """Method to create chat if chat does not exist"""
    try:
        chat_id = security.create_chat_hash()
        chat = Chat(id=chat_id, owner_id=current_user.id)
        try:
            session.add(chat)
            session.commit()
        except Exception as e:
            print(e)  # LOG
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail={"code": "DB_ERROR", "message": "Failed to start chat"},
            )

    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail={
                "Code": "INTERNAL_SERVER_ERROR",
                "message": "Something went wrong!",
            },
        )

    return {
        "code": "CHAT_CREATED",
        "message": "chat created successfully",
        "chat_id": chat_id,
    }


@router.post("/chat/{chat_id}", status_code=201)
async def talk_chat(
    session: SQLSessionDep,
    current_user: Annotated[User, Depends(security.get_current_user)],
    legal_agent: Annotated[LegalAgent, Depends(get_legal_agent)],
    chat_id: str,  # Required
    chat: ChatPayload = Body(...),
    model_family: str | None = None,
    model_name: str | None = None,
    request: Request = None,
):
    """
    End point to talk to the legal agent.
    /chat/chat_id=<chat_id>?model_family=&model_name=,
    body: {
        "user_query":"<query>"
    }
    returns agent response as content.
    """
    try:
        if chat_id is None:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "UNAUTHORIZED",
                    "message": "this chat cannot be queried",
                },
            )
        # Retrieve chat id to check if it exists or not.
        current_chat = session.exec(select(Chat).where(Chat.id == chat_id)).first()

        if not current_chat:
            raise HTTPException(
                status_code=404,
                detail={"code": "NOT_FOUND", "message": "chat could not be found"},
            )

        # Check user authenticity.
        if current_user.id != current_chat.owner_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "UNAUTHORIZED",
                    "message": "chat does not belong to the right user",
                },
            )

        user_query = chat.user_query
        if not user_query:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "user query is not passed",
                },
            )

        response = await legal_agent.invoke(query=user_query, session_id=chat_id)

        content = response.get("content", "")
        document_data = response.get("document_data", [])
        logger.info(f"\nDocument data : {document_data}\n")
        objective = response.get("objective", "")
        if objective:
            try:
                update = session.exec(select(Chat).where(Chat.id == chat_id)).first()
                update.header = objective
                session.add(update)
                session.commit()

            except Exception as e:
                session.rollback()
                print(e)  # LOG
                raise HTTPException(
                    status_code=500,
                    detail={"code": "DB_ERROR", "message": "Failed to save messages"},
                )

        if not content:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "No messages in model response, try again",
                },
            )

        logger.info(content)

        if content:
            human_message = Message(chat_id=chat_id, role="human", content=user_query)
            ai_message = Message(chat_id=chat_id, role="ai", content=content)
            try:
                session.add(human_message)
                session.add(ai_message)
                for doc in document_data:
                    upload_document_data = MessageFiles(
                        file_id=doc.file_id, message_id=ai_message.id
                    )
                    session.add(upload_document_data)
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)  # LOG
                raise HTTPException(
                    status_code=500,
                    detail={"code": "DB_ERROR", "message": "Failed to save messages"},
                )

    except Exception as e:
        logger.error(f"Error: {e}")  # LOG
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "There was a problem processing the model",
            },
        )

    return {
        "code": "MODEL_RESPONSE_SUCCESS",
        "message": "Model has successfully returned a response",
        "content": content,
        "chat_id": chat_id,
        "document_ids": document_data,
    }
