"""add reset_otps table for password reset OTP flow

Revision ID: 7a1b2c3d4e5f
Revises: 0003c0d56c4a
Create Date: 2026-09-04 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '7a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '0003c0d56c4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'reset_otps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('otp_code', sa.String(length=12), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_reset_otps_id', 'reset_otps', ['id'])
    op.create_index('ix_reset_otps_user_id', 'reset_otps', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_reset_otps_user_id', table_name='reset_otps')
    op.drop_index('ix_reset_otps_id', table_name='reset_otps')
    op.drop_table('reset_otps')
