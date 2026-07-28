"""baseline_users_sports_courts

Revision ID: 5de7dc1ae0b4
Revises: 
Create Date: 2026-07-28 16:48:02.647603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5de7dc1ae0b4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('role', sa.String(length=20), server_default='player', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('phone_number')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Sports table
    op.create_table(
        'sports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=False),
        sa.Column('name_ar', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('icon', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_sports_id'), 'sports', ['id'], unique=False)
    op.create_index(op.f('ix_sports_slug'), 'sports', ['slug'], unique=True)

    # Courts table
    op.create_table(
        'courts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('sport_id', sa.Integer(), nullable=False),
        sa.Column('name_en', sa.String(length=150), nullable=False),
        sa.Column('name_ar', sa.String(length=150), nullable=False),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('description_ar', sa.Text(), nullable=True),
        sa.Column('area', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('price_per_hour', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='KWD', nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('price_per_hour > 0', name='check_price_positive'),
        sa.CheckConstraint('capacity > 0', name='check_capacity_positive'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sport_id'], ['sports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courts_area'), 'courts', ['area'], unique=False)
    op.create_index(op.f('ix_courts_id'), 'courts', ['id'], unique=False)
    op.create_index(op.f('ix_courts_is_active'), 'courts', ['is_active'], unique=False)
    op.create_index(op.f('ix_courts_name_ar'), 'courts', ['name_ar'], unique=False)
    op.create_index(op.f('ix_courts_name_en'), 'courts', ['name_en'], unique=False)
    op.create_index(op.f('ix_courts_owner_id'), 'courts', ['owner_id'], unique=False)
    op.create_index(op.f('ix_courts_sport_id'), 'courts', ['sport_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_courts_sport_id'), table_name='courts')
    op.drop_index(op.f('ix_courts_owner_id'), table_name='courts')
    op.drop_index(op.f('ix_courts_name_en'), table_name='courts')
    op.drop_index(op.f('ix_courts_name_ar'), table_name='courts')
    op.drop_index(op.f('ix_courts_is_active'), table_name='courts')
    op.drop_index(op.f('ix_courts_id'), table_name='courts')
    op.drop_index(op.f('ix_courts_area'), table_name='courts')
    op.drop_table('courts')

    op.drop_index(op.f('ix_sports_slug'), table_name='sports')
    op.drop_index(op.f('ix_sports_id'), table_name='sports')
    op.drop_table('sports')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
