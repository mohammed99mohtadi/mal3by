"""add match join requests

Revision ID: b8c9d0e1f2a3
Revises: f1b2c3d4e5f6
"""
from alembic import op
import sqlalchemy as sa

revision = "b8c9d0e1f2a3"
down_revision = "f1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "match_join_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("requested_position_code", sa.String(length=100), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'withdrawn', 'expired')",
            name="ck_match_join_requests_status",
        ),
        sa.CheckConstraint(
            "requested_position_code IS NULL OR length(trim(requested_position_code)) > 0",
            name="ck_match_join_requests_position_code",
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_join_requests_match_id", "match_join_requests", ["match_id"])
    op.create_index("ix_match_join_requests_user_id", "match_join_requests", ["user_id"])
    op.create_index("ix_match_join_requests_status", "match_join_requests", ["status"])
    op.create_index("ix_match_join_requests_reviewed_by_user_id", "match_join_requests", ["reviewed_by_user_id"])
    op.create_index("ix_match_join_requests_match_status", "match_join_requests", ["match_id", "status"])
    op.create_index("ix_match_join_requests_user_status", "match_join_requests", ["user_id", "status"])
    op.create_index(
        "uq_match_join_requests_pending_match_user",
        "match_join_requests",
        ["match_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
        sqlite_where=sa.text("status = 'pending'"),
    )


def downgrade():
    op.drop_index("uq_match_join_requests_pending_match_user", table_name="match_join_requests")
    op.drop_index("ix_match_join_requests_user_status", table_name="match_join_requests")
    op.drop_index("ix_match_join_requests_match_status", table_name="match_join_requests")
    op.drop_index("ix_match_join_requests_reviewed_by_user_id", table_name="match_join_requests")
    op.drop_index("ix_match_join_requests_status", table_name="match_join_requests")
    op.drop_index("ix_match_join_requests_user_id", table_name="match_join_requests")
    op.drop_index("ix_match_join_requests_match_id", table_name="match_join_requests")
    op.drop_table("match_join_requests")
