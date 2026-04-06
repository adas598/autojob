from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.applied_history import ApplicationStatus


class AppliedHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    status: ApplicationStatus
    notes: str | None
    changed_at: datetime


class AppliedHistoryCreate(BaseModel):
    job_id: str
    status: ApplicationStatus
    notes: str | None = None


class AppliedHistoryUpdate(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None
