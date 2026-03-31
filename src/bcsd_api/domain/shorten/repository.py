from sqlalchemy import Connection, delete, insert, select, update

from bcsd_api.common.repository import BaseRepository
from bcsd_api.common.tables import link_clicks, links

_MUTABLE = frozenset({
    "title", "description", "url",
    "expires_at", "expired_at", "updated_at",
})


class PgLinkRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn, links)

    def find_by_code(self, code: str) -> dict | None:
        row = self._conn.execute(
            select(links).where(links.c.code == code),
        ).first()
        if not row:
            return None
        return row._asdict()

    def create(self, row: dict) -> None:
        self._conn.execute(insert(links).values(**row))

    def update(self, link_id: str, column: str, value: str) -> None:
        if column not in _MUTABLE:
            return
        stmt = update(links).where(links.c.id == link_id)
        self._conn.execute(stmt.values(**{column: value}))

    def delete(self, link_id: str) -> None:
        self._conn.execute(delete(links).where(links.c.id == link_id))

    def find_clicks(self, link_id: str) -> list[dict]:
        stmt = select(link_clicks).where(link_clicks.c.link_id == link_id)
        return [row._asdict() for row in self._conn.execute(stmt)]

    def add_click(self, row: dict) -> None:
        self._conn.execute(insert(link_clicks).values(**row))

    def delete_clicks(self, link_id: str) -> None:
        self._conn.execute(
            delete(link_clicks).where(link_clicks.c.link_id == link_id),
        )
