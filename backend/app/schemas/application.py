from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    cover_letter: str
    application_answers: dict
    generated_at: datetime
    created_at: datetime


class ApplicationUpdate(BaseModel):
    cover_letter: str | None = None
    application_answers: dict | None = None
