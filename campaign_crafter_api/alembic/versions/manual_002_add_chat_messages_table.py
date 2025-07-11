"""add_chat_messages_table

Revision ID: manual_002_add_chat_messages
Revises: 1a2b3c4d5e6f
Create Date: YYYY-MM-DD HH:MM:SS.MS

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'manual_002_add_chat_messages'
down_revision: Union[str, None] = None # Depends on characters table creation
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chat_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.Column('sender', sa.String(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    op.create_index(op.f('ix_chat_messages_character_id'), 'chat_messages', ['character_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_timestamp'), 'chat_messages', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chat_messages_timestamp'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_character_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
