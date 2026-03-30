from pydantic import BaseModel


class AnswerRequest(BaseModel):
    question_id: str
    value: str


class SubmitRequest(BaseModel):
    form_id: str
    answers: list[AnswerRequest]


class AnswerResponse(BaseModel):
    id: str
    question_id: str
    value: str


class ApplicationResponse(BaseModel):
    id: str
    form_id: str
    member_id: str
    status: str
    submitted_at: str | None = None
    approved_at: str | None = None
    approved_by: str | None = None
    updated_at: str | None = None
    answers: list[AnswerResponse] = []
