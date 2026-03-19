from collections.abc import Iterator
from functools import lru_cache

from fastapi import Depends, Request
from sqlalchemy import Connection

from .auth import token as jwt_token
from .authz.client import AuthzClient
from .config import Settings
from .database import create_engine, get_connection
from .email import ResendSender
from .email.sender import EmailSender
from .exception import Unauthorized
from .member.pg_repository import PgMemberRepository
from .sheets.client import SheetsClient
from .shorten.pg_repository import PgLinkRepository


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def _make_engine(database_url: str):
    return create_engine(database_url)


def get_conn(settings: Settings = Depends(get_settings)) -> Iterator[Connection]:
    engine = _make_engine(settings.database_url)
    yield from get_connection(engine)


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
    endpoint = f"{settings.spicedb_host}:{settings.spicedb_port}"
    return _create_authz(endpoint, settings.spicedb_token)


def get_member_repo(conn: Connection = Depends(get_conn)) -> PgMemberRepository:
    return PgMemberRepository(conn)


def get_link_repo(conn: Connection = Depends(get_conn)) -> PgLinkRepository:
    return PgLinkRepository(conn)


def current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    raw = jwt_token.extract_raw(request, settings.cookie_name)
    if not raw:
        raise Unauthorized("missing authorization")
    return jwt_token.decode_token(raw, settings.jwt_secret, settings.jwt_algorithm)
