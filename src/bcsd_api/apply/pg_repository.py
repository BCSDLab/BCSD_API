from sqlalchemy import Connection, insert, select, update

from bcsd_api.repository import BaseRepository
from bcsd_api.tables import application_answers, applications


class PgApplicationRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn, applications)

    def find_by_form(self, form_id: str) -> list[dict]:
        stmt = select(applications).where(applications.c.form_id == form_id)
        return [row._asdict() for row in self._conn.execute(stmt)]

    def find_by_member(self, member_id: str) -> list[dict]:
        stmt = select(applications).where(applications.c.member_id == member_id)
        return [row._asdict() for row in self._conn.execute(stmt)]

    def find_by_form_member(self, form_id: str, member_id: str) -> dict | None:
        stmt = select(applications).where(
            applications.c.form_id == form_id,
            applications.c.member_id == member_id,
        )
        row = self._conn.execute(stmt).first()
        if not row:
            return None
        return row._asdict()

    def create(self, row: dict) -> None:
        self._conn.execute(insert(applications).values(**row))

    def update_fields(self, app_id: str, updates: dict) -> None:
        self._conn.execute(
            update(applications).where(applications.c.id == app_id).values(**updates),
        )


class PgAnswerRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn, application_answers)

    def find_by_application(self, application_id: str) -> list[dict]:
        stmt = select(application_answers).where(
            application_answers.c.application_id == application_id,
        )
        return [row._asdict() for row in self._conn.execute(stmt)]

    def create(self, row: dict) -> None:
        self._conn.execute(insert(application_answers).values(**row))
