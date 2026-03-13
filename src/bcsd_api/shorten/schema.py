import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_RESERVED = re.compile(r"[/\?#&=%\\]")


class CreateRequest(BaseModel):
    title: str
    description: str | None = None
    url: str
    code: str | None = None
    expires_at: datetime | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if v is None:
            return v
        if len(v) < 2 or len(v) > 100:
            raise ValueError("code must be 2-100 characters")
        if _RESERVED.search(v):
            raise ValueError("code contains reserved characters")
        return v


class UpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    expires_at: datetime | None = None


class LinkResponse(BaseModel):
    id: str
    code: str
    title: str
    description: str | None = None
    url: str
    creator_id: str
    created_at: str
    expires_at: str | None = None
    expired_at: str | None = None
    updated_at: str

    @field_validator("expires_at", "expired_at", "description", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if v == "":
            return None
        return v


class DailyClick(BaseModel):
    date: str
    count: int


class LinkDetail(LinkResponse):
    total_clicks: int
    daily_clicks: list[DailyClick]


class CreatorOption(BaseModel):
    id: str
    name: str


class LinkFiltersResponse(BaseModel):
    creators: list[CreatorOption]
    expired: list[str] = ["active", "expired", "all"]
