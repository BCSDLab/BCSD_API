from fastapi import APIRouter, Depends

from bcsd_api.config import Settings
from bcsd_api.dependencies import get_settings, get_sheets
from bcsd_api.sheets.client import SheetsClient

from . import service
from .schema import (
    ConfirmEmailRequest,
    ConfirmEmailResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def post_login(
    body: LoginRequest,
    settings: Settings = Depends(get_settings),
    sheets: SheetsClient = Depends(get_sheets),
) -> LoginResponse:
    token = service.login(body.google_token, settings, sheets)
    return LoginResponse(access_token=token)


@router.post("/verify-email", response_model=MessageResponse)
async def post_verify(
    body: VerifyEmailRequest,
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await service.send_verify(body.email, settings)
    return MessageResponse(message="verification code sent")


@router.post("/confirm-email", response_model=ConfirmEmailResponse)
def post_confirm(body: ConfirmEmailRequest) -> ConfirmEmailResponse:
    result = service.confirm_verify(body.email, body.code)
    return ConfirmEmailResponse(verified=result)


@router.post("/register", response_model=LoginResponse)
def post_register(
    body: RegisterRequest,
    settings: Settings = Depends(get_settings),
    sheets: SheetsClient = Depends(get_sheets),
) -> LoginResponse:
    token = service.register(
        body.google_token, body.school_email, body.phone,
        body.firebase_token, body.track, settings, sheets,
    )
    return LoginResponse(access_token=token)
