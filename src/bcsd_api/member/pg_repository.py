from sqlalchemy import Connection

from bcsd_api.repository import BaseRepository
from bcsd_api.tables import members


class PgMemberRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn, members)
