"""add_encrypted_api_keys_to_user

Revision ID: zzzz_placeholder_add_api_keys
Revises: <PREVIOUS_REVISION_ID_NEEDS_UPDATE>
Create Date: 2023-10-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5f7e1a3b0d9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    #op.add_column('users', sa.Column('encrypted_openai_api_key', sa.String(), nullable=True))
    #op.add_column('users', sa.Column('encrypted_sd_api_key', sa.String(), nullable=True))
    op.add_column('users', sa.Column('encrypted_gemini_api_key', sa.String(), nullable=True))
    op.add_column('users', sa.Column('encrypted_other_llm_api_key', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'encrypted_sd_api_key')
    op.drop_column('users', 'encrypted_openai_api_key')
    op.drop_column('users', 'encrypted_other_llm_api_key')
    op.drop_column('users', 'encrypted_gemini_api_key')
