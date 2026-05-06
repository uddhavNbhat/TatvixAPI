from pydantic import BaseModel
from typing import List, Optional


class FileData(BaseModel):
    file_id: str
    mime_type: str
    pages: int


class PopulateWeaviate(BaseModel):
    files: List[FileData]


class WeaviateMetaDataSchema(BaseModel):
    text: str
    file_id: str
    page_no: str
