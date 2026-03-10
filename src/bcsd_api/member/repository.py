from bcsd_api.sheets.client import SheetsClient

_SHEET = "members"


class MemberRepository:
    def __init__(self, sheets: SheetsClient):
        self._sheets = sheets

    def find_all(self) -> list[dict]:
        return self._sheets.get_records(_SHEET)

    def find_by_id(self, member_id: str) -> dict | None:
        return self._sheets.find_row(_SHEET, "id", member_id)
