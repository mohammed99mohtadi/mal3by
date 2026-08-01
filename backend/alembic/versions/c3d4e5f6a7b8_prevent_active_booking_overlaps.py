"""prevent active booking overlaps

Revision ID: c3d4e5f6a7b8
Revises: b8c9d0e1f2a3
"""

from alembic import op


revision = "c3d4e5f6a7b8"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


CONSTRAINT_NAME = "excl_bookings_active_court_time_overlap"


def upgrade() -> None:
    # btree_gist supplies the GiST equality operator class for integer court_id.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        f"""
        ALTER TABLE bookings
        ADD CONSTRAINT {CONSTRAINT_NAME}
        EXCLUDE USING gist (
            court_id WITH =,
            tstzrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (status IN ('pending', 'pending_payment', 'confirmed'))
        """
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE bookings DROP CONSTRAINT {CONSTRAINT_NAME}")
    # Keep btree_gist: extensions are database-scoped and may be shared by other objects.
