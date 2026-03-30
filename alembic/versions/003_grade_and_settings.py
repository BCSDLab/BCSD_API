"""add grade column and app_settings table

Revision ID: 003
Revises: 002
"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"


def upgrade() -> None:
    op.add_column("members", sa.Column("grade", sa.String))
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String, primary_key=True),
        sa.Column("value", sa.String, nullable=False),
        sa.Column("updated_at", sa.String),
        sa.Column("updated_by", sa.String),
    )
    op.execute(
        "INSERT INTO app_settings (key, value) VALUES ('grade_threshold', '3')"
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_column("members", "grade")
