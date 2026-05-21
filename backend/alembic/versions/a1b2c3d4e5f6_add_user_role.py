"""add user role

Revision ID: a1b2c3d4e5f6
Revises: c3f8a2d91b4e
Create Date: 2026-05-07

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'c3f8a2d91b4e'
branch_labels = None
depends_on = None

user_role_enum = sa.Enum('user', 'admin', name='user_role_enum')


def upgrade() -> None:
    user_role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('users', sa.Column(
        'role',
        sa.Enum('user', 'admin', name='user_role_enum'),
        nullable=False,
        server_default=sa.text("'user'"),
    ))


def downgrade() -> None:
    op.drop_column('users', 'role')
    user_role_enum.drop(op.get_bind(), checkfirst=True)
