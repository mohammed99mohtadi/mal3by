"""create user profiles

Revision ID: e4f5a6b7c8d9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("preferred_language", sa.String(length=2), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("area", sa.String(length=100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "length(trim(display_name)) BETWEEN 2 AND 100",
            name="ck_user_profiles_display_name_length",
        ),
        sa.CheckConstraint(
            "preferred_language IS NULL OR preferred_language IN ('ar', 'en')",
            name="ck_user_profiles_preferred_language",
        ),
        sa.CheckConstraint("avatar_url IS NULL OR length(avatar_url) <= 500", name="ck_user_profiles_avatar_url_length"),
        sa.CheckConstraint("city IS NULL OR length(city) <= 100", name="ck_user_profiles_city_length"),
        sa.CheckConstraint("area IS NULL OR length(area) <= 100", name="ck_user_profiles_area_length"),
        sa.CheckConstraint("bio IS NULL OR length(bio) <= 1000", name="ck_user_profiles_bio_length"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_profiles_id", "user_profiles", ["id"], unique=False)
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)

    op.execute(
        sa.text(
            """
            INSERT INTO user_profiles (user_id, display_name, created_at, updated_at)
            SELECT users.id,
                   CASE
                       WHEN length(trim(users.full_name)) >= 2 THEN trim(users.full_name)
                       ELSE 'Player ' || users.id
                   END,
                   CURRENT_TIMESTAMP,
                   CURRENT_TIMESTAMP
            FROM users
            WHERE NOT EXISTS (
                SELECT 1 FROM user_profiles WHERE user_profiles.user_id = users.id
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
    op.drop_index("ix_user_profiles_id", table_name="user_profiles")
    op.drop_table("user_profiles")
