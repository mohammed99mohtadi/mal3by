"""add match position requirements

Revision ID: f1b2c3d4e5f6
Revises: d4b7e1c9a2f6
"""
from alembic import op
import sqlalchemy as sa
revision = "f1b2c3d4e5f6"
down_revision = "d4b7e1c9a2f6"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("match_position_requirements",sa.Column("id",sa.Integer(),nullable=False),sa.Column("match_id",sa.Integer(),nullable=False),sa.Column("position_code",sa.String(length=100),nullable=False),sa.Column("required_count",sa.Integer(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.CheckConstraint("required_count > 0",name="ck_match_position_requirements_positive_count"),sa.CheckConstraint("length(trim(position_code)) > 0",name="ck_match_position_requirements_position_code"),sa.ForeignKeyConstraint(["match_id"],["matches.id"],ondelete="RESTRICT"),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("match_id","position_code",name="uq_match_position_requirements_match_position"))
    op.create_index("ix_match_position_requirements_match_id","match_position_requirements",["match_id"])
def downgrade():
    op.drop_index("ix_match_position_requirements_match_id",table_name="match_position_requirements")
    op.drop_table("match_position_requirements")
