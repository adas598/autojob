from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
