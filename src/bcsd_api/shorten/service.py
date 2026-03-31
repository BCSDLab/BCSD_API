import random
import string
from collections import Counter
from datetime import datetime

from bcsd_api.exception import Conflict, Gone, NotFound
from bcsd_api.filter.base import PagedResponse, apply_filter
from bcsd_api.filter.links import LinkFilter
from bcsd_api.core.id_gen import generate_id
from bcsd_api.member.pg_repository import PgMemberRepository
from bcsd_api.core.timezone import KST

from .pg_repository import PgLinkRepository
from .schema import (
    CreateRequest,
    CreatorOption,
    DailyClick,
    LinkDetail,
    LinkFiltersResponse,
    LinkResponse,
    UpdateRequest,
)

_MAX_RETRIES = 5


def _generate_code() -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=6))


def _now_str() -> str:
    return datetime.now(KST).isoformat()


def _format_expires(expires_at) -> str:
    if not expires_at:
        return ""
    return expires_at.isoformat()


def _resolve_code(repo: PgLinkRepository, code: str | None) -> str:
    if not code:
        return _unique_code(repo)
    if repo.find_by_code(code):
        raise Conflict(f"code '{code}' already exists")
    return code


def _build_row(code: str, req: CreateRequest, creator_id: str) -> dict:
    now = _now_str()
    return {
        "id": generate_id("L"),
        "code": code,
        "title": req.title,
        "description": req.description or "",
        "url": req.url,
        "creator_id": creator_id,
        "created_at": now,
        "expires_at": _format_expires(req.expires_at),
        "expired_at": "",
        "updated_at": now,
    }


def create(repo: PgLinkRepository, req: CreateRequest, creator_id: str) -> LinkResponse:
    code = _resolve_code(repo, req.code)
    row = _build_row(code, req, creator_id)
    repo.create(row)
    return LinkResponse(**row)


def _unique_code(repo: PgLinkRepository) -> str:
    for _ in range(_MAX_RETRIES):
        code = _generate_code()
        if not repo.find_by_code(code):
            return code
    raise Conflict("failed to generate unique code")


def _is_expired(row: dict) -> bool:
    if row.get("expired_at"):
        return True
    expires = row.get("expires_at")
    if not expires:
        return False
    return datetime.fromisoformat(expires) < datetime.now(KST)


def _expired_label(row: dict) -> str:
    if _is_expired(row):
        return "expired"
    return "active"


def _add_expired_flag(rows: list[dict]) -> list[dict]:
    for row in rows:
        row["expired"] = _expired_label(row)
    return rows


def list_links(repo: PgLinkRepository, filt: LinkFilter) -> PagedResponse[LinkResponse]:
    rows = _add_expired_flag(repo.find_all())
    paged = apply_filter(rows, filt)
    items = [LinkResponse(**r) for r in paged.items]
    return PagedResponse(
        items=items, total=paged.total, page=paged.page, size=paged.size
    )


def _aggregate_clicks(clicks: list[dict]) -> list[DailyClick]:
    dates = []
    for c in clicks:
        raw = c.get("clicked_at", "")
        if not raw:
            continue
        dates.append(raw[:10])
    counts = Counter(dates)
    return [DailyClick(date=d, count=n) for d, n in sorted(counts.items())]


def get_detail(repo: PgLinkRepository, link_id: str) -> LinkDetail:
    row = repo.find_by_id(link_id)
    if not row:
        raise NotFound(f"link {link_id} not found")
    clicks = repo.find_clicks(link_id)
    return LinkDetail(
        **row,
        total_clicks=len(clicks),
        daily_clicks=_aggregate_clicks(clicks),
    )


def _serialize_field(key: str, val) -> str:
    if key == "expires_at" and val:
        return val.isoformat()
    if key == "expires_at":
        return ""
    return str(val)


def _apply_updates(repo: PgLinkRepository, link_id: str, updates: dict) -> None:
    for key, val in updates.items():
        repo.update(link_id, key, _serialize_field(key, val))
    repo.update(link_id, "updated_at", _now_str())


def update(repo: PgLinkRepository, link_id: str, req: UpdateRequest) -> LinkResponse:
    row = repo.find_by_id(link_id)
    if not row:
        raise NotFound(f"link {link_id} not found")
    updates = req.model_dump(exclude_none=True)
    _apply_updates(repo, link_id, updates)
    return LinkResponse(**{**row, **updates, "updated_at": _now_str()})


def toggle(repo: PgLinkRepository, link_id: str) -> LinkResponse:
    row = repo.find_by_id(link_id)
    if not row:
        raise NotFound(f"link {link_id} not found")
    if row.get("expired_at"):
        repo.update(link_id, "expired_at", "")
        row["expired_at"] = ""
        repo.update(link_id, "updated_at", _now_str())
        return LinkResponse(**row)
    now = _now_str()
    repo.update(link_id, "expired_at", now)
    row["expired_at"] = now
    repo.update(link_id, "updated_at", _now_str())
    return LinkResponse(**row)


def delete(repo: PgLinkRepository, link_id: str) -> None:
    row = repo.find_by_id(link_id)
    if not row:
        raise NotFound(f"link {link_id} not found")
    repo.delete_clicks(link_id)
    repo.delete(link_id)


def resolve(repo: PgLinkRepository, code: str) -> tuple[str, str]:
    row = repo.find_by_code(code)
    if not row:
        raise NotFound(f"short link '{code}' not found")
    if row.get("expired_at"):
        raise Gone("this link has expired")
    expires = row.get("expires_at")
    if expires and datetime.fromisoformat(expires) < datetime.now(KST):
        raise Gone("this link has expired")
    return row["url"], row["id"]


def record_click(repo: PgLinkRepository, link_id: str, referer: str, user_agent: str) -> None:
    row = {
        "id": generate_id("LC"),
        "link_id": link_id,
        "clicked_at": _now_str(),
        "referer": referer or "",
        "user_agent": user_agent or "",
    }
    repo.add_click(row)


def _creator_name(members_repo: PgMemberRepository, cid: str) -> str:
    member = members_repo.find_by_id(cid)
    if not member:
        return cid
    return member["name"]


def get_filters(repo: PgLinkRepository, members_repo: PgMemberRepository) -> LinkFiltersResponse:
    rows = repo.find_all()
    ids = list({r["creator_id"] for r in rows if r.get("creator_id")})
    creators = [CreatorOption(id=cid, name=_creator_name(members_repo, cid)) for cid in ids]
    return LinkFiltersResponse(creators=creators)
