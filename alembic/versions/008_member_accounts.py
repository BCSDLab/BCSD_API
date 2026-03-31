"""member_accounts for multi-provider auth

Revision ID: 008
Revises: 007
"""

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"


def upgrade() -> None:
    op.create_table(
        "member_accounts",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("member_id", sa.String, sa.ForeignKey("members.id")),
        sa.Column("provider", sa.String, nullable=False),
        sa.Column("provider_id", sa.String, nullable=False),
        sa.Column("created_at", sa.String),
    )
    op.create_unique_constraint(
        "uq_member_accounts_provider",
        "member_accounts",
        ["provider", "provider_id"],
    )
    op.execute("""
        INSERT INTO member_accounts (id, member_id, provider, provider_id, created_at)
        SELECT
            'MA-' || id,
            id,
            'google',
            email,
            join_date
        FROM members
        WHERE email IS NOT NULL AND email != ''
    """)


def downgrade() -> None:
    op.drop_table("member_accounts")
