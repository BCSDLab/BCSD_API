import strawberry

from bcsd_api.graphql.convert import SortFieldInput


@strawberry.type
class AnswerType:
    id: str
    question_id: str
    value: str


@strawberry.type
class ApplicationType:
    id: str
    form_id: str
    member_id: str
    status: str
    submitted_at: str | None
    approved_at: str | None
    approved_by: str | None
    updated_at: str | None
    answers: list[AnswerType]


@strawberry.type
class PagedApplications:
    items: list[ApplicationType]
    total: int
    page: int
    size: int


@strawberry.input
class AnswerInput:
    question_id: str
    value: str


@strawberry.input
class SubmitInput:
    form_id: str
    answers: list[AnswerInput]


@strawberry.input
class ApplicationFilterInput:
    page: int = 1
    size: int = 20
    sorts: list[SortFieldInput] | None = None
    status: list[str] | None = None
    form_id: str | None = None
    member_id: str | None = None
