"""add_user_id_to_roll_tables

Revision ID: 140efacee7ed
Revises: 
Create Date: 2025-06-08 13:34:34.800769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '140efacee7ed'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Ensure revision and down_revision at the top of the file are as Alembic generated them.
# If this is your first migration, down_revision should be None.

from alembic import op
import sqlalchemy as sa

# ... (revision variables at the top remain the same) ...

def upgrade() -> None:
    with op.batch_alter_table('roll_tables', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_roll_tables_user_id_users',
            'users',
            ['user_id'],
            ['id']
        )
        batch_op.create_index(op.f('ix_roll_tables_user_id'), ['user_id'], unique=False)

def downgrade() -> None:
    with op.batch_alter_table('roll_tables', schema=None) as batch_op:
        batch_op.drop_index(op.f('ix_roll_tables_user_id'))
        batch_op.drop_constraint('fk_roll_tables_user_id_users', type_='foreignkey')
        batch_op.drop_column('user_id')
