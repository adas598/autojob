from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.source import SourceType


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: SourceType
    name: str
    url: str
    enabled: bool
    created_at: datetime


class SourceCreate(BaseModel):
    type: SourceType
    name: str
    url: str = ""
    enabled: bool = True


class SourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    enabled: bool | None = None
