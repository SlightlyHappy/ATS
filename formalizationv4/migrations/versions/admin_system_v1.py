"""Add admin and system tables

Revision ID: admin_system_v1
Revises: initial_schema_v1
Create Date: 2025-08-05 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'admin_system_v1'
down_revision = 'initial_schema_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Create admin_users table
    op.create_table('admin_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('admin_level', sa.String(length=50), nullable=False, default='admin'),
        sa.Column('permissions', postgresql.JSONB(), nullable=True),
        sa.Column('last_admin_login', sa.DateTime(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_admin_users_user_id', 'admin_users', ['user_id'], unique=True)

    # Create admin_actions table
    op.create_table('admin_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_admin_actions_admin_user', 'admin_actions', ['admin_user_id'])
    op.create_index('idx_admin_actions_type', 'admin_actions', ['action_type'])

    # Create system_configurations table
    op.create_table('system_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('data_type', sa.String(length=20), nullable=False, default='string'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True, default=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_system_configurations_key', 'system_configurations', ['key'], unique=True)

    # Create admin_notifications table
    op.create_table('admin_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, default='medium'),
        sa.Column('is_read', sa.Boolean(), nullable=True, default=False),
        sa.Column('read_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['read_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_admin_notifications_type', 'admin_notifications', ['notification_type'])
    op.create_index('idx_admin_notifications_priority', 'admin_notifications', ['priority'])


def downgrade():
    op.drop_table('admin_notifications')
    op.drop_table('system_configurations')
    op.drop_table('admin_actions')
    op.drop_table('admin_users')
