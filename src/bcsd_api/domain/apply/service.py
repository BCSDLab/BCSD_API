from collections.abc import Sequence
from datetime import datetime

from bcsd_api.common.id_gen import generate_id
from bcsd_api.common.timezone import KST
from bcsd_api.domain.form.repository import PgFormRepository, PgQuestionRepository
from bcsd_api.domain.member.repository import PgMemberRepository
from bcsd_api.domain.setting.repository import PgSettingRepository
from bcsd_api.global_.exception import BadRequest, Conflict, Forbidden, NotFound
from .model import (
    AnswerRequest,
    AnswerResponse,
    ApplicationListResponse,
    MyApplicationResponse,
    PaymentInfoResponse,
)
from .repository import PgAnswerRepository, PgApplicationRepository


def _now() -> str:
    return datetime.now(KST).isoformat()


def submit(
    app_repo: PgApplicationRepository,
    ans_repo: PgAnswerRepository,
    form_repo: PgFormRepository,
    q_repo: PgQuestionRepository,
    form_id: str,
    answers: list[AnswerRequest],
    track: str,
    member_id: str,
) -> MyApplicationResponse:
    form = form_repo.find_by_id(form_id)
    if not form:
        raise NotFound(f"form {form_id} not found")
    _check_duplicate(app_repo, form_id, member_id)
    _validate_required(q_repo, form_id, answers)
    status = "pending_review" if form["type"] == "conversion" else "pending_payment"
    return _create_app(app_repo, ans_repo, form_id, member_id, track, status, answers)


def _check_duplicate(repo: PgApplicationRepository, form_id: str, member_id: str) -> None:
    if repo.find_by_form_member(form_id, member_id):
        raise Conflict("already applied to this form")


def _validate_required(
    q_repo: PgQuestionRepository, form_id: str, answers: list[AnswerRequest],
) -> None:
    questions = q_repo.find_by_form(form_id)
    required_ids = {q["id"] for q in questions if q["required"] == "true"}
    answered_ids = {a.question_id for a in answers}
    missing = required_ids - answered_ids
    if missing:
        raise BadRequest(f"missing required answers: {missing}")


def _create_app(
    app_repo, ans_repo, form_id, member_id, track, status, answers,
) -> MyApplicationResponse:
    now = _now()
    app_id = generate_id("AP")
    row = {
        "id": app_id, "form_id": form_id,
        "member_id": member_id, "track": track,
        "status": status, "submitted_at": now, "updated_at": now,
    }
    app_repo.create(row)
    saved = _save_answers(ans_repo, app_id, answers)
    return MyApplicationResponse(
        id=app_id, status=status, form_template_id=form_id,
        track=track, submitted_at=now, answers=saved,
    )


def _save_answers(
    ans_repo: PgAnswerRepository, app_id: str, answers: list[AnswerRequest],
) -> list[AnswerResponse]:
    result = []
    for a in answers:
        row = {
            "id": generate_id("AA"),
            "application_id": app_id,
            "question_id": a.question_id,
            "value": a.value,
        }
        ans_repo.create(row)
        result.append(AnswerResponse(question_id=a.question_id, value=a.value))
    return result


def my_application(
    app_repo: PgApplicationRepository,
    ans_repo: PgAnswerRepository,
    member_id: str,
) -> MyApplicationResponse | None:
    rows = app_repo.find_by_member(member_id)
    if not rows:
        return None
    row = rows[0]
    answers = _get_answers(ans_repo, row["id"])
    return MyApplicationResponse(
        id=row["id"], status=row["status"],
        form_template_id=row["form_id"],
        track=row.get("track", ""),
        submitted_at=row.get("submitted_at", ""),
        answers=answers,
    )


def _get_answers(ans_repo: PgAnswerRepository, app_id: str) -> list[AnswerResponse]:
    rows = ans_repo.find_by_application(app_id)
    return [AnswerResponse(question_id=r["question_id"], value=r["value"]) for r in rows]


def list_applications(
    app_repo: PgApplicationRepository,
    member_repo: PgMemberRepository,
) -> list[ApplicationListResponse]:
    rows = app_repo.find_all()
    return [_to_list_item(member_repo, r) for r in rows]


def _to_list_item(member_repo: PgMemberRepository, row: dict) -> ApplicationListResponse:
    member = member_repo.find_by_id(row["member_id"])
    name = member["name"] if member else row["member_id"]
    email = member["email"] if member else ""
    return ApplicationListResponse(
        id=row["id"], applicant_name=name,
        applicant_email=email, track=row.get("track", ""),
        status=row["status"], submitted_at=row.get("submitted_at", ""),
    )


def get_application(
    app_repo: PgApplicationRepository,
    ans_repo: PgAnswerRepository,
    app_id: str,
) -> MyApplicationResponse:
    row = app_repo.find_by_id(app_id)
    if not row:
        raise NotFound(f"application {app_id} not found")
    answers = _get_answers(ans_repo, row["id"])
    return MyApplicationResponse(
        id=row["id"], status=row["status"],
        form_template_id=row["form_id"],
        track=row.get("track", ""),
        submitted_at=row.get("submitted_at", ""),
        answers=answers,
    )


def confirm_payment(
    app_repo: PgApplicationRepository, app_id: str,
) -> MyApplicationResponse:
    row = app_repo.find_by_id(app_id)
    if not row:
        raise NotFound(f"application {app_id} not found")
    if row["status"] != "pending_payment":
        raise BadRequest("not in pending_payment status")
    app_repo.update_fields(app_id, {"status": "paid", "updated_at": _now()})
    row["status"] = "paid"
    return _row_to_my_app(row)


def approve(
    app_repo: PgApplicationRepository,
    member_repo: PgMemberRepository,
    form_repo: PgFormRepository,
    app_ids: Sequence[str],
    admin_id: str,
    authz=None,
) -> list[str]:
    now = _now()
    approved = []
    for app_id in app_ids:
        row = app_repo.find_by_id(app_id)
        if not row:
            continue
        form = form_repo.find_by_id(row["form_id"])
        new_status = "Regular" if form and form["type"] == "conversion" else "Beginner"
        app_repo.update_fields(app_id, {
            "status": "approved", "approved_at": now,
            "approved_by": admin_id, "updated_at": now,
        })
        member_repo.update_status(row["member_id"], new_status)
        _add_org_relation(authz, row["member_id"], new_status)
        approved.append(app_id)
    return approved


def _add_org_relation(authz, member_id: str, status: str) -> None:
    if not authz:
        return
    from bcsd_api.common.constants import ORG_ID, STATUS_RELATION

    relation = STATUS_RELATION.get(status)
    if not relation:
        return
    authz.add_relation("organization", ORG_ID, relation, member_id)


def cancel(
    app_repo: PgApplicationRepository,
    ans_repo: PgAnswerRepository,
    app_id: str,
    member_id: str,
) -> MyApplicationResponse:
    row = app_repo.find_by_id(app_id)
    if not row:
        raise NotFound(f"application {app_id} not found")
    if row["member_id"] != member_id:
        raise Forbidden("cannot cancel another member's application")
    if row["status"] not in ("pending_payment", "pending_review"):
        raise BadRequest("cannot cancel after payment or approval")
    app_repo.update_fields(app_id, {"status": "cancelled", "updated_at": _now()})
    row["status"] = "cancelled"
    answers = _get_answers(ans_repo, app_id)
    return MyApplicationResponse(
        id=row["id"], status="cancelled",
        form_template_id=row["form_id"],
        track=row.get("track", ""),
        submitted_at=row.get("submitted_at", ""),
        answers=answers,
    )


def _row_to_my_app(row: dict) -> MyApplicationResponse:
    return MyApplicationResponse(
        id=row["id"], status=row["status"],
        form_template_id=row["form_id"],
        track=row.get("track", ""),
        submitted_at=row.get("submitted_at", ""),
        answers=[],
    )


def get_payment_info(setting_repo: PgSettingRepository) -> PaymentInfoResponse | None:
    bank = setting_repo.get("payment_bank")
    if not bank:
        return None
    return PaymentInfoResponse(
        bank=bank,
        account=setting_repo.get("payment_account") or "",
        amount=int(setting_repo.get("payment_amount") or "10000"),
        holder=setting_repo.get("payment_holder") or "",
    )
