from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from typing import List, Annotated
from httpx import AsyncClient
from weaviate import WeaviateAsyncClient
from app.config.settings import settings
from app.utils.security import security
from app.utils.logger import logger
from app.utils.router import is_allowed_mime, read_file_content
from app.models.models import Files, Images, User
from app.utils.db.sql import SQLSessionDep
from app.utils.db.weaviate import get_data, store_data
from app.validators.setup import PopulateWeaviate
import json

router = APIRouter(prefix="/api")

@router.post("/files", status_code=200) # Test end point for dynamic testing, use Postman or thunder client or any API testing tool.
async def populate_file_service(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
    files: List[UploadFile] = File(...)
):
    try:
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No file uploaded!")

        data = []

        for index, f in enumerate(files):
            mime_type = is_allowed_mime(f.content_type)
            # Read file bytes once confirmed file was stored succesfully.
            file_bytes = await f.read()
            # Write additional logic here for OCR, but for now not implemented.
            file_record = Files(
                file_name=f.filename,
                mime_type=mime_type,
                user_id=current_user.id
            )
            session.add(file_record)
            session.flush() #Flush session objects as pre commit (for updating the table with file ids)
            payload = {
                "file" : (f.filename, file_bytes, f.content_type)
            }

            async with AsyncClient() as client:
                # Call the
                response = await client.post(
                    url=f'{settings.FILE_SERVICE_URI}/upload',
                    files=payload
                )
                
                logger.info(f"Response from file service: {json.loads(response.content)}")
            
            if response.status_code != 201:
                session.rollback()
                raise HTTPException(status_code=500, detail="File service upload failed")

            file_service_data = json.loads(response.content)
            
            file_record.file_path = file_service_data["file_id"]

            file_text = read_file_content(file_bytes)
            pages = 1
            for page_no, text in file_text.items():
                session.add(Images(file_id=file_record.id, page_no=page_no, text=text))
                pages += 1

            data.append({
                "file_id" : file_service_data["file_id"],
                "mime_type" : file_service_data["mime_type"],
                "pages": pages
            })
            session.commit()

        return {
                "code" : "UPLOAD_SUCCESS",
                "message" : "uploaded file successfully",
                "data" : data
            }
    # Seperatly raise http exceptions
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f'Error at populate_file_service: {e}')
        raise HTTPException(status_code=500, detail="File service upload failed")

@router.post("/weaviate", status_code=200)
async def populate(
    request: Request,
    current_user: Annotated[User, Depends(security.get_current_user)],
    session: SQLSessionDep,
    data: PopulateWeaviate
):
    try:
        # Get global client object
        client: WeaviateAsyncClient = request.app.state.weaviate_client
        text_data = await get_data(
            session=session,
            file_data=data
        )
        await store_data(text_data, client)
        return {
            "ok": True,
            "message": "Successfully populated Weaviate."
        }
    # Seperatly raise http exceptions
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f'Error at routers.populate: {e}')
        raise HTTPException(status_code=500, detail="Something went wrong!")
