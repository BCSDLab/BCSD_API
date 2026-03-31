from pydantic import BaseModel


class AnswerRequest(BaseModel):
    question_id: str
    value: str


class SubmitRequest(BaseModel):
    form_id: str
    answers: list[AnswerRequest]
    track: str


class AnswerResponse(BaseModel):
    question_id: str
    value: str


class PaymentInfoResponse(BaseModel):
    bank: str
    account: str
    amount: int
    holder: str


class MyApplicationResponse(BaseModel):
    id: str
    status: str
    form_template_id: str
    track: str
    submitted_at: str
    answers: list[AnswerResponse]
    payment_info: PaymentInfoResponse | None = None


class ApplicationListResponse(BaseModel):
    id: str
    applicant_name: str
    applicant_email: str
    track: str
    status: str
    submitted_at: str
