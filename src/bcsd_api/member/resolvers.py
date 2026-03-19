import strawberry
from strawberry.types import Info

from bcsd_api.filter.members import MemberFilter
from bcsd_api.graphql.context import GqlContext, require_user

from . import service
from .schema import MemberDetail, MemberResponse
from .types import (
    FiltersType,
    MeType,
    MemberDetailType,
    MemberFilterInput,
    MemberType,
    PagedMembers,
)


def _to_filter(inp: MemberFilterInput) -> MemberFilter:
    return MemberFilter(
        page=inp.page, size=inp.size,
        sort_by=inp.sort_by, sort_order=inp.sort_order,
        status=inp.status, track=inp.track,
        team=inp.team, payment_status=inp.payment_status,
        name=inp.name,
    )


def _to_member(m: MemberResponse) -> MemberType:
    return MemberType(
        id=m.id, name=m.name, email=m.email,
        status=m.status, track=m.track,
        team=m.team, payment_status=m.payment_status,
    )


def _to_detail(m: MemberDetail) -> MemberDetailType:
    return MemberDetailType(
        id=m.id, name=m.name, email=m.email,
        status=m.status, track=m.track,
        team=m.team, payment_status=m.payment_status,
        department=m.department, student_id=m.student_id,
        school_email=m.school_email, phone=m.phone,
        join_date=m.join_date, last_updated=m.last_updated,
    )


def resolve_members(
    info: Info[GqlContext, None],
    filter: MemberFilterInput | None = None,
) -> PagedMembers:
    ctx = info.context
    require_user(ctx)
    filt = _to_filter(filter) if filter else MemberFilter.model_validate({})
    paged = service.list_members(ctx.member_repo, filt)
    items = [_to_member(m) for m in paged.items]
    return PagedMembers(
        items=items, total=paged.total,
        page=paged.page, size=paged.size,
    )


def resolve_member(info: Info[GqlContext, None], id: strawberry.ID) -> MemberDetailType:
    require_user(info.context)
    m = service.get_member(info.context.member_repo, id)
    return _to_detail(m)


def resolve_filters(info: Info[GqlContext, None]) -> FiltersType:
    f = service.get_filters(info.context.conn)
    return FiltersType(
        tracks=f.tracks,
        statuses=f.statuses,
        payment_statuses=f.payment_statuses,
    )


def resolve_tracks(info: Info[GqlContext, None]) -> list[str]:
    from sqlalchemy import select

    from bcsd_api.tables import tracks

    rows = info.context.conn.execute(select(tracks.c.name))
    return [row.name for row in rows]


def resolve_me(info: Info[GqlContext, None]) -> MeType:
    user = require_user(info.context)
    return MeType(id=user["sub"], email=user["email"])
