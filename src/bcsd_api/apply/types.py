import strawberry

from bcsd_api.graphql.convert import SortFieldInput


@strawberry.type
class ApplicationAnswer:
    question_id: str
    value: str


@strawberry.type
class PaymentInfo:
    bank: str
    account: str
    amount: int
    holder: str


@strawberry.type
class MyApplication:
    id: str
    status: str
    form_template_id: str
    track: str
    submitted_at: str
    answers: list[ApplicationAnswer]
    payment_info: PaymentInfo | None


@strawberry.type
class ApplicationListItem:
    id: str
    applicant_name: str
    applicant_email: str
    track: str
    status: str
    submitted_at: str


@strawberry.type
class PagedApplications:
    items: list[ApplicationListItem]
    total: int
    page: int
    size: int


@strawberry.type
class BatchResult:
    count: int
    ids: list[str]


@strawberry.input
class AnswerInput:
    question_id: str
    value: str


@strawberry.input
class SubmitInput:
    form_template_id: str
    answers: list[AnswerInput]
    track: str


@strawberry.input
class ApplicationFilterInput:
    page: int = 1
    size: int = 20
    sorts: list[SortFieldInput] | None = None
    status: str | None = None
    track: str | None = None
