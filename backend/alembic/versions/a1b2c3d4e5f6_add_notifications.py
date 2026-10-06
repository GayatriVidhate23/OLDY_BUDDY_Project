"""Add Notifications and UserDevices tables

Revision ID: a1b2c3d4e5f6
Revises: 80ca1649d478
Create Date: 2026-10-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '80ca1649d478'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=True),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_attempt_at', sa.DateTime(), nullable=False),
        sa.Column('provider_message_id', sa.String(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['alert_id'], ['alert_notifications.id'], ),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_alert_id'), 'notifications', ['alert_id'], unique=False)
    op.create_index(op.f('ix_notifications_recipient_id'), 'notifications', ['recipient_id'], unique=False)

    # 2. Create user_devices table
    op.create_table(
        'user_devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('push_token', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('device_type', sa.String(), nullable=False, server_default='android'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_devices_id'), 'user_devices', ['id'], unique=False)
    op.create_index(op.f('ix_user_devices_user_id'), 'user_devices', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_devices_push_token'), 'user_devices', ['push_token'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_user_devices_push_token'), table_name='user_devices')
    op.drop_index(op.f('ix_user_devices_user_id'), table_name='user_devices')
    op.drop_index(op.f('ix_user_devices_id'), table_name='user_devices')
    op.drop_table('user_devices')

    op.drop_index(op.f('ix_notifications_recipient_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_alert_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
