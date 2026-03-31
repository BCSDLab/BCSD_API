import strawberry


@strawberry.type
class QuestionType:
    id: str
    type: str
    label: str
    required: bool
    options: list[str] | None
    order: int


@strawberry.type
class FormTemplateType:
    id: str
    type: str
    questions: list[QuestionType]
    updated_at: str


@strawberry.input
class QuestionInput:
    label: str
    type: str
    options: list[str] | None = None
    required: bool = True
    order: int = 0


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
