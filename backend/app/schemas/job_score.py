import uuid
from datetime import datetime

from pydantic import BaseModel


class JobScoreResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID
    overall_score: int
    rubric_breakdown: dict
    reasoning: str
    scored_at: datetime

    model_config = {"from_attributes": True}
