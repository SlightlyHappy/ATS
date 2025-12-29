"""
Startup Orchestrator for HR ATS Application
Centralized orchestration of all startup services and dependencies
"""

import os
import sys
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from .config import StartupConfig, ServiceConfig
from .services import (
    BaseService,
    DatabaseService,
    OllamaService,
    AIProcessorService,
    HealthCheckService
)

logger = logging.getLogger(__name__)

class StartupOrchestrator:
    """Orchestrates the startup of all application services"""
    
    def __init__(self, config: Optional[StartupConfig] = None):
        """Initialize orchestrator with configuration"""
        self.config = config or StartupConfig()
        self.services: Dict[str, BaseService] = {}
        self.startup_order: List[str] = []
        self.is_running = False
        self.startup_start_time: Optional[float] = None
        self.startup_duration: Optional[float] = None
        
        # Initialize services
        self._initialize_services()
        self._determine_startup_order()
    
    def _initialize_services(self):
        """Initialize all service instances"""
        logger.info("🔧 Initializing services...")
        
        # Create service instances
        self.services = {
            'database': DatabaseService(self.config.get_service_config('database')),
            'ollama': OllamaService(self.config.get_service_config('ollama')),
            'ai_processor': AIProcessorService(self.config.get_service_config('ai_processor')),
            'health_monitor': HealthCheckService(self.config.get_service_config('health_monitor'))
        }
        
        # Set up health monitor with other services
        health_service = self.services['health_monitor']
        monitored_services = [s for name, s in self.services.items() if name != 'health_monitor']
        health_service.set_monitored_services(monitored_services)
        
        logger.info(f"✅ Initialized {len(self.services)} services")
    
    def _determine_startup_order(self):
        """Determine the order in which services should be started"""
        # Build dependency graph and determine order
        ordered = []
        visited = set()
        
        def visit(service_name: str):
            if service_name in visited:
                return
            
            visited.add(service_name)
            service_config = self.config.get_service_config(service_name)
            
            if service_config:
                # Visit dependencies first
                for dep in service_config.dependencies:
                    if dep in self.services:
                        visit(dep)
                
                # Add this service
                if service_name not in ordered:
                    ordered.append(service_name)
        
        # Visit all services
        for service_name in self.services.keys():
            visit(service_name)
        
        self.startup_order = ordered
        logger.info(f"📋 Startup order: {' → '.join(self.startup_order)}")
    
    async def start_all(self) -> bool:
        """Start all services in dependency order"""
        self.startup_start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("🚀 STARTING HR ATS APPLICATION")
        logger.info("=" * 60)
        
        # Validate environment
        missing_vars = self.config.validate_environment()
        if missing_vars:
            logger.error("❌ Missing required environment variables:")
            for var in missing_vars:
                logger.error(f"   - {var}")
            return False
        
        try:
            # Start services in order
            started_services = []
            failed_services = []
            
            for service_name in self.startup_order:
                service = self.services[service_name]
                service_config = self.config.get_service_config(service_name)
                
                logger.info(f"🔄 Starting {service_name}...")
                
                try:
                    # Start service with timeout
                    success = await asyncio.wait_for(
                        service.start(),
                        timeout=service_config.timeout
                    )
                    
                    if success:
                        started_services.append(service_name)
                        logger.info(f"✅ {service_name} started successfully")
                    else:
                        if service_config.required:
                            failed_services.append(service_name)
                            logger.error(f"❌ {service_name} failed to start (REQUIRED)")
                        else:
                            logger.warning(f"⚠️ {service_name} failed to start (optional)")
                
                except asyncio.TimeoutError:
                    if service_config.required:
                        failed_services.append(service_name)
                        logger.error(f"❌ {service_name} startup timeout (REQUIRED)")
                    else:
                        logger.warning(f"⚠️ {service_name} startup timeout (optional)")
                
                except Exception as e:
                    if service_config.required:
                        failed_services.append(service_name)
                        logger.error(f"❌ {service_name} startup error: {e} (REQUIRED)")
                    else:
                        logger.warning(f"⚠️ {service_name} startup error: {e} (optional)")
            
            # Check if startup was successful
            if failed_services:
                logger.error(f"❌ Startup failed - required services failed: {failed_services}")
                return False
            
            self.is_running = True
            self.startup_duration = time.time() - self.startup_start_time
            
            logger.info("=" * 60)
            logger.info("✅ APPLICATION STARTUP COMPLETE")
            logger.info(f"⏱️ Startup time: {self.startup_duration:.2f} seconds")
            logger.info(f"🔥 Started services: {started_services}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Critical startup error: {e}")
            return False
    
    async def stop_all(self) -> bool:
        """Stop all services in reverse order"""
        if not self.is_running:
            return True
        
        logger.info("🛑 Stopping all services...")
        
        try:
            # Stop services in reverse order
            for service_name in reversed(self.startup_order):
                service = self.services[service_name]
                if service.is_running:
                    logger.info(f"🔄 Stopping {service_name}...")
                    await service.stop()
                    logger.info(f"✅ {service_name} stopped")
            
            self.is_running = False
            logger.info("✅ All services stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping services: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive startup status"""
        service_statuses = {
            name: service.get_status() 
            for name, service in self.services.items()
        }
        
        return {
            'is_running': self.is_running,
            'startup_time': self.startup_duration,
            'startup_order': self.startup_order,
            'services': service_statuses,
            'environment': {
                'is_production': self.config.is_production,
                'is_railway': self.config.is_railway,
                'debug_mode': self.config.debug_mode
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        health_service = self.services.get('health_monitor')
        if health_service and hasattr(health_service, 'get_system_status'):
            return health_service.get_system_status()
        
        # Fallback health check
        healthy_services = sum(1 for service in self.services.values() if service.health_status)
        total_services = len(self.services)
        
        return {
            'overall_health': healthy_services >= total_services * 0.7,
            'healthy_services': healthy_services,
            'total_services': total_services,
            'services': {name: service.health_status for name, service in self.services.items()}
        }
    
    @asynccontextmanager
    async def startup_context(self):
        """Context manager for startup/shutdown"""
        try:
            success = await self.start_all()
            if not success:
                raise RuntimeError("Failed to start application services")
            yield self
        finally:
            await self.stop_all()
    
    def create_flask_app(self):
        """Create and configure Flask application"""
        try:
            logger.info("🌟 Creating Flask application...")
            
            # Import after services are started
            from app import HRATSApplication
            
            app_instance = HRATSApplication()
            flask_app = app_instance.app
            
            # Add startup status endpoint
            @flask_app.route('/startup/status')
            def startup_status():
                return self.get_status()
            
            @flask_app.route('/startup/health')  
            def startup_health():
                return self.get_health_status()
            
            logger.info("✅ Flask application created successfully")
            return flask_app
            
        except Exception as e:
            logger.error(f"❌ Failed to create Flask application: {e}")
            raise

# Singleton instance for global access
_orchestrator_instance: Optional[StartupOrchestrator] = None

def get_orchestrator(config: Optional[StartupConfig] = None) -> StartupOrchestrator:
    """Get singleton orchestrator instance"""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = StartupOrchestrator(config)
    
    return _orchestrator_instance

def reset_orchestrator():
    """Reset orchestrator instance (for testing)"""
    global _orchestrator_instance
    _orchestrator_instance = None
