from fastapi import APIRouter, Depends
from sqlalchemy import Connection, select

from bcsd_api.dependencies import get_conn
from bcsd_api.tables import tracks

router = APIRouter(prefix="/v1/tracks", tags=["tracks"])


@router.get("", response_model=list[str])
def get_tracks(conn: Connection = Depends(get_conn)) -> list[str]:
    rows = conn.execute(select(tracks.c.name))
    return [row.name for row in rows]
