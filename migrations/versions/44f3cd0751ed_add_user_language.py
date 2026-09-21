"""add user language

Revision ID: 44f3cd0751ed
Revises: c9a39958e8df
Create Date: 2026-09-21 16:09:02.395219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44f3cd0751ed'
down_revision: Union[str, Sequence[str], None] = 'c9a39958e8df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    levelchoices = sa.dialects.postgresql.ENUM(
        'A1','A2','B1','B2','C1','C2',
        name='levelchoices',
        create_type=False
    )

    op.create_table(
        'user_language',
        sa.Column('id',sa.Integer(),nullable=False),
        sa.Column('user_id',sa.UUID(),nullable=False),
        sa.Column('language_id',sa.Integer(),nullable=False),
        sa.Column('level',levelchoices,nullable=True),
        sa.Column('placement_completed',sa.Boolean(),nullable=False),
        sa.ForeignKeyConstraint(['language_id'],['language.id']),
        sa.ForeignKeyConstraint(['user_id'],['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id','language_id',name='uq_user_language_user_language')
    )


def downgrade() -> None:
    op.drop_table('user_language')