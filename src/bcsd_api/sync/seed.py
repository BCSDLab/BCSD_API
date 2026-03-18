import logging

from sqlalchemy.dialects.postgresql import insert

from bcsd_api.config import Settings
from bcsd_api.database import create_engine
from bcsd_api.sheets.client import SheetsClient
from bcsd_api.tables import (
    events,
    fees,
    groups,
    link_clicks,
    links,
    members,
    payment_statuses,
    statuses,
    tracks,
    workflow_logs,
)

logger = logging.getLogger(__name__)

_TABLE_MAP = {
    "tracks": tracks,
    "statuses": statuses,
    "payment_statuses": payment_statuses,
    "members": members,
    "groups": groups,
    "events": events,
    "workflow_logs": workflow_logs,
    "fees": fees,
    "links": links,
    "link_clicks": link_clicks,
}

_SEED_ORDER = list(_TABLE_MAP.keys())


def _clean_row(table, row: dict) -> dict:
    columns = {c.name for c in table.columns}
    return {k: v for k, v in row.items() if k in columns}


def _seed_table(conn, sheets: SheetsClient, name: str) -> int:
    records = sheets.get_records(name)
    if not records:
        return 0
    table = _TABLE_MAP[name]
    cleaned = [_clean_row(table, r) for r in records]
    stmt = insert(table).on_conflict_do_nothing()
    conn.execute(stmt, cleaned)
    return len(cleaned)


def run_seed() -> None:
    settings = Settings()
    sheets = SheetsClient(
        settings.google_service_account_file,
        settings.google_sheets_id,
    )
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        for name in _SEED_ORDER:
            count = _seed_table(conn, sheets, name)
            logger.info("Seeded %s: %d rows", name, count)
        conn.commit()
    engine.dispose()
    logger.info("Seed complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_seed()
