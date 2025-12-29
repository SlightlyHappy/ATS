"""
Flask App Integration for Phase 3 Enterprise Features
Integrates Phase 3 services with the main Flask application.
"""
import logging
import os
from typing import Dict, Any, Optional

# Import Phase 3 services with graceful fallback
try:
    from .services.phase3_integration import phase3_integration
    from .services.redis_cluster_manager import redis_cluster_manager
    from .services.advanced_auto_scaler import advanced_auto_scaler
    from .services.background_task_optimizer import background_task_optimizer
    PHASE3_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Phase 3 services not available: {str(e)}")
    PHASE3_AVAILABLE = False

logger = logging.getLogger(__name__)

def init_phase3_services(app):
    """
    Initialize Phase 3 enterprise services with the Flask application.
    This function should be called during Flask app initialization.
    """
    if not PHASE3_AVAILABLE:
        logger.warning("Phase 3 services not available - skipping initialization")
        return False
    
    try:
        # Load Phase 3 configuration from environment or app config
        phase3_config = _load_phase3_config(app)
        
        # Initialize Phase 3 integration
        phase3_integration.init_app(app)
        
        # Configure individual services
        _configure_redis_cluster(app, phase3_config)
        _configure_auto_scaler(app, phase3_config)
        _configure_task_optimizer(app, phase3_config)
        
        # Register Phase 3 CLI commands
        _register_phase3_commands(app)
        
        logger.info("Phase 3 enterprise services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Phase 3 services: {str(e)}")
        return False


def _load_phase3_config(app) -> Dict[str, Any]:
    """Load Phase 3 configuration from environment and app config."""
    config = {}
    
    # Redis Cluster Configuration
    config['redis_cluster'] = {
        'nodes': os.getenv('REDIS_CLUSTER_NODES', '').split(',') if os.getenv('REDIS_CLUSTER_NODES') else [],
        'password': os.getenv('REDIS_PASSWORD', ''),
        'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '100')),
        'health_check_interval': int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30')),
        'enabled': os.getenv('ENABLE_REDIS_CLUSTER', 'false').lower() == 'true'
    }
    
    # Auto-Scaler Configuration
    config['auto_scaler'] = {
        'min_instances': int(os.getenv('AUTOSCALER_MIN_INSTANCES', '1')),
        'max_instances': int(os.getenv('AUTOSCALER_MAX_INSTANCES', '10')),
        'target_cpu_utilization': float(os.getenv('AUTOSCALER_TARGET_CPU', '70.0')),
        'enable_predictive_scaling': os.getenv('ENABLE_PREDICTIVE_SCALING', 'true').lower() == 'true',
        'enabled': os.getenv('ENABLE_AUTO_SCALING', 'false').lower() == 'true'
    }
    
    # Background Task Optimizer Configuration
    config['task_optimizer'] = {
        'max_concurrent_tasks': int(os.getenv('MAX_BACKGROUND_TASKS', '10')),
        'enable_dynamic_scaling': os.getenv('ENABLE_DYNAMIC_TASK_SCALING', 'true').lower() == 'true',
        'enable_batch_processing': os.getenv('ENABLE_BATCH_PROCESSING', 'true').lower() == 'true',
        'enabled': os.getenv('ENABLE_TASK_OPTIMIZER', 'true').lower() == 'true'
    }
    
    # Override with app config if available
    if hasattr(app, 'config'):
        app_phase3_config = app.config.get('PHASE3_CONFIG', {})
        for service, service_config in app_phase3_config.items():
            if service in config:
                config[service].update(service_config)
    
    return config


def _configure_redis_cluster(app, config: Dict[str, Any]):
    """Configure Redis cluster service."""
    redis_config = config.get('redis_cluster', {})
    
    if not redis_config.get('enabled', False):
        logger.info("Redis cluster disabled in configuration")
        return
    
    try:
        # Set app configuration for Redis cluster
        app.config.update({
            'REDIS_CLUSTER_NODES': redis_config.get('nodes', []),
            'REDIS_PASSWORD': redis_config.get('password', ''),
            'REDIS_MAX_CONNECTIONS': redis_config.get('max_connections', 100),
            'REDIS_HEALTH_CHECK_INTERVAL': redis_config.get('health_check_interval', 30)
        })
        
        logger.info("Redis cluster configuration loaded")
        
    except Exception as e:
        logger.error(f"Error configuring Redis cluster: {str(e)}")


def _configure_auto_scaler(app, config: Dict[str, Any]):
    """Configure auto-scaler service."""
    scaler_config = config.get('auto_scaler', {})
    
    if not scaler_config.get('enabled', False):
        logger.info("Auto-scaler disabled in configuration")
        return
    
    try:
        # Set app configuration for auto-scaler
        app.config.update({
            'AUTOSCALER_MIN_INSTANCES': scaler_config.get('min_instances', 1),
            'AUTOSCALER_MAX_INSTANCES': scaler_config.get('max_instances', 10),
            'AUTOSCALER_TARGET_CPU': scaler_config.get('target_cpu_utilization', 70.0),
            'ENABLE_PREDICTIVE_SCALING': scaler_config.get('enable_predictive_scaling', True)
        })
        
        logger.info("Auto-scaler configuration loaded")
        
    except Exception as e:
        logger.error(f"Error configuring auto-scaler: {str(e)}")


def _configure_task_optimizer(app, config: Dict[str, Any]):
    """Configure background task optimizer."""
    task_config = config.get('task_optimizer', {})
    
    if not task_config.get('enabled', False):
        logger.info("Task optimizer disabled in configuration")
        return
    
    try:
        # Set app configuration for task optimizer
        app.config.update({
            'MAX_BACKGROUND_TASKS': task_config.get('max_concurrent_tasks', 10),
            'ENABLE_DYNAMIC_TASK_SCALING': task_config.get('enable_dynamic_scaling', True),
            'ENABLE_BATCH_PROCESSING': task_config.get('enable_batch_processing', True)
        })
        
        logger.info("Background task optimizer configuration loaded")
        
    except Exception as e:
        logger.error(f"Error configuring task optimizer: {str(e)}")


def _register_phase3_commands(app):
    """Register CLI commands for Phase 3 services."""
    if not PHASE3_AVAILABLE:
        return
    
    try:
        import click
        
        @app.cli.command('phase3-status')
        def phase3_status_command():
            """Check Phase 3 services status."""
            try:
                status = phase3_integration.get_integration_status()
                click.echo("Phase 3 Services Status:")
                click.echo("-" * 30)
                
                for key, value in status.items():
                    if key != 'timestamp':
                        status_indicator = "✓" if value else "✗"
                        click.echo(f"{status_indicator} {key}: {value}")
                
                click.echo(f"\nTimestamp: {status.get('timestamp', 'N/A')}")
                
            except Exception as e:
                click.echo(f"Error getting Phase 3 status: {str(e)}", err=True)
        
        @app.cli.command('phase3-restart')
        def phase3_restart_command():
            """Restart Phase 3 services."""
            try:
                click.echo("Restarting Phase 3 services...")
                result = phase3_integration.restart_components()
                
                if result.get('success', False):
                    click.echo("✓ Phase 3 services restarted successfully")
                    for service, status in result.get('results', {}).items():
                        click.echo(f"  - {service}: {status}")
                else:
                    click.echo(f"✗ Error restarting Phase 3 services: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                click.echo(f"Error restarting Phase 3 services: {str(e)}", err=True)
        
        @app.cli.command('redis-cluster-status')
        def redis_cluster_status_command():
            """Check Redis cluster status."""
            try:
                status = redis_cluster_manager.get_cluster_status()
                click.echo("Redis Cluster Status:")
                click.echo("-" * 25)
                
                for key, value in status.items():
                    click.echo(f"{key}: {value}")
                
            except Exception as e:
                click.echo(f"Error getting Redis cluster status: {str(e)}", err=True)
        
        @app.cli.command('autoscaler-status')
        def autoscaler_status_command():
            """Check auto-scaler status."""
            try:
                status = advanced_auto_scaler.get_comprehensive_status()
                click.echo("Auto-Scaler Status:")
                click.echo("-" * 20)
                
                # Show key metrics
                click.echo(f"Monitoring Active: {status.get('monitoring_active', False)}")
                click.echo(f"Current Instances: {status.get('current_instances', 'N/A')}")
                click.echo(f"Recent Scaling Events: {len(status.get('recent_scaling_events', []))}")
                
            except Exception as e:
                click.echo(f"Error getting auto-scaler status: {str(e)}", err=True)
        
        @app.cli.command('task-optimizer-status')
        def task_optimizer_status_command():
            """Check background task optimizer status."""
            try:
                status = background_task_optimizer.get_comprehensive_status()
                click.echo("Background Task Optimizer Status:")
                click.echo("-" * 35)
                
                # Show key metrics
                queue_status = status.get('queue_status', {})
                click.echo(f"Monitoring Active: {background_task_optimizer.monitoring_active}")
                click.echo(f"Pending Tasks: {queue_status.get('pending_tasks', 0)}")
                click.echo(f"Running Tasks: {queue_status.get('running_tasks', 0)}")
                
                performance = status.get('performance_metrics', {})
                click.echo(f"Success Rate: {performance.get('success_rate', 0):.2%}")
                click.echo(f"Worker Utilization: {performance.get('worker_utilization', 0):.2%}")
                
            except Exception as e:
                click.echo(f"Error getting task optimizer status: {str(e)}", err=True)
        
        logger.info("Phase 3 CLI commands registered")
        
    except ImportError:
        logger.warning("Click not available - Phase 3 CLI commands not registered")
    except Exception as e:
        logger.error(f"Error registering Phase 3 CLI commands: {str(e)}")


# =============================================================================
# PHASE 3 MONITORING AND HEALTH CHECKS
# =============================================================================

def get_phase3_health_check() -> Dict[str, Any]:
    """Get Phase 3 services health check for monitoring."""
    if not PHASE3_AVAILABLE:
        return {
            'phase3_available': False,
            'status': 'not_available',
            'message': 'Phase 3 services not installed'
        }
    
    try:
        health_check = {
            'phase3_available': True,
            'status': 'healthy',
            'timestamp': None,
            'services': {}
        }
        
        # Redis Cluster Health
        try:
            redis_status = redis_cluster_manager.get_cluster_status()
            health_check['services']['redis_cluster'] = {
                'healthy': redis_status.get('cluster_healthy', False),
                'active_nodes': redis_status.get('active_nodes', 0),
                'total_nodes': redis_status.get('total_nodes', 0)
            }
        except Exception as e:
            health_check['services']['redis_cluster'] = {
                'healthy': False,
                'error': str(e)
            }
        
        # Auto-Scaler Health
        try:
            scaler_active = advanced_auto_scaler.monitoring_active
            health_check['services']['auto_scaler'] = {
                'healthy': scaler_active,
                'monitoring_active': scaler_active
            }
        except Exception as e:
            health_check['services']['auto_scaler'] = {
                'healthy': False,
                'error': str(e)
            }
        
        # Task Optimizer Health
        try:
            optimizer_active = background_task_optimizer.monitoring_active
            health_check['services']['task_optimizer'] = {
                'healthy': optimizer_active,
                'monitoring_active': optimizer_active
            }
        except Exception as e:
            health_check['services']['task_optimizer'] = {
                'healthy': False,
                'error': str(e)
            }
        
        # Determine overall status
        service_health = [service.get('healthy', False) for service in health_check['services'].values()]
        if not all(service_health):
            health_check['status'] = 'degraded'
        
        return health_check
        
    except Exception as e:
        return {
            'phase3_available': True,
            'status': 'error',
            'error': str(e)
        }


def get_phase3_metrics() -> Dict[str, Any]:
    """Get Phase 3 services metrics for monitoring dashboards."""
    if not PHASE3_AVAILABLE:
        return {'phase3_available': False}
    
    try:
        metrics = {
            'phase3_available': True,
            'timestamp': None,
            'redis_cluster': {},
            'auto_scaler': {},
            'task_optimizer': {}
        }
        
        # Redis Cluster Metrics
        try:
            redis_metrics = redis_cluster_manager.collect_health_metrics()
            metrics['redis_cluster'] = redis_metrics
        except Exception as e:
            metrics['redis_cluster'] = {'error': str(e)}
        
        # Auto-Scaler Metrics
        try:
            scaler_metrics = advanced_auto_scaler.get_performance_metrics()
            metrics['auto_scaler'] = scaler_metrics
        except Exception as e:
            metrics['auto_scaler'] = {'error': str(e)}
        
        # Task Optimizer Metrics
        try:
            task_metrics = background_task_optimizer.get_task_metrics()
            metrics['task_optimizer'] = task_metrics
        except Exception as e:
            metrics['task_optimizer'] = {'error': str(e)}
        
        return metrics
        
    except Exception as e:
        return {
            'phase3_available': True,
            'error': str(e)
        }


# =============================================================================
# BACKGROUND TASK SUBMISSION HELPERS
# =============================================================================

def submit_analysis_task(payload: Dict[str, Any], priority: str = 'NORMAL') -> Optional[str]:
    """Helper function to submit analysis tasks."""
    if not PHASE3_AVAILABLE:
        logger.warning("Phase 3 not available - cannot submit analysis task")
        return None
    
    try:
        from .services.background_task_optimizer import TaskPriority, WorkerType
        
        task_id = background_task_optimizer.submit_task(
            task_type='analysis',
            payload=payload,
            priority=TaskPriority[priority],
            worker_type=WorkerType.CPU_INTENSIVE
        )
        
        logger.info(f"Analysis task submitted: {task_id}")
        return task_id
        
    except Exception as e:
        logger.error(f"Error submitting analysis task: {str(e)}")
        return None


def submit_notification_task(payload: Dict[str, Any], priority: str = 'NORMAL') -> Optional[str]:
    """Helper function to submit notification tasks."""
    if not PHASE3_AVAILABLE:
        logger.warning("Phase 3 not available - cannot submit notification task")
        return None
    
    try:
        from .services.background_task_optimizer import TaskPriority, WorkerType
        
        task_id = background_task_optimizer.submit_task(
            task_type='notification',
            payload=payload,
            priority=TaskPriority[priority],
            worker_type=WorkerType.IO_INTENSIVE
        )
        
        logger.info(f"Notification task submitted: {task_id}")
        return task_id
        
    except Exception as e:
        logger.error(f"Error submitting notification task: {str(e)}")
        return None


def submit_cleanup_task(payload: Dict[str, Any], priority: str = 'LOW') -> Optional[str]:
    """Helper function to submit cleanup tasks."""
    if not PHASE3_AVAILABLE:
        logger.warning("Phase 3 not available - cannot submit cleanup task")
        return None
    
    try:
        from .services.background_task_optimizer import TaskPriority, WorkerType
        
        task_id = background_task_optimizer.submit_task(
            task_type='cleanup',
            payload=payload,
            priority=TaskPriority[priority],
            worker_type=WorkerType.IO_INTENSIVE
        )
        
        logger.info(f"Cleanup task submitted: {task_id}")
        return task_id
        
    except Exception as e:
        logger.error(f"Error submitting cleanup task: {str(e)}")
        return None


# =============================================================================
# CACHE MANAGEMENT HELPERS
# =============================================================================

def warm_critical_cache() -> bool:
    """Helper function to warm critical cache endpoints."""
    if not PHASE3_AVAILABLE:
        logger.warning("Phase 3 not available - cannot warm cache")
        return False
    
    try:
        from .services.redis_cluster_manager import CacheWarmingStrategy
        
        strategy = CacheWarmingStrategy(
            strategy_name='critical_endpoints',
            priority_order=['high', 'medium'],
            batch_size=25,
            delay_between_batches=0.1,
            warm_dependencies=True,
            max_warm_time=180
        )
        
        result = redis_cluster_manager.start_cache_warming(strategy)
        logger.info("Critical cache warming initiated")
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"Error warming critical cache: {str(e)}")
        return False


def invalidate_user_cache(user_id: str) -> bool:
    """Helper function to invalidate user-specific cache."""
    if not PHASE3_AVAILABLE:
        logger.warning("Phase 3 not available - cannot invalidate cache")
        return False
    
    try:
        from .services.redis_cluster_manager import InvalidationPolicy
        
        policy = InvalidationPolicy(
            policy_name='user_invalidation',
            invalidation_type='pattern',
            target_patterns=[f'user:{user_id}:*', f'profile:{user_id}:*'],
            cascade_invalidation=True,
            notification_enabled=False
        )
        
        result = redis_cluster_manager.trigger_invalidation(policy)
        logger.info(f"User cache invalidated for user {user_id}")
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"Error invalidating user cache: {str(e)}")
        return False


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

__all__ = [
    'init_phase3_services',
    'get_phase3_health_check',
    'get_phase3_metrics',
    'submit_analysis_task',
    'submit_notification_task',
    'submit_cleanup_task',
    'warm_critical_cache',
    'invalidate_user_cache',
    'PHASE3_AVAILABLE'
]
