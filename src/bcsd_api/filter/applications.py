from .base import BaseFilter


class ApplicationFilter(BaseFilter):
    status: str | None = None
    track: str | None = None
