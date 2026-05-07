from fastapi import Request, APIRouter, Depends, HTTPException
from sqlmodel import select
from typing import Annotated
from app.utils.security import security
from app.models.models import User, Folder
from app.utils.logger import logger
from app.utils.db.sql import SQLSessionDep

router = APIRouter(prefix="/api")


@router.get("/folder", status_code=200)
async def read_folder(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
    limit: int = 10,
    page: int = 1,
):
    try:
        if limit > 12:
            raise ValueError("Limit cannot be more than 12")
        # Calculate offset.
        offset = limit * (page - 1)
        # Get all present folders in descending order.
        folders = session.exec(
            select(Folder)
            .where(Folder.owner_id == current_user.id)
            .order_by(Folder.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        response = [
            {
                "id": f.id,
                "name": f.name,
            }
            for f in folders
        ]

        logger.info(f"Folder data: {response}")

        return {
            "code": "SUCCESS",
            "message": "folders have been retrieved successfully",
            "data": response,
        }

    except Exception as e:
        logger.error(f"Error at folders.read_folder: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "There was a problem processing the request",
            },
        )
