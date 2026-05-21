"""initial schema

Revision ID: 589bf38be6b5
Revises: 54e622dba982
Create Date: 2026-04-26 00:35:05.781124

"""
from typing import Sequence, Union

from alembic import op

revision: str = '589bf38be6b5'
down_revision: Union[str, Sequence[str], None] = '54e622dba982'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass