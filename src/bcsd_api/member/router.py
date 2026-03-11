from fastapi import APIRouter, Depends

from bcsd_api.dependencies import current_user, get_member_repo, get_sheets
from bcsd_api.filter.base import PagedResponse
from bcsd_api.filter.members import MemberFilter
from bcsd_api.sheets.client import SheetsClient

from . import service
from .repository import MemberRepository
from .schema import FiltersResponse, MemberDetail, MemberResponse

router = APIRouter(prefix="/v1/members", tags=["members"])


@router.get("/filters", response_model=FiltersResponse)
def get_filters(
    sheets: SheetsClient = Depends(get_sheets),
) -> FiltersResponse:
    return service.get_filters(sheets)


@router.get("", response_model=PagedResponse[MemberResponse])
def get_members(
    filt: MemberFilter = Depends(),
    _: dict = Depends(current_user),
    repo: MemberRepository = Depends(get_member_repo),
) -> PagedResponse[MemberResponse]:
    return service.list_members(repo, filt)


@router.get("/{member_id}", response_model=MemberDetail)
def get_member(
    member_id: str,
    _: dict = Depends(current_user),
    repo: MemberRepository = Depends(get_member_repo),
) -> MemberDetail:
    return service.get_member(repo, member_id)
