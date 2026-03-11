import gspread

from .helpers import add_column


def upgrade(spreadsheet: gspread.Spreadsheet) -> None:
    add_column(spreadsheet, "members", "email", "department")
    add_column(spreadsheet, "members", "department", "student_id")
