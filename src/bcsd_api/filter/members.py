from .base import BaseFilter


class MemberFilter(BaseFilter):
    status: str | None = None
    track: str | None = None
    team: str | None = None
    name: str | None = None
    email: str | None = None
    department: str | None = None
    student_id: str | None = None
    phone: str | None = None

    search_fields: list[str] = [
        "name", "email", "department", "student_id", "phone",
    ]
