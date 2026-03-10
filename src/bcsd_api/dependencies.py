from functools import lru_cache

from fastapi import Depends, Request

from .auth import token as jwt_token
from .config import Settings
from .email import ResendSender
from .email.sender import EmailSender
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


_sender_cache: EmailSender | None = None


def get_email_sender(settings: Settings = Depends(get_settings)) -> EmailSender:
    global _sender_cache
    if _sender_cache:
        return _sender_cache
    _sender_cache = ResendSender(settings.resend_api_key, settings.resend_sender)
    return _sender_cache


def get_member_repo(sheets: SheetsClient = Depends(get_sheets)) -> MemberRepository:
    return MemberRepository(sheets)


def _extract_token(request: Request, settings: Settings) -> str:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    cookie = request.cookies.get(settings.cookie_name)
    if cookie:
        return cookie
    raise Unauthorized("missing authorization")


def current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    raw = _extract_token(request, settings)
    return jwt_token.decode_token(raw, settings.jwt_secret, settings.jwt_algorithm)
