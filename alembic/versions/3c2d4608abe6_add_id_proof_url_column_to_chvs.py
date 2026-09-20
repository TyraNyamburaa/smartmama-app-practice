"""Add id_proof_url column to chvs

Revision ID: 3c2d4608abe6
Revises: 8b9c0d1e2f3a
Create Date: 2026-09-20 12:05:22.104591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c2d4608abe6'
down_revision: Union[str, Sequence[str], None] = '8b9c0d1e2f3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chvs', sa.Column('id_proof_url', sa.String(500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chvs', 'id_proof_url')
