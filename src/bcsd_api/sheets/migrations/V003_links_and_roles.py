import gspread

from .helpers import add_column, add_sheets


_SCHEMAS: dict[str, list[str]] = {
    "links": [
        "id", "code", "title", "description", "url",
        "creator_id", "created_at", "expires_at",
        "expired_at", "updated_at",
    ],
    "link_clicks": [
        "id", "link_id", "clicked_at", "referer", "user_agent",
    ],
}


def upgrade(spreadsheet: gspread.Spreadsheet) -> None:
    add_sheets(spreadsheet, _SCHEMAS)
    add_column(spreadsheet, "members", "team", "role")
