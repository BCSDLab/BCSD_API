from bcsd_api.sheets.client import SheetsClient

_LINKS = "links"
_CLICKS = "link_clicks"


class LinkRepository:
    def __init__(self, sheets: SheetsClient):
        self._sheets = sheets

    def find_all(self) -> list[dict]:
        return self._sheets.get_records(_LINKS)

    def find_by_id(self, link_id: str) -> dict | None:
        return self._sheets.find_row(_LINKS, "id", link_id)

    def find_by_code(self, code: str) -> dict | None:
        return self._sheets.find_row(_LINKS, "code", code)

    def create(self, row: dict) -> None:
        self._sheets.append_row(_LINKS, row)

    def update(self, link_id: str, column: str, value: str) -> None:
        self._sheets.update_cell(_LINKS, "id", link_id, column, value)

    def delete(self, link_id: str) -> None:
        self._sheets.delete_row(_LINKS, "id", link_id)

    def find_clicks(self, link_id: str) -> list[dict]:
        records = self._sheets.get_records(_CLICKS)
        return [r for r in records if r.get("link_id") == link_id]

    def add_click(self, row: dict) -> None:
        self._sheets.append_row(_CLICKS, row)

    def delete_clicks(self, link_id: str) -> None:
        self._sheets.delete_rows(_CLICKS, "link_id", link_id)
