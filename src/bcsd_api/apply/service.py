from datetime import datetime

from bcsd_api.exception import BadRequest, Conflict, Forbidden, NotFound
from bcsd_api.form.pg_repository import PgFormRepository, PgQuestionRepository
from bcsd_api.id_gen import generate_id
from bcsd_api.member.pg_repository import PgMemberRepository
from bcsd_api.timezone import KST

from .pg_repository import PgAnswerRepository, PgApplicationRepository
from .schema import AnswerRequest, AnswerResponse, ApplicationResponse


def _now() -> str:
    return datetime.now(KST).isoformat()


def submit(
    app_repo: PgApplicationRepository,
    ans_repo: PgAnswerRepository,
    form_repo: PgFormRepository,
    q_repo: PgQuestionRepository,
    req_form_id: str,
    answers: list[AnswerRequest],
    member_id: str,
) -> ApplicationResponse:
    form = form_repo.find_by_id(req_form_id)
    if not form:
        raise NotFound(f"form {req_form_id} not found")
    _check_duplicate(app_repo, req_form_id, member_id)
    _validate_required(q_repo, req_form_id, answers)
    status = "심사_대기" if form["type"] == "conversion" else "납부_대기"
    return _create_app(app_repo, ans_repo, req_form_id, member_id, status, answers)


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
    app_repo, ans_repo, form_id, member_id, status, answers,
) -> ApplicationResponse:
    now = _now()
    app_id = generate_id("AP")
    row = {
        "id": app_id, "form_id": form_id,
        "member_id": member_id, "status": status,
        "submitted_at": now, "updated_at": now,
    }
    app_repo.create(row)
    saved = _save_answers(ans_repo, app_id, answers)
    return ApplicationResponse(**row, answers=saved)


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
        result.append(AnswerResponse(**row))
    return result


def list_applications(
    app_repo: PgApplicationRepository, ans_repo: PgAnswerRepository, form_id: str,
) -> list[ApplicationResponse]:
    rows = app_repo.find_by_form(form_id)
    return [_with_answers(ans_repo, r) for r in rows]


def my_applications(
    app_repo: PgApplicationRepository, ans_repo: PgAnswerRepository, member_id: str,
) -> list[ApplicationResponse]:
    rows = app_repo.find_by_member(member_id)
    return [_with_answers(ans_repo, r) for r in rows]


def get_application(
    app_repo: PgApplicationRepository, ans_repo: PgAnswerRepository, app_id: str,
) -> ApplicationResponse:
    row = app_repo.find_by_id(app_id)
    if not row:
        raise NotFound(f"application {app_id} not found")
    return _with_answers(ans_repo, row)


def _with_answers(ans_repo: PgAnswerRepository, row: dict) -> ApplicationResponse:
    answers = [AnswerResponse(**a) for a in ans_repo.find_by_application(row["id"])]
    return ApplicationResponse(**row, answers=answers)


def confirm_payment(
    app_repo: PgApplicationRepository, app_id: str, admin_id: str,
) -> ApplicationResponse:
    row = app_repo.find_by_id(app_id)
    if not row:
        raise NotFound(f"application {app_id} not found")
    if row["status"] != "납부_대기":
        raise BadRequest("application is not in payment pending status")
    app_repo.update_fields(app_id, {"status": "납부_완료", "updated_at": _now()})
    return ApplicationResponse(**app_repo.find_by_id(app_id))


def approve(
    app_repo: PgApplicationRepository,
    member_repo: PgMemberRepository,
    form_repo: PgFormRepository,
    app_ids: list[str],
    admin_id: str,
) -> list[ApplicationResponse]:
    now = _now()
    result = []
    for app_id in app_ids:
        row = app_repo.find_by_id(app_id)
        if not row:
            continue
        form = form_repo.find_by_id(row["form_id"])
        new_status = "Regular" if form and form["type"] == "conversion" else "Beginner"
        app_repo.update_fields(app_id, {
            "status": "승인", "approved_at": now,
            "approved_by": admin_id, "updated_at": now,
        })
        member_repo.update_status(row["member_id"], new_status)
        result.append(ApplicationResponse(**app_repo.find_by_id(app_id)))
    return result


def cancel(
    app_repo: PgApplicationRepository, app_id: str, member_id: str,
) -> None:
    row = app_repo.find_by_id(app_id)
    if not row:
        raise NotFound(f"application {app_id} not found")
    if row["member_id"] != member_id:
        raise Forbidden("cannot cancel another member's application")
    if row["status"] not in ("납부_대기", "심사_대기"):
        raise BadRequest("cannot cancel after payment or approval")
    app_repo.update_fields(app_id, {"status": "취소", "updated_at": _now()})
