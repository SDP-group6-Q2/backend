"""drop fields duplicated by mcp-server's assistant dataset, drop client table

Revision ID: 3aca9460fa6c
Revises: dc842d66120d
Create Date: 2026-09-17 00:00:00.000000

Backend is a thin layer: auth, the assistant interface, and conversation
history. Everything below is data mcp-server's `assistant` database already
owns (assistant.users has firstname/lastname/email/jobtitle/visibility/
companyid; assistant.companies has companyname/country/sector/city/currency/
locale) -- a repo-wide grep found zero places in backend's own code that
branch on any of it, so nothing here was ever more than an unused/unfinished
local copy. Dropped in favor of fetching live via user_id when needed (see
app/services/mcp_directory_client.py).

The `client` table itself is dropped too: once its only real column
(company_id) is gone (superseded by deriving company transitively through
user.user_id), it held no data of its own -- just a second bridge key
duplicating what user_id already resolves to. Superusers (platform admins,
not scoped to any customer company) previously needed a placeholder Client
row just to satisfy the FK; dropping user.client_id removes that requirement
entirely.
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
    op.drop_column('user', 'first_name')
    op.drop_column('user', 'last_name')
    op.drop_column('user', 'job_title')

    op.drop_constraint('user_client_id_fkey', 'user', type_='foreignkey')
    op.drop_column('user', 'client_id')

    op.drop_table('client')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'client',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.String(length=20), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('locale', sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_client_company_id', 'client', ['company_id'], unique=True)
    op.create_index('ix_client_name', 'client', ['name'], unique=True)

    # NB: client_id is added back NOT NULL-able only (nullable=True) since there is
    # no data to backfill it with -- a stricter downgrade would need manual repair.
    op.add_column('user', sa.Column('client_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('user_client_id_fkey', 'user', 'client', ['client_id'], ['id'])

    op.add_column('user', sa.Column('job_title', sa.String(length=100), nullable=True))
    op.add_column('user', sa.Column('last_name', sa.String(length=50), nullable=True))
    op.add_column('user', sa.Column('first_name', sa.String(length=50), nullable=True))
    op.add_column('user', sa.Column('visibility', sa.String(length=20), nullable=True))
    op.create_check_constraint(
        'ck_user_visibility',
        'user',
        "visibility IN ('full', 'technician', 'commercial')",
    )
