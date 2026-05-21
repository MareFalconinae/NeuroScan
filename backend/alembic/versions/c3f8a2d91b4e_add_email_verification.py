"""add email verification fields

Revision ID: c3f8a2d91b4e
Revises: 589bf38be6b5
Create Date: 2026-05-04

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3f8a2d91b4e'
down_revision = '54e622dba982'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Mevcut kullanıcılar doğrulanmış sayılır (server_default=true)
    op.add_column('users', sa.Column(
        'email_verified', sa.Boolean(), nullable=False, server_default='true'
    ))
    op.add_column('users', sa.Column('verification_code', sa.String(6), nullable=True))
    op.add_column('users', sa.Column(
        'verification_code_expires_at', sa.DateTime(timezone=True), nullable=True
    ))


def downgrade() -> None:
    op.drop_column('users', 'verification_code_expires_at')
    op.drop_column('users', 'verification_code')
    op.drop_column('users', 'email_verified')
