import gspread

from .helpers import add_sheets, seed_sheet

_SCHEMAS: dict[str, list[str]] = {
    "members": [
        "id", "name", "email", "school_email", "phone",
        "status", "track", "team", "join_date",
        "payment_status", "last_updated",
    ],
    "fees": [
        "id", "member_id", "amount", "paid_date",
        "payment_method", "notes", "semester", "last_updated",
    ],
    "groups": [
        "id", "name", "type", "parent_id",
        "size", "leader_email", "last_updated",
    ],
    "events": [
        "id", "title", "date", "type",
        "organizer", "attendees", "notes",
    ],
    "workflow_logs": [
        "timestamp", "workflow_name", "status",
        "input_data", "output_data", "error_message",
    ],
    "tracks": ["name"],
    "statuses": ["name"],
    "payment_statuses": ["name"],
}

_SEEDS: dict[str, list[dict]] = {
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
        {"name": "미납"},
        {"name": "납부"},
        {"name": "면제"},
    ],
}


def upgrade(spreadsheet: gspread.Spreadsheet) -> None:
    add_sheets(spreadsheet, _SCHEMAS)
    for name, rows in _SEEDS.items():
        seed_sheet(spreadsheet, name, rows)
    _cleanup(spreadsheet)


def _cleanup(spreadsheet):
    titles = {ws.title for ws in spreadsheet.worksheets()}
    if "시트1" not in titles:
        return
    if len(spreadsheet.worksheets()) < 2:
        return
    spreadsheet.del_worksheet(spreadsheet.worksheet("시트1"))
