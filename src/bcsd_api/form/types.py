import strawberry


@strawberry.type
class QuestionType:
    id: str
    label: str
    type: str
    options: str | None
    required: str
    sort_order: int


@strawberry.type
class FormType:
    id: str
    title: str
    description: str | None
    recruitment_id: str
    type: str
    is_active: str
    created_by: str | None
    created_at: str | None
    updated_at: str | None
    questions: list[QuestionType]


@strawberry.input
class QuestionInput:
    label: str
    type: str
    options: str | None = None
    required: str = "true"
    sort_order: int = 0


@strawberry.input
class CreateFormInput:
    title: str
    recruitment_id: str
    type: str
    description: str | None = None
    questions: list[QuestionInput] = strawberry.field(default_factory=list)


@strawberry.input
class UpdateFormInput:
    title: str | None = None
    description: str | None = None
    is_active: str | None = None
    questions: list[QuestionInput] | None = None
