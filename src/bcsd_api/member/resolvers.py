import strawberry
from strawberry.types import Info

from bcsd_api.filter.members import MemberFilter
from bcsd_api.graphql.context import GqlContext, require_user
from bcsd_api.graphql.convert import from_model, from_paged, to_filter

from . import service
from .types import (
    FiltersType,
    MeType,
    MemberDetailType,
    MemberFilterInput,
    MemberType,
    PagedMembers,
)


def resolve_members(
    info: Info[GqlContext, None],
    filter: MemberFilterInput | None = None,
) -> PagedMembers:
    ctx = info.context
    require_user(ctx)
    filt = to_filter(filter, MemberFilter) if filter else MemberFilter.model_validate({})
    paged = service.list_members(ctx.member_repo, filt)
    return from_paged(paged, MemberType, PagedMembers)


def resolve_member(info: Info[GqlContext, None], id: strawberry.ID) -> MemberDetailType:
    require_user(info.context)
    m = service.get_member(info.context.member_repo, id)
    return from_model(m, MemberDetailType)


def resolve_filters(info: Info[GqlContext, None]) -> FiltersType:
    f = service.get_filters(info.context.conn)
    return from_model(f, FiltersType)


def resolve_tracks(info: Info[GqlContext, None]) -> list[str]:
    from sqlalchemy import select

    from bcsd_api.core.tables import tracks

    rows = info.context.conn.execute(select(tracks.c.name))
    return [row.name for row in rows]


def resolve_me(info: Info[GqlContext, None]) -> MeType:
    user = require_user(info.context)
    detail = service.get_member(info.context.member_repo, user["sub"])
    return MeType(
        id=user["sub"],
        email=user["email"],
        member=from_model(detail, MemberDetailType),
    )
