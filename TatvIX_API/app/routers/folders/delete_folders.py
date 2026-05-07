from fastapi import Request, APIRouter, Depends, HTTPException
from sqlmodel import select
from typing import Annotated
from app.utils.security import security
from app.models.models import User, Folder
from app.utils.logger import logger
from app.utils.db.sql import SQLSessionDep

router = APIRouter(prefix="/api")


@router.delete("/folder/{folder_id}", status_code=200)
async def delete_folder(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
    folder_id: str,
):
    try:
        folder = session.exec(
            select(Folder)
            .where(Folder.owner_id == current_user.id)
            .where(Folder.id == folder_id)
        ).first()

        if not folder:
            raise HTTPException(
                status_code=404,
                detail={"code": "NOT FOUND", "message": "no such folder exists!"},
            )

        try:
            session.delete(folder)
            session.commit()
            logger.info(f"Deleted folder: {folder.name}")
            logger.info(f"Deleted associated chats: {folder.chats}")
        except Exception as e:
            session.rollback()
            logger.info(f"Db error at folders.delete_folder: {e}")
            raise HTTPException(
                status_code=500,
                detail={"code": "DB_ERROR", "message": "Failed to delete folder"},
            )
        return {"code": "SUCCESS", "message": "deleted folder successfully!"}
    except Exception as e:
        logger.error(f"Error at folders.delete_folder: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "There was a problem processing the request",
            },
        )
