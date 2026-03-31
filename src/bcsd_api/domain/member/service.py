from sqlalchemy import Connection, select

from bcsd_api.global_.exception import NotFound
from bcsd_api.filter.base import PagedResponse, apply_filter
from bcsd_api.filter.members import MemberFilter
from bcsd_api.common.tables import members, statuses, tracks

from .repository import PgMemberRepository
from .model import FiltersResponse, MemberDetail, MemberResponse


def _names(conn: Connection, table) -> list[str]:
    rows = conn.execute(select(table.c.name))
    return [row.name for row in rows]


def _distinct(conn: Connection, column) -> list[str]:
    rows = conn.execute(select(column).distinct().order_by(column))
    return [row[0] for row in rows if row[0]]


def list_members(
    repo: PgMemberRepository, filt: MemberFilter,
) -> PagedResponse[MemberResponse]:
    rows = repo.find_all()
    paged = apply_filter(rows, filt)
    items = [MemberResponse(**r) for r in paged.items]
    return PagedResponse(
        items=items, total=paged.total, page=paged.page, size=paged.size,
    )


def get_member(repo: PgMemberRepository, member_id: str) -> MemberDetail:
    row = repo.find_by_id(member_id)
    if not row:
        raise NotFound(f"member {member_id} not found")
    return MemberDetail(**row)


def get_filters(conn: Connection) -> FiltersResponse:
    return FiltersResponse(
        tracks=_names(conn, tracks),
        statuses=_names(conn, statuses),
        departments=_distinct(conn, members.c.department),
        names=_distinct(conn, members.c.name),
        emails=_distinct(conn, members.c.email),
        student_ids=_distinct(conn, members.c.student_id),
        phones=_distinct(conn, members.c.phone),
    )
