from sqlalchemy import Connection, insert, select, update

from bcsd_api.common.repository import BaseRepository
from bcsd_api.common.tables import recruitment_periods


class PgRecruitRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn, recruitment_periods)

    def find_active(self, type: str | None = None) -> list[dict]:
        stmt = select(recruitment_periods).where(
            recruitment_periods.c.is_active == "true",
        )
        if type:
            stmt = stmt.where(recruitment_periods.c.type == type)
        return [row._asdict() for row in self._conn.execute(stmt)]

    def create(self, row: dict) -> None:
        self._conn.execute(insert(recruitment_periods).values(**row))

    def update_fields(self, period_id: str, updates: dict) -> None:
        self._conn.execute(
            update(recruitment_periods)
            .where(recruitment_periods.c.id == period_id)
            .values(**updates),
        )
