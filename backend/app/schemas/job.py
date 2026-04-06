from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStatus, MatchScore


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    company: str
    location: str
    salary: str | None
    description: str
    requirements: str
    url: str
    source: str
    date_posted: str | None
    status: JobStatus
    match_score: MatchScore | None
    match_reasoning: str | None
    scraped_at: datetime
    created_at: datetime


class JobStatusUpdate(BaseModel):
    status: JobStatus
