import importlib
import logging
import pkgutil
from datetime import datetime

import gspread

from . import migrations
from ..timezone import KST

logger = logging.getLogger(__name__)
_SHEET = "_migrations"
_HEADERS = ["version", "name", "applied_at"]


def run(spreadsheet: gspread.Spreadsheet) -> None:
    sheet = _ensure_sheet(spreadsheet)
    applied = _applied(sheet)
    pending = _pending(_discover(), applied)
    for entry in pending:
        _apply(sheet, entry, spreadsheet)


def _ensure_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet(_SHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(_SHEET, rows=100, cols=len(_HEADERS))
        ws.append_row(_HEADERS)
        return ws


def _applied(sheet):
    records = sheet.get_all_records()
    return {str(r["version"]) for r in records}


def _discover():
    modules = pkgutil.iter_modules(migrations.__path__)
    entries = [_parse(m) for m in modules if m.name.startswith("V")]
    entries.sort(key=lambda x: x[0])
    return entries


def _parse(info):
    parts = info.name.split("_", 1)
    version = parts[0]
    name = _tail(parts)
    module = importlib.import_module(
        f".migrations.{info.name}", package=__package__,
    )
    return (version, name, module)


def _tail(parts):
    if len(parts) < 2:
        return ""
    return parts[1]


def _pending(discovered, applied):
    return [(v, n, m) for v, n, m in discovered if v not in applied]


def _apply(sheet, entry, spreadsheet):
    version, name, module = entry
    logger.info("Applying migration: %s_%s", version, name)
    module.upgrade(spreadsheet)
    _record(sheet, version, name)


def _record(sheet, version, name):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([version, name, now])
