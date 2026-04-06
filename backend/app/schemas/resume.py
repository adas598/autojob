import uuid
from datetime import datetime

from pydantic import BaseModel


class ResumeResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    raw_text: str
    parsed_skills: list
    parsed_experience: list
    parsed_education: list
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    items: list[ResumeResponse]


class ResumeUploadResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    parsed_skills: list
    parsed_experience: list
    parsed_education: list
    is_active: bool
