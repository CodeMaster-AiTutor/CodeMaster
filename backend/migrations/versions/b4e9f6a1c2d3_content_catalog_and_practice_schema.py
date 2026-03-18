"""content catalog and practice schema

Revision ID: b4e9f6a1c2d3
Revises: 8f2c1a7b3d4e
Create Date: 2026-03-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b4e9f6a1c2d3"
down_revision = "8f2c1a7b3d4e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "featured_courses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("route_path", sa.String(length=255), nullable=True),
        sa.Column("external_url", sa.String(length=1024), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_featured_courses_slug"), "featured_courses", ["slug"], unique=True)
    op.create_index(op.f("ix_featured_courses_order_index"), "featured_courses", ["order_index"], unique=False)

    op.create_table(
        "learning_path_concepts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("tutorial_url", sa.String(length=1024), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_path_concepts_slug"), "learning_path_concepts", ["slug"], unique=True)
    op.create_index(op.f("ix_learning_path_concepts_level"), "learning_path_concepts", ["level"], unique=False)
    op.create_index(op.f("ix_learning_path_concepts_order_index"), "learning_path_concepts", ["order_index"], unique=False)

    op.create_table(
        "learning_path_subtopics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("concept_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["concept_id"], ["learning_path_concepts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_path_subtopics_concept_id"), "learning_path_subtopics", ["concept_id"], unique=False)
    op.create_index(op.f("ix_learning_path_subtopics_order_index"), "learning_path_subtopics", ["order_index"], unique=False)

    op.create_table(
        "theory_course_pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("html_path", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_theory_course_pages_slug"), "theory_course_pages", ["slug"], unique=True)
    op.create_index(op.f("ix_theory_course_pages_level"), "theory_course_pages", ["level"], unique=False)
    op.create_index(op.f("ix_theory_course_pages_order_index"), "theory_course_pages", ["order_index"], unique=False)

    with op.batch_alter_table("practice_problems", schema=None) as batch_op:
        batch_op.add_column(sa.Column("level", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("section", sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"))
        batch_op.alter_column("difficulty", existing_type=sa.String(length=20), nullable=False, server_default="Easy")
        batch_op.create_index(batch_op.f("ix_practice_problems_level"), ["level"], unique=False)
        batch_op.create_index(batch_op.f("ix_practice_problems_section"), ["section"], unique=False)
        batch_op.create_index(batch_op.f("ix_practice_problems_order_index"), ["order_index"], unique=False)

    op.execute(
        """
        UPDATE practice_problems
        SET level = CASE
            WHEN lower(difficulty) IN ('beginner', 'basic', 'easy') THEN 'beginner'
            WHEN lower(difficulty) IN ('intermediate', 'medium') THEN 'intermediate'
            ELSE 'advanced'
        END
        WHERE level IS NULL OR level = ''
        """
    )

    with op.batch_alter_table("practice_problems", schema=None) as batch_op:
        batch_op.alter_column("level", existing_type=sa.String(length=20), nullable=False)


def downgrade():
    with op.batch_alter_table("practice_problems", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_practice_problems_order_index"))
        batch_op.drop_index(batch_op.f("ix_practice_problems_section"))
        batch_op.drop_index(batch_op.f("ix_practice_problems_level"))
        batch_op.drop_column("order_index")
        batch_op.drop_column("section")
        batch_op.drop_column("level")

    op.drop_index(op.f("ix_theory_course_pages_order_index"), table_name="theory_course_pages")
    op.drop_index(op.f("ix_theory_course_pages_level"), table_name="theory_course_pages")
    op.drop_index(op.f("ix_theory_course_pages_slug"), table_name="theory_course_pages")
    op.drop_table("theory_course_pages")

    op.drop_index(op.f("ix_learning_path_subtopics_order_index"), table_name="learning_path_subtopics")
    op.drop_index(op.f("ix_learning_path_subtopics_concept_id"), table_name="learning_path_subtopics")
    op.drop_table("learning_path_subtopics")

    op.drop_index(op.f("ix_learning_path_concepts_order_index"), table_name="learning_path_concepts")
    op.drop_index(op.f("ix_learning_path_concepts_level"), table_name="learning_path_concepts")
    op.drop_index(op.f("ix_learning_path_concepts_slug"), table_name="learning_path_concepts")
    op.drop_table("learning_path_concepts")

    op.drop_index(op.f("ix_featured_courses_order_index"), table_name="featured_courses")
    op.drop_index(op.f("ix_featured_courses_slug"), table_name="featured_courses")
    op.drop_table("featured_courses")

