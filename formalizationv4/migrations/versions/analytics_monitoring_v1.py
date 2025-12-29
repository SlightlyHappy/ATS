"""Add enhanced monitoring analytics tables

Revision ID: analytics_monitoring_v1
Revises: sales_intelligence_v1
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'analytics_monitoring_v1'
down_revision = 'sales_intelligence_v1'
branch_labels = None
depends_on = None

def upgrade():
    # Create performance_metrics table
    op.create_table('performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('threshold_warning', sa.Float(), nullable=True),
        sa.Column('threshold_critical', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance_metrics
    op.create_index('idx_perf_metric_type_timestamp', 'performance_metrics', ['metric_type', 'timestamp'])
    op.create_index('idx_perf_category_timestamp', 'performance_metrics', ['category', 'timestamp'])
    op.create_index('idx_perf_status_timestamp', 'performance_metrics', ['status', 'timestamp'])
    
    # Create usage_insights table
    op.create_table('usage_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('event_action', sa.String(length=100), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('credits_used', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for usage_insights
    op.create_index('idx_usage_user_timestamp', 'usage_insights', ['user_id', 'timestamp'])
    op.create_index('idx_usage_event_type_timestamp', 'usage_insights', ['event_type', 'timestamp'])
    op.create_index('idx_usage_session_timestamp', 'usage_insights', ['session_id', 'timestamp'])
    op.create_index('idx_usage_success_timestamp', 'usage_insights', ['success', 'timestamp'])
    
    # Create error_tracking table
    op.create_table('error_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('error_code', sa.String(length=50), nullable=False),
        sa.Column('error_hash', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('endpoint', sa.String(length=200), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('environment', sa.String(length=20), nullable=True),
        sa.Column('python_version', sa.String(length=20), nullable=True),
        sa.Column('system_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.Column('occurrence_count', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['resolved_by'], ['admin_users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for error_tracking
    op.create_index('idx_error_hash', 'error_tracking', ['error_hash'])
    op.create_index('idx_error_category_severity', 'error_tracking', ['category', 'severity'])
    op.create_index('idx_error_status_last_seen', 'error_tracking', ['status', 'last_seen'])
    op.create_index('idx_error_user_timestamp', 'error_tracking', ['user_id', 'last_seen'])
    
    # Create system_alerts table
    op.create_table('system_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('alert_level', sa.String(length=20), nullable=False),
        sa.Column('alert_source', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('comparison_operator', sa.String(length=10), nullable=True),
        sa.Column('notifications_sent', sa.Integer(), nullable=True),
        sa.Column('last_notification', sa.DateTime(), nullable=True),
        sa.Column('notification_channels', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['admin_users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['admin_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for system_alerts
    op.create_index('idx_alert_type_status', 'system_alerts', ['alert_type', 'status'])
    op.create_index('idx_alert_level_triggered', 'system_alerts', ['alert_level', 'triggered_at'])
    op.create_index('idx_alert_status_updated', 'system_alerts', ['status', 'updated_at'])
    
    # Create analytics_snapshots table
    op.create_table('analytics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_type', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_users', sa.Integer(), nullable=True),
        sa.Column('new_users', sa.Integer(), nullable=True),
        sa.Column('active_users', sa.Integer(), nullable=True),
        sa.Column('returning_users', sa.Integer(), nullable=True),
        sa.Column('total_analyses', sa.Integer(), nullable=True),
        sa.Column('successful_analyses', sa.Integer(), nullable=True),
        sa.Column('failed_analyses', sa.Integer(), nullable=True),
        sa.Column('avg_processing_time', sa.Float(), nullable=True),
        sa.Column('credits_used', sa.Integer(), nullable=True),
        sa.Column('credits_purchased', sa.Integer(), nullable=True),
        sa.Column('credits_remaining', sa.Integer(), nullable=True),
        sa.Column('avg_response_time', sa.Float(), nullable=True),
        sa.Column('error_rate', sa.Float(), nullable=True),
        sa.Column('uptime_percentage', sa.Float(), nullable=True),
        sa.Column('queue_throughput', sa.Integer(), nullable=True),
        sa.Column('avg_queue_wait_time', sa.Float(), nullable=True),
        sa.Column('max_queue_size', sa.Integer(), nullable=True),
        sa.Column('avg_cpu_usage', sa.Float(), nullable=True),
        sa.Column('avg_memory_usage', sa.Float(), nullable=True),
        sa.Column('avg_disk_usage', sa.Float(), nullable=True),
        sa.Column('top_error_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_activity_patterns', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_trends', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for analytics_snapshots
    op.create_index('idx_snapshot_type_period', 'analytics_snapshots', ['snapshot_type', 'period_start'])
    op.create_index('idx_snapshot_period_end', 'analytics_snapshots', ['period_end'])

def downgrade():
    # Drop analytics_snapshots table
    op.drop_index('idx_snapshot_period_end', table_name='analytics_snapshots')
    op.drop_index('idx_snapshot_type_period', table_name='analytics_snapshots')
    op.drop_table('analytics_snapshots')
    
    # Drop system_alerts table
    op.drop_index('idx_alert_status_updated', table_name='system_alerts')
    op.drop_index('idx_alert_level_triggered', table_name='system_alerts')
    op.drop_index('idx_alert_type_status', table_name='system_alerts')
    op.drop_table('system_alerts')
    
    # Drop error_tracking table
    op.drop_index('idx_error_user_timestamp', table_name='error_tracking')
    op.drop_index('idx_error_status_last_seen', table_name='error_tracking')
    op.drop_index('idx_error_category_severity', table_name='error_tracking')
    op.drop_index('idx_error_hash', table_name='error_tracking')
    op.drop_table('error_tracking')
    
    # Drop usage_insights table
    op.drop_index('idx_usage_success_timestamp', table_name='usage_insights')
    op.drop_index('idx_usage_session_timestamp', table_name='usage_insights')
    op.drop_index('idx_usage_event_type_timestamp', table_name='usage_insights')
    op.drop_index('idx_usage_user_timestamp', table_name='usage_insights')
    op.drop_table('usage_insights')
    
    # Drop performance_metrics table
    op.drop_index('idx_perf_status_timestamp', table_name='performance_metrics')
    op.drop_index('idx_perf_category_timestamp', table_name='performance_metrics')
    op.drop_index('idx_perf_metric_type_timestamp', table_name='performance_metrics')
    op.drop_table('performance_metrics')
