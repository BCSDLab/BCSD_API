from datetime import datetime

from bcsd_api.exception import NotFound
from bcsd_api.core.id_gen import generate_id
from bcsd_api.core.timezone import KST

from .pg_repository import PgRecruitRepository
from .schema import CreatePeriodRequest, PeriodResponse, UpdatePeriodRequest


def _now() -> str:
    return datetime.now(KST).isoformat()


def create_period(
    repo: PgRecruitRepository, req: CreatePeriodRequest, creator_id: str,
) -> PeriodResponse:
    now = _now()
    row = {
        "id": generate_id("RP"), "title": req.title,
        "type": req.type, "start_date": req.start_date,
        "end_date": req.end_date, "is_active": "true",
        "created_by": creator_id, "created_at": now, "updated_at": now,
    }
    repo.create(row)
    return PeriodResponse(**row)


def update_period(
    repo: PgRecruitRepository, period_id: str, req: UpdatePeriodRequest,
) -> PeriodResponse:
    row = _get_or_raise(repo, period_id)
    updates = req.model_dump(exclude_none=True)
    updates["updated_at"] = _now()
    repo.update_fields(period_id, updates)
    row.update(updates)
    return PeriodResponse(**row)


def list_periods(repo: PgRecruitRepository) -> list[PeriodResponse]:
    return [PeriodResponse(**r) for r in repo.find_all()]


def get_period(repo: PgRecruitRepository, period_id: str) -> PeriodResponse:
    return PeriodResponse(**_get_or_raise(repo, period_id))


def active_period(repo: PgRecruitRepository, type: str) -> PeriodResponse | None:
    rows = repo.find_active(type)
    if not rows:
        return None
    return PeriodResponse(**rows[0])


def _get_or_raise(repo: PgRecruitRepository, period_id: str) -> dict:
    row = repo.find_by_id(period_id)
    if not row:
        raise NotFound(f"recruitment period {period_id} not found")
    return row
