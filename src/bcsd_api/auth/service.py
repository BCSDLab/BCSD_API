from datetime import datetime, timezone, timedelta

import firebase_admin.auth as firebase_auth

from bcsd_api.config import Settings
from bcsd_api.exception import BadRequest, Conflict, Unauthorized
from bcsd_api.id_gen import generate_id
from bcsd_api.sheets.client import SheetsClient

from . import google as google_auth
from . import token as jwt_token
from . import verify

_KST = timezone(timedelta(hours=9))


def login(google_token: str, settings: Settings, sheets: SheetsClient) -> str:
    profile = google_auth.verify_token(google_token, settings.google_client_id)
    member = sheets.find_row("members", "email", profile["email"])
    if not member:
        raise Unauthorized("member not found, registration required")
    payload = {"sub": member["id"], "email": profile["email"]}
    return _issue_jwt(payload, settings)


async def send_verify(email: str, settings: Settings) -> None:
    await verify.send_code(
        email, settings.smtp_host, settings.smtp_port,
        settings.smtp_user, settings.smtp_password,
    )


def confirm_verify(email: str, code: str) -> bool:
    return verify.confirm_code(email, code)


def register(
    google_token: str,
    school_email: str,
    phone: str,
    firebase_token: str,
    track: str,
    settings: Settings,
    sheets: SheetsClient,
) -> str:
    profile = google_auth.verify_token(google_token, settings.google_client_id)
    _check_duplicate(profile["email"], sheets)
    _verify_firebase(firebase_token)
    member_id = generate_id("M")
    row = _build_row(member_id, profile, school_email, phone, track)
    sheets.append_row("members", row)
    payload = {"sub": member_id, "email": profile["email"]}
    return _issue_jwt(payload, settings)


def _issue_jwt(payload: dict, settings: Settings) -> str:
    return jwt_token.create_token(
        payload, settings.jwt_secret,
        settings.jwt_algorithm, settings.jwt_expire_minutes,
    )


def _check_duplicate(email: str, sheets: SheetsClient) -> None:
    if sheets.find_row("members", "email", email):
        raise Conflict("member already registered")


def _verify_firebase(firebase_token: str) -> None:
    try:
        firebase_auth.verify_id_token(firebase_token)
    except Exception:
        raise BadRequest("invalid firebase phone token")


def _now_kst() -> str:
    return datetime.now(_KST).strftime("%Y-%m-%d %H:%M:%S")


def _build_row(
    member_id: str, profile: dict, school_email: str, phone: str, track: str
) -> dict:
    now = _now_kst()
    base = _base_fields(member_id, profile["name"], profile["email"])
    extra = {"school_email": school_email, "phone": phone, "track": track}
    timestamps = {"join_date": now, "last_updated": now}
    return {**base, **extra, **timestamps}


def _base_fields(member_id: str, name: str, email: str) -> dict:
    return {
        "id": member_id,
        "name": name,
        "email": email,
        "status": "Beginner",
        "team": "",
        "payment_status": "Unpaid",
    }
