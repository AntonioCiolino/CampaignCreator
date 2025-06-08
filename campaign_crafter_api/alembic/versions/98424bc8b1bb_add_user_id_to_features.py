"""add_user_id_to_features

Revision ID: 98424bc8b1bb
Revises: 140efacee7ed
Create Date: 2025-06-08 15:18:43.177206

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98424bc8b1bb'
down_revision: Union[str, None] = '140efacee7ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

down_revision = '140efacee7ed' # Should be ID of add_user_id_to_roll_tables migration

def upgrade() -> None:
    with op.batch_alter_table('features', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_features_user_id_users',
            'users',
            ['user_id'],
            ['id']
        )
        batch_op.create_index(op.f('ix_features_user_id'), ['user_id'], unique=False)

def downgrade() -> None:
    with op.batch_alter_table('features', schema=None) as batch_op:
        batch_op.drop_index(op.f('ix_features_user_id'))
        batch_op.drop_constraint('fk_features_user_id_users', type_='foreignkey')
        batch_op.drop_column('user_id')