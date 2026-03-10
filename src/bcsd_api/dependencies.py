from functools import lru_cache

from fastapi import Depends, Request

from .auth import token as jwt_token
from .config import Settings
from .exception import Unauthorized
from .member.repository import MemberRepository
from .sheets.client import SheetsClient


@lru_cache
def get_settings() -> Settings:
    return Settings()


_sheets_cache: SheetsClient | None = None


def get_sheets(settings: Settings = Depends(get_settings)) -> SheetsClient:
    global _sheets_cache
    if _sheets_cache:
        return _sheets_cache
    _sheets_cache = SheetsClient(
        settings.google_service_account_file, settings.google_sheets_id
    )
    return _sheets_cache


def get_member_repo(sheets: SheetsClient = Depends(get_sheets)) -> MemberRepository:
    return MemberRepository(sheets)


def _extract_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise Unauthorized("missing authorization header")
    return header[7:]


def current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    raw = _extract_token(request)
    return jwt_token.decode_token(raw, settings.jwt_secret, settings.jwt_algorithm)
