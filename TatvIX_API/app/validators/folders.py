from pydantic import BaseModel


class FolderData(BaseModel):
    name: str
