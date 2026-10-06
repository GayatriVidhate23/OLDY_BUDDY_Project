"""Merge multiple heads from branches

Revision ID: 459889842bec
Revises: 51c528af1935, a1b2c3d4e5f6
Create Date: 2026-10-06 13:30:56.381897

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '459889842bec'
down_revision = ('51c528af1935', 'a1b2c3d4e5f6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
