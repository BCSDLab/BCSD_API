from sqlalchemy import Connection, select

from bcsd_api.common.tables import app_settings


class PgSettingRepository:
    def __init__(self, conn: Connection):
        self._conn = conn

    def get(self, key: str) -> str | None:
        row = self._conn.execute(
            select(app_settings.c.value).where(app_settings.c.key == key),
        ).first()
        if not row:
            return None
        return row[0]

    def upsert(self, key: str, value: str, updated_by: str) -> None:
        from datetime import datetime

        from bcsd_api.common.timezone import KST

        now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        existing = self.get(key)
        if existing is not None:
            self._conn.execute(
                app_settings.update().where(app_settings.c.key == key).values(
                    value=value, updated_at=now, updated_by=updated_by,
                ),
            )
            return
        self._conn.execute(
            app_settings.insert().values(
                key=key, value=value, updated_at=now, updated_by=updated_by,
            ),
        )
