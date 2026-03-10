from pydantic import BaseModel


class MemberResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str
    track: str
    team: str
    payment_status: str


class MemberDetail(MemberResponse):
    school_email: str
    phone: str
    join_date: str
    last_updated: str
