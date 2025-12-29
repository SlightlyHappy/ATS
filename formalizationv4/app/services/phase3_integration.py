"""
Phase 3.3 Integration Module
Integrates Redis Cluster Manager, Advanced Auto-Scaler, and Background Task Optimizer
with existing Flask application infrastructure.
"""
import logging
from typing import Dict, Any, Optional
from flask import Blueprint, Flask, request, jsonify, current_app
from datetime import datetime
import json
import asyncio
from dataclasses import asdict

from .redis_cluster_manager import (
    redis_cluster_manager, 
    RedisClusterConfig, 
    CacheWarmingStrategy,
    InvalidationPolicy
)
from .advanced_auto_scaler import (
    advanced_auto_scaler,
    ScalingConfig,
    ScalingRule,
    ScalingMetric
)
from .background_task_optimizer import (
    background_task_optimizer,
    TaskPriority,
    WorkerType,
    TaskSchedulingConfig
)

logger = logging.getLogger(__name__)

# =============================================================================
# PHASE 3 INTEGRATION BLUEPRINT
# =============================================================================

phase3_bp = Blueprint('phase3', __name__, url_prefix='/api/v1/phase3')

# =============================================================================
# REDIS CLUSTER MANAGEMENT ENDPOINTS
# =============================================================================

@phase3_bp.route('/redis/cluster/status', methods=['GET'])
def get_redis_cluster_status():
    """Get Redis cluster status and health metrics."""
    try:
        status = redis_cluster_manager.get_cluster_status()
        return jsonify({
            'success': True,
            'cluster_status': status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting Redis cluster status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/redis/cluster/config', methods=['GET', 'PUT'])
def manage_redis_cluster_config():
    """Get or update Redis cluster configuration."""
    if request.method == 'GET':
        try:
            config = redis_cluster_manager.get_configuration()
            return jsonify({
                'success': True,
                'configuration': config
            })
        except Exception as e:
            logger.error(f"Error getting Redis cluster config: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'PUT':
        try:
            config_data = request.get_json()
            
            # Validate configuration
            required_fields = ['nodes', 'password', 'max_connections']
            if not all(field in config_data for field in required_fields):
                return jsonify({
                    'success': False,
                    'error': 'Missing required configuration fields'
                }), 400
            
            # Create new configuration
            new_config = RedisClusterConfig(
                nodes=config_data['nodes'],
                password=config_data['password'],
                max_connections=config_data['max_connections'],
                health_check_interval=config_data.get('health_check_interval', 30),
                retry_attempts=config_data.get('retry_attempts', 3),
                connection_timeout=config_data.get('connection_timeout', 5),
                socket_keepalive=config_data.get('socket_keepalive', True),
                socket_keepalive_options=config_data.get('socket_keepalive_options', {}),
                cluster_require_full_coverage=config_data.get('cluster_require_full_coverage', False)
            )
            
            # Update configuration
            result = redis_cluster_manager.update_configuration(new_config)
            
            return jsonify({
                'success': True,
                'result': result,
                'message': 'Redis cluster configuration updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating Redis cluster config: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@phase3_bp.route('/redis/cache/warm', methods=['POST'])
def warm_cache():
    """Trigger cache warming with specified strategy."""
    try:
        warm_data = request.get_json()
        strategy_name = warm_data.get('strategy', 'critical_endpoints')
        
        # Validate strategy
        valid_strategies = ['critical_endpoints', 'user_data', 'analytics_data', 'full_warm']
        if strategy_name not in valid_strategies:
            return jsonify({
                'success': False,
                'error': f'Invalid strategy. Must be one of: {valid_strategies}'
            }), 400
        
        # Create warming strategy
        strategy = CacheWarmingStrategy(
            strategy_name=strategy_name,
            priority_order=warm_data.get('priority_order', ['high', 'medium', 'low']),
            batch_size=warm_data.get('batch_size', 50),
            delay_between_batches=warm_data.get('delay_between_batches', 0.1),
            target_endpoints=warm_data.get('target_endpoints', []),
            warm_dependencies=warm_data.get('warm_dependencies', True),
            max_warm_time=warm_data.get('max_warm_time', 300)
        )
        
        # Start cache warming
        result = redis_cluster_manager.start_cache_warming(strategy)
        
        return jsonify({
            'success': True,
            'result': result,
            'message': f'Cache warming started with strategy: {strategy_name}'
        })
        
    except Exception as e:
        logger.error(f"Error warming cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/redis/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """Trigger cache invalidation with specified policy."""
    try:
        invalidation_data = request.get_json()
        
        # Create invalidation policy
        policy = InvalidationPolicy(
            policy_name=invalidation_data.get('policy_name', 'manual_invalidation'),
            invalidation_type=invalidation_data.get('invalidation_type', 'pattern'),
            target_patterns=invalidation_data.get('target_patterns', []),
            cascade_invalidation=invalidation_data.get('cascade_invalidation', False),
            batch_size=invalidation_data.get('batch_size', 100),
            delay_between_batches=invalidation_data.get('delay_between_batches', 0.05),
            notification_enabled=invalidation_data.get('notification_enabled', True)
        )
        
        # Trigger invalidation
        result = redis_cluster_manager.trigger_invalidation(policy)
        
        return jsonify({
            'success': True,
            'result': result,
            'message': 'Cache invalidation completed'
        })
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/redis/metrics', methods=['GET'])
def get_redis_metrics():
    """Get Redis cluster performance metrics."""
    try:
        metrics = redis_cluster_manager.collect_health_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting Redis metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# ADVANCED AUTO-SCALER ENDPOINTS
# =============================================================================

@phase3_bp.route('/autoscaler/status', methods=['GET'])
def get_autoscaler_status():
    """Get auto-scaler status and configuration."""
    try:
        status = advanced_auto_scaler.get_comprehensive_status()
        return jsonify({
            'success': True,
            'autoscaler_status': status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting auto-scaler status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/autoscaler/config', methods=['GET', 'PUT'])
def manage_autoscaler_config():
    """Get or update auto-scaler configuration."""
    if request.method == 'GET':
        try:
            config = advanced_auto_scaler.get_current_configuration()
            return jsonify({
                'success': True,
                'configuration': config
            })
        except Exception as e:
            logger.error(f"Error getting auto-scaler config: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'PUT':
        try:
            config_data = request.get_json()
            
            # Create new scaling configuration
            new_config = ScalingConfig(
                min_instances=config_data.get('min_instances', 1),
                max_instances=config_data.get('max_instances', 10),
                target_cpu_utilization=config_data.get('target_cpu_utilization', 70.0),
                target_memory_utilization=config_data.get('target_memory_utilization', 80.0),
                scale_up_threshold=config_data.get('scale_up_threshold', 80.0),
                scale_down_threshold=config_data.get('scale_down_threshold', 30.0),
                scale_up_cooldown=config_data.get('scale_up_cooldown', 300),
                scale_down_cooldown=config_data.get('scale_down_cooldown', 600),
                enable_predictive_scaling=config_data.get('enable_predictive_scaling', True),
                prediction_window_minutes=config_data.get('prediction_window_minutes', 15),
                scaling_step_size=config_data.get('scaling_step_size', 1)
            )
            
            # Update configuration
            result = advanced_auto_scaler.update_configuration(new_config)
            
            return jsonify({
                'success': True,
                'result': result,
                'message': 'Auto-scaler configuration updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating auto-scaler config: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@phase3_bp.route('/autoscaler/scaling-rules', methods=['GET', 'POST'])
def manage_scaling_rules():
    """Get or create scaling rules."""
    if request.method == 'GET':
        try:
            rules = advanced_auto_scaler.get_scaling_rules()
            return jsonify({
                'success': True,
                'scaling_rules': rules
            })
        except Exception as e:
            logger.error(f"Error getting scaling rules: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            rule_data = request.get_json()
            
            # Validate required fields
            required_fields = ['rule_name', 'metric_name', 'condition', 'threshold', 'action']
            if not all(field in rule_data for field in required_fields):
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields for scaling rule'
                }), 400
            
            # Create scaling rule
            scaling_rule = ScalingRule(
                rule_name=rule_data['rule_name'],
                metric_name=rule_data['metric_name'],
                condition=rule_data['condition'],
                threshold=rule_data['threshold'],
                action=rule_data['action'],
                priority=rule_data.get('priority', 1),
                cooldown_seconds=rule_data.get('cooldown_seconds', 300),
                enabled=rule_data.get('enabled', True)
            )
            
            # Add rule
            result = advanced_auto_scaler.add_scaling_rule(scaling_rule)
            
            return jsonify({
                'success': True,
                'result': result,
                'message': f'Scaling rule {rule_data["rule_name"]} created successfully'
            })
            
        except Exception as e:
            logger.error(f"Error creating scaling rule: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@phase3_bp.route('/autoscaler/scale', methods=['POST'])
def trigger_manual_scaling():
    """Trigger manual scaling action."""
    try:
        scale_data = request.get_json()
        
        action = scale_data.get('action')  # 'scale_up' or 'scale_down'
        instances = scale_data.get('instances', 1)
        reason = scale_data.get('reason', 'manual_trigger')
        
        if action not in ['scale_up', 'scale_down']:
            return jsonify({
                'success': False,
                'error': 'Action must be either "scale_up" or "scale_down"'
            }), 400
        
        # Trigger scaling
        if action == 'scale_up':
            result = advanced_auto_scaler.trigger_scale_up(instances, reason)
        else:
            result = advanced_auto_scaler.trigger_scale_down(instances, reason)
        
        return jsonify({
            'success': True,
            'result': result,
            'message': f'Manual scaling {action} completed'
        })
        
    except Exception as e:
        logger.error(f"Error triggering manual scaling: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/autoscaler/predictions', methods=['GET'])
def get_scaling_predictions():
    """Get scaling predictions and recommendations."""
    try:
        predictions = advanced_auto_scaler.get_scaling_predictions()
        return jsonify({
            'success': True,
            'predictions': predictions,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting scaling predictions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/autoscaler/metrics', methods=['GET'])
def get_autoscaler_metrics():
    """Get auto-scaler performance metrics."""
    try:
        metrics = advanced_auto_scaler.get_performance_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting auto-scaler metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# BACKGROUND TASK OPTIMIZER ENDPOINTS
# =============================================================================

@phase3_bp.route('/tasks/submit', methods=['POST'])
def submit_background_task():
    """Submit a background task for processing."""
    try:
        task_data = request.get_json()
        
        # Validate required fields
        required_fields = ['task_type', 'payload']
        if not all(field in task_data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: task_type and payload'
            }), 400
        
        # Parse optional fields
        priority = TaskPriority[task_data.get('priority', 'NORMAL')]
        worker_type = WorkerType[task_data.get('worker_type', 'GENERAL')]
        
        # Submit task
        task_id = background_task_optimizer.submit_task(
            task_type=task_data['task_type'],
            payload=task_data['payload'],
            priority=priority,
            worker_type=worker_type,
            dependencies=task_data.get('dependencies'),
            scheduled_at=task_data.get('scheduled_at'),
            max_retries=task_data.get('max_retries', 3),
            timeout_seconds=task_data.get('timeout_seconds', 300)
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Task submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting background task: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/tasks/<task_id>', methods=['GET', 'DELETE'])
def manage_background_task(task_id):
    """Get task status or cancel a task."""
    if request.method == 'GET':
        try:
            status = background_task_optimizer.get_task_status(task_id)
            if status is None:
                return jsonify({
                    'success': False,
                    'error': 'Task not found'
                }), 404
            
            return jsonify({
                'success': True,
                'task_status': status
            })
            
        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'DELETE':
        try:
            cancelled = background_task_optimizer.cancel_task(task_id)
            if not cancelled:
                return jsonify({
                    'success': False,
                    'error': 'Task not found or cannot be cancelled'
                }), 404
            
            return jsonify({
                'success': True,
                'message': 'Task cancelled successfully'
            })
            
        except Exception as e:
            logger.error(f"Error cancelling task: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@phase3_bp.route('/tasks/status', methods=['GET'])
def get_task_optimizer_status():
    """Get comprehensive background task optimizer status."""
    try:
        status = background_task_optimizer.get_comprehensive_status()
        return jsonify({
            'success': True,
            'optimizer_status': status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting task optimizer status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/tasks/metrics', methods=['GET'])
def get_task_metrics():
    """Get background task processing metrics."""
    try:
        metrics = background_task_optimizer.get_task_metrics()
        return jsonify({
            'success': True,
            'task_metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting task metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phase3_bp.route('/tasks/config', methods=['GET', 'PUT'])
def manage_task_config():
    """Get or update background task configuration."""
    if request.method == 'GET':
        try:
            config = {
                'max_concurrent_tasks': background_task_optimizer.config.max_concurrent_tasks,
                'max_workers_per_type': {k.value: v for k, v in background_task_optimizer.config.max_workers_per_type.items()},
                'enable_dynamic_scaling': background_task_optimizer.config.enable_dynamic_scaling,
                'enable_load_balancing': background_task_optimizer.config.enable_load_balancing,
                'batch_processing_enabled': background_task_optimizer.config.batch_processing_enabled
            }
            
            return jsonify({
                'success': True,
                'configuration': config
            })
            
        except Exception as e:
            logger.error(f"Error getting task config: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'PUT':
        try:
            config_data = request.get_json()
            
            # Update configuration
            if 'max_concurrent_tasks' in config_data:
                background_task_optimizer.config.max_concurrent_tasks = config_data['max_concurrent_tasks']
            
            if 'enable_dynamic_scaling' in config_data:
                background_task_optimizer.enable_dynamic_scaling = config_data['enable_dynamic_scaling']
            
            if 'batch_processing_enabled' in config_data:
                background_task_optimizer.config.batch_processing_enabled = config_data['batch_processing_enabled']
            
            return jsonify({
                'success': True,
                'message': 'Background task configuration updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating task config: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


# =============================================================================
# PHASE 3 COMBINED STATUS AND HEALTH CHECK
# =============================================================================

@phase3_bp.route('/health', methods=['GET'])
def phase3_health_check():
    """Comprehensive Phase 3 health check."""
    try:
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'phase3_status': 'healthy',
            'components': {}
        }
        
        # Check Redis Cluster Manager
        try:
            redis_status = redis_cluster_manager.get_cluster_status()
            health_status['components']['redis_cluster'] = {
                'status': 'healthy' if redis_status.get('cluster_healthy', False) else 'degraded',
                'active_nodes': redis_status.get('active_nodes', 0),
                'total_nodes': redis_status.get('total_nodes', 0)
            }
        except Exception as e:
            health_status['components']['redis_cluster'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check Advanced Auto-Scaler
        try:
            autoscaler_status = advanced_auto_scaler.get_comprehensive_status()
            health_status['components']['autoscaler'] = {
                'status': 'healthy' if autoscaler_status.get('monitoring_active', False) else 'inactive',
                'current_instances': autoscaler_status.get('current_instances', 0),
                'scaling_events': len(autoscaler_status.get('recent_scaling_events', []))
            }
        except Exception as e:
            health_status['components']['autoscaler'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check Background Task Optimizer
        try:
            task_status = background_task_optimizer.get_comprehensive_status()
            health_status['components']['task_optimizer'] = {
                'status': 'healthy' if background_task_optimizer.monitoring_active else 'inactive',
                'pending_tasks': task_status.get('queue_status', {}).get('pending_tasks', 0),
                'running_tasks': task_status.get('queue_status', {}).get('running_tasks', 0),
                'worker_utilization': task_status.get('performance_metrics', {}).get('worker_utilization', 0.0)
            }
        except Exception as e:
            health_status['components']['task_optimizer'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Determine overall status
        component_statuses = [comp['status'] for comp in health_status['components'].values()]
        if any(status == 'unhealthy' for status in component_statuses):
            health_status['phase3_status'] = 'unhealthy'
        elif any(status == 'degraded' for status in component_statuses):
            health_status['phase3_status'] = 'degraded'
        elif any(status == 'inactive' for status in component_statuses):
            health_status['phase3_status'] = 'inactive'
        
        return jsonify({
            'success': True,
            'health_status': health_status
        })
        
    except Exception as e:
        logger.error(f"Error in Phase 3 health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'phase3_status': 'error'
        }), 500


@phase3_bp.route('/status/comprehensive', methods=['GET'])
def get_comprehensive_phase3_status():
    """Get comprehensive status of all Phase 3 components."""
    try:
        comprehensive_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'phase3_version': '3.0.0',
            'components': {}
        }
        
        # Redis Cluster Manager Status
        try:
            redis_status = redis_cluster_manager.get_cluster_status()
            redis_metrics = redis_cluster_manager.collect_health_metrics()
            comprehensive_status['components']['redis_cluster_manager'] = {
                'cluster_status': redis_status,
                'health_metrics': redis_metrics,
                'component_version': '3.1.0'
            }
        except Exception as e:
            comprehensive_status['components']['redis_cluster_manager'] = {
                'error': str(e),
                'status': 'error'
            }
        
        # Advanced Auto-Scaler Status
        try:
            autoscaler_status = advanced_auto_scaler.get_comprehensive_status()
            autoscaler_metrics = advanced_auto_scaler.get_performance_metrics()
            comprehensive_status['components']['advanced_auto_scaler'] = {
                'scaler_status': autoscaler_status,
                'performance_metrics': autoscaler_metrics,
                'component_version': '3.2.0'
            }
        except Exception as e:
            comprehensive_status['components']['advanced_auto_scaler'] = {
                'error': str(e),
                'status': 'error'
            }
        
        # Background Task Optimizer Status
        try:
            task_status = background_task_optimizer.get_comprehensive_status()
            task_metrics = background_task_optimizer.get_task_metrics()
            comprehensive_status['components']['background_task_optimizer'] = {
                'optimizer_status': task_status,
                'task_metrics': task_metrics,
                'component_version': '3.2.0'
            }
        except Exception as e:
            comprehensive_status['components']['background_task_optimizer'] = {
                'error': str(e),
                'status': 'error'
            }
        
        return jsonify({
            'success': True,
            'comprehensive_status': comprehensive_status
        })
        
    except Exception as e:
        logger.error(f"Error getting comprehensive Phase 3 status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# PHASE 3 INTEGRATION CLASS
# =============================================================================

class Phase3Integration:
    """
    Integration class for Phase 3 enterprise features.
    Provides centralized management and configuration.
    """
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.redis_cluster_manager = redis_cluster_manager
        self.advanced_auto_scaler = advanced_auto_scaler
        self.background_task_optimizer = background_task_optimizer
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize Phase 3 integration with Flask app."""
        self.app = app
        
        # Register blueprint
        app.register_blueprint(phase3_bp)
        
        # Initialize all Phase 3 components
        self._initialize_components()
        
        # Setup shutdown handlers
        self._setup_shutdown_handlers()
        
        logger.info("Phase 3 Integration initialized successfully")
    
    def _initialize_components(self):
        """Initialize all Phase 3 components."""
        try:
            # Initialize Redis Cluster Manager
            if not self.redis_cluster_manager.is_initialized():
                self.redis_cluster_manager.init_app(self.app)
            
            # Initialize Advanced Auto-Scaler
            if not self.advanced_auto_scaler.monitoring_active:
                self.advanced_auto_scaler.init_app(self.app)
            
            # Initialize Background Task Optimizer
            if not self.background_task_optimizer.monitoring_active:
                self.background_task_optimizer.init_app(self.app)
            
            logger.info("All Phase 3 components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing Phase 3 components: {str(e)}")
            raise
    
    def _setup_shutdown_handlers(self):
        """Setup proper shutdown handlers for all components."""
        import atexit
        
        def shutdown_phase3():
            """Shutdown all Phase 3 components gracefully."""
            logger.info("Shutting down Phase 3 components...")
            
            try:
                self.background_task_optimizer.stop_monitoring()
                logger.info("Background task optimizer stopped")
            except Exception as e:
                logger.error(f"Error stopping background task optimizer: {str(e)}")
            
            try:
                self.advanced_auto_scaler.stop_monitoring()
                logger.info("Advanced auto-scaler stopped")
            except Exception as e:
                logger.error(f"Error stopping advanced auto-scaler: {str(e)}")
            
            try:
                self.redis_cluster_manager.shutdown()
                logger.info("Redis cluster manager stopped")
            except Exception as e:
                logger.error(f"Error stopping Redis cluster manager: {str(e)}")
        
        atexit.register(shutdown_phase3)
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get overall Phase 3 integration status."""
        try:
            return {
                'integration_active': True,
                'redis_cluster_initialized': self.redis_cluster_manager.is_initialized(),
                'autoscaler_monitoring': self.advanced_auto_scaler.monitoring_active,
                'task_optimizer_monitoring': self.background_task_optimizer.monitoring_active,
                'blueprint_registered': 'phase3' in self.app.blueprints if self.app else False,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting integration status: {str(e)}")
            return {'error': str(e)}
    
    def restart_components(self) -> Dict[str, Any]:
        """Restart all Phase 3 components."""
        try:
            results = {}
            
            # Restart Background Task Optimizer
            try:
                self.background_task_optimizer.stop_monitoring()
                self.background_task_optimizer.start_monitoring()
                results['task_optimizer'] = 'restarted'
            except Exception as e:
                results['task_optimizer'] = f'error: {str(e)}'
            
            # Restart Advanced Auto-Scaler
            try:
                self.advanced_auto_scaler.stop_monitoring()
                self.advanced_auto_scaler.start_monitoring()
                results['auto_scaler'] = 'restarted'
            except Exception as e:
                results['auto_scaler'] = f'error: {str(e)}'
            
            # Restart Redis Cluster Manager
            try:
                self.redis_cluster_manager.restart_cluster()
                results['redis_cluster'] = 'restarted'
            except Exception as e:
                results['redis_cluster'] = f'error: {str(e)}'
            
            logger.info("Phase 3 components restart completed")
            return {
                'success': True,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error restarting Phase 3 components: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# =============================================================================
# GLOBAL PHASE 3 INTEGRATION INSTANCE
# =============================================================================

phase3_integration = Phase3Integration()
