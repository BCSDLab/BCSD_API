from datetime import datetime

import strawberry

from bcsd_api.graphql.convert import SortFieldInput


@strawberry.type
class LinkType:
    id: str
    code: str
    title: str
    description: str | None
    url: str
    creator_id: str
    created_at: str
    expires_at: str | None
    expired_at: str | None
    updated_at: str


@strawberry.type
class DailyClickType:
    date: str
    count: int


@strawberry.type
class LinkDetailType(LinkType):
    total_clicks: int
    daily_clicks: list[DailyClickType]


@strawberry.type
class CreatorOptionType:
    id: str
    name: str


@strawberry.type
class LinkFiltersType:
    creators: list[CreatorOptionType]
    expired: list[str]


@strawberry.type
class PagedLinks:
    items: list[LinkType]
    total: int
    page: int
    size: int


@strawberry.input
class LinkFilterInput:
    page: int = 1
    size: int = 20
    sorts: list[SortFieldInput] | None = None
    creator_id: str | None = None
    expired: str | None = None
    title: str | None = None
    code: str | None = None


@strawberry.input
class CreateLinkInput:
    title: str
    url: str
    description: str | None = None
    code: str | None = None
    expires_at: datetime | None = None


@strawberry.input
class UpdateLinkInput:
    title: str | None = None
    description: str | None = None
    expires_at: datetime | None = None
