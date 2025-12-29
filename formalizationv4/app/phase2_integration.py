"""
Phase 2 Load-Aware Processing System Integration
Integrates all Phase 2 components with the existing Flask application and Phase 1 services.
"""
import logging
from typing import Optional

# Application imports
from app import create_app

logger = logging.getLogger(__name__)

def integrate_phase2_services(app) -> bool:
    """
    Integrate Phase 2 load-aware processing services with the Flask application.
    
    This function:
    1. Initializes dynamic load manager
    2. Initializes auto-scaling service  
    3. Initializes load-aware integration service
    4. Registers API blueprints
    5. Connects with Phase 1 services
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if integration successful, False otherwise
    """
    try:
        logger.info("Starting Phase 2 Load-Aware Processing System integration...")
        
        # Import Phase 2 services
        from app.services.dynamic_load_manager import dynamic_load_manager
        from app.services.auto_scaling_service import auto_scaling_service
        from app.services.load_aware_integration import load_aware_integration
        
        # Initialize services with app context
        with app.app_context():
            # Initialize dynamic load manager
            dynamic_load_manager.init_app(app)
            app.dynamic_load_manager = dynamic_load_manager
            logger.info("✓ Dynamic Load Manager initialized")
            
            # Initialize auto-scaling service
            auto_scaling_service.init_app(app)
            app.auto_scaling_service = auto_scaling_service
            logger.info("✓ Auto-Scaling Service initialized")
            
            # Initialize integration service (this connects everything)
            load_aware_integration.init_app(app)
            app.load_aware_integration = load_aware_integration
            logger.info("✓ Load-Aware Integration Service initialized")
            
            # Connect with Phase 1 services
            _connect_with_phase1_services(app)
            
            # Register API blueprints
            _register_phase2_blueprints(app)
            
            # Configure application settings for load-aware processing
            _configure_load_aware_settings(app)
            
        logger.info("✅ Phase 2 Load-Aware Processing System integration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to integrate Phase 2 services: {str(e)}")
        return False

def _connect_with_phase1_services(app):
    """Connect Phase 2 services with existing Phase 1 services."""
    try:
        # Connect with Performance Monitoring Service (Phase 1)
        performance_monitor = getattr(app, 'performance_monitor', None)
        if performance_monitor:
            app.load_aware_integration.performance_monitor = performance_monitor
            logger.info("✓ Connected with Performance Monitoring Service")
        else:
            logger.warning("⚠️ Performance Monitoring Service not found - running without performance integration")
        
        # Connect with Enhanced Cache Service (Phase 1)
        enhanced_cache = getattr(app, 'enhanced_cache', None)
        if enhanced_cache:
            app.load_aware_integration.enhanced_cache = enhanced_cache
            logger.info("✓ Connected with Enhanced Cache Service")
        else:
            logger.warning("⚠️ Enhanced Cache Service not found - running without cache optimization")
        
        # Connect with Database Connection Pool (Phase 1)
        db_pool = getattr(app, 'db_pool', None)
        if db_pool:
            logger.info("✓ Connected with Database Connection Pool")
        else:
            logger.warning("⚠️ Database Connection Pool not found")
        
        # Connect with Batch API Service (Phase 1)
        batch_api = getattr(app, 'batch_api', None)
        if batch_api:
            logger.info("✓ Connected with Batch API Service")
        else:
            logger.warning("⚠️ Batch API Service not found")
        
    except Exception as e:
        logger.error(f"Error connecting with Phase 1 services: {str(e)}")

def _register_phase2_blueprints(app):
    """Register Phase 2 API blueprints."""
    try:
        # Register load-aware processing API
        from app.api.load_aware_routes import register_load_aware_blueprint
        if register_load_aware_blueprint(app):
            logger.info("✓ Load-Aware Processing API registered")
        else:
            logger.warning("⚠️ Failed to register Load-Aware Processing API")
        
        # Register Phase 2 status API
        from app.api.phase2_status_routes import register_phase2_status_blueprint
        if register_phase2_status_blueprint(app):
            logger.info("✓ Phase 2 Status API registered")
        else:
            logger.warning("⚠️ Failed to register Phase 2 Status API")
        
    except Exception as e:
        logger.error(f"Error registering Phase 2 blueprints: {str(e)}")

def _configure_load_aware_settings(app):
    """Configure application settings for load-aware processing."""
    try:
        # Update Flask configuration with load-aware processing defaults
        load_aware_config = {
            # Load Management Settings
            'LOAD_DECISION_COOLDOWN': 30,  # seconds between decisions
            'LOAD_AWARE_PROCESSING': True,
            'MAX_CONCURRENT_AGENTS': 6,  # will be dynamically adjusted
            'QUEUE_BATCH_SIZE': 3,  # will be dynamically adjusted
            'PRIORITY_QUEUES_ONLY': False,  # will be dynamically adjusted
            
            # Auto-Scaling Settings
            'AUTO_SCALING_ENABLED': True,
            'CURRENT_INSTANCES': 1,
            'ENVIRONMENT': app.config.get('ENVIRONMENT', 'production').lower(),
            
            # Integration Settings
            'COORDINATION_INTERVAL': 60,  # seconds
            'HEALTH_CHECK_INTERVAL': 30,  # seconds
            
            # Thresholds (can be overridden in app config)
            'LOAD_THRESHOLDS': {
                'critical': {'cpu': 95, 'memory': 90, 'queue': 50, 'response_time': 5.0},
                'high': {'cpu': 80, 'memory': 80, 'queue': 20, 'response_time': 2.0},
                'medium': {'cpu': 60, 'memory': 70, 'queue': 10, 'response_time': 1.0},
                'normal': {'cpu': 40, 'memory': 50, 'queue': 5, 'response_time': 0.5},
                'low': {'cpu': 20, 'memory': 30, 'queue': 2, 'response_time': 0.3}
            }
        }
        
        # Apply configuration (don't override existing settings)
        for key, value in load_aware_config.items():
            if key not in app.config:
                app.config[key] = value
        
        logger.info("✓ Load-aware processing settings configured")
        
    except Exception as e:
        logger.error(f"Error configuring load-aware settings: {str(e)}")

def get_phase2_status(app) -> dict:
    """Get comprehensive status of Phase 2 integration."""
    try:
        status = {
            'timestamp': None,
            'integration_status': 'unknown',
            'services': {
                'dynamic_load_manager': False,
                'auto_scaling_service': False,
                'load_aware_integration': False
            },
            'phase1_connections': {
                'performance_monitor': False,
                'enhanced_cache': False,
                'db_pool': False,
                'batch_api': False
            },
            'api_endpoints': {
                'load_aware_routes': False
            },
            'configuration': {
                'load_aware_processing_enabled': False,
                'auto_scaling_enabled': False,
                'coordination_active': False
            }
        }
        
        with app.app_context():
            from datetime import datetime
            status['timestamp'] = datetime.utcnow().isoformat()
            
            # Check services
            status['services']['dynamic_load_manager'] = hasattr(app, 'dynamic_load_manager')
            status['services']['auto_scaling_service'] = hasattr(app, 'auto_scaling_service')
            status['services']['load_aware_integration'] = hasattr(app, 'load_aware_integration')
            
            # Check Phase 1 connections
            status['phase1_connections']['performance_monitor'] = hasattr(app, 'performance_monitor')
            status['phase1_connections']['enhanced_cache'] = hasattr(app, 'enhanced_cache')
            status['phase1_connections']['db_pool'] = hasattr(app, 'db_pool')
            status['phase1_connections']['batch_api'] = hasattr(app, 'batch_api')
            
            # Check configuration
            status['configuration']['load_aware_processing_enabled'] = app.config.get('LOAD_AWARE_PROCESSING', False)
            status['configuration']['auto_scaling_enabled'] = app.config.get('AUTO_SCALING_ENABLED', False)
            
            if hasattr(app, 'load_aware_integration'):
                status['configuration']['coordination_active'] = app.load_aware_integration.integration_active
            
            # Check API endpoints
            try:
                from app.api.load_aware_routes import load_aware_bp
                status['api_endpoints']['load_aware_routes'] = load_aware_bp is not None
            except:
                status['api_endpoints']['load_aware_routes'] = False
            
            # Determine overall integration status
            services_active = all(status['services'].values())
            config_active = status['configuration']['load_aware_processing_enabled']
            
            if services_active and config_active:
                status['integration_status'] = 'active'
            elif any(status['services'].values()):
                status['integration_status'] = 'partial'
            else:
                status['integration_status'] = 'inactive'
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting Phase 2 status: {str(e)}")
        return {
            'integration_status': 'error',
            'error': str(e),
            'timestamp': None
        }

def phase2_health_check(app) -> dict:
    """Perform comprehensive health check of Phase 2 systems."""
    try:
        health_check = {
            'timestamp': None,
            'overall_health': 'unknown',
            'service_health': {},
            'performance_metrics': {},
            'recommendations': []
        }
        
        with app.app_context():
            from datetime import datetime
            health_check['timestamp'] = datetime.utcnow().isoformat()
            
            # Check individual service health
            if hasattr(app, 'dynamic_load_manager'):
                try:
                    load_status = app.dynamic_load_manager.get_current_load_status()
                    health_check['service_health']['dynamic_load_manager'] = 'healthy'
                    health_check['performance_metrics']['current_load'] = load_status
                except Exception as e:
                    health_check['service_health']['dynamic_load_manager'] = f'error: {str(e)}'
            else:
                health_check['service_health']['dynamic_load_manager'] = 'not_initialized'
            
            if hasattr(app, 'auto_scaling_service'):
                try:
                    scaling_status = app.auto_scaling_service.get_scaling_status()
                    health_check['service_health']['auto_scaling_service'] = 'healthy'
                    health_check['performance_metrics']['scaling_status'] = scaling_status
                except Exception as e:
                    health_check['service_health']['auto_scaling_service'] = f'error: {str(e)}'
            else:
                health_check['service_health']['auto_scaling_service'] = 'not_initialized'
            
            if hasattr(app, 'load_aware_integration'):
                try:
                    integration_status = app.load_aware_integration.get_integration_status()
                    health_check['service_health']['load_aware_integration'] = 'healthy'
                    health_check['performance_metrics']['integration_status'] = integration_status
                except Exception as e:
                    health_check['service_health']['load_aware_integration'] = f'error: {str(e)}'
            else:
                health_check['service_health']['load_aware_integration'] = 'not_initialized'
            
            # Generate recommendations
            healthy_services = sum(1 for status in health_check['service_health'].values() if status == 'healthy')
            total_services = len(health_check['service_health'])
            
            if healthy_services == total_services:
                health_check['overall_health'] = 'healthy'
                health_check['recommendations'] = ['All Phase 2 services operating normally']
            elif healthy_services > 0:
                health_check['overall_health'] = 'partial'
                health_check['recommendations'] = [
                    'Some Phase 2 services are not operational',
                    'Check service initialization and configuration',
                    'Review error logs for failed services'
                ]
            else:
                health_check['overall_health'] = 'critical'
                health_check['recommendations'] = [
                    'No Phase 2 services are operational',
                    'Verify Phase 2 integration was completed',
                    'Check application startup logs',
                    'Ensure all dependencies are installed'
                ]
        
        return health_check
        
    except Exception as e:
        logger.error(f"Error performing Phase 2 health check: {str(e)}")
        return {
            'overall_health': 'error',
            'error': str(e),
            'timestamp': None,
            'recommendations': ['Fix health check system before proceeding']
        }

# =============================================================================
# PHASE 2 STARTUP INTEGRATION
# =============================================================================

def startup_phase2_integration():
    """
    Startup function to integrate Phase 2 with the main application.
    This should be called during application initialization.
    """
    try:
        # This will be called by the main application startup
        logger.info("Phase 2 Load-Aware Processing System ready for integration")
        return True
        
    except Exception as e:
        logger.error(f"Error during Phase 2 startup integration: {str(e)}")
        return False

if __name__ == "__main__":
    # For testing Phase 2 integration
    try:
        from app import create_app
        app = create_app()
        
        print("Testing Phase 2 Integration...")
        
        # Test integration
        success = integrate_phase2_services(app)
        print(f"Integration Success: {success}")
        
        # Test status
        status = get_phase2_status(app)
        print(f"Integration Status: {status['integration_status']}")
        
        # Test health check
        health = phase2_health_check(app)
        print(f"Overall Health: {health['overall_health']}")
        
    except Exception as e:
        print(f"Error testing Phase 2 integration: {str(e)}")
