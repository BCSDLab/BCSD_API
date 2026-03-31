from datetime import datetime

from bcsd_api.global_.exception import NotFound
from bcsd_api.common.id_gen import generate_id
from bcsd_api.common.timezone import KST

from .repository import PgFormRepository, PgQuestionRepository
from .model import (
    CreateFormRequest,
    FormResponse,
    QuestionRequest,
    QuestionResponse,
    UpdateFormRequest,
)


def _now() -> str:
    return datetime.now(KST).isoformat()


def create_form(
    form_repo: PgFormRepository,
    q_repo: PgQuestionRepository,
    req: CreateFormRequest,
    creator_id: str,
) -> FormResponse:
    now = _now()
    form_id = generate_id("F")
    row = {
        "id": form_id, "title": req.title,
        "description": req.description or "",
        "recruitment_id": req.recruitment_id,
        "type": req.type, "is_active": "true",
        "created_by": creator_id,
        "created_at": now, "updated_at": now,
    }
    form_repo.create(row)
    questions = _save_questions(q_repo, form_id, req.questions)
    return FormResponse(**row, questions=questions)


def update_form(
    form_repo: PgFormRepository,
    q_repo: PgQuestionRepository,
    form_id: str,
    req: UpdateFormRequest,
) -> FormResponse:
    _get_or_raise(form_repo, form_id)
    updates = {}
    if req.title is not None:
        updates["title"] = req.title
    if req.description is not None:
        updates["description"] = req.description
    if req.is_active is not None:
        updates["is_active"] = req.is_active
    updates["updated_at"] = _now()
    form_repo.update_fields(form_id, updates)
    if req.questions is not None:
        q_repo.delete_by_form(form_id)
        _save_questions(q_repo, form_id, req.questions)
    return get_form(form_repo, q_repo, form_id)


def get_form(
    form_repo: PgFormRepository, q_repo: PgQuestionRepository, form_id: str,
) -> FormResponse:
    row = _get_or_raise(form_repo, form_id)
    questions = [QuestionResponse(**q) for q in q_repo.find_by_form(form_id)]
    return FormResponse(**row, questions=questions)


def list_forms(
    form_repo: PgFormRepository,
    q_repo: PgQuestionRepository,
    recruitment_id: str | None = None,
) -> list[FormResponse]:
    if recruitment_id:
        rows = form_repo.find_by_recruitment(recruitment_id)
    else:
        rows = form_repo.find_all()
    result = []
    for row in rows:
        qs = [QuestionResponse(**q) for q in q_repo.find_by_form(row["id"])]
        result.append(FormResponse(**row, questions=qs))
    return result


def _get_or_raise(form_repo: PgFormRepository, form_id: str) -> dict:
    row = form_repo.find_by_id(form_id)
    if not row:
        raise NotFound(f"form {form_id} not found")
    return row


def _save_questions(
    q_repo: PgQuestionRepository, form_id: str, questions: list[QuestionRequest],
) -> list[QuestionResponse]:
    result = []
    for i, q in enumerate(questions):
        row = {
            "id": generate_id("FQ"), "form_id": form_id,
            "label": q.label, "type": q.type,
            "options": q.options or "",
            "required": q.required,
            "sort_order": q.sort_order or i,
            "created_at": _now(),
        }
        q_repo.create(row)
        result.append(QuestionResponse(**row))
    return result
