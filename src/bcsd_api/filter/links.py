from pydantic import field_validator

from .base import BaseFilter


class LinkFilter(BaseFilter):
    creator_id: list[str] | str | None = None
    expired: str | None = None
    title: str | None = None
    code: str | None = None

    search_fields: list[str] = ["title", "code"]

    @field_validator("expired", mode="before")
    @classmethod
    def all_to_none(cls, v):
        if v == "all":
            return None
        return v
