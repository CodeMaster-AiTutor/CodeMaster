"""add github oauth field

Revision ID: d2f3a4b5c6d7
Revises: a9c4e2d7b8f1
Create Date: 2026-04-13 00:00:00.000000
"""

from alembic import op


revision = "d2f3a4b5c6d7"
down_revision = "a9c4e2d7b8f1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS github_id VARCHAR(255)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_github_id ON users (github_id)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_github_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS github_id")
