"""remove_images_json_from_campaign_sections

Revision ID: 5a0e1d5eddbd
Revises: 8a69051d8d98
Create Date: 2025-06-15 01:28:36.723562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a0e1d5eddbd'
down_revision: Union[str, None] = '8a69051d8d98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('campaign_sections', 'images_json')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('campaign_sections', sa.Column('images_json', sa.JSON(), nullable=True))
