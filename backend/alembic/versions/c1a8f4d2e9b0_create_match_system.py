"""create match system

Revision ID: c1a8f4d2e9b0
Revises: ae676d58b47b
Create Date: 2026-07-29 02:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a8f4d2e9b0"
down_revision: Union[str, Sequence[str], None] = "ae676d58b47b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("court_id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sport_type", sa.String(length=100), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("join_policy", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("skill_level", sa.String(length=20), nullable=False),
        sa.Column("min_players", sa.Integer(), nullable=False),
        sa.Column("max_players", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invite_code", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("min_players >= 2", name="ck_matches_min_players"),
        sa.CheckConstraint("max_players >= min_players", name="ck_matches_player_range"),
        sa.CheckConstraint("max_players <= 100", name="ck_matches_max_players"),
        sa.CheckConstraint("end_time > start_time", name="ck_matches_end_after_start"),
        sa.CheckConstraint("visibility IN ('public', 'private')", name="ck_matches_visibility"),
        sa.CheckConstraint("join_policy IN ('open', 'approval_required')", name="ck_matches_join_policy"),
        sa.CheckConstraint("status IN ('open', 'full', 'cancelled', 'completed')", name="ck_matches_status"),
        sa.CheckConstraint("skill_level IN ('beginner', 'intermediate', 'advanced', 'all_levels')", name="ck_matches_skill_level"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["court_id"], ["courts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id", name="uq_matches_booking_id"),
        sa.UniqueConstraint("invite_code"),
    )
    op.create_index("ix_matches_creator_id", "matches", ["creator_id"])
    op.create_index("ix_matches_court_id", "matches", ["court_id"])
    op.create_index("ix_matches_booking_id", "matches", ["booking_id"])
    op.create_index("ix_matches_sport_type", "matches", ["sport_type"])
    op.create_index("ix_matches_visibility", "matches", ["visibility"])
    op.create_index("ix_matches_status", "matches", ["status"])
    op.create_index("ix_matches_skill_level", "matches", ["skill_level"])
    op.create_index("ix_matches_start_time", "matches", ["start_time"])
    op.create_index("ix_matches_invite_code", "matches", ["invite_code"])

    op.create_table(
        "match_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'left')", name="ck_match_participants_status"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", "user_id", name="uq_match_participants_match_user"),
    )
    op.create_index("ix_match_participants_match_id", "match_participants", ["match_id"])
    op.create_index("ix_match_participants_user_id", "match_participants", ["user_id"])
    op.create_index("ix_match_participants_status", "match_participants", ["status"])


def downgrade() -> None:
    op.drop_index("ix_match_participants_status", table_name="match_participants")
    op.drop_index("ix_match_participants_user_id", table_name="match_participants")
    op.drop_index("ix_match_participants_match_id", table_name="match_participants")
    op.drop_table("match_participants")
    op.drop_index("ix_matches_invite_code", table_name="matches")
    op.drop_index("ix_matches_start_time", table_name="matches")
    op.drop_index("ix_matches_skill_level", table_name="matches")
    op.drop_index("ix_matches_status", table_name="matches")
    op.drop_index("ix_matches_visibility", table_name="matches")
    op.drop_index("ix_matches_sport_type", table_name="matches")
    op.drop_index("ix_matches_booking_id", table_name="matches")
    op.drop_index("ix_matches_court_id", table_name="matches")
    op.drop_index("ix_matches_creator_id", table_name="matches")
    op.drop_table("matches")
