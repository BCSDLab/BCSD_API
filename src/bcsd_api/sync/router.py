from datetime import datetime

from fastapi import APIRouter, Depends, Header
from sqlalchemy import Connection, select, update

from bcsd_api.config import Settings
from bcsd_api.dependencies import get_conn, get_settings
from bcsd_api.exception import Forbidden, NotFound
from bcsd_api.tables import (
    events,
    fees,
    groups,
    link_clicks,
    links,
    members,
    payment_statuses,
    statuses,
    tracks,
    workflow_logs,
)
from bcsd_api.timezone import KST

router = APIRouter(prefix="/v1/internal", tags=["internal"])

_TABLES = {
    "members": members,
    "fees": fees,
    "groups": groups,
    "events": events,
    "workflow_logs": workflow_logs,
    "links": links,
    "link_clicks": link_clicks,
    "tracks": tracks,
    "statuses": statuses,
    "payment_statuses": payment_statuses,
}


def _verify_token(token: str, expected: str) -> None:
    if token != expected:
        raise Forbidden("invalid sync token")


@router.get("/dump/{table_name}")
def dump_table(
    table_name: str,
    conn: Connection = Depends(get_conn),
    settings: Settings = Depends(get_settings),
    x_sync_token: str = Header(...),
) -> list[dict]:
    _verify_token(x_sync_token, settings.sync_token)
    if table_name not in _TABLES:
        raise NotFound(f"table '{table_name}' not found")
    table = _TABLES[table_name]
    rows = conn.execute(select(table))
    return [row._asdict() for row in rows]


@router.post("/expire-links")
def expire_links(
    conn: Connection = Depends(get_conn),
    settings: Settings = Depends(get_settings),
    x_sync_token: str = Header(...),
) -> dict:
    _verify_token(x_sync_token, settings.sync_token)
    now = datetime.now(KST).isoformat()
    stmt = (
        update(links)
        .where(
            links.c.expires_at < now,
            links.c.expires_at != "",
            links.c.expired_at == "",
        )
        .values(expired_at=now, updated_at=now)
    )
    result = conn.execute(stmt)
    return {"expired_count": result.rowcount}
