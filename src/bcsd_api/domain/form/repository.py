from sqlalchemy import Connection, delete, insert, select, update

from bcsd_api.common.repository import BaseRepository
from bcsd_api.common.tables import form_questions, forms


class PgFormRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn, forms)

    def find_by_recruitment(self, recruitment_id: str) -> list[dict]:
        stmt = select(forms).where(forms.c.recruitment_id == recruitment_id)
        return [row._asdict() for row in self._conn.execute(stmt)]

    def create(self, row: dict) -> None:
        self._conn.execute(insert(forms).values(**row))

    def update_fields(self, form_id: str, updates: dict) -> None:
        self._conn.execute(
            update(forms).where(forms.c.id == form_id).values(**updates),
        )


class PgQuestionRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn, form_questions)

    def find_by_form(self, form_id: str) -> list[dict]:
        stmt = (
            select(form_questions)
            .where(form_questions.c.form_id == form_id)
            .order_by(form_questions.c.sort_order)
        )
        return [row._asdict() for row in self._conn.execute(stmt)]

    def create(self, row: dict) -> None:
        self._conn.execute(insert(form_questions).values(**row))

    def delete_by_form(self, form_id: str) -> None:
        self._conn.execute(
            delete(form_questions).where(form_questions.c.form_id == form_id),
        )
