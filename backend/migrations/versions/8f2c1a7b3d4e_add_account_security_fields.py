from alembic import op
import sqlalchemy as sa


revision = '8f2c1a7b3d4e'
down_revision = '6ca1fae7a995'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_updated_at TIMESTAMP")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMP")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS csrf_token VARCHAR(128)")


def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS csrf_token")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS deletion_requested_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS password_updated_at")
