"""Add API management tables (api_keys, rate_limit_rules, webhooks, access_logs)

Revision ID: api_management_v1
Revises: analytics_tables_v1
Create Date: 2025-08-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'api_management_v1'
down_revision = 'analytics_tables_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=128), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True, default=0),
        sa.Column('requests_today', sa.Integer(), nullable=True, default=0),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('key_hash', name='uq_api_keys_key_hash')
    )
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_keys_status', 'api_keys', ['status'])

    # Create rate_limit_rules table
    op.create_table('rate_limit_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('endpoint', sa.String(length=200), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('per_minute', sa.Integer(), nullable=True, default=0),
        sa.Column('per_hour', sa.Integer(), nullable=True, default=0),
        sa.Column('burst', sa.Integer(), nullable=True, default=0),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rate_limits_endpoint_method', 'rate_limit_rules', ['endpoint', 'method'])
    op.create_index('idx_rate_limits_enabled', 'rate_limit_rules', ['enabled'])

    # Create webhooks table
    op.create_table('webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('events', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('secret', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webhooks_status', 'webhooks', ['status'])

    # Create access_logs table
    op.create_table('access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('user_name', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True, default=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_access_logs_action_time', 'access_logs', ['action', 'timestamp'])
    op.create_index('idx_access_logs_success_time', 'access_logs', ['success', 'timestamp'])


def downgrade():
    op.drop_index('idx_access_logs_success_time', table_name='access_logs')
    op.drop_index('idx_access_logs_action_time', table_name='access_logs')
    op.drop_table('access_logs')

    op.drop_index('idx_webhooks_status', table_name='webhooks')
    op.drop_table('webhooks')

    op.drop_index('idx_rate_limits_enabled', table_name='rate_limit_rules')
    op.drop_index('idx_rate_limits_endpoint_method', table_name='rate_limit_rules')
    op.drop_table('rate_limit_rules')

    op.drop_index('idx_api_keys_status', table_name='api_keys')
    op.drop_index('idx_api_keys_user_id', table_name='api_keys')
    op.drop_table('api_keys')
