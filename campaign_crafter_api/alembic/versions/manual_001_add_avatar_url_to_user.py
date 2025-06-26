"""add_avatar_url_to_user_table

Revision ID: manual_001_add_avatar_url
Revises: 02b35f707b57
Create Date: YYYY-MM-DD HH:MM:SS.MS

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'manual_001_add_avatar_url' # Placeholder revision ID
down_revision = '02b35f707b57' # Assuming this is the correct previous head
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
