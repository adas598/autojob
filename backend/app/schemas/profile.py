from pydantic import BaseModel, ConfigDict


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    location: str
    visa_type: str
    visa_expiry: str
    work_rights: str
    target_titles: list[str]
    skills: list[str]
    work_history: list[dict]
    education: list[dict]
    salary_min: int | None
    salary_max: int | None
    preferred_locations: list[str]
    exclusion_keywords: list[str]
    exclusion_companies: list[str]
    resume_path: str | None
    writing_sample_path: str | None


class ProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    visa_type: str | None = None
    visa_expiry: str | None = None
    work_rights: str | None = None
    target_titles: list[str] | None = None
    skills: list[str] | None = None
    work_history: list[dict] | None = None
    education: list[dict] | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    preferred_locations: list[str] | None = None
    exclusion_keywords: list[str] | None = None
    exclusion_companies: list[str] | None = None
