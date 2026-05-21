"""fix username column length to match model

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-05-21

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3f8a2d91b4e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('users', 'username',
                    existing_type=sa.String(length=30),
                    type_=sa.String(length=32),
                    existing_nullable=False)


def downgrade() -> None:
    op.alter_column('users', 'username',
                    existing_type=sa.String(length=32),
                    type_=sa.String(length=30),
                    existing_nullable=False)
