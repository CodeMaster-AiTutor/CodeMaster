"""generator chat history

Revision ID: e1b2c3d4f5a6
Revises: b4e9f6a1c2d3
Create Date: 2026-03-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e1b2c3d4f5a6"
down_revision = "b4e9f6a1c2d3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "generator_chats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generator_chats_user_id"), "generator_chats", ["user_id"], unique=False)
    op.create_index(op.f("ix_generator_chats_created_at"), "generator_chats", ["created_at"], unique=False)
    op.create_index(op.f("ix_generator_chats_updated_at"), "generator_chats", ["updated_at"], unique=False)

    op.create_table(
        "generator_chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["generator_chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generator_chat_messages_chat_id"), "generator_chat_messages", ["chat_id"], unique=False)
    op.create_index(op.f("ix_generator_chat_messages_created_at"), "generator_chat_messages", ["created_at"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_generator_chat_messages_created_at"), table_name="generator_chat_messages")
    op.drop_index(op.f("ix_generator_chat_messages_chat_id"), table_name="generator_chat_messages")
    op.drop_table("generator_chat_messages")

    op.drop_index(op.f("ix_generator_chats_updated_at"), table_name="generator_chats")
    op.drop_index(op.f("ix_generator_chats_created_at"), table_name="generator_chats")
    op.drop_index(op.f("ix_generator_chats_user_id"), table_name="generator_chats")
    op.drop_table("generator_chats")
