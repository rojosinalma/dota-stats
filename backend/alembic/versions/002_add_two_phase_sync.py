"""add two-phase sync support

Revision ID: 002
Revises: 001
Create Date: 2025-01-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to matches table for two-phase sync
    op.add_column('matches', sa.Column('has_details', sa.Boolean(), nullable=True))
    op.add_column('matches', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('matches', sa.Column('last_fetch_attempt', sa.DateTime(timezone=True), nullable=True))
    op.add_column('matches', sa.Column('fetch_error', sa.String(), nullable=True))

    # Mark existing matches as having details (they already have complete data)
    op.execute("UPDATE matches SET has_details = TRUE WHERE has_details IS NULL")

    # Make columns nullable that weren't before (to support match stubs)
    # Keep id and user_id as NOT NULL
    op.alter_column('matches', 'start_time', nullable=True)
    op.alter_column('matches', 'duration', nullable=True)
    op.alter_column('matches', 'game_mode', nullable=True)
    op.alter_column('matches', 'lobby_type', nullable=True)
    op.alter_column('matches', 'radiant_win', nullable=True)
    op.alter_column('matches', 'hero_id', nullable=True)
    op.alter_column('matches', 'player_slot', nullable=True)
    op.alter_column('matches', 'radiant_team', nullable=True)
    op.alter_column('matches', 'kills', nullable=True)
    op.alter_column('matches', 'deaths', nullable=True)
    op.alter_column('matches', 'assists', nullable=True)


def downgrade():
    # Remove new columns
    op.drop_column('matches', 'fetch_error')
    op.drop_column('matches', 'last_fetch_attempt')
    op.drop_column('matches', 'retry_count')
    op.drop_column('matches', 'has_details')

    # Restore NOT NULL constraints (only safe if all rows have values)
    op.alter_column('matches', 'assists', nullable=False)
    op.alter_column('matches', 'deaths', nullable=False)
    op.alter_column('matches', 'kills', nullable=False)
    op.alter_column('matches', 'radiant_team', nullable=False)
    op.alter_column('matches', 'player_slot', nullable=False)
    op.alter_column('matches', 'hero_id', nullable=False)
    op.alter_column('matches', 'radiant_win', nullable=False)
    op.alter_column('matches', 'lobby_type', nullable=False)
    op.alter_column('matches', 'game_mode', nullable=False)
    op.alter_column('matches', 'duration', nullable=False)
    op.alter_column('matches', 'start_time', nullable=False)
