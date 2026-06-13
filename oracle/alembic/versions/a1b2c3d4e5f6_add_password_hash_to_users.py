"""add password_hash to users

Revision ID: a1b2c3d4e5f6
Revises: ee175c71814a
Create Date: 2026-06-12 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "ee175c71814a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
