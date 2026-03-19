import logging
from typing import List

import strawberry
from graphql import GraphQLError
from strawberry.types import ExecutionContext

from bcsd_api.exception.base import AppException
from bcsd_api.member import resolvers as member_resolvers
from bcsd_api.member.types import (
    FiltersType,
    MeType,
    MemberDetailType,
    MemberFilterInput,
    PagedMembers,
)
from bcsd_api.shorten import resolvers as link_resolvers
from bcsd_api.shorten.types import (
    CreateLinkInput,
    LinkDetailType,
    LinkFilterInput,
    LinkFiltersType,
    LinkType,
    PagedLinks,
    UpdateLinkInput,
)

from .errors import AppErrorExtension


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> str:
        return "ok"

    members: PagedMembers = strawberry.field(resolver=member_resolvers.resolve_members)
    member: MemberDetailType = strawberry.field(resolver=member_resolvers.resolve_member)
    member_filters: FiltersType = strawberry.field(resolver=member_resolvers.resolve_filters)
    tracks: list[str] = strawberry.field(resolver=member_resolvers.resolve_tracks)
    me: MeType = strawberry.field(resolver=member_resolvers.resolve_me)

    links: PagedLinks = strawberry.field(resolver=link_resolvers.resolve_links)
    link: LinkDetailType = strawberry.field(resolver=link_resolvers.resolve_link)
    link_filters: LinkFiltersType = strawberry.field(resolver=link_resolvers.resolve_link_filters)


@strawberry.type
class Mutation:
    create_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_create)
    update_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_update)
    toggle_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_toggle)
    delete_link: bool = strawberry.mutation(resolver=link_resolvers.resolve_delete)


logger = logging.getLogger("strawberry.execution")


class _Schema(strawberry.Schema):
    def process_errors(self, errors: List[GraphQLError], ctx: ExecutionContext | None = None) -> None:
        for err in errors:
            if isinstance(err.original_error, AppException):
                continue
            logger.error(err.message, exc_info=err.original_error)


schema = _Schema(
    query=Query,
    mutation=Mutation,
    extensions=[AppErrorExtension],
)
