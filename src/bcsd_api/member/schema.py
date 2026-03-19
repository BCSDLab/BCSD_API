from pydantic import BaseModel, field_validator


class MemberResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str
    track: str
    team: str
    department: str = ""
    student_id: str = ""
    phone: str = ""

    @field_validator("student_id", mode="before")
    @classmethod
    def coerce_student_id(cls, v):
        return str(v)


class MemberDetail(MemberResponse):
    school_email: str
    join_date: str
    last_updated: str


class FiltersResponse(BaseModel):
    tracks: list[str]
    statuses: list[str]
