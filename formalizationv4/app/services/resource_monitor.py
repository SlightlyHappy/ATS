"""
Smart Resource Scaling - Resource Monitor Service
Implements real-time system resource monitoring and scaling decisions.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psutil

from app import db
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitors system resources and provides metrics for scaling decisions."""
    
    def __init__(self):
        self.metrics_history = []
        self.scaling_decisions = []
        self.alert_thresholds = {
            'memory_critical': 0.9,      # 90% memory usage
            'memory_warning': 0.8,       # 80% memory usage
            'cpu_critical': 0.95,        # 95% CPU usage
            'cpu_warning': 0.8,          # 80% CPU usage
            'disk_warning': 0.85,        # 85% disk usage
        }
        self.running = False
        self.monitor_task = None
    
    async def start_monitoring(self):
        """Start continuous resource monitoring."""
        if self.running:
            logger.warning("Resource monitor is already running")
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop - collects metrics every 15 seconds."""
        while self.running:
            try:
                metrics = await self.collect_system_metrics()
                
                # Check for immediate alerts
                await self._check_alert_conditions(metrics)
                
                # Store metrics for scaling decisions
                await self._store_metrics(metrics)
                
                await asyncio.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {str(e)}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics every 15 seconds."""
        try:
            metrics = {
                'timestamp': datetime.utcnow(),
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'per_core': psutil.cpu_percent(interval=1, percpu=True),
                    'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                    'context_switches': psutil.cpu_stats().ctx_switches
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent,
                    'used': psutil.virtual_memory().used,
                    'swap_percent': psutil.swap_memory().percent
                },
                'disk': {
                    'usage_percent': psutil.disk_usage('/').percent,
                    'read_bytes': psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0,
                    'write_bytes': psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
                },
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv,
                    'connections': len(psutil.net_connections()),
                    'active_connections': len([c for c in psutil.net_connections() if c.status == 'ESTABLISHED'])
                },
                'processes': {
                    'total': len(psutil.pids()),
                    'ai_workers': await self.count_ai_worker_processes(),
                    'queue_workers': await self.count_queue_worker_processes(),
                    'web_workers': await self.count_web_worker_processes()
                }
            }
            
            # Add queue-specific metrics
            queue_metrics = await self._get_queue_metrics()
            metrics.update(queue_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            raise
    
    async def _get_queue_metrics(self) -> Dict[str, Any]:
        """Get queue-specific metrics."""
        try:
            from app.models.queue import AnalysisQueue, QueueStatus
            
            # Get queue statistics
            total_queued = AnalysisQueue.query.count()
            pending_count = AnalysisQueue.query.filter_by(
                status=QueueStatus.PENDING.value
            ).count()
            processing_count = AnalysisQueue.query.filter_by(
                status=QueueStatus.PROCESSING.value
            ).count()
            
            return {
                'queue_length': pending_count,
                'total_queued': total_queued,
                'processing_count': processing_count,
                'queue_efficiency': processing_count / max(total_queued, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting queue metrics: {str(e)}")
            return {
                'queue_length': 0,
                'total_queued': 0,
                'processing_count': 0,
                'queue_efficiency': 0
            }
    
    async def count_ai_worker_processes(self) -> int:
        """Count AI worker processes."""
        try:
            count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('ollama' in arg.lower() or 'qwen' in arg.lower() for arg in cmdline):
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return count
        except Exception:
            return 0
    
    async def count_queue_worker_processes(self) -> int:
        """Count queue worker processes."""
        try:
            count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('worker.py' in arg or 'queue_service' in arg for arg in cmdline):
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return count
        except Exception:
            return 0
    
    async def count_web_worker_processes(self) -> int:
        """Count web server worker processes."""
        try:
            count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('flask' in arg.lower() or 'gunicorn' in arg.lower() or 'wsgi' in arg.lower() for arg in cmdline):
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return count
        except Exception:
            return 0
    
    async def _check_alert_conditions(self, metrics: Dict[str, Any]):
        """Check for alert conditions and send notifications."""
        try:
            cpu_percent = metrics['cpu']['percent']
            memory_percent = metrics['memory']['percent']
            
            # Critical alerts
            if cpu_percent > self.alert_thresholds['cpu_critical'] * 100:
                await self._send_alert(
                    f"CRITICAL: CPU usage at {cpu_percent:.1f}%",
                    'critical'
                )
            
            if memory_percent > self.alert_thresholds['memory_critical'] * 100:
                await self._send_alert(
                    f"CRITICAL: Memory usage at {memory_percent:.1f}%",
                    'critical'
                )
            
            # Warning alerts
            elif cpu_percent > self.alert_thresholds['cpu_warning'] * 100:
                await self._send_alert(
                    f"WARNING: High CPU usage at {cpu_percent:.1f}%",
                    'warning'
                )
            
            elif memory_percent > self.alert_thresholds['memory_warning'] * 100:
                await self._send_alert(
                    f"WARNING: High memory usage at {memory_percent:.1f}%",
                    'warning'
                )
                
        except Exception as e:
            logger.error(f"Error checking alert conditions: {str(e)}")
    
    async def _send_alert(self, message: str, level: str):
        """Send alert notification."""
        try:
            logger.warning(f"RESOURCE ALERT [{level.upper()}]: {message}")
            
            # Try to send WebSocket notification
            try:
                from flask import current_app
                if hasattr(current_app, 'websocket_service'):
                    current_app.websocket_service.broadcast_system_alert(
                        alert_type='resource',
                        message=message,
                        severity=level
                    )
            except Exception as e:
                logger.error(f"Failed to send WebSocket alert: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
    
    async def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in history for analysis."""
        try:
            self.metrics_history.append(metrics)
            
            # Keep only last 24 hours of metrics (5760 entries at 15-second intervals)
            if len(self.metrics_history) > 5760:
                self.metrics_history = self.metrics_history[-5760:]
            
            # Store in analytics service if available
            try:
                analytics_service.record_performance_metric(
                    'system', 'cpu_usage', 'system',
                    metrics['cpu']['percent'], 'percent', 80, 95
                )
                analytics_service.record_performance_metric(
                    'system', 'memory_usage', 'system',
                    metrics['memory']['percent'], 'percent', 80, 90
                )
                analytics_service.record_performance_metric(
                    'queue', 'queue_length', 'queue',
                    metrics['queue_length'], 'count', 20, 50
                )
            except Exception as e:
                logger.debug(f"Could not store metrics in analytics service: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error storing metrics: {str(e)}")
    
    def get_recent_metrics(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get metrics from the last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m['timestamp'] > cutoff_time]
    
    def get_average_metrics(self, minutes: int = 5) -> Dict[str, float]:
        """Get average metrics over the last N minutes."""
        recent_metrics = self.get_recent_metrics(minutes)
        
        if not recent_metrics:
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'queue_length': 0,
                'processing_count': 0
            }
        
        return {
            'cpu_percent': sum(m['cpu']['percent'] for m in recent_metrics) / len(recent_metrics),
            'memory_percent': sum(m['memory']['percent'] for m in recent_metrics) / len(recent_metrics),
            'queue_length': sum(m['queue_length'] for m in recent_metrics) / len(recent_metrics),
            'processing_count': sum(m['processing_count'] for m in recent_metrics) / len(recent_metrics)
        }
    
    def is_sustained_high_cpu(self, metrics: Dict[str, Any], threshold: float = 0.8, duration: int = 300) -> bool:
        """Check if CPU usage has been sustained above threshold for duration seconds."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=duration)
        recent_metrics = [m for m in self.metrics_history if m['timestamp'] > cutoff_time]
        
        if len(recent_metrics) < duration // 15:  # Not enough data points
            return False
        
        high_cpu_count = sum(1 for m in recent_metrics if m['cpu']['percent'] > threshold * 100)
        return high_cpu_count / len(recent_metrics) > 0.8  # 80% of the time
    
    def is_sustained_low_cpu(self, metrics: Dict[str, Any], threshold: float = 0.3, duration: int = 600) -> bool:
        """Check if CPU usage has been sustained below threshold for duration seconds."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=duration)
        recent_metrics = [m for m in self.metrics_history if m['timestamp'] > cutoff_time]
        
        if len(recent_metrics) < duration // 15:  # Not enough data points
            return False
        
        low_cpu_count = sum(1 for m in recent_metrics if m['cpu']['percent'] < threshold * 100)
        return low_cpu_count / len(recent_metrics) > 0.8  # 80% of the time
    
    def is_peak_hours(self) -> bool:
        """Check if current time is during peak hours (9 AM - 6 PM)."""
        current_hour = datetime.utcnow().hour
        return 9 <= current_hour <= 18
    
    def is_off_peak_hours(self) -> bool:
        """Check if current time is during off-peak hours (10 PM - 6 AM)."""
        current_hour = datetime.utcnow().hour
        return current_hour >= 22 or current_hour <= 6

# Global instance
resource_monitor = ResourceMonitor()
