from fastapi import APIRouter, Depends

from bcsd_api.dependencies import current_user, get_link_repo, get_member_repo
from bcsd_api.filter.base import PagedResponse
from bcsd_api.filter.links import LinkFilter
from bcsd_api.member.pg_repository import PgMemberRepository

from . import service
from .pg_repository import PgLinkRepository
from .schema import (
    CreateRequest,
    LinkDetail,
    LinkFiltersResponse,
    LinkResponse,
    UpdateRequest,
)

router = APIRouter(prefix="/v1/shorten", tags=["shorten"])


@router.post("", response_model=LinkResponse, status_code=201)
def create_link(
    req: CreateRequest,
    user: dict = Depends(current_user),
    repo: PgLinkRepository = Depends(get_link_repo),
) -> LinkResponse:
    return service.create(repo, req, user["sub"])


@router.get("/filters", response_model=LinkFiltersResponse)
def get_filters(
    repo: PgLinkRepository = Depends(get_link_repo),
    members_repo: PgMemberRepository = Depends(get_member_repo),
    _: dict = Depends(current_user),
) -> LinkFiltersResponse:
    return service.get_filters(repo, members_repo)


@router.get("", response_model=PagedResponse[LinkResponse])
def list_links(
    filt: LinkFilter = Depends(),
    _: dict = Depends(current_user),
    repo: PgLinkRepository = Depends(get_link_repo),
) -> PagedResponse[LinkResponse]:
    return service.list_links(repo, filt)


@router.get("/{link_id}", response_model=LinkDetail)
def get_link(
    link_id: str,
    _: dict = Depends(current_user),
    repo: PgLinkRepository = Depends(get_link_repo),
) -> LinkDetail:
    return service.get_detail(repo, link_id)


@router.post("/{link_id}", response_model=LinkResponse)
def update_link(
    link_id: str,
    req: UpdateRequest,
    _: dict = Depends(current_user),
    repo: PgLinkRepository = Depends(get_link_repo),
) -> LinkResponse:
    return service.update(repo, link_id, req)


@router.patch("/{link_id}/toggle", response_model=LinkResponse)
def toggle_link(
    link_id: str,
    _: dict = Depends(current_user),
    repo: PgLinkRepository = Depends(get_link_repo),
) -> LinkResponse:
    return service.toggle(repo, link_id)


@router.delete("/{link_id}", status_code=204)
def delete_link(
    link_id: str,
    _: dict = Depends(current_user),
    repo: PgLinkRepository = Depends(get_link_repo),
) -> None:
    service.delete(repo, link_id)
