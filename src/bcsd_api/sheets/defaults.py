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
    "statuses": [
        {"name": "Beginner"},
        {"name": "Regular"},
        {"name": "Mentor"},
    ],
    "payment_statuses": [
        {"name": "Unpaid"},
        {"name": "Paid"},
        {"name": "Exempt"},
    ],
}


def seed(sheets: SheetsClient) -> None:
    for sheet_name, rows in _DEFAULTS.items():
        if sheets.get_records(sheet_name):
            continue
        for row in rows:
            sheets.append_row(sheet_name, row)
