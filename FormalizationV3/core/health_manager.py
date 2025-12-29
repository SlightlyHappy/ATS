"""
Health Management System for HR ATS
Centralized health monitoring and endpoint registration
"""

import logging
from datetime import datetime
from typing import Dict, Any
from flask import Flask, jsonify

from core.initializers import ApplicationComponents

logger = logging.getLogger(__name__)

class HealthManager:
    """Centralized health management for all services"""
    
    def __init__(self, app: Flask, components: ApplicationComponents):
        self.app = app
        self.components = components
        self._cache = {}
    
    def register_endpoints(self):
        """Register all health check endpoints"""
        logger.info("🏥 Registering health endpoints...")
        
        self._register_critical_endpoints()
        self._register_service_endpoints()
        self._register_system_endpoints()
        
        logger.info("✅ Health endpoints registered")
    
    def _register_critical_endpoints(self):
        """Register critical health endpoints for Railway"""
        
        @self.app.route('/health', methods=['GET'])
        @self.app.route('/', methods=['GET'])
        def railway_health_check():
            """Primary health check endpoint for Railway"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "3.0.0-refactored",
                "message": "HR ATS System Operational",
                "service": "hr-tools-backend"
            })
        
        @self.app.route('/api/health', methods=['GET'])
        def api_health_check():
            """API health check endpoint"""
            return jsonify({
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "hr-tools-api"
            })
    
    def _register_service_endpoints(self):
        """Register individual service health endpoints"""
        
        @self.app.route('/api/health/database', methods=['GET'])
        def database_health():
            """Database health check"""
            return self._check_service_health('database')
        
        @self.app.route('/api/health/storage', methods=['GET'])
        def storage_health():
            """Storage health check"""
            return self._check_service_health('storage')
        
        @self.app.route('/api/health/ai', methods=['GET'])
        def ai_health():
            """AI processor health check"""
            return self._check_service_health('ai')
        
        @self.app.route('/api/health/auth', methods=['GET'])
        def auth_health():
            """Authentication health check"""
            return self._check_service_health('auth')
        
        @self.app.route('/api/health/credits', methods=['GET'])
        def credits_health():
            """Credit system health check"""
            return self._check_service_health('credits')
    
    def _register_system_endpoints(self):
        """Register system-wide health endpoints"""
        
        @self.app.route('/api/system/status', methods=['GET'])
        def system_status():
            """Comprehensive system status"""
            return self._get_comprehensive_status()
        
        @self.app.route('/api/system/memory', methods=['GET'])
        def memory_status():
            """Memory usage status"""
            return self._get_memory_status()
    
    def _check_service_health(self, service_name: str):
        """Check health of individual service"""
        try:
            service_map = {
                'database': self.components.db_manager,
                'storage': self.components.storage,
                'ai': self.components.ai_processor,
                'auth': self.components.auth,
                'credits': self.components.credit_manager,
                'supabase': self.components.supabase
            }
            
            service = service_map.get(service_name)
            if not service:
                return jsonify({
                    "status": "unavailable",
                    "service": service_name,
                    "message": "Service not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }), 404
            
            # Try to call health_check method if available
            if hasattr(service, 'health_check'):
                health_result = service.health_check()
                return jsonify({
                    "status": "healthy",
                    "service": service_name,
                    "details": health_result,
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    "status": "healthy",
                    "service": service_name,
                    "message": "Service available",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return jsonify({
                "status": "unhealthy",
                "service": service_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 503
    
    def _get_comprehensive_status(self):
        """Get comprehensive system status"""
        try:
            services = {
                'database': self.components.db_manager is not None,
                'storage': self.components.storage is not None,
                'ai': self.components.ai_processor is not None,
                'auth': self.components.auth is not None,
                'credits': self.components.credit_manager is not None,
                'supabase': self.components.supabase is not None,
                'analytics': self.components.analytics_engine is not None,
                'email_automation': self.components.email_automation is not None,
                'sales_intelligence': self.components.sales_intelligence is not None,
            }
            
            # Count healthy services
            healthy_count = sum(1 for status in services.values() if status)
            total_count = len(services)
            
            overall_status = "healthy" if healthy_count >= total_count * 0.7 else "degraded"
            
            return jsonify({
                "status": overall_status,
                "services": services,
                "summary": {
                    "healthy": healthy_count,
                    "total": total_count,
                    "percentage": round((healthy_count / total_count) * 100, 2)
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"System status check failed: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500
    
    def _get_memory_status(self):
        """Get memory usage status"""
        try:
            import psutil
            import os
            
            # Process memory info
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            # System memory info
            system_memory = psutil.virtual_memory()
            
            return jsonify({
                "status": "ok",
                "process_memory": {
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                    "percent": round(process.memory_percent(), 2)
                },
                "system_memory": {
                    "total_gb": round(system_memory.total / 1024 / 1024 / 1024, 2),
                    "available_gb": round(system_memory.available / 1024 / 1024 / 1024, 2),
                    "percent_used": system_memory.percent
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Memory status check failed: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500
