from sqlalchemy import Connection, insert, select, update

from bcsd_api.common.repository import BaseRepository
from bcsd_api.common.tables import member_accounts, members


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

    def find_by_provider(self, provider: str, provider_id: str) -> dict | None:
        stmt = (
            select(members)
            .join(member_accounts, member_accounts.c.member_id == members.c.id)
            .where(
                member_accounts.c.provider == provider,
                member_accounts.c.provider_id == provider_id,
            )
        )
        row = self._conn.execute(stmt).first()
        if not row:
            return None
        return row._asdict()

    def create(self, row: dict) -> None:
        self._conn.execute(insert(members).values(**row))

    def add_account(self, account_id: str, member_id: str, provider: str, provider_id: str, created_at: str) -> None:
        self._conn.execute(insert(member_accounts).values(
            id=account_id, member_id=member_id,
            provider=provider, provider_id=provider_id,
            created_at=created_at,
        ))

    def find_account(self, provider: str, provider_id: str) -> dict | None:
        row = self._conn.execute(
            select(member_accounts).where(
                member_accounts.c.provider == provider,
                member_accounts.c.provider_id == provider_id,
            ),
        ).first()
        if not row:
            return None
        return row._asdict()

    def update_status(self, member_id: str, status: str) -> None:
        self._conn.execute(
            update(members).where(members.c.id == member_id).values(status=status),
        )
