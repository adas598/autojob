from datetime import datetime

from pydantic import BaseModel


class SettingResponse(BaseModel):
    key: str
    value: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: dict


class UsageSummary(BaseModel):
    total_tokens_input: int
    total_tokens_output: int
    total_cost_usd: float
    cap_type: str | None
    cap_value: float | None
    usage_percentage: float | None
    period_start: datetime | None
