from strawberry.types import Info

from bcsd_api.filter.links import LinkFilter
from bcsd_api.graphql.context import GqlContext, require_user

from . import service
from .schema import (
    CreateRequest,
    DailyClick,
    LinkDetail,
    LinkFiltersResponse,
    LinkResponse,
    UpdateRequest,
)
from .types import (
    CreateLinkInput,
    CreatorOptionType,
    DailyClickType,
    LinkDetailType,
    LinkFilterInput,
    LinkFiltersType,
    LinkType,
    PagedLinks,
    UpdateLinkInput,
)


def _to_filter(inp: LinkFilterInput) -> LinkFilter:
    return LinkFilter(
        page=inp.page, size=inp.size,
        sort_by=inp.sort_by, sort_order=inp.sort_order,
        creator_id=inp.creator_id, expired=inp.expired,
    )


def _to_link(r: LinkResponse) -> LinkType:
    return LinkType(
        id=r.id, code=r.code, title=r.title,
        description=r.description, url=r.url,
        creator_id=r.creator_id, created_at=r.created_at,
        expires_at=r.expires_at, expired_at=r.expired_at,
        updated_at=r.updated_at,
    )


def _to_daily(d: DailyClick) -> DailyClickType:
    return DailyClickType(date=d.date, count=d.count)


def _to_detail(d: LinkDetail) -> LinkDetailType:
    return LinkDetailType(
        id=d.id, code=d.code, title=d.title,
        description=d.description, url=d.url,
        creator_id=d.creator_id, created_at=d.created_at,
        expires_at=d.expires_at, expired_at=d.expired_at,
        updated_at=d.updated_at,
        total_clicks=d.total_clicks,
        daily_clicks=[_to_daily(c) for c in d.daily_clicks],
    )


# --- Queries ---

def resolve_links(
    info: Info[GqlContext, None],
    filter: LinkFilterInput | None = None,
) -> PagedLinks:
    ctx = info.context
    require_user(ctx)
    filt = _to_filter(filter) if filter else LinkFilter.model_validate({})
    paged = service.list_links(ctx.link_repo, filt)
    items = [_to_link(r) for r in paged.items]
    return PagedLinks(
        items=items, total=paged.total,
        page=paged.page, size=paged.size,
    )


def resolve_link(info: Info[GqlContext, None], id: str) -> LinkDetailType:
    require_user(info.context)
    d = service.get_detail(info.context.link_repo, id)
    return _to_detail(d)


def resolve_link_filters(info: Info[GqlContext, None]) -> LinkFiltersType:
    ctx = info.context
    require_user(ctx)
    f = service.get_filters(ctx.link_repo, ctx.member_repo)
    return LinkFiltersType(
        creators=[CreatorOptionType(id=c.id, name=c.name) for c in f.creators],
        expired=f.expired,
    )


# --- Mutations ---

def resolve_create(info: Info[GqlContext, None], input: CreateLinkInput) -> LinkType:
    user = require_user(info.context)
    req = CreateRequest(
        title=input.title, url=input.url,
        description=input.description,
        code=input.code, expires_at=input.expires_at,
    )
    result = service.create(info.context.link_repo, req, user["sub"])
    return _to_link(result)


def resolve_update(
    info: Info[GqlContext, None], id: str, input: UpdateLinkInput,
) -> LinkType:
    require_user(info.context)
    req = UpdateRequest(
        title=input.title, description=input.description,
        expires_at=input.expires_at,
    )
    result = service.update(info.context.link_repo, id, req)
    return _to_link(result)


def resolve_toggle(info: Info[GqlContext, None], id: str) -> LinkType:
    require_user(info.context)
    result = service.toggle(info.context.link_repo, id)
    return _to_link(result)


def resolve_delete(info: Info[GqlContext, None], id: str) -> bool:
    require_user(info.context)
    service.delete(info.context.link_repo, id)
    return True
