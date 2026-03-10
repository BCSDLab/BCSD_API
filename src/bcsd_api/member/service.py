from bcsd_api.exception import NotFound
from bcsd_api.filter.base import PagedResponse, apply_filter
from bcsd_api.filter.members import MemberFilter

from .repository import MemberRepository
from .schema import MemberDetail, MemberResponse


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
