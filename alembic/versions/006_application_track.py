"""add track column to applications

Revision ID: 006
Revises: 005
"""

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"


def upgrade() -> None:
    op.add_column("applications", sa.Column("track", sa.String))


def downgrade() -> None:
    op.drop_column("applications", "track")
