"""
Performance Monitoring Service - Phase 2 Implementation
Implements comprehensive performance monitoring, alerting, and optimization
recommendations as outlined in the optimization gameplan.
"""
import time
import psutil
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from collections import deque, defaultdict
import json

from flask import current_app, g
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

# =============================================================================
# PERFORMANCE METRICS DATA CLASSES
# =============================================================================

@dataclass
class PerformanceMetric:
    """Single performance metric data point."""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    category: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    
    @property
    def status(self) -> str:
        """Get metric status based on thresholds."""
        if self.threshold_critical and self.value >= self.threshold_critical:
            return 'critical'
        elif self.threshold_warning and self.value >= self.threshold_warning:
            return 'warning'
        else:
            return 'healthy'


@dataclass
class SystemMetrics:
    """System-wide performance metrics snapshot."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_usage: float
    disk_io_read: float
    disk_io_write: float
    network_io_sent: float
    network_io_recv: float
    load_average: List[float]
    process_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'memory_available': self.memory_available,
            'disk_usage': self.disk_usage,
            'disk_io': {
                'read': self.disk_io_read,
                'write': self.disk_io_write
            },
            'network_io': {
                'sent': self.network_io_sent,
                'received': self.network_io_recv
            },
            'load_average': self.load_average,
            'process_count': self.process_count
        }


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    timestamp: datetime
    connection_count: int
    active_connections: int
    idle_connections: int
    query_time_avg: float
    query_time_max: float
    queries_per_second: float
    cache_hit_ratio: Optional[float] = None
    table_scan_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'connections': {
                'total': self.connection_count,
                'active': self.active_connections,
                'idle': self.idle_connections
            },
            'query_performance': {
                'avg_time': self.query_time_avg,
                'max_time': self.query_time_max,
                'queries_per_second': self.queries_per_second
            },
            'cache_hit_ratio': self.cache_hit_ratio,
            'table_scan_ratio': self.table_scan_ratio
        }


@dataclass
class ApplicationMetrics:
    """Application-specific performance metrics."""
    timestamp: datetime
    active_users: int
    requests_per_second: float
    avg_response_time: float
    error_rate: float
    queue_length: int
    queue_processing_rate: float
    cache_hit_rate: float
    memory_usage_app: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'active_users': self.active_users,
            'requests_per_second': self.requests_per_second,
            'avg_response_time': self.avg_response_time,
            'error_rate': self.error_rate,
            'queue': {
                'length': self.queue_length,
                'processing_rate': self.queue_processing_rate
            },
            'cache_hit_rate': self.cache_hit_rate,
            'memory_usage_app': self.memory_usage_app
        }


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    id: str
    timestamp: datetime
    severity: str  # 'warning', 'critical'
    category: str  # 'system', 'database', 'application'
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'category': self.category,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'message': self.message,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


# =============================================================================
# PERFORMANCE MONITORING SERVICE
# =============================================================================

class PerformanceMonitoringService:
    """
    Comprehensive performance monitoring service implementing the optimization
    gameplan monitoring requirements.
    """
    
    def __init__(self, app=None):
        self.app = app
        
        # Configuration
        self.monitoring_interval = 15  # seconds
        self.metrics_retention_hours = 24
        self.alert_cooldown_minutes = 5
        
        # Metrics storage (in-memory circular buffers)
        self.system_metrics_history = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.database_metrics_history = deque(maxlen=1440)
        self.application_metrics_history = deque(maxlen=1440)
        
        # Alerts
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history = deque(maxlen=1000)
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Performance thresholds (from optimization gameplan)
        self.thresholds = {
            'response_time': {'warning': 1.0, 'critical': 2.0},  # seconds
            'error_rate': {'warning': 0.5, 'critical': 1.0},     # percentage
            'memory_usage': {'warning': 85.0, 'critical': 95.0}, # percentage
            'cpu_usage': {'warning': 80.0, 'critical': 90.0},    # percentage
            'cache_hit_rate': {'warning': 60.0, 'critical': 40.0}, # percentage (lower is worse)
            'db_connections': {'warning': 18, 'critical': 25},    # count
            'queue_length': {'warning': 20, 'critical': 50}       # count
        }
        
        # Background monitoring
        self._monitoring_active = False
        # Increase workers to accommodate all monitoring loops without starvation
        self._monitoring_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="perf_monitor")
        
        # Request tracking
        self.request_times = deque(maxlen=1000)
        self.error_count = 0
        self.total_requests = 0
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the performance monitoring service with Flask app."""
        self.app = app
        
        # Load configuration from app
        config = app.config
        self.monitoring_interval = config.get('PERFORMANCE_MONITORING_INTERVAL', 15)
        self.metrics_retention_hours = config.get('METRICS_RETENTION_HOURS', 24)
        
        # Update thresholds from config
        self.thresholds.update({
            'response_time': {
                'warning': config.get('RESPONSE_TIME_THRESHOLD', 1.0),
                'critical': config.get('RESPONSE_TIME_THRESHOLD', 1.0) * 2
            },
            'error_rate': {
                'warning': config.get('ERROR_RATE_THRESHOLD', 0.5),
                'critical': config.get('ERROR_RATE_THRESHOLD', 0.5) * 2
            },
            'memory_usage': {
                'warning': config.get('MEMORY_THRESHOLD', 85),
                'critical': config.get('MEMORY_THRESHOLD', 85) + 10
            },
            'cpu_usage': {
                'warning': config.get('CPU_THRESHOLD', 80),
                'critical': config.get('CPU_THRESHOLD', 80) + 10
            },
            'cache_hit_rate': {
                'warning': config.get('CACHE_HIT_RATE_THRESHOLD', 60),
                'critical': config.get('CACHE_HIT_RATE_THRESHOLD', 60) - 20
            },
            'db_connections': {
                'warning': config.get('DATABASE_CONNECTION_THRESHOLD', 18),
                'critical': config.get('DATABASE_CONNECTION_THRESHOLD', 18) + 7
            }
        })
        
        # Register request hooks for monitoring
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)
        
        # Start background monitoring
        self.start_monitoring()
        
        logger.info("Performance monitoring service initialized")
    
    # =============================================================================
    # MONITORING CONTROL
    # =============================================================================
    
    def start_monitoring(self):
        """Start background performance monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        # Submit monitoring tasks
        self._monitoring_executor.submit(self._monitor_system_metrics)
        self._monitoring_executor.submit(self._monitor_database_metrics)
        self._monitoring_executor.submit(self._monitor_application_metrics)
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background performance monitoring."""
        self._monitoring_active = False
        logger.info("Performance monitoring stopped")
    
    # =============================================================================
    # METRICS COLLECTION
    # =============================================================================
    
    def collect_current_metrics(self) -> Dict[str, Any]:
        """Collect all current performance metrics."""
        try:
            current_time = datetime.utcnow()
            
            # Collect metrics
            system_metrics = self._collect_system_metrics()
            database_metrics = self._collect_database_metrics()
            application_metrics = self._collect_application_metrics()
            
            return {
                'timestamp': current_time.isoformat(),
                'system': system_metrics.to_dict() if system_metrics else None,
                'database': database_metrics.to_dict() if database_metrics else None,
                'application': application_metrics.to_dict() if application_metrics else None,
                'alerts': {
                    'active_count': len(self.active_alerts),
                    'active_alerts': [alert.to_dict() for alert in self.active_alerts.values()]
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting current metrics: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def _collect_system_metrics(self) -> Optional[SystemMetrics]:
        """Collect system-level performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_read = disk_io.read_bytes / (1024**2) if disk_io else 0  # MB
            disk_io_write = disk_io.write_bytes / (1024**2) if disk_io else 0  # MB
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_sent = network_io.bytes_sent / (1024**2) if network_io else 0  # MB
            network_recv = network_io.bytes_recv / (1024**2) if network_io else 0  # MB
            
            # Load average
            try:
                load_avg = list(psutil.getloadavg())
            except (AttributeError, OSError):
                load_avg = [0.0, 0.0, 0.0]  # Windows doesn't have load average
            
            # Process count
            process_count = len(psutil.pids())
            
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                memory_available=memory_available,
                disk_usage=disk_percent,
                disk_io_read=disk_io_read,
                disk_io_write=disk_io_write,
                network_io_sent=network_sent,
                network_io_recv=network_recv,
                load_average=load_avg,
                process_count=process_count
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return None
    
    def _collect_database_metrics(self) -> Optional[DatabaseMetrics]:
        """Collect database performance metrics."""
        try:
            # Get database engine and pool info
            engine = db.engine
            pool = engine.pool
            
            connection_count = pool.size()
            active_connections = pool.checkedout()
            idle_connections = pool.checkedin()
            
            # Query performance metrics
            query_time_avg = 0.0
            query_time_max = 0.0
            queries_per_second = 0.0
            
            try:
                # Get query statistics from PostgreSQL
                result = db.session.execute(text("""
                    SELECT 
                        AVG(mean_time) as avg_time,
                        MAX(max_time) as max_time,
                        SUM(calls) as total_calls
                    FROM pg_stat_statements 
                    WHERE query NOT LIKE '%pg_stat_statements%'
                    LIMIT 1
                """)).fetchone()
                
                if result:
                    query_time_avg = float(result.avg_time or 0) / 1000  # Convert to seconds
                    query_time_max = float(result.max_time or 0) / 1000
                    queries_per_second = float(result.total_calls or 0) / 3600  # Rough estimate
                    
            except Exception as e:
                logger.debug(f"Could not get PostgreSQL query stats: {str(e)}")
            
            return DatabaseMetrics(
                timestamp=datetime.utcnow(),
                connection_count=connection_count,
                active_connections=active_connections,
                idle_connections=idle_connections,
                query_time_avg=query_time_avg,
                query_time_max=query_time_max,
                queries_per_second=queries_per_second
            )
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {str(e)}")
            return None
    
    def _collect_application_metrics(self) -> Optional[ApplicationMetrics]:
        """Collect application-specific performance metrics."""
        try:
            # Active users (rough estimate based on recent activity)
            active_users = self._estimate_active_users()
            
            # Request metrics
            requests_per_second = self._calculate_requests_per_second()
            avg_response_time = self._calculate_avg_response_time()
            error_rate = self._calculate_error_rate()
            
            # Queue metrics
            queue_length = self._get_queue_length()
            queue_processing_rate = self._calculate_queue_processing_rate()
            
            # Cache metrics
            cache_hit_rate = self._get_cache_hit_rate()
            
            # Application memory usage
            current_process = psutil.Process()
            memory_usage_app = current_process.memory_info().rss / (1024**2)  # MB
            
            return ApplicationMetrics(
                timestamp=datetime.utcnow(),
                active_users=active_users,
                requests_per_second=requests_per_second,
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                queue_length=queue_length,
                queue_processing_rate=queue_processing_rate,
                cache_hit_rate=cache_hit_rate,
                memory_usage_app=memory_usage_app
            )
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {str(e)}")
            return None
    
    # =============================================================================
    # METRICS CALCULATION HELPERS
    # =============================================================================
    
    def _estimate_active_users(self) -> int:
        """Estimate active users from recent database activity."""
        try:
            result = db.session.execute(text("""
                SELECT COUNT(DISTINCT user_id) 
                FROM (
                    SELECT user_id FROM analysis_queue 
                    WHERE created_at >= NOW() - INTERVAL '1 hour'
                    UNION
                    SELECT user_id FROM resumes 
                    WHERE created_at >= NOW() - INTERVAL '1 hour'
                ) as active_user_activity
            """)).scalar()
            
            return int(result or 0)
            
        except Exception:
            return 0
    
    def _calculate_requests_per_second(self) -> float:
        """Calculate requests per second from recent request times."""
        if len(self.request_times) < 2:
            return 0.0
        
        now = time.time()
        minute_ago = now - 60
        
        recent_requests = [t for t in self.request_times if t > minute_ago]
        return len(recent_requests) / 60.0
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time from recent requests."""
        if not hasattr(self, '_response_times') or not self._response_times:
            return 0.0
        
        return sum(self._response_times) / len(self._response_times)
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.total_requests == 0:
            return 0.0
        
        return (self.error_count / self.total_requests) * 100
    
    def _get_queue_length(self) -> int:
        """Get current queue length."""
        try:
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM analysis_queue 
                WHERE status IN ('pending', 'processing')
            """)).scalar()
            
            return int(result or 0)
            
        except Exception:
            return 0
    
    def _calculate_queue_processing_rate(self) -> float:
        """Calculate queue processing rate (items per minute)."""
        try:
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM analysis_queue 
                WHERE status = 'completed' 
                AND completed_at >= NOW() - INTERVAL '1 hour'
            """)).scalar()
            
            completed_last_hour = int(result or 0)
            return completed_last_hour / 60.0  # per minute
            
        except Exception:
            return 0.0
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate from enhanced cache service."""
        try:
            # This would integrate with the enhanced cache service
            # For now, return a placeholder
            from app.services.enhanced_cache_service import enhanced_cache
            
            if hasattr(enhanced_cache, 'get_metrics'):
                metrics = enhanced_cache.get_metrics()
                return metrics.get('hit_rate', 0.0)
            
        except Exception:
            pass
        
        return 0.0
    
    # =============================================================================
    # ALERT MANAGEMENT
    # =============================================================================
    
    def check_and_trigger_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and trigger alerts."""
        try:
            current_time = datetime.utcnow()
            
            # Check system metrics
            if metrics.get('system'):
                self._check_system_alerts(metrics['system'], current_time)
            
            # Check database metrics
            if metrics.get('database'):
                self._check_database_alerts(metrics['database'], current_time)
            
            # Check application metrics
            if metrics.get('application'):
                self._check_application_alerts(metrics['application'], current_time)
            
            # Clean up resolved alerts
            self._cleanup_resolved_alerts()
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    def _check_system_alerts(self, system_metrics: Dict[str, Any], timestamp: datetime):
        """Check system metrics for alert conditions."""
        # CPU usage alert
        cpu_usage = system_metrics.get('cpu_usage', 0)
        self._check_metric_threshold(
            'cpu_usage', cpu_usage, 'system', timestamp,
            f"High CPU usage: {cpu_usage:.1f}%"
        )
        
        # Memory usage alert
        memory_usage = system_metrics.get('memory_usage', 0)
        self._check_metric_threshold(
            'memory_usage', memory_usage, 'system', timestamp,
            f"High memory usage: {memory_usage:.1f}%"
        )
        
        # Disk usage alert
        disk_usage = system_metrics.get('disk_usage', 0)
        if disk_usage > 90:  # Hard threshold for disk space
            self._trigger_alert(
                'disk_usage', disk_usage, 90, 'critical', 'system', timestamp,
                f"Critical disk usage: {disk_usage:.1f}%"
            )
    
    def _check_database_alerts(self, db_metrics: Dict[str, Any], timestamp: datetime):
        """Check database metrics for alert conditions."""
        # Connection count alert
        connections = db_metrics.get('connections', {})
        total_connections = connections.get('total', 0)
        
        self._check_metric_threshold(
            'db_connections', total_connections, 'database', timestamp,
            f"High database connection count: {total_connections}"
        )
        
        # Query time alert
        query_perf = db_metrics.get('query_performance', {})
        avg_query_time = query_perf.get('avg_time', 0)
        
        if avg_query_time > 2.0:  # 2 seconds threshold
            self._trigger_alert(
                'query_time', avg_query_time, 2.0, 'warning', 'database', timestamp,
                f"Slow database queries: {avg_query_time:.2f}s average"
            )
    
    def _check_application_alerts(self, app_metrics: Dict[str, Any], timestamp: datetime):
        """Check application metrics for alert conditions."""
        # Response time alert
        response_time = app_metrics.get('avg_response_time', 0)
        self._check_metric_threshold(
            'response_time', response_time, 'application', timestamp,
            f"Slow response time: {response_time:.2f}s"
        )
        
        # Error rate alert
        error_rate = app_metrics.get('error_rate', 0)
        self._check_metric_threshold(
            'error_rate', error_rate, 'application', timestamp,
            f"High error rate: {error_rate:.1f}%"
        )
        
        # Queue length alert
        queue_length = app_metrics.get('queue', {}).get('length', 0)
        self._check_metric_threshold(
            'queue_length', queue_length, 'application', timestamp,
            f"Long queue: {queue_length} items"
        )
        
        # Cache hit rate alert (lower is worse)
        cache_hit_rate = app_metrics.get('cache_hit_rate', 100)
        cache_thresholds = self.thresholds.get('cache_hit_rate', {})
        
        if cache_hit_rate < cache_thresholds.get('critical', 40):
            self._trigger_alert(
                'cache_hit_rate', cache_hit_rate, cache_thresholds['critical'],
                'critical', 'application', timestamp,
                f"Low cache hit rate: {cache_hit_rate:.1f}%"
            )
        elif cache_hit_rate < cache_thresholds.get('warning', 60):
            self._trigger_alert(
                'cache_hit_rate', cache_hit_rate, cache_thresholds['warning'],
                'warning', 'application', timestamp,
                f"Low cache hit rate: {cache_hit_rate:.1f}%"
            )
    
    def _check_metric_threshold(self, metric_name: str, value: float, category: str, 
                               timestamp: datetime, message: str):
        """Check a metric against its configured thresholds."""
        thresholds = self.thresholds.get(metric_name, {})
        
        if value >= thresholds.get('critical', float('inf')):
            self._trigger_alert(
                metric_name, value, thresholds['critical'], 'critical',
                category, timestamp, message
            )
        elif value >= thresholds.get('warning', float('inf')):
            self._trigger_alert(
                metric_name, value, thresholds['warning'], 'warning',
                category, timestamp, message
            )
    
    def _trigger_alert(self, metric_name: str, current_value: float, threshold_value: float,
                      severity: str, category: str, timestamp: datetime, message: str):
        """Trigger a performance alert."""
        alert_key = f"{category}_{metric_name}_{severity}"
        
        # Check cooldown
        if alert_key in self.last_alert_times:
            time_since_last = timestamp - self.last_alert_times[alert_key]
            if time_since_last.total_seconds() < (self.alert_cooldown_minutes * 60):
                return
        
        # Create alert
        alert_id = f"{alert_key}_{int(timestamp.timestamp())}"
        alert = PerformanceAlert(
            id=alert_id,
            timestamp=timestamp,
            severity=severity,
            category=category,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_times[alert_key] = timestamp
        
        logger.warning(f"Performance alert triggered: {message}")
    
    def _cleanup_resolved_alerts(self):
        """Clean up alerts that are no longer active."""
        current_time = datetime.utcnow()
        resolved_alerts = []
        
        for alert_id, alert in self.active_alerts.items():
            # Check if alert condition is resolved
            if self._is_alert_resolved(alert, current_time):
                alert.resolved = True
                alert.resolved_at = current_time
                resolved_alerts.append(alert_id)
        
        # Remove resolved alerts
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]
            logger.info(f"Performance alert resolved: {alert_id}")
    
    def _is_alert_resolved(self, alert: PerformanceAlert, current_time: datetime) -> bool:
        """Check if an alert condition is resolved."""
        # Auto-resolve alerts older than 30 minutes
        if (current_time - alert.timestamp).total_seconds() > 1800:
            return True
        
        # Could implement more sophisticated resolution logic here
        return False
    
    # =============================================================================
    # BACKGROUND MONITORING LOOPS
    # =============================================================================
    
    def _monitor_system_metrics(self):
        """Background loop for system metrics monitoring."""
        while self._monitoring_active:
            try:
                if not self.app:
                    logger.warning("Performance monitor has no app bound; skipping system metrics collection")
                    time.sleep(self.monitoring_interval)
                    continue
                # Ensure Flask application context for any framework-bound operations
                with self.app.app_context():
                    metrics = self._collect_system_metrics()
                    if metrics:
                        self.system_metrics_history.append(metrics)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in system metrics monitoring: {str(e)}")
                time.sleep(self.monitoring_interval)
    
    def _monitor_database_metrics(self):
        """Background loop for database metrics monitoring."""
        while self._monitoring_active:
            try:
                if not self.app:
                    logger.warning("Performance monitor has no app bound; skipping database metrics collection")
                    time.sleep(self.monitoring_interval)
                    continue
                # Database access requires an application context
                with self.app.app_context():
                    metrics = self._collect_database_metrics()
                    if metrics:
                        self.database_metrics_history.append(metrics)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in database metrics monitoring: {str(e)}")
                time.sleep(self.monitoring_interval)
    
    def _monitor_application_metrics(self):
        """Background loop for application metrics monitoring."""
        while self._monitoring_active:
            try:
                if not self.app:
                    logger.warning("Performance monitor has no app bound; skipping application metrics collection")
                    time.sleep(self.monitoring_interval)
                    continue
                # Some helpers use db/session; run under app context
                with self.app.app_context():
                    metrics = self._collect_application_metrics()
                    if metrics:
                        self.application_metrics_history.append(metrics)
                        
                        # Check for alerts
                        all_metrics = {
                            'system': self.system_metrics_history[-1].to_dict() if self.system_metrics_history else None,
                            'database': self.database_metrics_history[-1].to_dict() if self.database_metrics_history else None,
                            'application': metrics.to_dict()
                        }
                        self.check_and_trigger_alerts(all_metrics)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in application metrics monitoring: {str(e)}")
                time.sleep(self.monitoring_interval)
    
    # =============================================================================
    # REQUEST TRACKING
    # =============================================================================
    
    def _before_request(self):
        """Track request start time (per-request via Flask g)."""
        if not hasattr(self, '_response_times'):
            self._response_times = deque(maxlen=1000)
        try:
            g._perf_request_start = time.time()
        except Exception:
            # Fallback if request context is unavailable (shouldn't happen in before_request)
            pass
        self.request_times.append(time.time())
        self.total_requests += 1

    def _after_request(self, response):
        """Track request completion and response time."""
        start_time = None
        try:
            start_time = getattr(g, '_perf_request_start', None)
        except Exception:
            start_time = None
        if start_time:
            response_time = time.time() - start_time
            self._response_times.append(response_time)
        # Track errors by response code
        if getattr(response, 'status_code', 200) >= 400:
            self.error_count += 1
        return response

    def _teardown_request(self, exception):
        """Clean up request tracking."""
        try:
            if hasattr(g, '_perf_request_start'):
                delattr(g, '_perf_request_start')
        except Exception:
            pass
        if exception:
            self.error_count += 1
    
    # =============================================================================
    # METRICS RETRIEVAL
    # =============================================================================
    
    def get_metrics_history(self, hours: int = 1) -> Dict[str, List[Dict]]:
        """Get metrics history for the specified number of hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter metrics by time
        system_history = [
            m.to_dict() for m in self.system_metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        database_history = [
            m.to_dict() for m in self.database_metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        application_history = [
            m.to_dict() for m in self.application_metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        return {
            'system': system_history,
            'database': database_history,
            'application': application_history
        }
    
    def get_current_status(self) -> Dict[str, Any]:
        """Lightweight snapshot of current monitoring status for other services.
        Safe to call from background threads when app context is available."""
        try:
            # If running outside an app/request context, attempt to use bound app
            if self.app:
                with self.app.app_context():
                    current_metrics = self.collect_current_metrics()
            else:
                current_metrics = self.collect_current_metrics()
            
            # Determine overall status from active alerts
            alert_severities = [alert.severity for alert in self.active_alerts.values()]
            if 'critical' in alert_severities:
                overall_status = 'critical'
            elif 'warning' in alert_severities:
                overall_status = 'warning'
            else:
                overall_status = 'healthy'
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': overall_status,
                # Keep key name aligned with callers in integration layer
                'alerts_count': len(self.active_alerts),
                'monitoring_active': self._monitoring_active,
                'metrics': current_metrics
            }
        except Exception as e:
            logger.error(f"Error getting current performance status: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'error',
                'alerts_count': len(self.active_alerts),
                'monitoring_active': self._monitoring_active,
                'error': str(e)
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and health status."""
        current_metrics = self.collect_current_metrics()
        
        # Calculate overall health status
        alert_severities = [alert.severity for alert in self.active_alerts.values()]
        
        if 'critical' in alert_severities:
            overall_status = 'critical'
        elif 'warning' in alert_severities:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'current_metrics': current_metrics,
            'active_alerts_count': len(self.active_alerts),
            'metrics_collected': {
                'system_points': len(self.system_metrics_history),
                'database_points': len(self.database_metrics_history),
                'application_points': len(self.application_metrics_history)
            },
            'monitoring_active': self._monitoring_active,
            'uptime_hours': (datetime.utcnow() - datetime.utcnow().replace(hour=0, minute=0, second=0)).total_seconds() / 3600
        }
    
    def get_alerts(self, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """Get current alerts."""
        alerts = list(self.active_alerts.values())
        
        if include_resolved:
            # Add recent resolved alerts from history
            resolved_alerts = [
                alert for alert in self.alert_history
                if alert.resolved and 
                (datetime.utcnow() - alert.resolved_at).total_seconds() < 3600  # Last hour
            ]
            alerts.extend(resolved_alerts)
        
        return [alert.to_dict() for alert in alerts]


# =============================================================================
# GLOBAL PERFORMANCE MONITORING SERVICE
# =============================================================================

performance_monitor = PerformanceMonitoringService()
