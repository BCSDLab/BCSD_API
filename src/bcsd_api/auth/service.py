from datetime import datetime

from sqlalchemy import Connection, select

from bcsd_api.config import Settings
from bcsd_api.email.sender import EmailSender
from bcsd_api.exception import Conflict, Unauthorized
from bcsd_api.id_gen import generate_id
from bcsd_api.member.pg_repository import PgMemberRepository
from bcsd_api.tables import app_settings
from bcsd_api.timezone import KST

from . import google as google_auth
from . import token as jwt_token
from . import verify


def login(
    google_token: str, settings: Settings, repo: PgMemberRepository,
) -> str:
    profile = google_auth.verify_token(google_token, settings.google_client_id)
    member = repo.find_by_provider("google", profile["email"])
    if not member:
        raise Unauthorized("member not found, registration required")
    payload = {"sub": member["id"], "email": profile["email"]}
    return _issue_jwt(payload, settings)


def send_verify(email: str, sender: EmailSender) -> None:
    verify.send_code(email, sender)


def confirm_verify(email: str, code: str) -> bool:
    return verify.confirm_code(email, code)


def register(
    google_token: str, name: str, department: str,
    student_id: str, school_email: str, phone: str,
    track: str | None, grade: str,
    settings: Settings, repo: PgMemberRepository, conn: Connection,
) -> tuple[str, str]:
    profile = google_auth.verify_token(google_token, settings.google_client_id)
    _check_google(profile["email"], repo)
    _check_school_email(school_email, repo)
    member_id = generate_id("M")
    now = _now_kst()
    row = _build_row(
        member_id, name, profile["email"],
        department, student_id, school_email, phone, track, grade,
    )
    repo.create(row)
    repo.add_account(generate_id("MA"), member_id, "google", profile["email"], now)
    routing = _resolve_routing(grade, conn)
    token = _issue_jwt({"sub": member_id, "email": profile["email"]}, settings)
    return token, routing


def _issue_jwt(payload: dict, settings: Settings) -> str:
    return jwt_token.create_token(
        payload, settings.jwt_secret,
        settings.jwt_algorithm, settings.jwt_expire_minutes,
    )


def _check_google(email: str, repo: PgMemberRepository) -> None:
    if repo.find_account("google", email):
        raise Conflict("이미 가입된 Google 계정입니다")


def _check_school_email(school_email: str, repo: PgMemberRepository) -> None:
    if repo.find_by_school_email(school_email):
        raise Conflict("이미 가입된 학교 이메일입니다")


def _now_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")


def _build_row(
    member_id: str, name: str, email: str,
    department: str, student_id: str,
    school_email: str, phone: str, track: str | None, grade: str,
) -> dict:
    now = _now_kst()
    return {
        "id": member_id, "name": name, "email": email,
        "department": department, "student_id": student_id,
        "school_email": school_email, "phone": phone,
        "track": track or "", "grade": grade,
        "status": "Beginner", "team": "", "payment_status": "미납",
        "join_date": now, "last_updated": now,
    }


_GRADE_MAP = {"1학년": 1, "2학년": 2, "3학년": 3, "4학년": 4, "대학원": 5}


def _resolve_routing(grade: str, conn: Connection) -> str:
    threshold = _grade_threshold(conn)
    level = _GRADE_MAP.get(grade, 1)
    if level >= threshold:
        return "conversion"
    return "beginner"


def _grade_threshold(conn: Connection) -> int:
    row = conn.execute(
        select(app_settings.c.value).where(app_settings.c.key == "grade_threshold"),
    ).first()
    if not row:
        return 3
    return int(row[0])
