"""merge heads

Revision ID: 941ae7daa8ce
Revises: 51c528af1935, a1b2c3d4e5f6
Create Date: 2026-10-07 13:22:18.421363

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '941ae7daa8ce'
down_revision = ('51c528af1935', 'a1b2c3d4e5f6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
