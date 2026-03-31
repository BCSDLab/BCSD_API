"""add unique constraint on school_email

Revision ID: 007
Revises: 006
"""

from alembic import op

revision = "007"
down_revision = "006"


def upgrade() -> None:
    op.create_unique_constraint("uq_members_school_email", "members", ["school_email"])


def downgrade() -> None:
    op.drop_constraint("uq_members_school_email", "members")
