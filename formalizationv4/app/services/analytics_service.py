"""
Enhanced analytics service for comprehensive system monitoring and insights.
Implements Priority 1.3: Enhanced Monitoring features.
"""
import hashlib
import logging
import psutil
import platform
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import sessionmaker
from flask import request, g

from app import db
from app.models.analytics import (
    PerformanceMetric, UsageInsight, ErrorTracking, 
    SystemAlert, AnalyticsSnapshot
)
from app.models.user import User, CreditTransaction
from app.models.resume import Resume
from app.models.analysis import Analysis
from app.models.queue import AnalysisQueue, QueueStatus
from app.services.error_handler import ApplicationError, ErrorCategory, ErrorSeverity

class AnalyticsService:
    """Comprehensive analytics and monitoring service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    # ========== Performance Analytics ==========
    
    def record_performance_metric(self, metric_type: str, metric_name: str, 
                                category: str, value: float, unit: str = None,
                                threshold_warning: float = None, 
                                threshold_critical: float = None,
                                tags: Dict = None) -> PerformanceMetric:
        """Record a performance metric with improved session management."""
        try:
            # Skip analytics if disabled to prevent database lock issues
            if not os.environ.get('ANALYTICS_ENABLED', 'true').lower() == 'true':
                return None
                
            # Determine status based on thresholds
            status = 'normal'
            if threshold_critical and value >= threshold_critical:
                status = 'critical'
            elif threshold_warning and value >= threshold_warning:
                status = 'warning'
            
            metric = PerformanceMetric(
                metric_type=metric_type,
                metric_name=metric_name,
                category=category,
                value=value,
                unit=unit,
                threshold_warning=threshold_warning,
                threshold_critical=threshold_critical,
                status=status,
                tags=tags or {}
            )
            
            # Use a separate session to avoid locking issues
            Session = sessionmaker(bind=db.engine)
            session = Session()
            
            try:
                session.add(metric)
                session.commit()
                # Emit performance metric to admins (non-blocking best-effort)
                try:
                    from flask import current_app
                    payload = {
                        'metric_type': metric_type,
                        'metric_name': metric_name,
                        'category': category,
                        'value': value,
                        'unit': unit,
                        'status': 'normal' if not threshold_warning and not threshold_critical else (
                            'critical' if (threshold_critical and value >= threshold_critical) else (
                                'warning' if (threshold_warning and value >= threshold_warning) else 'normal'
                            )
                        ),
                        'tags': tags or {},
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    if hasattr(current_app, 'websocket_service') and current_app.websocket_service:
                        current_app.websocket_service.socketio.emit('performance_metric', payload, room='admin_dashboard')
                except Exception:
                    pass
                
                # Trigger alert if critical (but don't block on it)
                if status == 'critical':
                    try:
                        self._create_performance_alert(metric)
                    except Exception as alert_error:
                        self.logger.warning(f"Failed to create alert: {alert_error}")
                
                return metric
            finally:
                session.close()
            
        except Exception as e:
            self.logger.error(f"Failed to record performance metric: {str(e)}")
            # Don't raise exception - analytics shouldn't break the app
            return None
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system performance metrics with enhanced monitoring."""
        try:
            metrics = {}
            
            # System resource metrics with enhanced monitoring
            cpu_times = psutil.cpu_times()
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            net_io = psutil.net_io_counters()
            
            # Process-specific metrics
            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            process_cpu = current_process.cpu_percent()
            
            # Enhanced system metrics recording
            self.record_performance_metric('cpu', 'cpu_usage_percent', 'system', 
                                         cpu_percent, 'percent', 70, 85,
                                         tags={'cpu_count': cpu_count, 'cores': cpu_count})
            
            self.record_performance_metric('cpu', 'cpu_user_time', 'system', 
                                         cpu_times.user, 'seconds')
            
            self.record_performance_metric('cpu', 'cpu_system_time', 'system', 
                                         cpu_times.system, 'seconds')
            
            self.record_performance_metric('memory', 'memory_usage_percent', 'system', 
                                         memory.percent, 'percent', 80, 90,
                                         tags={'total_mb': memory.total // (1024*1024)})
            
            self.record_performance_metric('memory', 'memory_available_bytes', 'system', 
                                         memory.available, 'bytes')
            
            self.record_performance_metric('memory', 'swap_usage_percent', 'system', 
                                         swap.percent, 'percent', 50, 75)
            
            self.record_performance_metric('disk', 'disk_usage_percent', 'system', 
                                         disk.percent, 'percent', 85, 95)
            
            if disk_io:
                self.record_performance_metric('disk', 'disk_read_bytes_per_sec', 'system', 
                                             disk_io.read_bytes, 'bytes/sec')
                
                self.record_performance_metric('disk', 'disk_write_bytes_per_sec', 'system', 
                                             disk_io.write_bytes, 'bytes/sec')
            
            # Network metrics
            if net_io:
                self.record_performance_metric('network', 'network_bytes_sent', 'system', 
                                             net_io.bytes_sent, 'bytes')
                
                self.record_performance_metric('network', 'network_bytes_recv', 'system', 
                                             net_io.bytes_recv, 'bytes')
            
            # Process-specific metrics
            self.record_performance_metric('process', 'process_memory_mb', 'application', 
                                         process_memory.rss // (1024*1024), 'mb')
            
            self.record_performance_metric('process', 'process_cpu_percent', 'application', 
                                         process_cpu, 'percent', 50, 80)
            
            # Database metrics
            db_metrics = self._collect_database_metrics()
            
            # Queue metrics
            queue_metrics = self._collect_queue_metrics()
            
            # Application metrics
            app_metrics = self._collect_application_metrics()
            
            metrics.update({
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent,
                    'disk_free': disk.free
                },
                'database': db_metrics,
                'queue': queue_metrics,
                'application': app_metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Emit health update for admin dashboards (best-effort)
            try:
                from flask import current_app
                if hasattr(current_app, 'websocket_service') and current_app.websocket_service:
                    payload = {
                        'api_status': 'healthy',
                        'database_status': db_metrics.get('status', 'unknown') if isinstance(db_metrics, dict) else 'unknown',
                        'ai_service_status': 'healthy',
                        'queue_worker_status': queue_metrics.get('health', 'unknown') if isinstance(queue_metrics, dict) else 'unknown',
                        'response_ms': int((db_metrics.get('basic_response_time', 0) or 0) * 1000) if isinstance(db_metrics, dict) else None,
                        'uptime_pct': app_metrics.get('health_score', 100) if isinstance(app_metrics, dict) else 100,
                        'timestamp': metrics['timestamp']
                    }
                    current_app.websocket_service.socketio.emit('health_update', payload, room='admin_dashboard')
            except Exception:
                pass
            
            return metrics
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive database performance metrics."""
        try:
            # Connection pool info
            pool = db.engine.pool
            pool_metrics = {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid_connections': getattr(pool, 'invalidated', 0)  # Safer attribute access
            }
            
            # Record pool metrics
            self.record_performance_metric('database', 'pool_checked_out', 'database', 
                                         pool.checkedout(), 'count', 
                                         pool.size() * 0.7, pool.size() * 0.9)
            
            # Query performance with multiple tests
            start_time = datetime.utcnow()
            db.session.execute(db.text('SELECT 1')).fetchone()
            basic_response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Test table count query (more realistic)
            start_time = datetime.utcnow()
            result = db.session.execute(db.text('SELECT COUNT(*) FROM users')).fetchone()
            user_count = result[0] if result else 0
            count_query_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Test join query performance
            start_time = datetime.utcnow()
            db.session.execute(db.text('''
                SELECT COUNT(*) FROM analysis_queue aq 
                LEFT JOIN users u ON aq.user_id = u.id 
                WHERE aq.created_at > NOW() - INTERVAL '1 hour'
            ''')).fetchone()
            join_query_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Record database response times
            self.record_performance_metric('database', 'basic_response_time', 'database', 
                                         basic_response_time, 'seconds', 0.5, 2.0)
            
            self.record_performance_metric('database', 'count_query_time', 'database', 
                                         count_query_time, 'seconds', 1.0, 3.0)
            
            self.record_performance_metric('database', 'join_query_time', 'database', 
                                         join_query_time, 'seconds', 2.0, 5.0)
            
            # Database size metrics (PostgreSQL specific)
            try:
                size_result = db.session.execute(db.text(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                )).fetchone()
                db_size = size_result[0] if size_result else 'Unknown'
                
                # Table sizes
                table_sizes = db.session.execute(db.text('''
                    SELECT schemaname, tablename, 
                           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
                    LIMIT 10
                ''')).fetchall()
                
                largest_tables = [
                    {'table': row[1], 'size': row[2]} 
                    for row in table_sizes
                ]
                
            except Exception as db_size_error:
                self.logger.warning(f"Could not get database size info: {db_size_error}")
                db_size = 'Unknown'
                largest_tables = []
            
            # Active connections
            try:
                active_connections = db.session.execute(db.text(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )).fetchone()[0]
                
                self.record_performance_metric('database', 'active_connections', 'database', 
                                             active_connections, 'count', 20, 50)
            except Exception:
                active_connections = 0
            
            return {
                'basic_response_time': basic_response_time,
                'count_query_time': count_query_time,
                'join_query_time': join_query_time,
                'pool_metrics': pool_metrics,
                'user_count': user_count,
                'database_size': db_size,
                'largest_tables': largest_tables,
                'active_connections': active_connections,
                'status': 'healthy' if basic_response_time < 1.0 else 'slow'
            }
            
        except Exception as e:
            self.logger.error(f"Database metrics collection failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _collect_queue_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive queue performance metrics."""
        try:
            # Queue statistics
            total_queued = AnalysisQueue.query.count()
            pending = AnalysisQueue.query.filter_by(status=QueueStatus.PENDING.value).count()
            processing = AnalysisQueue.query.filter_by(status=QueueStatus.PROCESSING.value).count()
            completed = AnalysisQueue.query.filter_by(status=QueueStatus.COMPLETED.value).count()
            failed = AnalysisQueue.query.filter_by(status=QueueStatus.FAILED.value).count()
            
            # Time-based analysis
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            last_week = now - timedelta(days=7)
            
            # Recent activity metrics
            recent_1h = AnalysisQueue.query.filter(AnalysisQueue.created_at >= last_hour).count()
            recent_24h = AnalysisQueue.query.filter(AnalysisQueue.created_at >= last_24h).count()
            recent_week = AnalysisQueue.query.filter(AnalysisQueue.created_at >= last_week).count()
            
            # Completion rate analysis
            completed_1h = AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.COMPLETED.value,
                    AnalysisQueue.completed_at >= last_hour
                )
            ).count()
            
            completed_24h = AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.COMPLETED.value,
                    AnalysisQueue.completed_at >= last_24h
                )
            ).count()
            
            # Failed analysis in last 24h
            failed_24h = AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.FAILED.value,
                    AnalysisQueue.updated_at >= last_24h
                )
            ).count()
            
            # Stuck processing jobs (processing > 10 minutes)
            stuck_cutoff = now - timedelta(minutes=10)
            stuck_jobs = AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.PROCESSING.value,
                    AnalysisQueue.started_at < stuck_cutoff
                )
            ).count()
            
            # Average processing time (last 24 hours)
            recent_completed = AnalysisQueue.query.filter(
                and_(
                    AnalysisQueue.status == QueueStatus.COMPLETED.value,
                    AnalysisQueue.completed_at >= last_24h,
                    AnalysisQueue.completed_at.isnot(None),
                    AnalysisQueue.started_at.isnot(None)
                )
            ).all()
            
            processing_times = []
            wait_times = []
            for item in recent_completed:
                if item.completed_at and item.started_at:
                    processing_time = (item.completed_at - item.started_at).total_seconds()
                    processing_times.append(processing_time)
                    
                    # Calculate wait time (created to started)
                    if item.created_at:
                        wait_time = (item.started_at - item.created_at).total_seconds()
                        wait_times.append(wait_time)
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
            max_processing_time = max(processing_times) if processing_times else 0
            min_processing_time = min(processing_times) if processing_times else 0
            
            # Success rate calculations
            success_rate_1h = (completed_1h / recent_1h * 100) if recent_1h > 0 else 100
            success_rate_24h = (completed_24h / recent_24h * 100) if recent_24h > 0 else 100
            
            # Throughput (items per hour)
            throughput_1h = completed_1h
            throughput_24h = completed_24h / 24 if completed_24h > 0 else 0
            
            # Record enhanced queue metrics
            self.record_performance_metric('queue', 'pending_count', 'queue', 
                                         pending, 'count', 50, 100)
            
            self.record_performance_metric('queue', 'processing_count', 'queue', 
                                         processing, 'count', 5, 10)
            
            self.record_performance_metric('queue', 'failed_count_24h', 'queue', 
                                         failed_24h, 'count', 5, 15)
            
            self.record_performance_metric('queue', 'stuck_jobs', 'queue', 
                                         stuck_jobs, 'count', 0, 2)
            
            if avg_processing_time > 0:
                self.record_performance_metric('queue', 'avg_processing_time', 'queue', 
                                             avg_processing_time, 'seconds', 120, 300)
            
            if avg_wait_time > 0:
                self.record_performance_metric('queue', 'avg_wait_time', 'queue', 
                                             avg_wait_time, 'seconds', 30, 120)
            
            self.record_performance_metric('queue', 'success_rate_24h', 'queue', 
                                         success_rate_24h, 'percent', 90, 95)
            
            self.record_performance_metric('queue', 'throughput_per_hour', 'queue', 
                                         throughput_24h, 'items/hour')
            
            return {
                'total_queued': total_queued,
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'failed': failed,
                'failed_24h': failed_24h,
                'stuck_jobs': stuck_jobs,
                'recent_activity': {
                    'last_1h': recent_1h,
                    'last_24h': recent_24h,
                    'last_week': recent_week
                },
                'completion_stats': {
                    'completed_1h': completed_1h,
                    'completed_24h': completed_24h
                },
                'timing_stats': {
                    'avg_processing_time': avg_processing_time,
                    'avg_wait_time': avg_wait_time,
                    'max_processing_time': max_processing_time,
                    'min_processing_time': min_processing_time
                },
                'performance_metrics': {
                    'success_rate_1h': success_rate_1h,
                    'success_rate_24h': success_rate_24h,
                    'throughput_1h': throughput_1h,
                    'throughput_24h': throughput_24h
                },
                'health': 'healthy' if pending < 50 and failed_24h < 10 and stuck_jobs == 0 else 'warning'
            }
            
        except Exception as e:
            self.logger.error(f"Queue metrics collection failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _collect_application_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive application-specific metrics."""
        try:
            # User metrics
            total_users = User.query.count()
            active_users_24h = self._get_active_users_count(hours=24)
            active_users_7d = self._get_active_users_count(hours=24*7)
            
            # New user registrations
            new_users_24h = User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            new_users_7d = User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Analysis metrics
            total_analyses = Analysis.query.count()
            analyses_24h = Analysis.query.filter(
                Analysis.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            analyses_7d = Analysis.query.filter(
                Analysis.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Success rate
            successful_analyses_24h = Analysis.query.filter(
                and_(
                    Analysis.created_at >= datetime.utcnow() - timedelta(hours=24),
                    Analysis.status == 'completed'
                )
            ).count()
            
            success_rate = (successful_analyses_24h / analyses_24h * 100) if analyses_24h > 0 else 100
            
            # Credit metrics - CreditTransaction already imported at the top
            
            total_credits_used_24h = db.session.query(
                func.sum(CreditTransaction.amount)
            ).filter(
                and_(
                    CreditTransaction.transaction_type == 'debit',
                    CreditTransaction.created_at >= datetime.utcnow() - timedelta(hours=24)
                )
            ).scalar() or 0
            
            total_credits_used_7d = db.session.query(
                func.sum(CreditTransaction.amount)
            ).filter(
                and_(
                    CreditTransaction.transaction_type == 'debit',
                    CreditTransaction.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).scalar() or 0
            
            # Average credits per user
            total_user_credits = db.session.query(
                func.sum(User.credits_balance)
            ).scalar() or 0
            
            avg_credits_per_user = total_user_credits / total_users if total_users > 0 else 0
            
            # Resume upload metrics
            resumes_uploaded_24h = Resume.query.filter(
                Resume.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            resumes_uploaded_7d = Resume.query.filter(
                Resume.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Error rate calculation
            from app.models.analytics import ErrorTracking
            errors_24h = ErrorTracking.query.filter(
                ErrorTracking.first_seen >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            # Calculate overall application health score
            health_score = 100
            
            # Deduct points for various issues
            if success_rate < 95:
                health_score -= (95 - success_rate) * 2
            if errors_24h > 10:
                health_score -= min(errors_24h * 2, 30)
            if active_users_24h == 0 and total_users > 0:
                health_score -= 20
            
            # Record application metrics
            self.record_performance_metric('application', 'active_users_24h', 'application', 
                                         active_users_24h, 'count')
            
            self.record_performance_metric('application', 'analyses_24h', 'application', 
                                         analyses_24h, 'count')
            
            self.record_performance_metric('application', 'success_rate', 'application', 
                                         success_rate, 'percent', 90, 95)
            
            self.record_performance_metric('application', 'credits_used_24h', 'application', 
                                         abs(total_credits_used_24h), 'count')
            
            self.record_performance_metric('application', 'error_count_24h', 'application', 
                                         errors_24h, 'count', 5, 15)
            
            return {
                'user_metrics': {
                    'total_users': total_users,
                    'active_users_24h': active_users_24h,
                    'active_users_7d': active_users_7d,
                    'new_users_24h': new_users_24h,
                    'new_users_7d': new_users_7d
                },
                'analysis_metrics': {
                    'total_analyses': total_analyses,
                    'analyses_24h': analyses_24h,
                    'analyses_7d': analyses_7d,
                    'successful_analyses_24h': successful_analyses_24h,
                    'success_rate': success_rate
                },
                'credit_metrics': {
                    'total_credits_used_24h': abs(total_credits_used_24h),
                    'total_credits_used_7d': abs(total_credits_used_7d),
                    'total_user_credits': total_user_credits,
                    'avg_credits_per_user': avg_credits_per_user
                },
                'resume_metrics': {
                    'resumes_uploaded_24h': resumes_uploaded_24h,
                    'resumes_uploaded_7d': resumes_uploaded_7d
                },
                'error_metrics': {
                    'errors_24h': errors_24h
                },
                'health_score': max(0, min(100, health_score)),
                'status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical'
            }
            
        except Exception as e:
            self.logger.error(f"Application metrics collection failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def get_performance_trends(self, metric_type: str, hours: int = 24) -> List[Dict]:
        """Get performance trends for a specific metric over time."""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            metrics = PerformanceMetric.query.filter(
                and_(
                    PerformanceMetric.metric_type == metric_type,
                    PerformanceMetric.timestamp >= start_time
                )
            ).order_by(PerformanceMetric.timestamp).all()
            
            return [metric.to_dict() for metric in metrics]
            
        except Exception as e:
            self.logger.error(f"Failed to get performance trends: {str(e)}")
            return []
    
    # ========== Usage Insights ==========
    
    def track_user_action(self, event_type: str, event_category: str, 
                         event_action: str, user_id: str = None,
                         resource_type: str = None, resource_id: str = None,
                         credits_used: int = 0, duration_seconds: float = None,
                         success: bool = True, error_code: str = None,
                         error_message: str = None, metadata: Dict = None) -> UsageInsight:
        """Track user action for analytics."""
        try:
            # Get session info from request context
            session_id = getattr(g, 'session_id', None)
            ip_address = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent') if request else None
            referrer = request.referrer if request else None
            
            insight = UsageInsight(
                user_id=user_id,
                event_type=event_type,
                event_category=event_category,
                event_action=event_action,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                resource_type=resource_type,
                resource_id=resource_id,
                credits_used=credits_used,
                duration_seconds=duration_seconds,
                success=success,
                error_code=error_code,
                error_message=error_message,
                event_metadata=metadata or {}
            )
            
            db.session.add(insight)
            db.session.commit()
            
            # Emit API log row for admin dashboards when applicable
            try:
                if event_type == 'api_call':
                    from flask import current_app
                    payload = {
                        'id': str(insight.id),
                        'method': (metadata or {}).get('method'),
                        'path': (metadata or {}).get('path') or (metadata or {}).get('endpoint'),
                        'status': (metadata or {}).get('status_code'),
                        'response_ms': int((duration_seconds or 0) * 1000),
                        'user_id': user_id,
                        'timestamp': insight.timestamp.isoformat()
                    }
                    if hasattr(current_app, 'websocket_service') and current_app.websocket_service:
                        current_app.websocket_service.socketio.emit('api_log_created', payload, room='admin_dashboard')
            except Exception:
                pass
            
            return insight
        except Exception as e:
            self.logger.error(f"Failed to track user action: {str(e)}")
            db.session.rollback()
            # Don't raise error to avoid disrupting user flow
            return None
    
    def get_user_behavior_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive user behavior insights."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # User activity patterns
            activity_by_hour = db.session.query(
                func.extract('hour', UsageInsight.timestamp).label('hour'),
                func.count().label('count')
            ).filter(
                UsageInsight.timestamp >= start_date
            ).group_by('hour').all()
            
            # Most common actions
            top_actions = db.session.query(
                UsageInsight.event_action,
                func.count().label('count')
            ).filter(
                UsageInsight.timestamp >= start_date
            ).group_by(UsageInsight.event_action).order_by(desc('count')).limit(10).all()
            
            # User retention analysis
            retention_data = self._calculate_user_retention(days)
            
            # Credit usage patterns
            credit_patterns = self._analyze_credit_usage_patterns(days)
            
            # Error analysis
            error_patterns = self._analyze_error_patterns(days)
            
            return {
                'period_days': days,
                'activity_by_hour': [{'hour': hour, 'count': count} for hour, count in activity_by_hour],
                'top_actions': [{'action': action, 'count': count} for action, count in top_actions],
                'retention_data': retention_data,
                'credit_patterns': credit_patterns,
                'error_patterns': error_patterns,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user behavior insights: {str(e)}")
            return {'error': str(e)}
    
    def _get_active_users_count(self, hours: int = 24) -> int:
        """Get count of active users in specified time period."""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            active_count = db.session.query(
                func.count(func.distinct(UsageInsight.user_id))
            ).filter(
                and_(
                    UsageInsight.user_id.isnot(None),
                    UsageInsight.timestamp >= start_time
                )
            ).scalar()
            
            return active_count or 0
            
        except Exception as e:
            self.logger.error(f"Failed to get active users count: {str(e)}")
            return 0
    
    def _calculate_user_retention(self, days: int) -> Dict[str, Any]:
        """Calculate user retention metrics."""
        try:
            # Get new users in the period
            start_date = datetime.utcnow() - timedelta(days=days)
            new_users = User.query.filter(User.created_at >= start_date).count()
            
            # Get returning users (users who registered before the period but were active during)
            returning_users = db.session.query(
                func.count(func.distinct(UsageInsight.user_id))
            ).join(User).filter(
                and_(
                    User.created_at < start_date,
                    UsageInsight.timestamp >= start_date,
                    UsageInsight.user_id.isnot(None)
                )
            ).scalar() or 0
            
            # Calculate retention rate
            total_existing_users = User.query.filter(User.created_at < start_date).count()
            retention_rate = (returning_users / total_existing_users * 100) if total_existing_users > 0 else 0
            
            return {
                'new_users': new_users,
                'returning_users': returning_users,
                'retention_rate': round(retention_rate, 2),
                'total_existing_users': total_existing_users
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate user retention: {str(e)}")
            return {}
    
    def _analyze_credit_usage_patterns(self, days: int) -> Dict[str, Any]:
        """Analyze credit usage patterns."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Credit usage by day
            daily_usage = db.session.query(
                func.date(UsageInsight.timestamp).label('date'),
                func.sum(UsageInsight.credits_used).label('credits_used')
            ).filter(
                and_(
                    UsageInsight.timestamp >= start_date,
                    UsageInsight.credits_used > 0
                )
            ).group_by('date').order_by('date').all()
            
            # Average credits per user
            avg_credits_per_user = db.session.query(
                func.avg(UsageInsight.credits_used)
            ).filter(
                and_(
                    UsageInsight.timestamp >= start_date,
                    UsageInsight.credits_used > 0
                )
            ).scalar() or 0
            
            # Heavy users (top 10%)
            user_credit_usage = db.session.query(
                UsageInsight.user_id,
                func.sum(UsageInsight.credits_used).label('total_credits')
            ).filter(
                and_(
                    UsageInsight.timestamp >= start_date,
                    UsageInsight.user_id.isnot(None),
                    UsageInsight.credits_used > 0
                )
            ).group_by(UsageInsight.user_id).order_by(desc('total_credits')).all()
            
            heavy_users_count = max(1, len(user_credit_usage) // 10)  # Top 10%
            heavy_users = user_credit_usage[:heavy_users_count]
            
            return {
                'daily_usage': [{'date': str(date), 'credits_used': int(credits or 0)} 
                              for date, credits in daily_usage],
                'avg_credits_per_user': round(float(avg_credits_per_user), 2),
                'heavy_users_count': len(heavy_users),
                'total_users_with_usage': len(user_credit_usage)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze credit usage patterns: {str(e)}")
            return {}
    
    def _analyze_error_patterns(self, days: int) -> Dict[str, Any]:
        """Analyze error patterns in user actions."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Error rate by action type
            error_by_action = db.session.query(
                UsageInsight.event_action,
                func.count().label('total'),
                func.sum(func.case([(UsageInsight.success.is_(False), 1)], else_=0)).label('errors')
            ).filter(
                UsageInsight.timestamp >= start_date
            ).group_by(UsageInsight.event_action).all()
            
            error_rates = []
            for action, total, errors in error_by_action:
                error_rate = (errors / total * 100) if total > 0 else 0
                error_rates.append({
                    'action': action,
                    'total': total,
                    'errors': errors or 0,
                    'error_rate': round(error_rate, 2)
                })
            
            # Sort by error rate descending
            error_rates.sort(key=lambda x: x['error_rate'], reverse=True)
            
            return {
                'error_rates_by_action': error_rates[:10],  # Top 10
                'overall_error_rate': round(
                    sum(item['errors'] for item in error_rates) / 
                    sum(item['total'] for item in error_rates) * 100, 2
                ) if error_rates else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze error patterns: {str(e)}")
            return {}
    
    # ========== Error Tracking ==========
    
    def track_error(self, error: Exception, user_id: str = None, 
                   endpoint: str = None, method: str = None) -> ErrorTracking:
        """Track and categorize errors for monitoring."""
        try:
            # Generate error hash for grouping
            error_string = f"{type(error).__name__}:{str(error)}"
            error_hash = hashlib.sha256(error_string.encode()).hexdigest()
            
            # Get or create error tracking entry
            existing_error = ErrorTracking.query.filter_by(error_hash=error_hash).first()
            
            if existing_error:
                # Update existing error
                existing_error.occurrence_count += 1
                existing_error.last_seen = datetime.utcnow()
                existing_error.updated_at = datetime.utcnow()
                
                # Update severity if needed
                if existing_error.occurrence_count > 10:
                    existing_error.severity = 'high'
                elif existing_error.occurrence_count > 50:
                    existing_error.severity = 'critical'
                
                db.session.commit()
                return existing_error
            else:
                # Create new error tracking entry
                from app.services.error_handler import ApplicationError
                
                if isinstance(error, ApplicationError):
                    category = error.category.value
                    severity = error.severity.value
                    error_code = error.error_code
                    user_message = error.user_message
                else:
                    category = 'system'
                    severity = 'medium'
                    error_code = f"SYS_{datetime.utcnow().strftime('%Y%m%d')}_{hash(error_string) % 10000:04d}"
                    user_message = "An unexpected error occurred"
                
                # Get system info
                system_info = {
                    'platform': platform.platform(),
                    'python_version': platform.python_version(),
                    'cpu_count': psutil.cpu_count() if psutil else 'unknown'
                }
                
                # Get request context
                session_id = getattr(g, 'session_id', None)
                request_id = getattr(g, 'request_id', None)
                
                error_tracking = ErrorTracking(
                    error_code=error_code,
                    error_hash=error_hash,
                    category=category,
                    severity=severity,
                    message=str(error),
                    user_message=user_message,
                    stack_trace=self._get_stack_trace(error),
                    user_id=user_id,
                    session_id=session_id,
                    request_id=request_id,
                    endpoint=endpoint,
                    method=method,
                    environment='production',
                    python_version=platform.python_version(),
                    system_info=system_info
                )
                
                db.session.add(error_tracking)
                db.session.commit()
                
                # Create alert for high severity errors
                if severity in ['high', 'critical']:
                    self._create_error_alert(error_tracking)
                
                return error_tracking
                
        except Exception as e:
            self.logger.error(f"Failed to track error: {str(e)}")
            db.session.rollback()
            return None
    
    def get_error_dashboard(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive error dashboard data."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Error statistics
            total_errors = ErrorTracking.query.filter(
                ErrorTracking.last_seen >= start_date
            ).count()
            
            unique_errors = ErrorTracking.query.filter(
                ErrorTracking.last_seen >= start_date
            ).count()
            
            # Errors by severity
            errors_by_severity = db.session.query(
                ErrorTracking.severity,
                func.count().label('count'),
                func.sum(ErrorTracking.occurrence_count).label('total_occurrences')
            ).filter(
                ErrorTracking.last_seen >= start_date
            ).group_by(ErrorTracking.severity).all()
            
            # Top errors by occurrence
            top_errors = ErrorTracking.query.filter(
                ErrorTracking.last_seen >= start_date
            ).order_by(desc(ErrorTracking.occurrence_count)).limit(10).all()
            
            # Error trends (daily)
            error_trends = db.session.query(
                func.date(ErrorTracking.last_seen).label('date'),
                func.count().label('count')
            ).filter(
                ErrorTracking.last_seen >= start_date
            ).group_by('date').order_by('date').all()
            
            # Unresolved critical errors
            critical_unresolved = ErrorTracking.query.filter(
                and_(
                    ErrorTracking.severity == 'critical',
                    ErrorTracking.status == 'open'
                )
            ).count()
            
            return {
                'period_days': days,
                'summary': {
                    'total_errors': total_errors,
                    'unique_errors': unique_errors,
                    'critical_unresolved': critical_unresolved
                },
                'errors_by_severity': [
                    {
                        'severity': severity,
                        'unique_count': count,
                        'total_occurrences': total_occurrences
                    }
                    for severity, count, total_occurrences in errors_by_severity
                ],
                'top_errors': [error.to_dict() for error in top_errors],
                'error_trends': [
                    {'date': str(date), 'count': count}
                    for date, count in error_trends
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get error dashboard: {str(e)}")
            return {'error': str(e)}
    
    def _get_stack_trace(self, error: Exception) -> str:
        """Get formatted stack trace for error."""
        import traceback
        return traceback.format_exc()
    
    # ========== Alert Management ==========
    
    def _create_performance_alert(self, metric: PerformanceMetric):
        """Create alert for performance threshold breach."""
        try:
            alert = SystemAlert(
                alert_type='performance',
                alert_level='warning' if metric.status == 'warning' else 'critical',
                alert_source='monitor',
                title=f'Performance Alert: {metric.metric_name}',
                message=f'{metric.metric_name} has reached {metric.value}{metric.unit or ""}, '
                       f'exceeding {"warning" if metric.status == "warning" else "critical"} threshold',
                details={
                    'metric_id': str(metric.id),
                    'metric_type': metric.metric_type,
                    'metric_name': metric.metric_name,
                    'current_value': metric.value,
                    'threshold_warning': metric.threshold_warning,
                    'threshold_critical': metric.threshold_critical,
                    'unit': metric.unit
                },
                threshold_value=metric.threshold_critical if metric.status == 'critical' else metric.threshold_warning,
                current_value=metric.value
            )
            
            db.session.add(alert)
            db.session.commit()
            
            # Send notification
            self._send_alert_notification(alert)
            
        except Exception as e:
            self.logger.error(f"Failed to create performance alert: {str(e)}")
            db.session.rollback()
    
    def _create_error_alert(self, error_tracking: ErrorTracking):
        """Create alert for high severity errors."""
        try:
            alert = SystemAlert(
                alert_type='error',
                alert_level='critical' if error_tracking.severity == 'critical' else 'error',
                alert_source='error_tracking',
                title=f'Error Alert: {error_tracking.category}',
                message=f'High severity error detected: {error_tracking.message[:100]}...',
                details={
                    'error_id': str(error_tracking.id),
                    'error_code': error_tracking.error_code,
                    'category': error_tracking.category,
                    'severity': error_tracking.severity,
                    'occurrence_count': error_tracking.occurrence_count,
                    'endpoint': error_tracking.endpoint
                }
            )
            
            db.session.add(alert)
            db.session.commit()
            
            # Send notification
            self._send_alert_notification(alert)
            
        except Exception as e:
            self.logger.error(f"Failed to create error alert: {str(e)}")
            db.session.rollback()
    
    def _send_alert_notification(self, alert: SystemAlert):
        """Send alert notification through available channels."""
        try:
            # Log the alert
            self.logger.warning(f"ALERT: {alert.title} - {alert.message}")
            
            # Send WebSocket notifications
            try:
                from flask import current_app
                if hasattr(current_app, 'websocket_service') and current_app.websocket_service:
                    # Existing broadcast
                    current_app.websocket_service.broadcast_system_alert(
                        alert_type=alert.alert_type,
                        message=alert.message,
                        severity=alert.alert_level,
                        details=alert.details
                    )
                    # New explicit event for admin dashboards
                    payload = {
                        'id': str(alert.id),
                        'alert_type': alert.alert_type,
                        'severity': alert.alert_level,
                        'title': alert.title,
                        'message': alert.message,
                        'created_at': datetime.utcnow().isoformat()
                    }
                    current_app.websocket_service.socketio.emit('alert_created', payload, room='admin_dashboard')
            except Exception as e:
                self.logger.error(f"Failed to send WebSocket alert: {str(e)}")
            
            # Update notification tracking
            alert.notifications_sent += 1
            alert.last_notification = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {str(e)}")
            # Don't raise
    
    # ========== Analytics Snapshots ==========
    
    def create_analytics_snapshot(self, snapshot_type: str) -> AnalyticsSnapshot:
        """Create analytics snapshot for historical tracking."""
        try:
            # Define period based on snapshot type
            now = datetime.utcnow()
            if snapshot_type == 'hourly':
                period_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
                period_end = now.replace(minute=0, second=0, microsecond=0)
            elif snapshot_type == 'daily':
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                period_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif snapshot_type == 'weekly':
                days_since_monday = now.weekday()
                period_start = (now - timedelta(days=days_since_monday + 7)).replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            elif snapshot_type == 'monthly':
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                period_start = period_start.replace(day=1)
                period_end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                raise ValueError(f"Invalid snapshot type: {snapshot_type}")
            
            # Collect metrics for the period
            snapshot_data = self._collect_snapshot_metrics(period_start, period_end)
            
            # Create snapshot
            snapshot = AnalyticsSnapshot(
                snapshot_type=snapshot_type,
                period_start=period_start,
                period_end=period_end,
                **snapshot_data
            )
            
            db.session.add(snapshot)
            db.session.commit()
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to create analytics snapshot: {str(e)}")
            db.session.rollback()
            raise ApplicationError(
                f"Failed to create analytics snapshot: {str(e)}",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM
            )
    
    def _collect_snapshot_metrics(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Collect metrics for snapshot period."""
        try:
            # User metrics
            total_users = User.query.filter(User.created_at <= period_end).count()
            new_users = User.query.filter(
                and_(User.created_at >= period_start, User.created_at < period_end)
            ).count()
            
            # Active users during period
            active_users = db.session.query(
                func.count(func.distinct(UsageInsight.user_id))
            ).filter(
                and_(
                    UsageInsight.timestamp >= period_start,
                    UsageInsight.timestamp < period_end,
                    UsageInsight.user_id.isnot(None)
                )
            ).scalar() or 0
            
            # Analysis metrics
            total_analyses = Analysis.query.filter(Analysis.created_at <= period_end).count()
            period_analyses = Analysis.query.filter(
                and_(Analysis.created_at >= period_start, Analysis.created_at < period_end)
            ).all()
            
            successful_analyses = len([a for a in period_analyses if a.status == 'completed'])
            failed_analyses = len([a for a in period_analyses if a.status == 'failed'])
            
            # Average processing time
            processing_times = [a.processing_time for a in period_analyses 
                              if a.processing_time and a.status == 'completed']
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Credit metrics
            period_credit_transactions = CreditTransaction.query.filter(
                and_(
                    CreditTransaction.created_at >= period_start,
                    CreditTransaction.created_at < period_end
                )
            ).all()
            
            credits_used = sum(abs(t.amount) for t in period_credit_transactions if t.transaction_type == 'debit')
            credits_purchased = sum(t.amount for t in period_credit_transactions if t.transaction_type == 'credit')
            
            # Performance metrics from period
            period_metrics = PerformanceMetric.query.filter(
                and_(
                    PerformanceMetric.timestamp >= period_start,
                    PerformanceMetric.timestamp < period_end
                )
            ).all()
            
            cpu_metrics = [m.value for m in period_metrics if m.metric_type == 'cpu']
            memory_metrics = [m.value for m in period_metrics if m.metric_type == 'memory']
            
            avg_cpu_usage = sum(cpu_metrics) / len(cpu_metrics) if cpu_metrics else 0
            avg_memory_usage = sum(memory_metrics) / len(memory_metrics) if memory_metrics else 0
            
            # Error metrics
            period_errors = ErrorTracking.query.filter(
                and_(
                    ErrorTracking.last_seen >= period_start,
                    ErrorTracking.last_seen < period_end
                )
            ).all()
            
            error_rate = len(period_errors) / len(period_analyses) * 100 if period_analyses else 0
            
            return {
                'total_users': total_users,
                'new_users': new_users,
                'active_users': active_users,
                'total_analyses': total_analyses,
                'successful_analyses': successful_analyses,
                'failed_analyses': failed_analyses,
                'avg_processing_time': round(avg_processing_time, 2),
                'credits_used': credits_used,
                'credits_purchased': credits_purchased,
                'avg_cpu_usage': round(avg_cpu_usage, 2),
                'avg_memory_usage': round(avg_memory_usage, 2),
                'error_rate': round(error_rate, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect snapshot metrics: {str(e)}")
            return {}
    
    # ========== Enhanced Monitoring Methods ==========
    
    def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check with detailed analysis."""
        try:
            # Collect current metrics
            metrics = self.collect_system_metrics()
            
            # Analyze for alerts
            alerts = self._analyze_metrics_for_alerts(metrics)
            
            # Calculate health score
            health_score = self._calculate_health_score(metrics)
            
            # Determine overall status
            if health_score >= 90:
                overall_status = 'excellent'
            elif health_score >= 75:
                overall_status = 'good'
            elif health_score >= 50:
                overall_status = 'fair'
            elif health_score >= 25:
                overall_status = 'poor'
            else:
                overall_status = 'critical'
            
            # Get recent error trends
            recent_errors = ErrorTracking.query.filter(
                ErrorTracking.last_seen >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            # Get queue statistics
            queue_stats = {
                'pending': AnalysisQueue.query.filter_by(status=QueueStatus.PENDING.value).count(),
                'processing': AnalysisQueue.query.filter_by(status=QueueStatus.PROCESSING.value).count(),
                'failed_last_hour': AnalysisQueue.query.filter(
                    and_(
                        AnalysisQueue.status == QueueStatus.FAILED.value,
                        AnalysisQueue.updated_at >= datetime.utcnow() - timedelta(hours=1)
                    )
                ).count()
            }
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': overall_status,
                'health_score': health_score,
                'system_metrics': metrics,
                'alerts': alerts,
                'recent_errors': recent_errors,
                'queue_statistics': queue_stats,
                'recommendations': self._generate_recommendations(metrics, alerts)
            }
            
        except Exception as e:
            self.logger.error(f"Comprehensive health check failed: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'unknown',
                'health_score': 0,
                'error': str(e)
            }
    
    def get_monitoring_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get performance metrics for the period
            metrics = PerformanceMetric.query.filter(
                and_(
                    PerformanceMetric.timestamp >= start_time,
                    PerformanceMetric.timestamp <= end_time
                )
            ).order_by(PerformanceMetric.timestamp).all()
            
            # Organize metrics by type
            cpu_metrics = [{'timestamp': m.timestamp.isoformat(), 'value': m.value} 
                          for m in metrics if m.metric_type == 'cpu']
            memory_metrics = [{'timestamp': m.timestamp.isoformat(), 'value': m.value} 
                             for m in metrics if m.metric_type == 'memory']
            db_metrics = [{'timestamp': m.timestamp.isoformat(), 'value': m.value} 
                         for m in metrics if m.metric_type == 'database']
            
            # Get analysis statistics
            analyses = Analysis.query.filter(
                and_(
                    Analysis.created_at >= start_time,
                    Analysis.created_at <= end_time
                )
            ).all()
            
            successful_analyses = len([a for a in analyses if a.status == 'completed'])
            failed_analyses = len([a for a in analyses if a.status == 'failed'])
            
            # Get error trends
            errors = ErrorTracking.query.filter(
                and_(
                    ErrorTracking.last_seen >= start_time,
                    ErrorTracking.last_seen <= end_time
                )
            ).all()
            
            # Get alerts
            alerts = SystemAlert.query.filter(
                and_(
                    SystemAlert.created_at >= start_time,
                    SystemAlert.created_at <= end_time
                )
            ).order_by(SystemAlert.created_at.desc()).all()
            
            # Get current system status
            current_health = self.perform_comprehensive_health_check()
            
            return {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'hours': hours
                },
                'current_status': current_health,
                'performance_trends': {
                    'cpu': cpu_metrics,
                    'memory': memory_metrics,
                    'database': db_metrics
                },
                'analysis_statistics': {
                    'total': len(analyses),
                    'successful': successful_analyses,
                    'failed': failed_analyses,
                    'success_rate': (successful_analyses / len(analyses) * 100) if analyses else 0
                },
                'error_trends': [{
                    'timestamp': e.last_seen.isoformat(),
                    'category': e.category,
                    'severity': e.severity,
                    'count': e.occurrence_count
                } for e in errors],
                'recent_alerts': [{
                    'id': a.id,
                    'alert_type': a.alert_type,
                    'severity': a.severity,
                    'message': a.message,
                    'timestamp': a.created_at.isoformat(),
                    'resolved': a.resolved
                } for a in alerts[:20]]  # Last 20 alerts
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get monitoring dashboard data: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_metrics_for_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze metrics and generate alerts."""
        alerts = []
        
        try:
            # CPU usage alerts
            if 'cpu_usage' in metrics and metrics['cpu_usage'] > 90:
                alerts.append({
                    'type': 'high_cpu_usage',
                    'severity': 'critical' if metrics['cpu_usage'] > 95 else 'warning',
                    'message': f"CPU usage is {metrics['cpu_usage']}%",
                    'value': metrics['cpu_usage'],
                    'threshold': 90
                })
            
            # Memory usage alerts
            if 'memory_usage' in metrics and metrics['memory_usage'] > 85:
                alerts.append({
                    'type': 'high_memory_usage',
                    'severity': 'critical' if metrics['memory_usage'] > 95 else 'warning',
                    'message': f"Memory usage is {metrics['memory_usage']}%",
                    'value': metrics['memory_usage'],
                    'threshold': 85
                })
            
            # Disk usage alerts
            if 'disk_usage' in metrics and metrics['disk_usage'] > 80:
                alerts.append({
                    'type': 'high_disk_usage',
                    'severity': 'critical' if metrics['disk_usage'] > 90 else 'warning',
                    'message': f"Disk usage is {metrics['disk_usage']}%",
                    'value': metrics['disk_usage'],
                    'threshold': 80
                })
            
            # Database connection alerts
            if 'database_connections' in metrics and metrics['database_connections'] > 80:
                alerts.append({
                    'type': 'high_db_connections',
                    'severity': 'warning',
                    'message': f"Database connections: {metrics['database_connections']}",
                    'value': metrics['database_connections'],
                    'threshold': 80
                })
            
            # Response time alerts
            if 'avg_response_time' in metrics and metrics['avg_response_time'] > 2000:
                alerts.append({
                    'type': 'slow_response_time',
                    'severity': 'critical' if metrics['avg_response_time'] > 5000 else 'warning',
                    'message': f"Average response time is {metrics['avg_response_time']}ms",
                    'value': metrics['avg_response_time'],
                    'threshold': 2000
                })
            
        except Exception as e:
            self.logger.error(f"Failed to analyze metrics for alerts: {str(e)}")
        
        return alerts
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate overall system health score (0-100)."""
        try:
            score = 100
            
            # CPU usage penalty
            if 'cpu_usage' in metrics:
                if metrics['cpu_usage'] > 95:
                    score -= 30
                elif metrics['cpu_usage'] > 85:
                    score -= 20
                elif metrics['cpu_usage'] > 75:
                    score -= 10
            
            # Memory usage penalty
            if 'memory_usage' in metrics:
                if metrics['memory_usage'] > 95:
                    score -= 25
                elif metrics['memory_usage'] > 85:
                    score -= 15
                elif metrics['memory_usage'] > 75:
                    score -= 8
            
            # Disk usage penalty
            if 'disk_usage' in metrics:
                if metrics['disk_usage'] > 90:
                    score -= 20
                elif metrics['disk_usage'] > 80:
                    score -= 10
            
            # Response time penalty
            if 'avg_response_time' in metrics:
                if metrics['avg_response_time'] > 5000:
                    score -= 15
                elif metrics['avg_response_time'] > 2000:
                    score -= 8
            
            # Database penalty
            if 'database_connections' in metrics and metrics['database_connections'] > 90:
                score -= 10
            
            return max(0, score)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate health score: {str(e)}")
            return 50  # Default moderate score
    
    def _generate_recommendations(self, metrics: Dict[str, Any], alerts: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on metrics and alerts."""
        recommendations = []
        
        try:
            # CPU recommendations
            if any(alert['type'] == 'high_cpu_usage' for alert in alerts):
                recommendations.append("Consider scaling up CPU resources or optimizing high-CPU processes")
            
            # Memory recommendations
            if any(alert['type'] == 'high_memory_usage' for alert in alerts):
                recommendations.append("Consider increasing memory allocation or reviewing memory leaks")
            
            # Disk recommendations
            if any(alert['type'] == 'high_disk_usage' for alert in alerts):
                recommendations.append("Clean up old files or increase disk space")
            
            # Database recommendations
            if any(alert['type'] == 'high_db_connections' for alert in alerts):
                recommendations.append("Optimize database queries or increase connection pool size")
            
            # Response time recommendations
            if any(alert['type'] == 'slow_response_time' for alert in alerts):
                recommendations.append("Optimize API endpoints or consider caching strategies")
            
            # General recommendations based on metrics
            if 'cpu_usage' in metrics and 'memory_usage' in metrics:
                if metrics['cpu_usage'] > 70 and metrics['memory_usage'] > 70:
                    recommendations.append("System is under high load - consider horizontal scaling")
            
            if not recommendations:
                recommendations.append("System is performing well - no immediate action required")
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {str(e)}")
            recommendations = ["Unable to generate recommendations due to an error"]
        
        return recommendations

# Global analytics service instance
analytics_service = AnalyticsService()
