from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import RedirectResponse

from bcsd_api.dependencies import get_link_repo
from bcsd_api.shorten import service
from bcsd_api.shorten.repository import LinkRepository

router = APIRouter(tags=["redirect"])


@router.get("/s/{code}")
def redirect_link(
    code: str,
    request: Request,
    background: BackgroundTasks,
    repo: LinkRepository = Depends(get_link_repo),
) -> RedirectResponse:
    url, link_id = service.resolve(repo, code)
    referer = request.headers.get("referer", "")
    agent = request.headers.get("user-agent", "")
    background.add_task(service.record_click, repo, link_id, referer, agent)
    return RedirectResponse(url=url, status_code=302)
