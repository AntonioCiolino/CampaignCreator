"""add_images_json_to_campaign_sections

Revision ID: 8a69051d8d98
Revises: zzzz_placeholder_add_api_keys
Create Date: 2025-06-15 01:25:46.968812

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a69051d8d98'
down_revision: Union[str, None] = 'zzzz_placeholder_add_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('campaign_sections', sa.Column('images_json', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('campaign_sections', 'images_json')
