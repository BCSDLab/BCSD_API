from pydantic import BaseModel


class QuestionRequest(BaseModel):
    label: str
    type: str
    options: str | None = None
    required: str = "true"
    sort_order: int = 0


class QuestionResponse(BaseModel):
    id: str
    form_id: str
    label: str
    type: str
    options: str | None = None
    required: str = "true"
    sort_order: int = 0
    created_at: str | None = None


class CreateFormRequest(BaseModel):
    title: str
    description: str | None = None
    recruitment_id: str
    type: str
    questions: list[QuestionRequest] = []


class UpdateFormRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    is_active: str | None = None
    questions: list[QuestionRequest] | None = None


class FormResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    recruitment_id: str
    type: str
    is_active: str
    created_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    questions: list[QuestionResponse] = []
