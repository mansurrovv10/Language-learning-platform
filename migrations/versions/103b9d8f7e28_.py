"""add level tests and user language

Revision ID: 103b9d8f7e28
Revises: 1b40c6d2e4d3
Create Date: 2026-09-19 01:30:30.974095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '103b9d8f7e28'
down_revision: Union[str, Sequence[str], None] = '1b40c6d2e4d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_language',
    sa.Column('id',sa.Integer(),nullable=False),
    sa.Column('user_id',sa.UUID(),nullable=False),
    sa.Column('language_id',sa.Integer(),nullable=False),
    sa.Column('level',sa.Enum('A1','A2','B1','B2','C1','C2',name='levelchoices',create_type=False),nullable=True),
    sa.Column('placement_completed',sa.Boolean(),nullable=False,server_default=sa.false()),
    sa.ForeignKeyConstraint(['language_id'],['language.id']),
    sa.ForeignKeyConstraint(['user_id'],['user.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id','language_id',name='uq_user_language_user_language'))
    op.create_table('level_test',
    sa.Column('id',sa.UUID(),nullable=False),
    sa.Column('language_id',sa.Integer(),nullable=False),
    sa.Column('is_placement',sa.Boolean(),nullable=False),
    sa.Column('target_level',sa.Enum('A1','A2','B1','B2','C1','C2',name='levelchoices',create_type=False),nullable=True),
    sa.Column('passing_score',sa.Integer(),nullable=False,server_default='70'),
    sa.Column('is_active',sa.Boolean(),nullable=False,server_default=sa.true()),
    sa.Column('created_at',sa.DateTime(),nullable=False),
    sa.ForeignKeyConstraint(['language_id'],['language.id']),
    sa.PrimaryKeyConstraint('id'))
    op.create_table('level_test_question',
    sa.Column('id',sa.Integer(),nullable=False),
    sa.Column('test_id',sa.UUID(),nullable=False),
    sa.Column('level',sa.Enum('A1','A2','B1','B2','C1','C2',name='levelchoices',create_type=False),nullable=False),
    sa.Column('type',sa.Enum('CHOICE','TRANSLATE','FILL_GAP','MATCH',name='exercisetype',create_type=False),nullable=False),
    sa.Column('question',sa.Text(),nullable=False),
    sa.Column('options',sa.JSON(),nullable=False),
    sa.Column('correct_answer',sa.JSON(),nullable=False),
    sa.Column('order',sa.Integer(),nullable=False,server_default='1'),
    sa.ForeignKeyConstraint(['test_id'],['level_test.id']),
    sa.PrimaryKeyConstraint('id'))
    op.create_table('level_test_attempt',
    sa.Column('id',sa.UUID(),nullable=False),
    sa.Column('test_id',sa.UUID(),nullable=False),
    sa.Column('user_id',sa.UUID(),nullable=False),
    sa.Column('language_id',sa.Integer(),nullable=False),
    sa.Column('score',sa.Float(),nullable=True),
    sa.Column('result_level',sa.Enum('A1','A2','B1','B2','C1','C2',name='levelchoices',create_type=False),nullable=True),
    sa.Column('passed',sa.Boolean(),nullable=True),
    sa.Column('completed_at',sa.DateTime(),nullable=True),
    sa.Column('created_at',sa.DateTime(),nullable=False),
    sa.ForeignKeyConstraint(['language_id'],['language.id']),
    sa.ForeignKeyConstraint(['test_id'],['level_test.id']),
    sa.ForeignKeyConstraint(['user_id'],['user.id']),
    sa.PrimaryKeyConstraint('id'))
    op.create_table('user_exercise_progress',
    sa.Column('id',sa.Integer(),nullable=False),
    sa.Column('user_id',sa.UUID(),nullable=False),
    sa.Column('exercise_id',sa.Integer(),nullable=False),
    sa.Column('completed',sa.Boolean(),nullable=False,server_default=sa.false()),
    sa.Column('score',sa.Integer(),nullable=False,server_default='0'),
    sa.ForeignKeyConstraint(['exercise_id'],['exercise.id']),
    sa.ForeignKeyConstraint(['user_id'],['user.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id','exercise_id',name='uq_user_exercise_progress_user_exercise'))


def downgrade() -> None:
    op.drop_table('user_exercise_progress')
    op.drop_table('level_test_attempt')
    op.drop_table('level_test_question')
    op.drop_table('level_test')
    op.drop_table('user_language')
