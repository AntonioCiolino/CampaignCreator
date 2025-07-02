"""features updates

Revision ID: b8e043e9c082
Revises: f0aecf752cf0
Create Date: 2025-07-02 17:13:42.230823

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8e043e9c082'
down_revision: Union[str, None] = 'f0aecf752cf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('features', sa.Column('feature_category', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('features', 'feature_category')
