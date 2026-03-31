import json

import strawberry
from strawberry.types import Info

from bcsd_api.global_.authz.check import require_admin
from bcsd_api.graphql.context import GqlContext, require_user

from . import service
from .model import CreateFormRequest, QuestionRequest, UpdateFormRequest
from .types import (
    CreateFormInput,
    FormTemplateType,
    QuestionInput,
    QuestionType,
    UpdateFormInput,
)


def _parse_options(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw.split(",") if raw else None


def _to_question(q) -> QuestionType:
    return QuestionType(
        id=q.id, type=q.type, label=q.label,
        required=q.required == "true",
        options=_parse_options(q.options),
        order=q.sort_order,
    )


def _to_form_template(f) -> FormTemplateType:
    questions = [_to_question(q) for q in f.questions]
    return FormTemplateType(
        id=f.id, type=f.type,
        questions=questions,
        updated_at=f.updated_at or f.created_at or "",
    )


def _to_question_req(inputs: list[QuestionInput]) -> list[QuestionRequest]:
    return [
        QuestionRequest(
            label=q.label, type=q.type,
            options=json.dumps(q.options) if q.options else None,
            required="true" if q.required else "false",
            sort_order=q.order,
        )
        for q in inputs
    ]


def resolve_form_template(
    info: Info[GqlContext, None], type: str,
) -> FormTemplateType | None:
    require_user(info.context)
    ctx = info.context
    forms = service.list_forms(ctx.form_repo, ctx.question_repo)
    for f in forms:
        if f.type == type and f.is_active == "true":
            return _to_form_template(f)
    return None


def resolve_form(info: Info[GqlContext, None], id: strawberry.ID) -> FormTemplateType:
    require_user(info.context)
    ctx = info.context
    f = service.get_form(ctx.form_repo, ctx.question_repo, id)
    return _to_form_template(f)


def resolve_forms(
    info: Info[GqlContext, None], recruitment_id: str | None = None,
) -> list[FormTemplateType]:
    require_user(info.context)
    ctx = info.context
    forms = service.list_forms(ctx.form_repo, ctx.question_repo, recruitment_id)
    return [_to_form_template(f) for f in forms]


def resolve_create_form(
    info: Info[GqlContext, None], input: CreateFormInput,
) -> FormTemplateType:
    user = require_user(info.context)
    require_admin(info.context.authz, user["sub"])
    ctx = info.context
    req = CreateFormRequest(
        title=input.title, description=input.description,
        recruitment_id=input.recruitment_id, type=input.type,
        questions=_to_question_req(input.questions),
    )
    f = service.create_form(ctx.form_repo, ctx.question_repo, req, user["sub"])
    return _to_form_template(f)


def resolve_update_form(
    info: Info[GqlContext, None], id: strawberry.ID, input: UpdateFormInput,
) -> FormTemplateType:
    user = require_user(info.context)
    require_admin(info.context.authz, user["sub"])
    ctx = info.context
    questions = None
    if input.questions is not None:
        questions = _to_question_req(input.questions)
    req = UpdateFormRequest(
        title=input.title, description=input.description,
        is_active=input.is_active, questions=questions,
    )
    f = service.update_form(ctx.form_repo, ctx.question_repo, id, req)
    return _to_form_template(f)
