from pydantic import field_validator

from .base import BaseFilter


class LinkFilter(BaseFilter):
    creator_id: str | None = None
    expired: str | None = None

    @field_validator("expired", mode="before")
    @classmethod
    def all_to_none(cls, v):
        if v == "all":
            return None
        return v
