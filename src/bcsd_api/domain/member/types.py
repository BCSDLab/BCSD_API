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
    department: str
    student_id: str
    phone: str


@strawberry.type
class MemberDetailType(MemberType):
    school_email: str
    join_date: str
    last_updated: str


@strawberry.type
class FiltersType:
    tracks: list[str]
    statuses: list[str]
    departments: list[str]
    names: list[str]
    emails: list[str]
    student_ids: list[str]
    phones: list[str]


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
    status: list[str] | None = None
    track: list[str] | None = None
    team: list[str] | None = None
    name: str | None = None
    email: str | None = None
    department: str | None = None
    student_id: str | None = None
    phone: str | None = None
