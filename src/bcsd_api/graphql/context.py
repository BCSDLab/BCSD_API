import logging

from fastapi import Depends, Request
from sqlalchemy import Connection
from strawberry.fastapi import BaseContext

from bcsd_api.auth import token as jwt_token
from bcsd_api.authz.client import AuthzClient
from bcsd_api.config import Settings
from bcsd_api.dependencies import (
    get_ans_repo,
    get_app_repo,
    get_authz,
    get_conn,
    get_form_repo,
    get_link_repo,
    get_member_repo,
    get_question_repo,
    get_recruit_repo,
    get_setting_repo,
    get_settings,
)
from bcsd_api.exception import Unauthorized
from bcsd_api.apply.pg_repository import PgAnswerRepository, PgApplicationRepository
from bcsd_api.form.pg_repository import PgFormRepository, PgQuestionRepository
from bcsd_api.member.pg_repository import PgMemberRepository
from bcsd_api.recruit.pg_repository import PgRecruitRepository
from bcsd_api.setting.pg_repository import PgSettingRepository
from bcsd_api.shorten.pg_repository import PgLinkRepository

logger = logging.getLogger(__name__)


class GqlContext(BaseContext):
    def __init__(
        self, conn, member_repo, link_repo,
        setting_repo, recruit_repo, form_repo, question_repo,
        app_repo, ans_repo, authz, user,
    ):
        self.conn = conn
        self.member_repo = member_repo
        self.link_repo = link_repo
        self.setting_repo = setting_repo
        self.recruit_repo = recruit_repo
        self.form_repo = form_repo
        self.question_repo = question_repo
        self.app_repo = app_repo
        self.ans_repo = ans_repo
        self.authz = authz
        self.user = user


def _try_auth(request: Request, settings: Settings) -> dict | None:
    raw = jwt_token.extract_raw(request, settings.cookie_name)
    if not raw:
        return None
    return jwt_token.decode_or_none(raw, settings.jwt_secret, settings.jwt_algorithm)


def _try_authz(settings: Settings) -> AuthzClient | None:
    try:
        return get_authz(settings)
    except Exception:
        logger.warning("SpiceDB unavailable, skipping authz")
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
    setting_repo: PgSettingRepository = Depends(get_setting_repo),
    recruit_repo: PgRecruitRepository = Depends(get_recruit_repo),
    form_repo: PgFormRepository = Depends(get_form_repo),
    question_repo: PgQuestionRepository = Depends(get_question_repo),
    app_repo: PgApplicationRepository = Depends(get_app_repo),
    ans_repo: PgAnswerRepository = Depends(get_ans_repo),
) -> GqlContext:
    user = _try_auth(request, settings)
    authz = _try_authz(settings)
    return GqlContext(
        conn=conn,
        member_repo=member_repo,
        link_repo=link_repo,
        setting_repo=setting_repo,
        recruit_repo=recruit_repo,
        form_repo=form_repo,
        question_repo=question_repo,
        app_repo=app_repo,
        ans_repo=ans_repo,
        authz=authz,
        user=user,
    )
