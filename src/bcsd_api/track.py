from fastapi import APIRouter, Depends

from bcsd_api.dependencies import get_sheets
from bcsd_api.sheets.client import SheetsClient

router = APIRouter(prefix="/v1/tracks", tags=["tracks"])


@router.get("", response_model=list[str])
def get_tracks(sheets: SheetsClient = Depends(get_sheets)) -> list[str]:
    records = sheets.get_records("tracks")
    return [r["name"] for r in records]
