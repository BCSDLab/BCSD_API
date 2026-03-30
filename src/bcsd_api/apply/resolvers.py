import strawberry
from strawberry.types import Info

from bcsd_api.graphql.context import GqlContext, require_user
from bcsd_api.graphql.convert import from_model

from . import service
from .schema import AnswerRequest
from .types import AnswerType, ApplicationType, SubmitInput


def _to_app_type(app) -> ApplicationType:
    data = app.model_dump()
    data["answers"] = [AnswerType(**a) for a in data["answers"]]
    return ApplicationType(**data)


def resolve_submit(info: Info[GqlContext, None], input: SubmitInput) -> ApplicationType:
    user = require_user(info.context)
    ctx = info.context
    answers = [AnswerRequest(question_id=a.question_id, value=a.value) for a in input.answers]
    app = service.submit(
        ctx.app_repo, ctx.ans_repo,
        ctx.form_repo, ctx.question_repo,
        input.form_id, answers, user["sub"],
    )
    return _to_app_type(app)


def resolve_applications(
    info: Info[GqlContext, None], form_id: str,
) -> list[ApplicationType]:
    require_user(info.context)
    ctx = info.context
    apps = service.list_applications(ctx.app_repo, ctx.ans_repo, form_id)
    return [_to_app_type(a) for a in apps]


def resolve_application(
    info: Info[GqlContext, None], id: strawberry.ID,
) -> ApplicationType:
    require_user(info.context)
    ctx = info.context
    app = service.get_application(ctx.app_repo, ctx.ans_repo, id)
    return _to_app_type(app)


def resolve_my_applications(info: Info[GqlContext, None]) -> list[ApplicationType]:
    user = require_user(info.context)
    ctx = info.context
    apps = service.my_applications(ctx.app_repo, ctx.ans_repo, user["sub"])
    return [_to_app_type(a) for a in apps]


def resolve_confirm_payment(
    info: Info[GqlContext, None], id: strawberry.ID,
) -> ApplicationType:
    user = require_user(info.context)
    app = service.confirm_payment(info.context.app_repo, id, user["sub"])
    return _to_app_type(app)


def resolve_approve(
    info: Info[GqlContext, None], ids: list[strawberry.ID],
) -> list[ApplicationType]:
    user = require_user(info.context)
    ctx = info.context
    apps = service.approve(
        ctx.app_repo, ctx.member_repo, ctx.form_repo,
        ids, user["sub"],
    )
    return [_to_app_type(a) for a in apps]


def resolve_cancel(info: Info[GqlContext, None], id: strawberry.ID) -> bool:
    user = require_user(info.context)
    service.cancel(info.context.app_repo, id, user["sub"])
    return True
