from pydantic import BaseModel, field_validator


class MemberResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str
    track: str
    team: str
    payment_status: str


class MemberDetail(MemberResponse):
    department: str
    student_id: str = ""
    school_email: str
    phone: str
    join_date: str
    last_updated: str

    @field_validator("student_id", mode="before")
    @classmethod
    def coerce_student_id(cls, v):
        return str(v)


class FiltersResponse(BaseModel):
    tracks: list[str]
    statuses: list[str]
    payment_statuses: list[str]
