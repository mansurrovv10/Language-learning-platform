"""rename user.password to password_hash

Revision ID: a2c4e6b8d1f3
Revises: 7f44570f8381
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a2c4e6b8d1f3'
down_revision: Union[str, Sequence[str], None] = '7f44570f8381'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('user', 'password', new_column_name='password_hash')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('user', 'password_hash', new_column_name='password')