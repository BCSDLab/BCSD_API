"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "members",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("department", sa.String),
        sa.Column("student_id", sa.String),
        sa.Column("school_email", sa.String),
        sa.Column("phone", sa.String),
        sa.Column("status", sa.String, nullable=False, server_default="Beginner"),
        sa.Column("track", sa.String),
        sa.Column("team", sa.String),
        sa.Column("role", sa.String),
        sa.Column("join_date", sa.String),
        sa.Column("payment_status", sa.String, server_default="미납"),
        sa.Column("last_updated", sa.String),
    )

    op.create_table(
        "tracks",
        sa.Column("name", sa.String, primary_key=True),
    )

    op.create_table(
        "statuses",
        sa.Column("name", sa.String, primary_key=True),
    )

    op.create_table(
        "payment_statuses",
        sa.Column("name", sa.String, primary_key=True),
    )

    op.create_table(
        "groups",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String),
        sa.Column("type", sa.String),
        sa.Column("parent_id", sa.String),
        sa.Column("size", sa.Integer),
        sa.Column("leader_email", sa.String),
        sa.Column("last_updated", sa.String),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("title", sa.String),
        sa.Column("date", sa.String),
        sa.Column("type", sa.String),
        sa.Column("organizer", sa.String),
        sa.Column("attendees", sa.Text),
        sa.Column("notes", sa.Text),
    )

    op.create_table(
        "workflow_logs",
        sa.Column("timestamp", sa.String, primary_key=True),
        sa.Column("workflow_name", sa.String, primary_key=True),
        sa.Column("status", sa.String),
        sa.Column("input_data", sa.Text),
        sa.Column("output_data", sa.Text),
        sa.Column("error_message", sa.Text),
    )

    op.create_table(
        "fees",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("member_id", sa.String, sa.ForeignKey("members.id")),
        sa.Column("amount", sa.Integer),
        sa.Column("paid_date", sa.String),
        sa.Column("payment_method", sa.String),
        sa.Column("notes", sa.Text),
        sa.Column("semester", sa.String),
        sa.Column("last_updated", sa.String),
    )

    op.create_table(
        "links",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("code", sa.String, nullable=False, unique=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("creator_id", sa.String, sa.ForeignKey("members.id")),
        sa.Column("created_at", sa.String),
        sa.Column("expires_at", sa.String),
        sa.Column("expired_at", sa.String),
        sa.Column("updated_at", sa.String),
    )

    op.create_table(
        "link_clicks",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column(
            "link_id",
            sa.String,
            sa.ForeignKey("links.id", ondelete="CASCADE"),
        ),
        sa.Column("clicked_at", sa.String),
        sa.Column("referer", sa.Text),
        sa.Column("user_agent", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("link_clicks")
    op.drop_table("links")
    op.drop_table("fees")
    op.drop_table("workflow_logs")
    op.drop_table("events")
    op.drop_table("groups")
    op.drop_table("payment_statuses")
    op.drop_table("statuses")
    op.drop_table("tracks")
    op.drop_table("members")
