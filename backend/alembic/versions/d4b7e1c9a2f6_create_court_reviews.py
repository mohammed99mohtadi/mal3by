"""create court reviews

Revision ID: d4b7e1c9a2f6
Revises: c1a8f4d2e9b0
"""
from alembic import op
import sqlalchemy as sa

revision = "d4b7e1c9a2f6"
down_revision = "c1a8f4d2e9b0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("court_reviews",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("court_id", sa.Integer(), nullable=False), sa.Column("booking_id", sa.Integer(), nullable=False), sa.Column("reviewer_id", sa.Integer(), nullable=False), sa.Column("rating", sa.Integer(), nullable=False), sa.Column("comment", sa.Text()), sa.Column("status", sa.String(20), nullable=False), sa.Column("is_verified_booking", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("moderated_at", sa.DateTime(timezone=True)), sa.Column("moderated_by_id", sa.Integer()), sa.Column("moderation_reason", sa.String(500)),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_court_reviews_rating"), sa.CheckConstraint("status IN ('published', 'hidden', 'removed')", name="ck_court_reviews_status"),
        sa.ForeignKeyConstraint(["court_id"], ["courts.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["moderated_by_id"], ["users.id"], ondelete="RESTRICT"), sa.UniqueConstraint("booking_id", name="uq_court_reviews_booking_id"))
    for name, columns in (("ix_court_reviews_court_id", ["court_id"]), ("ix_court_reviews_booking_id", ["booking_id"]), ("ix_court_reviews_reviewer_id", ["reviewer_id"]), ("ix_court_reviews_rating", ["rating"]), ("ix_court_reviews_status", ["status"]), ("ix_court_reviews_created_at", ["created_at"])): op.create_index(name, "court_reviews", columns)
    op.create_table("court_review_responses", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("review_id", sa.Integer(), nullable=False), sa.Column("owner_id", sa.Integer(), nullable=False), sa.Column("response_text", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["review_id"], ["court_reviews.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"), sa.UniqueConstraint("review_id", name="uq_court_review_responses_review_id"))
    op.create_index("ix_court_review_responses_review_id", "court_review_responses", ["review_id"]); op.create_index("ix_court_review_responses_owner_id", "court_review_responses", ["owner_id"])


def downgrade():
    op.drop_index("ix_court_review_responses_owner_id", table_name="court_review_responses"); op.drop_index("ix_court_review_responses_review_id", table_name="court_review_responses"); op.drop_table("court_review_responses")
    for name in ("ix_court_reviews_created_at", "ix_court_reviews_status", "ix_court_reviews_rating", "ix_court_reviews_reviewer_id", "ix_court_reviews_booking_id", "ix_court_reviews_court_id"): op.drop_index(name, table_name="court_reviews")
    op.drop_table("court_reviews")
