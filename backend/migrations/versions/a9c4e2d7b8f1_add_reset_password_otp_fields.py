"""add reset password otp fields

Revision ID: a9c4e2d7b8f1
Revises: f7a1d9c3b2e4
Create Date: 2026-04-13 00:00:00.000000
"""

from alembic import op


revision = "a9c4e2d7b8f1"
down_revision = "f7a1d9c3b2e4"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_password_otp_hash VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_password_otp_expires_at TIMESTAMP")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_reset_password_otp_hash ON users (reset_password_otp_hash)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_reset_password_otp_hash")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS reset_password_otp_expires_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS reset_password_otp_hash")
