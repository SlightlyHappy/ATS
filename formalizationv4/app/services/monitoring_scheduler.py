"""
Background monitoring scheduler for automated system monitoring.
Implements Priority 1.3: Enhanced Monitoring features.
RAILWAY DEPLOYMENT: Uses standard threading only - NO EVENTLET.
"""
import logging
import time
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# CRITICAL: Ensure no eventlet usage to prevent RLock conflicts
# Railway deployment uses gthread workers - eventlet causes "cannot notify on un-acquired lock" errors
# Force threading mode to prevent Gunicorn auto-detection of eventlet

import threading

# Absolutely no eventlet - causes RLock monkey patching issues
USE_EVENTLET = False
greenthread = None

# Log the threading configuration
logger = logging.getLogger(__name__)
logger.info("🔧 Monitoring scheduler: THREADING MODE (eventlet disabled)")

from app import create_app, db
# Import services lazily to avoid circular imports and context issues
# from app.services.analytics_service import analytics_service
# from app.services.error_handler import ApplicationError

class MonitoringScheduler:
    """Background scheduler for automated monitoring tasks."""
    
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.threads = []
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        self._analytics_service = None
        
        # Enhanced monitoring intervals (in seconds)
        self.intervals = {
            'system_metrics': 30,          # Every 30 seconds - more frequent for production
            'comprehensive_health': 60,    # Every minute - full health check
            'performance_analysis': 180,   # Every 3 minutes - detailed performance analysis
            'usage_analysis': 600,         # Every 10 minutes - user behavior analysis
            'error_analysis': 900,         # Every 15 minutes - error pattern analysis
            'alert_cleanup': 1800,         # Every 30 minutes - clean up old alerts
            'hourly_snapshot': 3600,       # Every hour - analytics snapshot
            'daily_maintenance': 86400,    # Every day - maintenance tasks
            'weekly_reports': 604800       # Every week - comprehensive reports
        }
        
        # Last run timestamps
        self.last_run = {key: datetime.min for key in self.intervals.keys()}
    
    def _get_analytics_service(self):
        """Safely get analytics service within app context."""
        if self._analytics_service is None:
            try:
                from app.services.analytics_service import analytics_service
                self._analytics_service = analytics_service
            except ImportError:
                self.logger.warning("Analytics service not available")
                return None
        return self._analytics_service
    
    def init_app(self, app):
        """Initialize with Flask app if not provided during construction."""
        if self.app is None:
            self.app = app
    
    def start(self):
        """Start the monitoring scheduler with eventlet compatibility."""
        if self.running:
            self.logger.warning("Monitoring scheduler is already running")
            return
        
        self.running = True
        self.logger.info(f"Starting monitoring scheduler (eventlet: {USE_EVENTLET})...")
        
        # Start main monitoring loop
        if USE_EVENTLET and greenthread:
            # Use eventlet green thread
            monitor_greenthread = greenthread.spawn(self._monitoring_loop)
            self.threads.append(monitor_greenthread)
            self.logger.info("Monitoring scheduler started with eventlet green threads")
        else:
            # Use standard threading
            monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitor_thread.start()
            self.threads.append(monitor_thread)
            self.logger.info("Monitoring scheduler started with standard threading")
    
    def stop(self):
        """Stop the monitoring scheduler."""
        self.logger.info("Stopping monitoring scheduler...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            if USE_EVENTLET and greenthread and hasattr(thread, 'wait'):
                # Eventlet green thread
                try:
                    thread.wait(timeout=5)
                except Exception as e:
                    self.logger.warning(f"Error stopping green thread: {e}")
            elif hasattr(thread, 'join'):
                # Standard thread
                thread.join(timeout=5)
        
        self.logger.info("Monitoring scheduler stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Check each monitoring task
                for task_name, interval in self.intervals.items():
                    if (current_time - self.last_run[task_name]).total_seconds() >= interval:
                        try:
                            self._run_monitoring_task(task_name)
                            self.last_run[task_name] = current_time
                        except Exception as e:
                            self.logger.error(f"Error running monitoring task {task_name}: {str(e)}")
                
                # Sleep for a short interval before next check
                if USE_EVENTLET and greenthread:
                    greenthread.sleep(30)  # Use eventlet sleep
                else:
                    time.sleep(30)  # Use standard sleep
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                # Wait longer on error
                if USE_EVENTLET and greenthread:
                    greenthread.sleep(60)
                else:
                    time.sleep(60)
    
    def _run_monitoring_task(self, task_name: str):
        """Run a specific monitoring task with enhanced capabilities."""
        if not self.app:
            self.logger.warning("Flask app not initialized, skipping monitoring task")
            return
            
        with self.app.app_context():
            try:
                start_time = datetime.utcnow()
                
                # Check if analytics service is available before proceeding
                analytics_service = self._get_analytics_service()
                if not analytics_service:
                    self.logger.warning("Analytics service not available, skipping monitoring task")
                    return
                
                try:
                    if not hasattr(analytics_service, 'collect_system_metrics'):
                        self.logger.warning("Analytics service not fully initialized, skipping monitoring task")
                        return
                except AttributeError:
                    self.logger.warning("Analytics service not available, skipping monitoring task")
                    return
                
                if task_name == 'system_metrics':
                    self._collect_system_metrics()
                elif task_name == 'comprehensive_health':
                    self._comprehensive_health_check()
                elif task_name == 'performance_analysis':
                    self._detailed_performance_analysis()
                elif task_name == 'usage_analysis':
                    self._analyze_usage_patterns()
                elif task_name == 'error_analysis':
                    self._analyze_error_patterns()
                elif task_name == 'alert_cleanup':
                    self._cleanup_alerts()
                elif task_name == 'hourly_snapshot':
                    self._create_hourly_snapshot()
                elif task_name == 'daily_maintenance':
                    self._perform_daily_maintenance()
                elif task_name == 'weekly_reports':
                    self._generate_weekly_reports()
                else:
                    self.logger.warning(f"Unknown monitoring task: {task_name}")
                
                # Record task execution time (only if analytics service is available)
                try:
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    if analytics_service:
                        analytics_service.record_performance_metric(
                            'monitoring', f'{task_name}_execution_time', 'monitoring',
                            execution_time, 'seconds'
                        )
                    self.logger.debug(f"Monitoring task {task_name} completed in {execution_time:.2f}s")
                except Exception as metric_error:
                    self.logger.debug(f"Could not record performance metric for {task_name}: {metric_error}")
                    
            except Exception as e:
                self.logger.error(f"Error in monitoring task {task_name}: {str(e)}")
                # Track the error in our error tracking system (if available)
                try:
                    if analytics_service:
                        analytics_service.track_error(e, endpoint=f'monitoring_task_{task_name}')
                except Exception:
                    pass  # Fail silently if error tracking isn't available
    
    def _collect_system_metrics(self):
        """Collect and store current system metrics with enhanced monitoring."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for system metrics collection")
                return
                
            metrics = analytics_service.collect_system_metrics()
            
            # Check for immediate alert conditions
            self._check_immediate_alerts(metrics)
            
            self.logger.debug("Enhanced system metrics collected successfully")
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {str(e)}")
            raise
    
    def _comprehensive_health_check(self):
        """Perform comprehensive health check using enhanced monitoring."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for health check")
                return
                
            health_report = analytics_service.perform_comprehensive_health_check()
            
            # Log health status
            status = health_report.get('overall_status', 'unknown')
            score = health_report.get('health_score', 0)
            
            self.logger.info(f"System health check: {status} (score: {score})")
            
            # Handle critical status
            if status == 'critical':
                self.logger.critical("SYSTEM CRITICAL: Immediate attention required")
            elif status == 'poor':
                self.logger.warning("SYSTEM DEGRADED: Performance issues detected")
                
        except Exception as e:
            self.logger.error(f"Comprehensive health check failed: {str(e)}")
            raise
    
    def _detailed_performance_analysis(self):
        """Perform detailed performance analysis."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for performance analysis")
                return
                
            # Analyze performance trends
            cpu_trends = analytics_service.get_performance_trends('cpu', 1)  # Last hour
            memory_trends = analytics_service.get_performance_trends('memory', 1)
            db_trends = analytics_service.get_performance_trends('database', 1)
            
            # Check for performance degradation patterns
            if cpu_trends:
                recent_cpu = cpu_trends[-10:]  # Last 10 measurements
                if len(recent_cpu) >= 5:
                    avg_cpu = sum(point['value'] for point in recent_cpu) / len(recent_cpu)
                    if avg_cpu > 85:
                        self.logger.warning(f"Sustained high CPU usage detected: {avg_cpu:.1f}%")
            
            if memory_trends:
                recent_memory = memory_trends[-10:]
                if len(recent_memory) >= 5:
                    avg_memory = sum(point['value'] for point in recent_memory) / len(recent_memory)
                    if avg_memory > 90:
                        self.logger.warning(f"Sustained high memory usage detected: {avg_memory:.1f}%")
            
            self.logger.debug("Detailed performance analysis completed")
            
        except Exception as e:
            self.logger.error(f"Performance analysis failed: {str(e)}")
            raise
    
    def _check_immediate_alerts(self, metrics: Dict[str, Any]):
        """Check for conditions requiring immediate alerts."""
        try:
            system = metrics.get('system', {})
            database = metrics.get('database', {})
            queue = metrics.get('queue', {})
            
            # Critical resource usage
            if system.get('cpu_percent', 0) > 95:
                self.logger.critical("CRITICAL: CPU usage above 95%")
            
            if system.get('memory_percent', 0) > 98:
                self.logger.critical("CRITICAL: Memory usage above 98%")
            
            if system.get('disk_percent', 0) > 98:
                self.logger.critical("CRITICAL: Disk usage above 98%")
            
            # Database issues
            if database.get('basic_response_time', 0) > 10:
                self.logger.critical("CRITICAL: Database response time above 10 seconds")
            
            # Queue issues
            if queue.get('stuck_jobs', 0) > 5:
                self.logger.critical(f"CRITICAL: {queue['stuck_jobs']} stuck processing jobs detected")
            
        except Exception as e:
            self.logger.error(f"Immediate alert check failed: {str(e)}")
    
    def _cleanup_alerts(self):
        """Clean up old resolved alerts."""
        try:
            from app.models.analytics import SystemAlert
            
            # Remove resolved alerts older than 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            old_alerts = SystemAlert.query.filter(
                SystemAlert.resolved_at.isnot(None),
                SystemAlert.resolved_at < cutoff_date
            ).all()
            
            for alert in old_alerts:
                db.session.delete(alert)
            
            db.session.commit()
            
            if old_alerts:
                self.logger.info(f"Cleaned up {len(old_alerts)} old resolved alerts")
                
        except Exception as e:
            self.logger.error(f"Alert cleanup failed: {str(e)}")
            db.session.rollback()
    
    def _perform_daily_maintenance(self):
        """Perform daily maintenance tasks."""
        try:
            # Clean up old data
            self._cleanup_old_data()
            
            # Optimize database if needed
            self._optimize_database()
            
            # Generate daily health report
            self._generate_daily_health_report()
            
            self.logger.info("Daily maintenance completed successfully")
            
        except Exception as e:
            self.logger.error(f"Daily maintenance failed: {str(e)}")
            raise
    
    def _optimize_database(self):
        """Perform database optimization tasks."""
        try:
            # Analyze database table statistics (PostgreSQL)
            db.session.execute(db.text("ANALYZE"))
            db.session.commit()
            
            self.logger.info("Database optimization completed")
            
        except Exception as e:
            self.logger.warning(f"Database optimization failed: {str(e)}")
    
    def _generate_daily_health_report(self):
        """Generate daily health summary report."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for daily health report")
                return
                
            # Get enhanced dashboard data for daily snapshot
            dashboard_data = analytics_service.get_monitoring_dashboard_data(24)
            
            health_score = dashboard_data.get('health_report', {}).get('health_score', 0)
            total_alerts = dashboard_data.get('summary', {}).get('total_alerts', 0)
            critical_alerts = dashboard_data.get('summary', {}).get('critical_alerts', 0)
            
            self.logger.info(
                f"Daily Health Report - Score: {health_score}, "
                f"Alerts: {total_alerts} ({critical_alerts} critical)"
            )
            
            # Store daily snapshot
            analytics_service.create_analytics_snapshot(
                snapshot_type='daily_health',
                data=dashboard_data
            )
            
        except Exception as e:
            self.logger.error(f"Daily health report generation failed: {str(e)}")
    
    def _generate_weekly_reports(self):
        """Generate weekly comprehensive reports."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for weekly reports")
                return
                
            # Get weekly dashboard data
            weekly_data = analytics_service.get_monitoring_dashboard_data(168)  # 7 days
            
            # Store weekly snapshot
            analytics_service.create_analytics_snapshot(
                snapshot_type='weekly_report',
                data=weekly_data
            )
            
            self.logger.info("Weekly comprehensive report generated")
            
        except Exception as e:
            self.logger.error(f"Weekly report generation failed: {str(e)}")
    
    def _check_metric_thresholds(self, metrics: dict):
        """Check if any metrics exceed thresholds and create alerts."""
        try:
            alerts_created = 0
            
            # Check system metrics
            system_metrics = metrics.get('system', {})
            
            # CPU threshold check
            cpu_percent = system_metrics.get('cpu_percent', 0)
            if cpu_percent > 90:
                self._create_threshold_alert(
                    'cpu_critical',
                    f'CPU usage critical: {cpu_percent}%',
                    'critical',
                    cpu_percent,
                    90
                )
                alerts_created += 1
            elif cpu_percent > 80:
                self._create_threshold_alert(
                    'cpu_warning',
                    f'CPU usage high: {cpu_percent}%',
                    'warning',
                    cpu_percent,
                    80
                )
                alerts_created += 1
            
            # Memory threshold check
            memory_percent = system_metrics.get('memory_percent', 0)
            if memory_percent > 95:
                self._create_threshold_alert(
                    'memory_critical',
                    f'Memory usage critical: {memory_percent}%',
                    'critical',
                    memory_percent,
                    95
                )
                alerts_created += 1
            elif memory_percent > 85:
                self._create_threshold_alert(
                    'memory_warning',
                    f'Memory usage high: {memory_percent}%',
                    'warning',
                    memory_percent,
                    85
                )
                alerts_created += 1
            
            # Disk threshold check
            disk_percent = system_metrics.get('disk_percent', 0)
            if disk_percent > 95:
                self._create_threshold_alert(
                    'disk_critical',
                    f'Disk usage critical: {disk_percent}%',
                    'critical',
                    disk_percent,
                    95
                )
                alerts_created += 1
            
            # Queue health check
            queue_metrics = metrics.get('queue', {})
            failed_count = queue_metrics.get('failed', 0)
            pending_count = queue_metrics.get('pending', 0)
            
            if failed_count > 20:
                self._create_threshold_alert(
                    'queue_failures',
                    f'High queue failure rate: {failed_count} failed jobs',
                    'critical',
                    failed_count,
                    20
                )
                alerts_created += 1
            
            if pending_count > 100:
                self._create_threshold_alert(
                    'queue_backlog',
                    f'Large queue backlog: {pending_count} pending jobs',
                    'warning',
                    pending_count,
                    100
                )
                alerts_created += 1
            
            if alerts_created > 0:
                self.logger.warning(f"Created {alerts_created} threshold alerts")
                
        except Exception as e:
            self.logger.error(f"Failed to check metric thresholds: {str(e)}")
    
    def _create_threshold_alert(self, alert_type: str, message: str, 
                              level: str, current_value: float, threshold: float):
        """Create a threshold-based alert."""
        try:
            from app.models.analytics import SystemAlert
            
            # Check if we already have an active alert of this type
            existing_alert = SystemAlert.query.filter_by(
                alert_type=alert_type,
                status='active'
            ).first()
            
            if existing_alert:
                # Update existing alert
                existing_alert.current_value = current_value
                existing_alert.message = message
                existing_alert.notifications_sent += 1
                existing_alert.last_notification = datetime.utcnow()
            else:
                # Create new alert
                alert = SystemAlert(
                    alert_type=alert_type,
                    alert_level=level,
                    alert_source='monitor',
                    title=f'System Threshold Alert: {alert_type}',
                    message=message,
                    threshold_value=threshold,
                    current_value=current_value,
                    details={
                        'metric_type': alert_type,
                        'threshold': threshold,
                        'current_value': current_value,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                db.session.add(alert)
            
            db.session.commit()
            
            # Send notification
            self._send_alert_notification(message, level)
            
        except Exception as e:
            self.logger.error(f"Failed to create threshold alert: {str(e)}")
            db.session.rollback()
    
    def _send_alert_notification(self, message: str, level: str):
        """Send alert notification through available channels."""
        try:
            # Log the alert
            if level == 'critical':
                self.logger.critical(f"CRITICAL ALERT: {message}")
            else:
                self.logger.warning(f"ALERT: {message}")
            
            # Send WebSocket notification to admin users
            try:
                from app.services.websocket_service import websocket_service
                if websocket_service:
                    websocket_service.broadcast_system_alert(
                        alert_type='threshold',
                        message=message,
                        severity=level
                    )
            except Exception as e:
                self.logger.error(f"Failed to send WebSocket alert notification: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {str(e)}")
    
    def _performance_health_check(self):
        """Perform comprehensive performance health check."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for performance health check")
                return
                
            # Check database response time
            start_time = datetime.utcnow()
            db.session.execute(db.text('SELECT COUNT(*) FROM users')).scalar()
            db_response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Record database performance metric
            analytics_service.record_performance_metric(
                'database', 'health_check_response_time', 'database',
                db_response_time, 'seconds', 2.0, 5.0
            )
            
            # Check queue processing efficiency
            from app.models.queue import AnalysisQueue, QueueStatus
            
            # Get queue statistics
            total_queued = AnalysisQueue.query.count()
            processing_count = AnalysisQueue.query.filter_by(
                status=QueueStatus.PROCESSING.value
            ).count()
            
            # Calculate queue efficiency
            if total_queued > 0:
                processing_ratio = processing_count / total_queued
                analytics_service.record_performance_metric(
                    'queue', 'processing_efficiency', 'queue',
                    processing_ratio * 100, 'percent', 50, 20
                )
            
            # Check for stuck jobs
            stuck_jobs = AnalysisQueue.query.filter(
                AnalysisQueue.status == QueueStatus.PROCESSING.value,
                AnalysisQueue.updated_at < datetime.utcnow() - timedelta(minutes=10)
            ).count()
            
            if stuck_jobs > 0:
                self.logger.warning(f"Found {stuck_jobs} stuck processing jobs")
                analytics_service.record_performance_metric(
                    'queue', 'stuck_jobs', 'queue',
                    stuck_jobs, 'count', 1, 5
                )
            
            self.logger.debug("Performance health check completed")
            
        except Exception as e:
            self.logger.error(f"Performance health check failed: {str(e)}")
            raise
    
    def _analyze_usage_patterns(self):
        """Analyze recent usage patterns for insights."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for usage pattern analysis")
                return
                
            # Get usage insights for the last hour
            insights = analytics_service.get_user_behavior_insights(days=1)
            
            # Look for unusual patterns
            if isinstance(insights, dict) and 'error_patterns' in insights:
                error_patterns = insights['error_patterns']
                overall_error_rate = error_patterns.get('overall_error_rate', 0)
                
                # Alert on high error rates
                if overall_error_rate > 10:  # More than 10% error rate
                    self._create_threshold_alert(
                        'high_error_rate',
                        f'High error rate detected: {overall_error_rate}%',
                        'warning',
                        overall_error_rate,
                        10
                    )
            
            self.logger.debug("Usage pattern analysis completed")
            
        except Exception as e:
            self.logger.error(f"Usage pattern analysis failed: {str(e)}")
    
    def _analyze_error_patterns(self):
        """Analyze error patterns and trends."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for error pattern analysis")
                return
                
            # Get error dashboard data
            error_data = analytics_service.get_error_dashboard(days=1)
            
            if isinstance(error_data, dict) and 'summary' in error_data:
                summary = error_data['summary']
                critical_unresolved = summary.get('critical_unresolved', 0)
                
                # Alert on unresolved critical errors
                if critical_unresolved > 0:
                    self._create_threshold_alert(
                        'unresolved_critical_errors',
                        f'{critical_unresolved} unresolved critical errors',
                        'critical',
                        critical_unresolved,
                        0
                    )
            
            self.logger.debug("Error pattern analysis completed")
            
        except Exception as e:
            self.logger.error(f"Error pattern analysis failed: {str(e)}")
    
    def _create_hourly_snapshot(self):
        """Create hourly analytics snapshot."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for hourly snapshot")
                return
                
            snapshot = analytics_service.create_analytics_snapshot('hourly')
            self.logger.info(f"Created hourly analytics snapshot: {snapshot.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to create hourly snapshot: {str(e)}")
    
    def _create_daily_snapshot(self):
        """Create daily analytics snapshot."""
        try:
            analytics_service = self._get_analytics_service()
            if not analytics_service:
                self.logger.warning("Analytics service not available for daily snapshot")
                return
                
            # Only create daily snapshot once per day
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            if self.last_run['daily_snapshot'] < today:
                snapshot = analytics_service.create_analytics_snapshot('daily')
                self.logger.info(f"Created daily analytics snapshot: {snapshot.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to create daily snapshot: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data to manage database size."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)  # Keep 30 days
            
            # Clean up old performance metrics (keep detailed data for 30 days)
            from app.models.analytics import PerformanceMetric, UsageInsight, ErrorTracking
            
            old_metrics = PerformanceMetric.query.filter(
                PerformanceMetric.timestamp < cutoff_date
            ).count()
            
            if old_metrics > 0:
                PerformanceMetric.query.filter(
                    PerformanceMetric.timestamp < cutoff_date
                ).delete()
                
                self.logger.info(f"Cleaned up {old_metrics} old performance metrics")
            
            # Clean up old usage insights (keep for 60 days)
            usage_cutoff = datetime.utcnow() - timedelta(days=60)
            old_usage = UsageInsight.query.filter(
                UsageInsight.timestamp < usage_cutoff
            ).count()
            
            if old_usage > 0:
                UsageInsight.query.filter(
                    UsageInsight.timestamp < usage_cutoff
                ).delete()
                
                self.logger.info(f"Cleaned up {old_usage} old usage insights")
            
            # Clean up resolved errors older than 90 days
            error_cutoff = datetime.utcnow() - timedelta(days=90)
            old_errors = ErrorTracking.query.filter(
                ErrorTracking.status == 'resolved',
                ErrorTracking.resolved_at < error_cutoff
            ).count()
            
            if old_errors > 0:
                ErrorTracking.query.filter(
                    ErrorTracking.status == 'resolved',
                    ErrorTracking.resolved_at < error_cutoff
                ).delete()
                
                self.logger.info(f"Cleaned up {old_errors} old resolved errors")
            
            db.session.commit()
            self.logger.info("Data cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {str(e)}")
            db.session.rollback()

# Global monitoring scheduler instance - initialized later to avoid circular imports
monitoring_scheduler = None

def init_monitoring_scheduler(app):
    """Initialize the monitoring scheduler with the Flask app."""
    global monitoring_scheduler
    if monitoring_scheduler is None:
        try:
            monitoring_scheduler = MonitoringScheduler(app)
            monitoring_scheduler._initialized = True
            app.logger.info("Monitoring scheduler initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize monitoring scheduler: {e}")
            # Return a dummy scheduler to prevent further errors
            class DummyScheduler:
                def start(self): pass
                def stop(self): pass
            monitoring_scheduler = DummyScheduler()
    return monitoring_scheduler

def start_monitoring():
    """Start the monitoring scheduler."""
    try:
        if monitoring_scheduler and hasattr(monitoring_scheduler, '_initialized') and monitoring_scheduler._initialized:
            monitoring_scheduler.start()
        else:
            print("Monitoring scheduler not properly initialized")
    except Exception as e:
        print(f"Failed to start monitoring scheduler: {e}")

def stop_monitoring():
    """Stop the monitoring scheduler."""
    try:
        if monitoring_scheduler and hasattr(monitoring_scheduler, 'stop'):
            monitoring_scheduler.stop()
    except Exception as e:
        print(f"Failed to stop monitoring scheduler: {e}")

if __name__ == "__main__":
    # Allow running the monitoring scheduler standalone
    import signal
    import sys
    from app import create_app
    
    # Initialize scheduler with Flask app
    app = create_app()
    scheduler_instance = MonitoringScheduler(app)
    
    def signal_handler(sig, frame):
        print('Stopping monitoring scheduler...')
        if scheduler_instance:
            scheduler_instance.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting monitoring scheduler...")
    if scheduler_instance:
        scheduler_instance.start()
        
        # Keep the main thread alive
        try:
            while scheduler_instance.running:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler_instance.stop()
    else:
        print("Failed to initialize monitoring scheduler")
