#!/usr/bin/env python3
"""
Production health monitoring script for the AI Resume Analysis System.
Monitors system health, queue performance, and triggers alerts.
"""
import os
import sys
import time
import logging
import asyncio
import requests
from datetime import datetime, timedelta
import psutil
import signal

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.queue import AnalysisQueue, QueueStatus
from app.models.analysis import Analysis
from app.services.websocket_service import websocket_service

class ProductionHealthMonitor:
    """Production health monitoring service."""
    
    def __init__(self):
        self.app = create_app()
        self.running = True
        self.check_interval = 60  # Check every minute
        self.alert_threshold = {
            'cpu_percent': 85,
            'memory_percent': 90,
            'disk_percent': 95,
            'queue_failures': 10,
            'response_time': 5.0  # seconds
        }
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the monitor."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/health_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def check_system_resources(self):
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            alerts = []
            
            if cpu_percent > self.alert_threshold['cpu_percent']:
                alerts.append(f"HIGH CPU USAGE: {cpu_percent}%")
                
            if memory.percent > self.alert_threshold['memory_percent']:
                alerts.append(f"HIGH MEMORY USAGE: {memory.percent}%")
                
            if disk.percent > self.alert_threshold['disk_percent']:
                alerts.append(f"HIGH DISK USAGE: {disk.percent}%")
                
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'alerts': alerts
            }
            
        except Exception as e:
            self.logger.error(f"Error checking system resources: {str(e)}")
            return {'alerts': [f"System check failed: {str(e)}"]}
    
    def check_database_health(self):
        """Check database connectivity and performance."""
        try:
            with self.app.app_context():
                start_time = time.time()
                db.session.execute(db.text('SELECT 1'))
                response_time = time.time() - start_time
                
                alerts = []
                if response_time > self.alert_threshold['response_time']:
                    alerts.append(f"SLOW DATABASE RESPONSE: {response_time:.2f}s")
                
                return {
                    'response_time': response_time,
                    'status': 'healthy',
                    'alerts': alerts
                }
                
        except Exception as e:
            self.logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'alerts': [f"Database connection failed: {str(e)}"]
            }
    
    def check_queue_health(self):
        """Check queue processing health."""
        try:
            with self.app.app_context():
                # Get queue statistics
                total_queued = AnalysisQueue.query.count()
                pending = AnalysisQueue.query.filter_by(status=QueueStatus.PENDING).count()
                processing = AnalysisQueue.query.filter_by(status=QueueStatus.PROCESSING).count()
                failed = AnalysisQueue.query.filter_by(status=QueueStatus.FAILED).count()
                
                # Check for stuck processing jobs
                stuck_jobs = AnalysisQueue.query.filter(
                    AnalysisQueue.status == QueueStatus.PROCESSING,
                    AnalysisQueue.updated_at < datetime.utcnow() - timedelta(minutes=10)
                ).count()
                
                alerts = []
                if failed > self.alert_threshold['queue_failures']:
                    alerts.append(f"HIGH QUEUE FAILURE RATE: {failed} failed jobs")
                
                if stuck_jobs > 0:
                    alerts.append(f"STUCK PROCESSING JOBS: {stuck_jobs} jobs")
                
                if pending > 50:
                    alerts.append(f"HIGH QUEUE BACKLOG: {pending} pending jobs")
                
                return {
                    'total_queued': total_queued,
                    'pending': pending,
                    'processing': processing,
                    'failed': failed,
                    'stuck_jobs': stuck_jobs,
                    'alerts': alerts
                }
                
        except Exception as e:
            self.logger.error(f"Queue health check failed: {str(e)}")
            return {'alerts': [f"Queue check failed: {str(e)}"]}
    
    def check_api_health(self):
        """Check API endpoint health."""
        try:
            base_url = os.getenv('BASE_URL', 'http://localhost:8000')
            
            start_time = time.time()
            response = requests.get(f"{base_url}/api/health/simple", timeout=10)
            response_time = time.time() - start_time
            
            alerts = []
            if response.status_code != 200:
                alerts.append(f"API HEALTH CHECK FAILED: Status {response.status_code}")
            
            if response_time > self.alert_threshold['response_time']:
                alerts.append(f"SLOW API RESPONSE: {response_time:.2f}s")
            
            return {
                'status_code': response.status_code,
                'response_time': response_time,
                'alerts': alerts
            }
            
        except Exception as e:
            self.logger.error(f"API health check failed: {str(e)}")
            return {'alerts': [f"API check failed: {str(e)}"]}
    
    def send_alert(self, alerts):
        """Send alerts for critical issues."""
        if not alerts:
            return
            
        alert_message = "\n".join(alerts)
        self.logger.critical(f"PRODUCTION ALERTS:\n{alert_message}")
        
        # In production, you would send these to:
        # - Slack/Discord webhook
        # - Email notifications
        # - PagerDuty/similar service
        # - WebSocket to admin dashboard
        
        # Example WebSocket notification
        try:
            if websocket_service:
                websocket_service.broadcast_system_alert(
                    alert_type='health_monitor',
                    message=f"Production alert: {len(alerts)} issues detected",
                    severity='critical'
                )
        except Exception as e:
            self.logger.error(f"Failed to send WebSocket alert: {str(e)}")
    
    def cleanup_stuck_jobs(self):
        """Clean up stuck processing jobs."""
        try:
            with self.app.app_context():
                # Find jobs stuck for more than 10 minutes
                stuck_jobs = AnalysisQueue.query.filter(
                    AnalysisQueue.status == QueueStatus.PROCESSING,
                    AnalysisQueue.updated_at < datetime.utcnow() - timedelta(minutes=10)
                ).all()
                
                for job in stuck_jobs:
                    job.status = QueueStatus.FAILED
                    job.error_message = "Job stuck in processing state - automatically failed"
                    job.updated_at = datetime.utcnow()
                
                if stuck_jobs:
                    db.session.commit()
                    self.logger.info(f"Cleaned up {len(stuck_jobs)} stuck jobs")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up stuck jobs: {str(e)}")
    
    def run_health_check(self):
        """Run complete health check cycle."""
        self.logger.info("Running health check cycle...")
        
        all_alerts = []
        
        # Check system resources
        system_check = self.check_system_resources()
        all_alerts.extend(system_check.get('alerts', []))
        
        # Check database
        db_check = self.check_database_health()
        all_alerts.extend(db_check.get('alerts', []))
        
        # Check queue
        queue_check = self.check_queue_health()
        all_alerts.extend(queue_check.get('alerts', []))
        
        # Check API
        api_check = self.check_api_health()
        all_alerts.extend(api_check.get('alerts', []))
        
        # Clean up stuck jobs
        self.cleanup_stuck_jobs()
        
        # Send alerts if any
        if all_alerts:
            self.send_alert(all_alerts)
        else:
            self.logger.info("All health checks passed")
        
        # Log summary
        self.logger.info(f"Health check summary: "
                        f"CPU: {system_check.get('cpu_percent', 'N/A')}%, "
                        f"Memory: {system_check.get('memory_percent', 'N/A')}%, "
                        f"DB: {db_check.get('response_time', 'N/A')}s, "
                        f"Queue: {queue_check.get('pending', 'N/A')} pending")
    
    def run(self):
        """Main monitoring loop."""
        self.logger.info("Starting production health monitor...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        while self.running:
            try:
                self.run_health_check()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(self.check_interval)
        
        self.logger.info("Health monitor stopped")

if __name__ == "__main__":
    monitor = ProductionHealthMonitor()
    monitor.run()
