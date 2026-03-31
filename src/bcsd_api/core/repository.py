from sqlalchemy import Connection, select


class BaseRepository:
    def __init__(self, conn: Connection, table):
        self._conn = conn
        self._table = table

    def find_all(self) -> list[dict]:
        rows = self._conn.execute(select(self._table))
        return [row._asdict() for row in rows]

    def find_by_id(self, id: str) -> dict | None:
        stmt = select(self._table).where(self._table.c.id == id)
        row = self._conn.execute(stmt).first()
        if not row:
            return None
        return row._asdict()
