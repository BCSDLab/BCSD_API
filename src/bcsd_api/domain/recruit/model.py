from pydantic import BaseModel


class CreatePeriodRequest(BaseModel):
    title: str
    type: str
    start_date: str
    end_date: str


class UpdatePeriodRequest(BaseModel):
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_active: str | None = None


class PeriodResponse(BaseModel):
    id: str
    title: str
    type: str
    start_date: str
    end_date: str
    is_active: str
    created_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
