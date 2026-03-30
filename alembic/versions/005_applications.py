"""applications and answers

Revision ID: 005
Revises: 004
"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("form_id", sa.String, sa.ForeignKey("forms.id")),
        sa.Column("member_id", sa.String, sa.ForeignKey("members.id")),
        sa.Column("status", sa.String, nullable=False, server_default="납부_대기"),
        sa.Column("submitted_at", sa.String),
        sa.Column("approved_at", sa.String),
        sa.Column("approved_by", sa.String),
        sa.Column("updated_at", sa.String),
    )
    op.create_table(
        "application_answers",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("application_id", sa.String, sa.ForeignKey("applications.id", ondelete="CASCADE")),
        sa.Column("question_id", sa.String, sa.ForeignKey("form_questions.id")),
        sa.Column("value", sa.Text, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("application_answers")
    op.drop_table("applications")
