"""remove user role

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-20

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

user_role_enum = sa.Enum('user', 'admin', name='user_role_enum')


def upgrade() -> None:
    op.drop_column('users', 'role')
    user_role_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    user_role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('users', sa.Column(
        'role',
        sa.Enum('user', 'admin', name='user_role_enum'),
        nullable=False,
        server_default=sa.text("'user'"),
    ))
