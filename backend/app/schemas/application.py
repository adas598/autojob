import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.base import ApplicationStatus


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    status: ApplicationStatus
    tailored_content: dict | None
    applied_at: datetime | None
    updated_at: datetime
    job_title: str | None = None
    job_company: str | None = None

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
