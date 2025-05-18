from pydantic import BaseModel
from datetime import datetime
from typing import List

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class NoteCreate(BaseModel):
    title: str
    content: str

class FileInfo(BaseModel):
    id: str
    filename: str
    path: str

class NoteOut(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    user_id: int
    files: List[FileInfo] = []
    model_config = {
        "from_attributes": True
    }

