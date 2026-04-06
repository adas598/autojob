import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.base import JobType, Portal, Seniority, VisaStatus


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    location: str
    salary_min: int | None
    salary_max: int | None
    job_type: JobType | None
    seniority: Seniority | None
    visa_status: list[VisaStatus]
    description: str
    source_url: str
    portal: Portal
    external_id: str
    scraped_at: datetime
    created_at: datetime
    overall_score: int | None = None
    rubric_breakdown: dict | None = None
    reasoning: str | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: list[JobResponse]


class JobFilterParams(BaseModel):
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: JobType | None = None
    seniority: Seniority | None = None
    visa_status: VisaStatus | None = None
    portal: Portal | None = None
    score_min: int | None = None
    score_max: int | None = None
    show_all: bool = False
    sort_by: str = "overall_score"
    sort_order: str = "desc"
    page: int = 1
    per_page: int = 20
