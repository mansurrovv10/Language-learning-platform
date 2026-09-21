"""add level tests

Revision ID: c9a39958e8df
Revises: 103b9d8f7e28
Create Date: 2026-09-21 15:36:35.471212

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9a39958e8df'
down_revision: Union[str, Sequence[str], None] = '103b9d8f7e28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    levelchoices = sa.dialects.postgresql.ENUM(
        'A1','A2','B1','B2','C1','C2',
        name='levelchoices',
        create_type=False
    )

    exercisetype = sa.dialects.postgresql.ENUM(
        'CHOICE','TRANSLATE','FILL_GAP','MATCH',
        name='exercisetype',
        create_type=False
    )

    op.create_table('level_test',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('language_id', sa.Integer(), nullable=False),
    sa.Column('is_placement', sa.Boolean(), nullable=False),
    sa.Column('target_level', levelchoices, nullable=True),
    sa.Column('passing_score', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['language_id'], ['language.id']),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('level_test_attempt',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('test_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('language_id', sa.Integer(), nullable=False),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('result_level', levelchoices, nullable=True),
    sa.Column('passed', sa.Boolean(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['language_id'], ['language.id']),
    sa.ForeignKeyConstraint(['test_id'], ['level_test.id']),
    sa.ForeignKeyConstraint(['user_id'], ['user.id']),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('level_test_question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('test_id', sa.UUID(), nullable=False),
    sa.Column('level', levelchoices, nullable=False),
    sa.Column('type', exercisetype, nullable=False),
    sa.Column('question', sa.Text(), nullable=False),
    sa.Column('options', sa.JSON(), nullable=False),
    sa.Column('correct_answer', sa.JSON(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['test_id'], ['level_test.id']),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('level_test_question')
    op.drop_table('level_test_attempt')
    op.drop_table('level_test')