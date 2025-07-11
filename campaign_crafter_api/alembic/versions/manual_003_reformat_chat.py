"""add_chat_messages_table

Revision ID: manual_002_add_chat_messages
Revises: 1a2b3c4d5e6f
Create Date: YYYY-MM-DD HH:MM:SS.MS

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'manual_003_reformat_chat'
down_revision: Union[str, None] = None # Depends on characters table creation
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('character_id', sa.Integer(), sa.ForeignKey('characters.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('conversation_history', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),  # handle default in app code
    )

    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    op.create_index(op.f('ix_chat_messages_character_id'), 'chat_messages', ['character_id'], unique=False)
    with op.batch_alter_table('chat_messages') as batch_op:
        batch_op.create_unique_constraint(
            'uq_character_user_conversation', 
            ['character_id', 'user_id']
    )
    op.create_index(op.f('ix_chat_messages_user_id'), 'chat_messages', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chat_messages_timestamp'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_character_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
