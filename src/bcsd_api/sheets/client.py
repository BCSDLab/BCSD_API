import gspread
from google.oauth2.service_account import Credentials


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        creds = Credentials.from_service_account_file(
            credentials_file, scopes=_SCOPES
        )
        gc = gspread.authorize(creds)
        self._spreadsheet = gc.open_by_key(spreadsheet_id)

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
