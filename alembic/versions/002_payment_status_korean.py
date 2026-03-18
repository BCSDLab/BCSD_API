"""payment_status values to Korean

Revision ID: 002
Revises: 001
"""

from alembic import op

revision = "002"
down_revision = "001"

_MAPPING = {
    "Unpaid": "미납",
    "Paid": "납부",
    "Exempt": "면제",
}


def upgrade() -> None:
    for eng, kor in _MAPPING.items():
        op.execute(
            f"UPDATE payment_statuses SET name = '{kor}' WHERE name = '{eng}'"
        )
        op.execute(
            f"UPDATE members SET payment_status = '{kor}' WHERE payment_status = '{eng}'"
        )
    op.execute("ALTER TABLE members ALTER COLUMN payment_status SET DEFAULT '미납'")


def downgrade() -> None:
    for eng, kor in _MAPPING.items():
        op.execute(
            f"UPDATE payment_statuses SET name = '{eng}' WHERE name = '{kor}'"
        )
        op.execute(
            f"UPDATE members SET payment_status = '{eng}' WHERE payment_status = '{kor}'"
        )
    op.execute("ALTER TABLE members ALTER COLUMN payment_status SET DEFAULT 'Unpaid'")
