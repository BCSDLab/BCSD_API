from collections.abc import Iterator
from functools import lru_cache

from fastapi import Depends, Request
from sqlalchemy import Connection

from .global_.auth import token as jwt_token
from .global_.authz.client import AuthzClient
from .common.config import Settings
from .common.database import create_engine, get_connection
from .infra.email import ResendSender
from .infra.email.sender import EmailSender
from .global_.exception import Unauthorized
from .domain.apply.repository import PgAnswerRepository, PgApplicationRepository
from .domain.form.repository import PgFormRepository, PgQuestionRepository
from .domain.member.repository import PgMemberRepository
from .domain.recruit.repository import PgRecruitRepository
from .domain.setting.repository import PgSettingRepository
from .domain.shorten.repository import PgLinkRepository


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


def get_setting_repo(conn: Connection = Depends(get_conn)) -> PgSettingRepository:
    return PgSettingRepository(conn)


def get_recruit_repo(conn: Connection = Depends(get_conn)) -> PgRecruitRepository:
    return PgRecruitRepository(conn)


def get_form_repo(conn: Connection = Depends(get_conn)) -> PgFormRepository:
    return PgFormRepository(conn)


def get_question_repo(conn: Connection = Depends(get_conn)) -> PgQuestionRepository:
    return PgQuestionRepository(conn)


def get_app_repo(conn: Connection = Depends(get_conn)) -> PgApplicationRepository:
    return PgApplicationRepository(conn)


def get_ans_repo(conn: Connection = Depends(get_conn)) -> PgAnswerRepository:
    return PgAnswerRepository(conn)


def current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    raw = jwt_token.extract_raw(request, settings.cookie_name)
    if not raw:
        raise Unauthorized("missing authorization")
    return jwt_token.decode_token(raw, settings.jwt_secret, settings.jwt_algorithm)
