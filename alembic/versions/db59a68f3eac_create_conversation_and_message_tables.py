"""create conversation and message tables

Revision ID: db59a68f3eac
Revises: 5f3859bb587f
Create Date: 2026-08-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db59a68f3eac'
down_revision: Union[str, Sequence[str], None] = '5f3859bb587f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('conversation',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('machine_id', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_machine_id'), 'conversation', ['machine_id'], unique=False)
    op.create_index(op.f('ix_conversation_user_id'), 'conversation', ['user_id'], unique=False)

    op.create_table('message',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('conversation_id', sa.Uuid(), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_conversation_id'), 'message', ['conversation_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_message_conversation_id'), table_name='message')
    op.drop_table('message')
    op.drop_index(op.f('ix_conversation_user_id'), table_name='conversation')
    op.drop_index(op.f('ix_conversation_machine_id'), table_name='conversation')
    op.drop_table('conversation')
