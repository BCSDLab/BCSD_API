from .base import BaseFilter


class MemberFilter(BaseFilter):
    status: str | None = None
    track: str | None = None
    team: str | None = None
    payment_status: str | None = None
    name: str | None = None

    search_fields: list[str] = ["name"]
