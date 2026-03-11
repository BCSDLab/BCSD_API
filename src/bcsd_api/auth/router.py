from fastapi import APIRouter, Depends, Response

from bcsd_api.config import Settings
from bcsd_api.dependencies import (
    current_user, get_email_sender, get_settings, get_sheets,
)
from bcsd_api.email.sender import EmailSender
from bcsd_api.sheets.client import SheetsClient

from . import service
from .schema import (
    ConfirmEmailRequest,
    ConfirmEmailResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    MessageResponse,
    RegisterRequest,
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
    sheets: SheetsClient = Depends(get_sheets),
) -> LoginResponse:
    token = service.login(body.google_token, settings, sheets)
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


@router.post("/register", response_model=LoginResponse)
def post_register(
    body: RegisterRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    sheets: SheetsClient = Depends(get_sheets),
) -> LoginResponse:
    token = service.register(
        body.google_token, body.name, body.department,
        body.student_id, body.school_email,
        body.phone, body.track, settings, sheets,
    )
    _set_cookie(response, token, settings)
    return LoginResponse(access_token=token)


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
