from fastapi import Request, APIRouter, Depends, HTTPException
from typing import Annotated
from app.utils.security import security
from app.models.models import User, Folder
from app.utils.logger import logger
from app.validators.folders import FolderData
from app.utils.db.sql import SQLSessionDep

router = APIRouter(prefix="/api")


@router.post("/dashboard/folder", status_code=200)
async def create_folder(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
    folder_data: FolderData,
):
    try:
        folder = Folder(name=folder_data.name, owner_id=current_user.id)
        try:
            session.add(folder)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.info(f"Db error at folders.create_folder: {e}")
            raise HTTPException(
                status_code=500,
                detail={"code": "DB_ERROR", "message": "Failed to create folder"},
            )
        return {"code": "SUCCESS", "message": "created folder successfully!"}
    except Exception as e:
        logger.error(f"Error at folders.create_folder: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "There was a problem processing the request",
            },
        )
