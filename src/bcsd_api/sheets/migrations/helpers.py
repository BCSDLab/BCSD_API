def add_sheet(spreadsheet, name, headers):
    existing = {ws.title for ws in spreadsheet.worksheets()}
    if name in existing:
        return
    ws = spreadsheet.add_worksheet(name, rows=1000, cols=len(headers))
    ws.append_row(headers)


def add_sheets(spreadsheet, schemas: dict[str, list[str]]):
    existing = {ws.title for ws in spreadsheet.worksheets()}
    for name, headers in schemas.items():
        if name in existing:
            continue
        ws = spreadsheet.add_worksheet(name, rows=1000, cols=len(headers))
        ws.append_row(headers)


def seed_sheet(spreadsheet, name, rows: list[dict]):
    ws = spreadsheet.worksheet(name)
    if ws.get_all_records():
        return
    headers = ws.row_values(1)
    for row in rows:
        values = [row.get(h, "") for h in headers]
        ws.append_row(values)


def add_column(spreadsheet, sheet_name, after, name):
    ws = spreadsheet.worksheet(sheet_name)
    headers = ws.row_values(1)
    if name in headers:
        return
    position = headers.index(after) + 1
    body = {"requests": [_dimension_body(ws.id, position)]}
    spreadsheet.batch_update(body)
    ws.update_cell(1, position + 1, name)


def _dimension_body(sheet_id, position):
    return {
        "insertDimension": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": position,
                "endIndex": position + 1,
            },
        },
    }
