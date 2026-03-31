import strawberry
from strawberry.types import Info

from bcsd_api.global_.authz.check import require_admin
from bcsd_api.graphql.context import GqlContext, require_user

from . import service
from .model import CreatePeriodRequest, UpdatePeriodRequest
from .types import CreatePeriodInput, RecruitmentPeriodType, UpdatePeriodInput


def _to_period(p) -> RecruitmentPeriodType:
    return RecruitmentPeriodType(
        id=p.id, type=p.type,
        start_date=p.start_date, end_date=p.end_date,
        is_active=p.is_active == "true",
    )


def resolve_periods(info: Info[GqlContext, None]) -> list[RecruitmentPeriodType]:
    require_user(info.context)
    periods = service.list_periods(info.context.recruit_repo)
    return [_to_period(p) for p in periods]


def resolve_period(info: Info[GqlContext, None], id: strawberry.ID) -> RecruitmentPeriodType:
    require_user(info.context)
    p = service.get_period(info.context.recruit_repo, id)
    return _to_period(p)


def resolve_recruitment_period(
    info: Info[GqlContext, None], type: str,
) -> RecruitmentPeriodType | None:
    require_user(info.context)
    p = service.active_period(info.context.recruit_repo, type)
    if not p:
        return None
    return _to_period(p)


def resolve_create_period(
    info: Info[GqlContext, None], input: CreatePeriodInput,
) -> RecruitmentPeriodType:
    user = require_user(info.context)
    require_admin(info.context.authz, user["sub"])
    req = CreatePeriodRequest(
        title=input.title, type=input.type,
        start_date=input.start_date, end_date=input.end_date,
    )
    p = service.create_period(info.context.recruit_repo, req, user["sub"])
    return _to_period(p)


def resolve_update_period(
    info: Info[GqlContext, None], id: strawberry.ID, input: UpdatePeriodInput,
) -> RecruitmentPeriodType:
    user = require_user(info.context)
    require_admin(info.context.authz, user["sub"])
    is_active = None
    if input.is_active is not None:
        is_active = "true" if input.is_active else "false"
    req = UpdatePeriodRequest(
        title=input.title, start_date=input.start_date,
        end_date=input.end_date, is_active=is_active,
    )
    p = service.update_period(info.context.recruit_repo, id, req)
    return _to_period(p)
