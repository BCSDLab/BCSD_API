from sqlalchemy import Connection, insert, select, update

from bcsd_api.repository import BaseRepository
from bcsd_api.tables import members


class PgMemberRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn, members)

    def find_by_email(self, email: str) -> dict | None:
        row = self._conn.execute(
            select(members).where(members.c.email == email),
        ).first()
        if not row:
            return None
        return row._asdict()

    def find_by_school_email(self, school_email: str) -> dict | None:
        row = self._conn.execute(
            select(members).where(members.c.school_email == school_email),
        ).first()
        if not row:
            return None
        return row._asdict()

    def create(self, row: dict) -> None:
        self._conn.execute(insert(members).values(**row))

    def update_status(self, member_id: str, status: str) -> None:
        self._conn.execute(
            update(members).where(members.c.id == member_id).values(status=status),
        )
