import strawberry
from strawberry.types import Info

from bcsd_api.graphql.context import GqlContext, require_user
from bcsd_api.graphql.convert import from_model

from . import service
from .schema import CreateFormRequest, QuestionRequest, UpdateFormRequest
from .types import CreateFormInput, FormType, QuestionType, UpdateFormInput


def _to_questions(inputs: list) -> list[QuestionRequest]:
    return [
        QuestionRequest(
            label=q.label, type=q.type,
            options=q.options, required=q.required,
            sort_order=q.sort_order,
        )
        for q in inputs
    ]


def _to_form_type(f) -> FormType:
    data = f.model_dump()
    data["questions"] = [QuestionType(**q) for q in data["questions"]]
    return FormType(**data)


def resolve_form(info: Info[GqlContext, None], id: strawberry.ID) -> FormType:
    require_user(info.context)
    ctx = info.context
    f = service.get_form(ctx.form_repo, ctx.question_repo, id)
    return _to_form_type(f)


def resolve_forms(
    info: Info[GqlContext, None], recruitment_id: str | None = None,
) -> list[FormType]:
    require_user(info.context)
    ctx = info.context
    forms = service.list_forms(ctx.form_repo, ctx.question_repo, recruitment_id)
    return [_to_form_type(f) for f in forms]


def resolve_create_form(
    info: Info[GqlContext, None], input: CreateFormInput,
) -> FormType:
    user = require_user(info.context)
    ctx = info.context
    req = CreateFormRequest(
        title=input.title, description=input.description,
        recruitment_id=input.recruitment_id, type=input.type,
        questions=_to_questions(input.questions),
    )
    f = service.create_form(ctx.form_repo, ctx.question_repo, req, user["sub"])
    return _to_form_type(f)


def resolve_update_form(
    info: Info[GqlContext, None], id: strawberry.ID, input: UpdateFormInput,
) -> FormType:
    require_user(info.context)
    ctx = info.context
    questions = None
    if input.questions is not None:
        questions = _to_questions(input.questions)
    req = UpdateFormRequest(
        title=input.title, description=input.description,
        is_active=input.is_active, questions=questions,
    )
    f = service.update_form(ctx.form_repo, ctx.question_repo, id, req)
    return _to_form_type(f)
