"""fix_roll_table_unique_constraint

Revision ID: 737cb3ada9c6
Revises: 570430d398e9
Create Date: 2026-02-01 21:04:16.362586

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '737cb3ada9c6'
down_revision: Union[str, None] = '570430d398e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the existing unique constraint on name
    with op.batch_alter_table('roll_tables', schema=None) as batch_op:
        batch_op.drop_index('ix_roll_tables_name')
        batch_op.create_index('ix_roll_tables_name', ['name'], unique=False)
        # Create a composite unique constraint on (name, user_id)
        # Note: SQLite doesn't support unique constraints with NULL values properly
        # So we'll use a unique index with a WHERE clause for non-NULL user_ids
        # and rely on application logic for system tables (user_id IS NULL)
        batch_op.create_index(
            'ix_roll_tables_name_user_id_unique',
            ['name', 'user_id'],
            unique=True,
            sqlite_where=sa.text('user_id IS NOT NULL')
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('roll_tables', schema=None) as batch_op:
        batch_op.drop_index('ix_roll_tables_name_user_id_unique')
        batch_op.drop_index('ix_roll_tables_name')
        batch_op.create_index('ix_roll_tables_name', ['name'], unique=True)
