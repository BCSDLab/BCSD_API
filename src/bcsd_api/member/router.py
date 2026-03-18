from fastapi import APIRouter, Depends
from sqlalchemy import Connection

from bcsd_api.dependencies import current_user, get_conn, get_member_repo
from bcsd_api.filter.base import PagedResponse
from bcsd_api.filter.members import MemberFilter

from . import service
from .pg_repository import PgMemberRepository
from .schema import FiltersResponse, MemberDetail, MemberResponse

router = APIRouter(prefix="/v1/members", tags=["members"])


@router.get("/filters", response_model=FiltersResponse)
def get_filters(
    conn: Connection = Depends(get_conn),
) -> FiltersResponse:
    return service.get_filters(conn)


@router.get("", response_model=PagedResponse[MemberResponse])
def get_members(
    filt: MemberFilter = Depends(),
    _: dict = Depends(current_user),
    repo: PgMemberRepository = Depends(get_member_repo),
) -> PagedResponse[MemberResponse]:
    return service.list_members(repo, filt)


@router.get("/{member_id}", response_model=MemberDetail)
def get_member(
    member_id: str,
    _: dict = Depends(current_user),
    repo: PgMemberRepository = Depends(get_member_repo),
) -> MemberDetail:
    return service.get_member(repo, member_id)
