"""drop visibility from user table

Revision ID: 3aca9460fa6c
Revises: dc842d66120d
Create Date: 2026-09-17 00:00:00.000000

visibility duplicated mcp-server's assistant.users.visibility, which is the
only place it was ever actually enforced (a repo-wide grep found zero places
in backend's own code that branched on it) -- dropped in favor of fetching it
live from mcp-server when needed, via user_id (see app/services/mcp_directory_client.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3aca9460fa6c'
down_revision: Union[str, Sequence[str], None] = 'dc842d66120d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('ck_user_visibility', 'user', type_='check')
    op.drop_column('user', 'visibility')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('user', sa.Column('visibility', sa.String(length=20), nullable=True))
    op.create_check_constraint(
        'ck_user_visibility',
        'user',
        "visibility IN ('full', 'technician', 'commercial')",
    )
