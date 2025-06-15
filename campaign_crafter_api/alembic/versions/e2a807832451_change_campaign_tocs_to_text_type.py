"""change_campaign_tocs_to_text_type

Revision ID: e2a807832451
Revises: 5a0e1d5eddbd
Create Date: 2025-06-15 01:55:46.518419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2a807832451'
down_revision: Union[str, None] = '5a0e1d5eddbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('campaigns', 'homebrewery_toc',
                    existing_type=sa.JSON(),
                    type_=sa.Text(),
                    nullable=True)
    op.alter_column('campaigns', 'display_toc',
                    existing_type=sa.JSON(),
                    type_=sa.Text(),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('campaigns', 'homebrewery_toc',
                    existing_type=sa.Text(),
                    type_=sa.JSON(),
                    nullable=True)
    op.alter_column('campaigns', 'display_toc',
                    existing_type=sa.Text(),
                    type_=sa.JSON(),
                    nullable=True)
