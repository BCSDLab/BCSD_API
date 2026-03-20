import strawberry
from strawberry.types import Info

from bcsd_api.filter.links import LinkFilter
from bcsd_api.graphql.context import GqlContext, require_user
from bcsd_api.graphql.convert import from_model, from_paged, to_sorts

from . import service
from .schema import CreateRequest, UpdateRequest
from .types import (
    CreateLinkInput,
    CreatorOptionType,
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
        sorts=to_sorts(inp.sorts),
        creator_id=inp.creator_id, expired=inp.expired,
        title=inp.title, code=inp.code,
    )


def resolve_links(
    info: Info[GqlContext, None],
    filter: LinkFilterInput | None = None,
) -> PagedLinks:
    ctx = info.context
    require_user(ctx)
    filt = _to_filter(filter) if filter else LinkFilter.model_validate({})
    paged = service.list_links(ctx.link_repo, filt)
    return from_paged(paged, LinkType, PagedLinks)


def resolve_link(info: Info[GqlContext, None], id: strawberry.ID) -> LinkDetailType:
    require_user(info.context)
    d = service.get_detail(info.context.link_repo, id)
    return from_model(d, LinkDetailType)


def resolve_link_filters(info: Info[GqlContext, None]) -> LinkFiltersType:
    ctx = info.context
    require_user(ctx)
    f = service.get_filters(ctx.link_repo, ctx.member_repo)
    return LinkFiltersType(
        creators=[CreatorOptionType(id=c.id, name=c.name) for c in f.creators],
        expired=f.expired,
    )


def resolve_create(info: Info[GqlContext, None], input: CreateLinkInput) -> LinkType:
    user = require_user(info.context)
    req = CreateRequest(
        title=input.title, url=input.url,
        description=input.description,
        code=input.code, expires_at=input.expires_at,
    )
    result = service.create(info.context.link_repo, req, user["sub"])
    return from_model(result, LinkType)


def resolve_update(
    info: Info[GqlContext, None], id: strawberry.ID, input: UpdateLinkInput,
) -> LinkType:
    require_user(info.context)
    req = UpdateRequest(
        title=input.title, description=input.description,
        expires_at=input.expires_at,
    )
    result = service.update(info.context.link_repo, id, req)
    return from_model(result, LinkType)


def resolve_toggle(info: Info[GqlContext, None], id: strawberry.ID) -> LinkType:
    require_user(info.context)
    result = service.toggle(info.context.link_repo, id)
    return from_model(result, LinkType)


def resolve_delete(info: Info[GqlContext, None], id: strawberry.ID) -> bool:
    require_user(info.context)
    service.delete(info.context.link_repo, id)
    return True
