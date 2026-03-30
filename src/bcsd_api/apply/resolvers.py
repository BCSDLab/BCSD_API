import strawberry
from strawberry.types import Info

from bcsd_api.authz.check import require_fee_edit
from bcsd_api.filter.applications import ApplicationFilter
from bcsd_api.filter.base import apply_filter
from bcsd_api.graphql.context import GqlContext, require_user
from bcsd_api.graphql.convert import to_filter

from . import service
from .schema import AnswerRequest
from .types import (
    ApplicationFilterInput,
    ApplicationListItem,
    BatchResult,
    MyApplication,
    ApplicationAnswer,
    PagedApplications,
    PaymentInfo,
    SubmitInput,
)


def _to_my_app(app, payment_info=None) -> MyApplication:
    answers = [ApplicationAnswer(question_id=a.question_id, value=a.value) for a in app.answers]
    pi = None
    if payment_info:
        pi = PaymentInfo(
            bank=payment_info.bank, account=payment_info.account,
            amount=payment_info.amount, holder=payment_info.holder,
        )
    return MyApplication(
        id=app.id, status=app.status,
        form_template_id=app.form_template_id,
        track=app.track, submitted_at=app.submitted_at,
        answers=answers, payment_info=pi,
    )


def resolve_my_application(info: Info[GqlContext, None]) -> MyApplication | None:
    user = require_user(info.context)
    ctx = info.context
    app = service.my_application(ctx.app_repo, ctx.ans_repo, user["sub"])
    if not app:
        return None
    pi = service.get_payment_info(ctx.setting_repo)
    return _to_my_app(app, pi)


def resolve_submit(info: Info[GqlContext, None], input: SubmitInput) -> MyApplication:
    user = require_user(info.context)
    ctx = info.context
    answers = [AnswerRequest(question_id=a.question_id, value=a.value) for a in input.answers]
    app = service.submit(
        ctx.app_repo, ctx.ans_repo,
        ctx.form_repo, ctx.question_repo,
        input.form_template_id, answers, input.track, user["sub"],
    )
    pi = service.get_payment_info(ctx.setting_repo)
    return _to_my_app(app, pi)


def resolve_cancel(info: Info[GqlContext, None], id: strawberry.ID) -> MyApplication:
    user = require_user(info.context)
    ctx = info.context
    app = service.cancel(ctx.app_repo, ctx.ans_repo, id, user["sub"])
    return _to_my_app(app)


def resolve_applications(
    info: Info[GqlContext, None],
    filter: ApplicationFilterInput | None = None,
) -> PagedApplications:
    user = require_user(info.context)
    require_fee_edit(info.context.authz, user["sub"])
    ctx = info.context
    filt = to_filter(filter, ApplicationFilter) if filter else ApplicationFilter.model_validate({})
    items = service.list_applications(ctx.app_repo, ctx.member_repo)
    rows = [i.model_dump() for i in items]
    paged = apply_filter(rows, filt)
    list_items = [ApplicationListItem(**r) for r in paged.items]
    return PagedApplications(
        items=list_items, total=paged.total,
        page=paged.page, size=paged.size,
    )


def resolve_approve(
    info: Info[GqlContext, None], id: strawberry.ID,
) -> MyApplication:
    user = require_user(info.context)
    require_fee_edit(info.context.authz, user["sub"])
    ctx = info.context
    service.approve(
        ctx.app_repo, ctx.member_repo, ctx.form_repo,
        [id], user["sub"], ctx.authz,
    )
    app = service.get_application(ctx.app_repo, ctx.ans_repo, id)
    return _to_my_app(app)


def resolve_batch_approve(
    info: Info[GqlContext, None], ids: list[strawberry.ID],
) -> BatchResult:
    user = require_user(info.context)
    require_fee_edit(info.context.authz, user["sub"])
    ctx = info.context
    approved = service.approve(
        ctx.app_repo, ctx.member_repo, ctx.form_repo,
        ids, user["sub"], ctx.authz,
    )
    return BatchResult(count=len(approved), ids=approved)
