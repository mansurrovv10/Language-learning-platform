"""add chat creator

Revision ID: 215e3f5e606c
Revises: 4d1f9a2b8c3e
Create Date: 2026-09-18 15:18:23.111829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '215e3f5e606c'
down_revision: Union[str, Sequence[str], None] = '4d1f9a2b8c3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat', sa.Column('creator_id', sa.UUID(), nullable=False))
    op.create_foreign_key('fk_chat_creator_id_user', 'chat', 'user', ['creator_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_chat_creator_id_user', 'chat', type_='foreignkey')
    op.drop_column('chat', 'creator_id')