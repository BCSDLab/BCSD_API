from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from bcsd_api.dependencies import get_link_repo
from bcsd_api.exception import Gone
from bcsd_api.shorten import service
from bcsd_api.shorten.pg_repository import PgLinkRepository

router = APIRouter(tags=["redirect"])


@router.get("/s/{code}")
def redirect_link(
    code: str,
    request: Request,
    repo: PgLinkRepository = Depends(get_link_repo),
) -> RedirectResponse:
    try:
        url, link_id = service.resolve(repo, code)
    except Gone:
        return RedirectResponse(url="/expired", status_code=302)
    referer = request.headers.get("referer", "")
    agent = request.headers.get("user-agent", "")
    service.record_click(repo, link_id, referer, agent)
    return RedirectResponse(url=url, status_code=302)
