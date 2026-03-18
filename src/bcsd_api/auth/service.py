from datetime import datetime

from bcsd_api.config import Settings
from bcsd_api.email.sender import EmailSender
from bcsd_api.exception import Conflict, Unauthorized
from bcsd_api.id_gen import generate_id
from bcsd_api.sheets.client import SheetsClient

from . import google as google_auth
from . import token as jwt_token
from . import verify
from bcsd_api.timezone import KST


def login(google_token: str, settings: Settings, sheets: SheetsClient) -> str:
    profile = google_auth.verify_token(google_token, settings.google_client_id)
    member = sheets.find_row("members", "email", profile["email"])
    if not member:
        raise Unauthorized("member not found, registration required")
    payload = {"sub": member["id"], "email": profile["email"]}
    return _issue_jwt(payload, settings)


def send_verify(email: str, sender: EmailSender) -> None:
    verify.send_code(email, sender)


def confirm_verify(email: str, code: str) -> bool:
    return verify.confirm_code(email, code)


def register(
    google_token: str,
    name: str,
    department: str,
    student_id: str,
    school_email: str,
    phone: str,
    track: str,
    settings: Settings,
    sheets: SheetsClient,
) -> str:
    profile = google_auth.verify_token(google_token, settings.google_client_id)
    _check_duplicate(profile["email"], sheets)
    member_id = generate_id("M")
    row = _build_row(
        member_id, name, profile["email"],
        department, student_id, school_email, phone, track,
    )
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


def _now_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")


def _build_row(
    member_id: str, name: str, email: str,
    department: str, student_id: str,
    school_email: str, phone: str, track: str,
) -> dict:
    now = _now_kst()
    base = _base_fields(member_id, name, email)
    extra = {
        "department": department, "student_id": student_id,
        "school_email": school_email, "phone": phone, "track": track,
    }
    timestamps = {"join_date": now, "last_updated": now}
    return {**base, **extra, **timestamps}


def _base_fields(member_id: str, name: str, email: str) -> dict:
    return {
        "id": member_id,
        "name": name,
        "email": email,
        "status": "Beginner",
        "team": "",
        "payment_status": "미납",
    }
