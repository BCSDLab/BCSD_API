from bcsd_api.exception import NotFound
from bcsd_api.filter.base import PagedResponse, apply_filter
from bcsd_api.filter.members import MemberFilter
from bcsd_api.sheets.client import SheetsClient

from .repository import MemberRepository
from .schema import FiltersResponse, MemberDetail, MemberResponse

def _names(sheets: SheetsClient, sheet: str) -> list[str]:
    return [r["name"] for r in sheets.get_records(sheet)]


def list_members(
    repo: MemberRepository, filt: MemberFilter
) -> PagedResponse[MemberResponse]:
    rows = repo.find_all()
    paged = apply_filter(rows, filt)
    items = [MemberResponse(**r) for r in paged.items]
    return PagedResponse(
        items=items, total=paged.total, page=paged.page, size=paged.size
    )


def get_member(repo: MemberRepository, member_id: str) -> MemberDetail:
    row = repo.find_by_id(member_id)
    if not row:
        raise NotFound(f"member {member_id} not found")
    return MemberDetail(**row)


def get_filters(sheets: SheetsClient) -> FiltersResponse:
    return FiltersResponse(
        tracks=_names(sheets, "tracks"),
        statuses=_names(sheets, "statuses"),
        payment_statuses=_names(sheets, "payment_statuses"),
    )
