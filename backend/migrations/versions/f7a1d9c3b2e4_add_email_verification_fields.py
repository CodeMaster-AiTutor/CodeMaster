"""add email verification fields

Revision ID: f7a1d9c3b2e4
Revises: e1b2c3d4f5a6
Create Date: 2026-04-12 00:00:00.000000
"""

from alembic import op


revision = "f7a1d9c3b2e4"
down_revision = "e1b2c3d4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token_hash VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email_verification_token_hash ON users (email_verification_token_hash)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_email_verification_token_hash")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email_verification_expires_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email_verification_token_hash")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email_verified")
