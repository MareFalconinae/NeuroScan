"""add pending_registrations table, drop verification cols from users

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pending_registrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('verification_code', sa.String(length=6), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pending_registrations_email', 'pending_registrations',
                    ['email'], unique=True)

    op.drop_column('users', 'verification_code_expires_at')
    op.drop_column('users', 'verification_code')


def downgrade() -> None:
    op.add_column('users', sa.Column('verification_code', sa.String(6), nullable=True))
    op.add_column('users', sa.Column(
        'verification_code_expires_at', sa.DateTime(timezone=True), nullable=True
    ))

    op.drop_index('ix_pending_registrations_email', table_name='pending_registrations')
    op.drop_table('pending_registrations')
