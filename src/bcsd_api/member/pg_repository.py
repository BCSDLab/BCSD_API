from sqlalchemy import Connection, select

from bcsd_api.tables import members


class PgMemberRepository:
    def __init__(self, conn: Connection):
        self._conn = conn

    def find_all(self) -> list[dict]:
        rows = self._conn.execute(select(members))
        return [row._asdict() for row in rows]

    def find_by_id(self, member_id: str) -> dict | None:
        stmt = select(members).where(members.c.id == member_id)
        row = self._conn.execute(stmt).first()
        if not row:
            return None
        return row._asdict()
