from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy import Connection

from bcsd_api.auth import token as jwt_token
from bcsd_api.config import Settings
from bcsd_api.dependencies import (
    get_conn,
    get_link_repo,
    get_member_repo,
    get_settings,
)
from bcsd_api.exception import Unauthorized
from bcsd_api.member.pg_repository import PgMemberRepository
from bcsd_api.shorten.pg_repository import PgLinkRepository


@dataclass
class GqlContext:
    conn: Connection
    member_repo: PgMemberRepository
    link_repo: PgLinkRepository
    user: dict | None


def _try_auth(request: Request, settings: Settings) -> dict | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        raw = header[7:]
    else:
        raw = request.cookies.get(settings.cookie_name, "")
    if not raw:
        return None
    try:
        return jwt_token.decode_token(
            raw, settings.jwt_secret, settings.jwt_algorithm,
        )
    except Exception:
        return None


def require_user(ctx: GqlContext) -> dict:
    if not ctx.user:
        raise Unauthorized("authentication required")
    return ctx.user


async def context_getter(
    request: Request,
    settings: Settings = Depends(get_settings),
    conn: Connection = Depends(get_conn),
    member_repo: PgMemberRepository = Depends(get_member_repo),
    link_repo: PgLinkRepository = Depends(get_link_repo),
) -> GqlContext:
    user = _try_auth(request, settings)
    return GqlContext(
        conn=conn,
        member_repo=member_repo,
        link_repo=link_repo,
        user=user,
    )
