"""merge_heads

Revision ID: 570430d398e9
Revises: manual_002_add_chat_messages, manual_004_add_memory_summary_to_chat_messages
Create Date: 2026-02-01 21:04:02.089678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '570430d398e9'
down_revision: Union[str, None] = ('manual_002_add_chat_messages', 'manual_004_add_memory_summary_to_chat_messages')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
