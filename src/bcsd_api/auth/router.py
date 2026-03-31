from fastapi import APIRouter, Depends, Response
from sqlalchemy import Connection

from bcsd_api.core.config import Settings
from bcsd_api.dependencies import (
    current_user, get_conn, get_email_sender, get_member_repo, get_settings,
)
from bcsd_api.email.sender import EmailSender
from bcsd_api.member.pg_repository import PgMemberRepository

from . import service
from .schema import (
    ConfirmEmailRequest,
    ConfirmEmailResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _set_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        max_age=settings.jwt_expire_minutes * 60,
    )


@router.post("/login", response_model=LoginResponse)
def post_login(
    body: LoginRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    repo: PgMemberRepository = Depends(get_member_repo),
) -> LoginResponse:
    token = service.login(body.google_token, settings, repo)
    _set_cookie(response, token, settings)
    return LoginResponse(access_token=token)


@router.post("/verify-email", response_model=MessageResponse)
def post_verify(
    body: VerifyEmailRequest,
    sender: EmailSender = Depends(get_email_sender),
) -> MessageResponse:
    service.send_verify(body.email, sender)
    return MessageResponse(message="verification code sent")


@router.post("/confirm-email", response_model=ConfirmEmailResponse)
def post_confirm(body: ConfirmEmailRequest) -> ConfirmEmailResponse:
    result = service.confirm_verify(body.email, body.code)
    return ConfirmEmailResponse(verified=result)


@router.post("/register", response_model=RegisterResponse)
def post_register(
    body: RegisterRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    repo: PgMemberRepository = Depends(get_member_repo),
    conn: Connection = Depends(get_conn),
) -> RegisterResponse:
    token, routing = service.register(
        body.google_token, body.name, body.department,
        body.student_id, body.school_email,
        body.phone, body.track, body.grade,
        settings, repo, conn,
    )
    _set_cookie(response, token, settings)
    return RegisterResponse(access_token=token, routing=routing)


@router.get("/me", response_model=MeResponse)
def get_me(user: dict = Depends(current_user)) -> MeResponse:
    return MeResponse(id=user["sub"], email=user["email"])


@router.post("/logout", response_model=MessageResponse)
def post_logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    response.delete_cookie(
        key=settings.cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
    return MessageResponse(message="logged out")
