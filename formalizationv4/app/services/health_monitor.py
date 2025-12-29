"""
Production health monitoring service for Railway deployment
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from flask import current_app
import psutil
import os

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Production health monitoring service"""
    
    def __init__(self, app=None):
        self.app = app
        self.last_check = datetime.utcnow()
        self.health_status = {
            'status': 'starting',
            'checks': {},
            'last_update': None,
            'uptime_start': datetime.utcnow()
        }
        self.monitoring_active = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        app.health_monitor = self
        
        # Start monitoring in production
        if app.config.get('ENV') == 'production':
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start background health monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Health monitoring started")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self.update_health_status()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(60)  # Back off on errors
    
    def update_health_status(self):
        """Update comprehensive health status"""
        checks = {}
        overall_status = 'healthy'
        
        # Database check
        try:
            with self.app.app_context():
                from app import db
                db.engine.execute('SELECT 1')
                checks['database'] = {'status': 'healthy', 'response_time': 0.1}
        except Exception as e:
            checks['database'] = {'status': 'unhealthy', 'error': str(e)}
            overall_status = 'unhealthy'
        
        # Memory check
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            checks['memory'] = {
                'status': 'healthy' if memory_percent < 90 else 'warning',
                'usage_percent': memory_percent,
                'available_mb': memory.available // 1024 // 1024
            }
            if memory_percent > 95:
                overall_status = 'critical'
        except Exception as e:
            checks['memory'] = {'status': 'unknown', 'error': str(e)}
        
        # Disk check
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            checks['disk'] = {
                'status': 'healthy' if disk_percent < 85 else 'warning',
                'usage_percent': disk_percent,
                'free_mb': disk.free // 1024 // 1024
            }
            if disk_percent > 95:
                overall_status = 'critical'
        except Exception as e:
            checks['disk'] = {'status': 'unknown', 'error': str(e)}
        
        # Model loader check
        try:
            with self.app.app_context():
                if hasattr(self.app, 'model_loader'):
                    models = self.app.model_loader.get_all_models(self.app)
                    errors = self.app.model_loader.get_load_errors()
                    checks['models'] = {
                        'status': 'healthy' if len(errors) == 0 else 'warning',
                        'loaded_count': len(models),
                        'error_count': len(errors)
                    }
                    if len(models) == 0:
                        overall_status = 'degraded'
                else:
                    checks['models'] = {'status': 'not_available'}
        except Exception as e:
            checks['models'] = {'status': 'error', 'error': str(e)}
            overall_status = 'degraded'
        
        # Application uptime
        uptime = datetime.utcnow() - self.health_status['uptime_start']
        checks['uptime'] = {
            'status': 'healthy',
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_human': str(uptime)
        }
        
        # Update status
        self.health_status.update({
            'status': overall_status,
            'checks': checks,
            'last_update': datetime.utcnow().isoformat(),
            'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'unknown')
        })
        
        self.last_check = datetime.utcnow()
    
    def get_health_status(self):
        """Get current health status"""
        # If monitoring is not active, do a quick check
        if not self.monitoring_active or \
           datetime.utcnow() - self.last_check > timedelta(minutes=2):
            self.update_health_status()
        
        return self.health_status.copy()
    
    def is_healthy(self):
        """Simple health check"""
        status = self.get_health_status()
        return status['status'] in ['healthy', 'warning']
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        logger.info("Health monitoring stopped")

# Global instance
health_monitor = HealthMonitor()
