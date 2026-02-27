from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
from weaviate import WeaviateClient
from app.utils.security import security
from app.utils.logger import logger
from app.models.models import User

router = APIRouter(prefix="/api")

@router.delete('/weaviate', status_code=204)
async def drop_weaviate(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)]
):
    try:
        client: WeaviateClient = request.app.state.weaviate_client
        exists = client.collections.exists("Vectorbase")
        if exists:
            client.collections.delete("Vectorbase")
    
    # Seperatly raise http exceptions
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f'Error at routers.drop_weaviate: {e}')
        raise HTTPException(status_code=500, detail="Something went wrong!")
