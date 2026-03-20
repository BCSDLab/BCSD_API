from .base import BaseFilter


class MemberFilter(BaseFilter):
    status: list[str] | str | None = None
    track: list[str] | str | None = None
    team: list[str] | str | None = None
    name: str | None = None
    email: str | None = None
    department: str | None = None
    student_id: str | None = None
    phone: str | None = None

    search_fields: list[str] = [
        "name", "email", "department", "student_id", "phone",
    ]
