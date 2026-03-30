import strawberry
from strawberry.types import Info

from bcsd_api.graphql.context import GqlContext, require_user
from bcsd_api.graphql.convert import from_model

from . import service
from .schema import CreatePeriodRequest, UpdatePeriodRequest
from .types import CreatePeriodInput, PeriodType, UpdatePeriodInput


def resolve_periods(info: Info[GqlContext, None]) -> list[PeriodType]:
    require_user(info.context)
    periods = service.list_periods(info.context.recruit_repo)
    return [from_model(p, PeriodType) for p in periods]


def resolve_period(info: Info[GqlContext, None], id: strawberry.ID) -> PeriodType:
    require_user(info.context)
    p = service.get_period(info.context.recruit_repo, id)
    return from_model(p, PeriodType)


def resolve_active_period(
    info: Info[GqlContext, None], type: str,
) -> PeriodType | None:
    require_user(info.context)
    p = service.active_period(info.context.recruit_repo, type)
    if not p:
        return None
    return from_model(p, PeriodType)


def resolve_create_period(
    info: Info[GqlContext, None], input: CreatePeriodInput,
) -> PeriodType:
    user = require_user(info.context)
    req = CreatePeriodRequest(
        title=input.title, type=input.type,
        start_date=input.start_date, end_date=input.end_date,
    )
    p = service.create_period(info.context.recruit_repo, req, user["sub"])
    return from_model(p, PeriodType)


def resolve_update_period(
    info: Info[GqlContext, None], id: strawberry.ID, input: UpdatePeriodInput,
) -> PeriodType:
    require_user(info.context)
    req = UpdatePeriodRequest(
        title=input.title, start_date=input.start_date,
        end_date=input.end_date, is_active=input.is_active,
    )
    p = service.update_period(info.context.recruit_repo, id, req)
    return from_model(p, PeriodType)
