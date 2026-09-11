"""add achievement conditions column

Revision ID: 4d1f9a2b8c3e
Revises: 9c763efd6580
Create Date: 2026-09-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d1f9a2b8c3e'
down_revision: Union[str, Sequence[str], None] = '9c763efd6580'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'achievement',
        sa.Column('conditions', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('achievement', 'conditions')