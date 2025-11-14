from fastapi import APIRouter,Depends
from app.utils.security import security
from typing import Annotated
from app.db_models.models import User

router = APIRouter(prefix="/api")


@router.post("/chat",status_code=200)
def chat(current_user: Annotated[User,Depends(security.get_current_user)]):
    return {"message":"chatting endpoint"}