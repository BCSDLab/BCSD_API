from functools import lru_cache

from fastapi import Depends, Request

from .auth import token as jwt_token
from .authz.client import AuthzClient
from .config import Settings
from .email import ResendSender
from .email.sender import EmailSender
from .exception import Unauthorized
from .member.repository import MemberRepository
from .sheets.client import SheetsClient


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@lru_cache
def _create_sheets(credentials: str, sheets_id: str) -> SheetsClient:
    return SheetsClient(credentials, sheets_id)


def get_sheets(settings: Settings = Depends(get_settings)) -> SheetsClient:
    return _create_sheets(settings.google_service_account_file, settings.google_sheets_id)


@lru_cache
def _create_sender(api_key: str, sender: str) -> EmailSender:
    return ResendSender(api_key, sender)


def get_email_sender(settings: Settings = Depends(get_settings)) -> EmailSender:
    return _create_sender(settings.resend_api_key, settings.resend_sender)


@lru_cache
def _create_authz(endpoint: str, token: str) -> AuthzClient:
    return AuthzClient(endpoint, token)


def get_authz(settings: Settings = Depends(get_settings)) -> AuthzClient:
    return _create_authz(settings.spicedb_endpoint, settings.spicedb_token)


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
