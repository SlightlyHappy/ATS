"""
Analytics models for comprehensive system monitoring and insights.
"""
from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import func, Index
import uuid

class PerformanceMetric(db.Model):
    """Store detailed performance metrics for system monitoring."""
    __tablename__ = 'performance_metrics'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric identification
    metric_type = db.Column(db.String(50), nullable=False)  # cpu, memory, disk, response_time, etc.
    metric_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # system, application, database, queue
    
    # Metric values
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))  # percentage, seconds, bytes, count
    threshold_warning = db.Column(db.Float)
    threshold_critical = db.Column(db.Float)
    
    # Status and context
    status = db.Column(db.String(20), default='normal')  # normal, warning, critical
    tags = db.Column(JSONB)  # Additional metadata
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_perf_metric_type_timestamp', 'metric_type', 'timestamp'),
        Index('idx_perf_category_timestamp', 'category', 'timestamp'),
        Index('idx_perf_status_timestamp', 'status', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<PerformanceMetric {self.metric_name}: {self.value}{self.unit}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'metric_type': self.metric_type,
            'metric_name': self.metric_name,
            'category': self.category,
            'value': self.value,
            'unit': self.unit,
            'status': self.status,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
            'created_at': self.created_at.isoformat()
        }

class UsageInsight(db.Model):
    """Track user behavior and usage patterns."""
    __tablename__ = 'usage_insights'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    
    # Event tracking
    event_type = db.Column(db.String(50), nullable=False)  # login, upload, analysis, download, etc.
    event_category = db.Column(db.String(50), nullable=False)  # authentication, file_processing, analysis
    event_action = db.Column(db.String(100), nullable=False)
    
    # Context and metadata
    session_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.Text)
    
    # Event details
    resource_type = db.Column(db.String(50))  # resume, batch, analysis
    resource_id = db.Column(UUID(as_uuid=True))
    credits_used = db.Column(db.Integer, default=0)
    
    # Performance data
    duration_seconds = db.Column(db.Float)
    success = db.Column(db.Boolean, default=True)
    error_code = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    
    # Additional context
    event_metadata = db.Column(JSONB)  # Flexible storage for event-specific data
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_usage_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_usage_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_usage_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_usage_success_timestamp', 'success', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<UsageInsight {self.event_type} - {self.event_action}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'event_action': self.event_action,
            'session_id': self.session_id,
            'resource_type': self.resource_type,
            'resource_id': str(self.resource_id) if self.resource_id else None,
            'credits_used': self.credits_used,
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'error_code': self.error_code,
            'metadata': self.event_metadata,
            'timestamp': self.timestamp.isoformat()
        }

class ErrorTracking(db.Model):
    """Advanced error tracking and monitoring."""
    __tablename__ = 'error_tracking'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Error identification
    error_code = db.Column(db.String(50), nullable=False)
    error_hash = db.Column(db.String(64), nullable=False)  # Hash for grouping similar errors
    
    # Error classification
    category = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    status = db.Column(db.String(20), default='open')  # open, investigating, resolved, ignored
    
    # Error details
    message = db.Column(db.Text, nullable=False)
    user_message = db.Column(db.Text)
    stack_trace = db.Column(db.Text)
    
    # Context information
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100))
    request_id = db.Column(db.String(100))
    endpoint = db.Column(db.String(200))
    method = db.Column(db.String(10))
    
    # Environment data
    environment = db.Column(db.String(20), default='production')
    python_version = db.Column(db.String(20))
    system_info = db.Column(JSONB)
    
    # Occurrence tracking
    first_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    occurrence_count = db.Column(db.Integer, default=1)
    
    # Resolution tracking
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id'))
    resolution_notes = db.Column(db.Text)
    
    # Additional metadata
    tags = db.Column(JSONB)
    error_metadata = db.Column(JSONB)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for error analytics
    __table_args__ = (
        Index('idx_error_hash', 'error_hash'),
        Index('idx_error_category_severity', 'category', 'severity'),
        Index('idx_error_status_last_seen', 'status', 'last_seen'),
        Index('idx_error_user_timestamp', 'user_id', 'last_seen'),
    )
    
    def __repr__(self):
        return f'<ErrorTracking {self.error_code} - {self.severity}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'error_code': self.error_code,
            'error_hash': self.error_hash,
            'category': self.category,
            'severity': self.severity,
            'status': self.status,
            'message': self.message,
            'user_message': self.user_message,
            'user_id': str(self.user_id) if self.user_id else None,
            'endpoint': self.endpoint,
            'method': self.method,
            'environment': self.environment,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'occurrence_count': self.occurrence_count,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'tags': self.tags,
            'metadata': self.error_metadata
        }

class SystemAlert(db.Model):
    """System-wide alerts and notifications."""
    __tablename__ = 'system_alerts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert identification
    alert_type = db.Column(db.String(50), nullable=False)  # performance, error, security, capacity
    alert_level = db.Column(db.String(20), nullable=False)  # info, warning, error, critical
    alert_source = db.Column(db.String(50), nullable=False)  # monitor, health_check, user_action
    
    # Alert content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    details = db.Column(JSONB)
    
    # Alert lifecycle
    status = db.Column(db.String(20), default='active')  # active, acknowledged, resolved, suppressed
    acknowledged_at = db.Column(db.DateTime)
    acknowledged_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id'))
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id'))
    
    # Alert rules and thresholds
    threshold_value = db.Column(db.Float)
    current_value = db.Column(db.Float)
    comparison_operator = db.Column(db.String(10))  # >, <, >=, <=, ==, !=
    
    # Notification tracking
    notifications_sent = db.Column(db.Integer, default=0)
    last_notification = db.Column(db.DateTime)
    notification_channels = db.Column(JSONB)  # email, webhook, websocket
    
    # Timestamps
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for alert management
    __table_args__ = (
        Index('idx_alert_type_status', 'alert_type', 'status'),
        Index('idx_alert_level_triggered', 'alert_level', 'triggered_at'),
        Index('idx_alert_status_updated', 'status', 'updated_at'),
    )
    
    def __repr__(self):
        return f'<SystemAlert {self.alert_type} - {self.alert_level}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'alert_type': self.alert_type,
            'alert_level': self.alert_level,
            'alert_source': self.alert_source,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'status': self.status,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'threshold_value': self.threshold_value,
            'current_value': self.current_value,
            'notifications_sent': self.notifications_sent,
            'triggered_at': self.triggered_at.isoformat(),
            'created_at': self.created_at.isoformat()
        }

class AnalyticsSnapshot(db.Model):
    """Periodic snapshots of system analytics for historical tracking."""
    __tablename__ = 'analytics_snapshots'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Snapshot metadata
    snapshot_type = db.Column(db.String(20), nullable=False)  # hourly, daily, weekly, monthly
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # User metrics
    total_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    returning_users = db.Column(db.Integer, default=0)
    
    # Analysis metrics
    total_analyses = db.Column(db.Integer, default=0)
    successful_analyses = db.Column(db.Integer, default=0)
    failed_analyses = db.Column(db.Integer, default=0)
    avg_processing_time = db.Column(db.Float, default=0)
    
    # Credit metrics
    credits_used = db.Column(db.Integer, default=0)
    credits_purchased = db.Column(db.Integer, default=0)
    credits_remaining = db.Column(db.Integer, default=0)
    
    # Performance metrics
    avg_response_time = db.Column(db.Float, default=0)
    error_rate = db.Column(db.Float, default=0)
    uptime_percentage = db.Column(db.Float, default=100.0)
    
    # Queue metrics
    queue_throughput = db.Column(db.Integer, default=0)
    avg_queue_wait_time = db.Column(db.Float, default=0)
    max_queue_size = db.Column(db.Integer, default=0)
    
    # System resource metrics
    avg_cpu_usage = db.Column(db.Float, default=0)
    avg_memory_usage = db.Column(db.Float, default=0)
    avg_disk_usage = db.Column(db.Float, default=0)
    
    # Additional analytics data
    top_error_types = db.Column(JSONB)
    user_activity_patterns = db.Column(JSONB)
    performance_trends = db.Column(JSONB)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_snapshot_type_period', 'snapshot_type', 'period_start'),
        Index('idx_snapshot_period_end', 'period_end'),
    )
    
    def __repr__(self):
        return f'<AnalyticsSnapshot {self.snapshot_type} - {self.period_start}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'snapshot_type': self.snapshot_type,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_users': self.total_users,
            'new_users': self.new_users,
            'active_users': self.active_users,
            'total_analyses': self.total_analyses,
            'successful_analyses': self.successful_analyses,
            'failed_analyses': self.failed_analyses,
            'avg_processing_time': self.avg_processing_time,
            'credits_used': self.credits_used,
            'avg_response_time': self.avg_response_time,
            'error_rate': self.error_rate,
            'uptime_percentage': self.uptime_percentage,
            'queue_throughput': self.queue_throughput,
            'avg_cpu_usage': self.avg_cpu_usage,
            'avg_memory_usage': self.avg_memory_usage,
            'top_error_types': self.top_error_types,
            'created_at': self.created_at.isoformat()
        }
