import strawberry
from strawberry.types import Info

from bcsd_api.authz.check import require_fee_edit
from bcsd_api.filter.applications import ApplicationFilter
from bcsd_api.filter.base import apply_filter
from bcsd_api.graphql.context import GqlContext, require_user
from bcsd_api.graphql.convert import to_filter

from . import service
from .schema import AnswerRequest, ApplicationResponse
from .types import (
    AnswerType,
    ApplicationFilterInput,
    ApplicationType,
    PagedApplications,
    SubmitInput,
)


def _to_app_type(app: ApplicationResponse) -> ApplicationType:
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
    info: Info[GqlContext, None],
    filter: ApplicationFilterInput | None = None,
) -> PagedApplications:
    user = require_user(info.context)
    require_fee_edit(info.context.authz, user["sub"])
    ctx = info.context
    filt = to_filter(filter, ApplicationFilter) if filter else ApplicationFilter.model_validate({})
    rows = ctx.app_repo.find_all()
    apps = [service._with_answers(ctx.ans_repo, r) for r in rows]
    paged = apply_filter([a.model_dump() for a in apps], filt)
    items = [_to_app_type(ApplicationResponse(**r)) for r in paged.items]
    return PagedApplications(
        items=items, total=paged.total,
        page=paged.page, size=paged.size,
    )


def resolve_application(
    info: Info[GqlContext, None], id: strawberry.ID,
) -> ApplicationType:
    user = require_user(info.context)
    require_fee_edit(info.context.authz, user["sub"])
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
    require_fee_edit(info.context.authz, user["sub"])
    app = service.confirm_payment(info.context.app_repo, id, user["sub"])
    return _to_app_type(app)


def resolve_approve(
    info: Info[GqlContext, None], ids: list[strawberry.ID],
) -> list[ApplicationType]:
    user = require_user(info.context)
    require_fee_edit(info.context.authz, user["sub"])
    ctx = info.context
    apps = service.approve(
        ctx.app_repo, ctx.member_repo, ctx.form_repo,
        ids, user["sub"], ctx.authz,
    )
    return [_to_app_type(a) for a in apps]


def resolve_cancel(info: Info[GqlContext, None], id: strawberry.ID) -> bool:
    user = require_user(info.context)
    service.cancel(info.context.app_repo, id, user["sub"])
    return True
