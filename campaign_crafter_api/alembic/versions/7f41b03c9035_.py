"""empty message

Revision ID: 7f41b03c9035
Revises: 1a2b3c4d5e6f, 2b5c879d0a3e, manual_001_add_avatar_url
Create Date: 2025-07-02 16:36:11.923452

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f41b03c9035'
down_revision: Union[str, None] = ('1a2b3c4d5e6f', '2b5c879d0a3e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
