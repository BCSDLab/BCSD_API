import strawberry

from bcsd_api.graphql.convert import SortFieldInput


@strawberry.type
class MemberType:
    id: str
    name: str
    email: str
    status: str
    track: str
    team: str
    payment_status: str


@strawberry.type
class MemberDetailType(MemberType):
    department: str
    student_id: str
    school_email: str
    phone: str
    join_date: str
    last_updated: str


@strawberry.type
class FiltersType:
    tracks: list[str]
    statuses: list[str]
    payment_statuses: list[str]


@strawberry.type
class MeType:
    id: str
    email: str
    member: MemberDetailType


@strawberry.type
class PagedMembers:
    items: list[MemberType]
    total: int
    page: int
    size: int


@strawberry.input
class MemberFilterInput:
    page: int = 1
    size: int = 20
    sorts: list[SortFieldInput] | None = None
    status: str | None = None
    track: str | None = None
    team: str | None = None
    payment_status: str | None = None
    name: str | None = None
