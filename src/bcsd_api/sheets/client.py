import gspread
from google.oauth2.service_account import Credentials


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


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
}


class SheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        creds = Credentials.from_service_account_file(
            credentials_file, scopes=_SCOPES
        )
        gc = gspread.authorize(creds)
        self._spreadsheet = gc.open_by_key(spreadsheet_id)

    def init_sheets(self) -> None:
        existing = {ws.title for ws in self._spreadsheet.worksheets()}
        for name, headers in _SCHEMAS.items():
            if name in existing:
                continue
            ws = self._spreadsheet.add_worksheet(name, rows=1000, cols=len(headers))
            ws.append_row(headers)
        self._delete_default(existing)

    def _delete_default(self, existing: set[str]) -> None:
        default = "시트1"
        if default not in existing:
            return
        if len(self._spreadsheet.worksheets()) < 2:
            return
        self._spreadsheet.del_worksheet(self._spreadsheet.worksheet(default))

    def get_records(self, sheet_name: str) -> list[dict]:
        worksheet = self._spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_records()

    def find_row(self, sheet_name: str, column: str, value: str) -> dict | None:
        records = self.get_records(sheet_name)
        for record in records:
            if str(record.get(column, "")) == value:
                return record
        return None

    def append_row(self, sheet_name: str, row: dict) -> None:
        worksheet = self._spreadsheet.worksheet(sheet_name)
        headers = worksheet.row_values(1)
        values = [row.get(h, "") for h in headers]
        worksheet.append_row(values)

    def _find_index(self, records: list[dict], column: str, value: str) -> int | None:
        for idx, record in enumerate(records):
            if str(record.get(column, "")) == value:
                return idx
        return None

    def update_cell(
        self, sheet_name: str, column: str, value: str, target_col: str, new_value: str
    ) -> None:
        worksheet = self._spreadsheet.worksheet(sheet_name)
        records = worksheet.get_all_records()
        idx = self._find_index(records, column, value)
        if idx is None:
            return
        headers = worksheet.row_values(1)
        col_idx = headers.index(target_col) + 1
        worksheet.update_cell(idx + 2, col_idx, new_value)
