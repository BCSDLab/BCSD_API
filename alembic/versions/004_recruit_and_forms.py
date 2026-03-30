"""recruitment periods and forms

Revision ID: 004
Revises: 003
"""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"


def upgrade() -> None:
    op.create_table(
        "recruitment_periods",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("start_date", sa.String, nullable=False),
        sa.Column("end_date", sa.String, nullable=False),
        sa.Column("is_active", sa.String, server_default="true"),
        sa.Column("created_by", sa.String, sa.ForeignKey("members.id")),
        sa.Column("created_at", sa.String),
        sa.Column("updated_at", sa.String),
    )
    op.create_table(
        "forms",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("recruitment_id", sa.String, sa.ForeignKey("recruitment_periods.id")),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("is_active", sa.String, server_default="true"),
        sa.Column("created_by", sa.String, sa.ForeignKey("members.id")),
        sa.Column("created_at", sa.String),
        sa.Column("updated_at", sa.String),
    )
    op.create_table(
        "form_questions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("form_id", sa.String, sa.ForeignKey("forms.id", ondelete="CASCADE")),
        sa.Column("label", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("options", sa.Text),
        sa.Column("required", sa.String, server_default="true"),
        sa.Column("sort_order", sa.Integer, nullable=False),
        sa.Column("created_at", sa.String),
    )


def downgrade() -> None:
    op.drop_table("form_questions")
    op.drop_table("forms")
    op.drop_table("recruitment_periods")
