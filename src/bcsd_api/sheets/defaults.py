from .client import SheetsClient


_DEFAULTS: dict[str, list[dict]] = {
    "tracks": [
        {"name": "Backend"},
        {"name": "Frontend"},
        {"name": "iOS"},
        {"name": "Android"},
        {"name": "UI/UX"},
        {"name": "Data Analysis"},
        {"name": "Game"},
    ],
}


def seed(sheets: SheetsClient) -> None:
    for sheet_name, rows in _DEFAULTS.items():
        if sheets.get_records(sheet_name):
            return
        for row in rows:
            sheets.append_row(sheet_name, row)
