"""Add analytics tables

Revision ID: analytics_tables_v1
Revises: candidate_tables_v1
Create Date: 2025-08-05 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'analytics_tables_v1'
down_revision = 'candidate_tables_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Create performance_metrics table
    op.create_table('performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_category', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(length=20), nullable=True),
        sa.Column('metric_date', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_performance_metrics_name', 'performance_metrics', ['metric_name'])
    op.create_index('idx_performance_metrics_category', 'performance_metrics', ['metric_category'])
    op.create_index('idx_performance_metrics_date', 'performance_metrics', ['metric_date'])

    # Create usage_insights table
    op.create_table('usage_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('feature_name', sa.String(length=100), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True, default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_usage_insights_user_id', 'usage_insights', ['user_id'])
    op.create_index('idx_usage_insights_feature', 'usage_insights', ['feature_name'])
    op.create_index('idx_usage_insights_action', 'usage_insights', ['action_type'])
    op.create_index('idx_usage_insights_created_at', 'usage_insights', ['created_at'])

    # Create error_tracking table
    op.create_table('error_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('request_path', sa.String(length=500), nullable=True),
        sa.Column('request_method', sa.String(length=10), nullable=True),
        sa.Column('http_status_code', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, default='error'),
        sa.Column('resolved', sa.Boolean(), nullable=False, default=False),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_error_tracking_user_id', 'error_tracking', ['user_id'])
    op.create_index('idx_error_tracking_type', 'error_tracking', ['error_type'])
    op.create_index('idx_error_tracking_severity', 'error_tracking', ['severity'])
    op.create_index('idx_error_tracking_created_at', 'error_tracking', ['created_at'])

    # Create system_alerts table
    op.create_table('system_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, default='info'),
        sa.Column('status', sa.String(length=20), nullable=False, default='active'),
        sa.Column('triggered_by', sa.String(length=100), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_system_alerts_type', 'system_alerts', ['alert_type'])
    op.create_index('idx_system_alerts_severity', 'system_alerts', ['severity'])
    op.create_index('idx_system_alerts_status', 'system_alerts', ['status'])
    op.create_index('idx_system_alerts_created_at', 'system_alerts', ['created_at'])

    # Create analytics_snapshots table
    op.create_table('analytics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('snapshot_type', sa.String(length=50), nullable=False),
        sa.Column('total_users', sa.Integer(), nullable=True, default=0),
        sa.Column('active_users', sa.Integer(), nullable=True, default=0),
        sa.Column('total_resumes', sa.Integer(), nullable=True, default=0),
        sa.Column('resumes_analyzed', sa.Integer(), nullable=True, default=0),
        sa.Column('total_analyses', sa.Integer(), nullable=True, default=0),
        sa.Column('successful_analyses', sa.Integer(), nullable=True, default=0),
        sa.Column('failed_analyses', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_analysis_time_seconds', sa.Float(), nullable=True),
        sa.Column('system_uptime_percentage', sa.Float(), nullable=True),
        sa.Column('error_rate_percentage', sa.Float(), nullable=True),
        sa.Column('performance_score', sa.Float(), nullable=True),
        sa.Column('user_satisfaction_score', sa.Float(), nullable=True),
        sa.Column('detailed_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analytics_snapshots_date', 'analytics_snapshots', ['snapshot_date'])
    op.create_index('idx_analytics_snapshots_type', 'analytics_snapshots', ['snapshot_type'])


def downgrade():
    op.drop_table('analytics_snapshots')
    op.drop_table('system_alerts')
    op.drop_table('error_tracking')
    op.drop_table('usage_insights')
    op.drop_table('performance_metrics')
