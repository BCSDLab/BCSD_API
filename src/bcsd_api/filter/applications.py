from .base import BaseFilter


class ApplicationFilter(BaseFilter):
    status: list[str] | str | None = None
    form_id: str | None = None
    member_id: str | None = None
