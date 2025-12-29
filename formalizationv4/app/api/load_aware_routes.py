"""
Load-Aware Processing API Blueprint - Phase 2.4 Implementation
Provides REST API endpoints for monitoring and controlling load-aware processing,
auto-scaling, and system health management.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

try:
    from flask import Blueprint, jsonify, request, current_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Blueprint = jsonify = request = current_app = None

from app.services.load_aware_integration import load_aware_integration

logger = logging.getLogger(__name__)

# =============================================================================
# BLUEPRINT CREATION
# =============================================================================

if FLASK_AVAILABLE:
    load_aware_bp = Blueprint('load_aware', __name__, url_prefix='/api/load-aware')
else:
    load_aware_bp = None
    logger.warning("Flask not available, load-aware API endpoints disabled")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def safe_jsonify(data: Any, status_code: int = 200):
    """Safe JSON response with error handling."""
    try:
        if not FLASK_AVAILABLE:
            return {'error': 'Flask not available'}, 500
            
        response = jsonify(data)
        response.status_code = status_code
        return response
    except Exception as e:
        logger.error(f"Error creating JSON response: {str(e)}")
        error_response = jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        })
        error_response.status_code = 500
        return error_response

def validate_json_request():
    """Validate and parse JSON request data."""
    try:
        if not request.is_json:
            return None, {'error': 'Content-Type must be application/json'}, 400
        
        data = request.get_json()
        if data is None:
            return None, {'error': 'Invalid JSON data'}, 400
        
        return data, None, None
        
    except Exception as e:
        return None, {'error': f'JSON parsing error: {str(e)}'}, 400

# =============================================================================
# SYSTEM HEALTH AND STATUS ENDPOINTS
# =============================================================================

if FLASK_AVAILABLE:
    @load_aware_bp.route('/health', methods=['GET'])
    def get_system_health():
        """Get comprehensive system health status."""
        try:
            health_report = load_aware_integration.get_system_health_report()
            return safe_jsonify(health_report)
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return safe_jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500)

    @load_aware_bp.route('/status', methods=['GET'])
    def get_integration_status():
        """Get current load-aware processing integration status."""
        try:
            status = load_aware_integration.get_integration_status()
            return safe_jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting integration status: {str(e)}")
            return safe_jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500)

    @load_aware_bp.route('/metrics', methods=['GET'])
    def get_current_metrics():
        """Get current system metrics and load information."""
        try:
            # Get query parameters
            include_history = request.args.get('history', 'false').lower() == 'true'
            hours = int(request.args.get('hours', 1))
            
            # Get current load status
            load_status = load_aware_integration.load_manager.get_current_load_status()
            
            response = {
                'timestamp': datetime.utcnow().isoformat(),
                'current_load_status': load_status
            }
            
            # Add history if requested
            if include_history:
                load_history = load_aware_integration.load_manager.get_load_history(hours)
                scaling_history = load_aware_integration.scaling_service.get_scaling_metrics_history(hours)
                
                response['load_history'] = load_history
                response['scaling_history'] = scaling_history
            
            return safe_jsonify(response)
            
        except Exception as e:
            logger.error(f"Error getting current metrics: {str(e)}")
            return safe_jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500)

# =============================================================================
# LOAD MANAGEMENT ENDPOINTS
# =============================================================================

if FLASK_AVAILABLE:
    @load_aware_bp.route('/load-management/decision', methods=['POST'])
    def force_load_decision():
        """Force a new load management decision."""
        try:
            # Parse request
            data, error, status = validate_json_request()
            if error:
                return safe_jsonify(error, status)
            
            force = data.get('force', False) if data else False
            
            # Make decision
            decision = load_aware_integration.load_manager.make_processing_decision(force=force)
            
            return safe_jsonify({
                'success': True,
                'decision': decision.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error forcing load decision: {str(e)}")
            return safe_jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500)

    @load_aware_bp.route('/load-management/strategy', methods=['POST'])
    def force_strategy_change():
        """Force a specific processing strategy."""
        try:
            # Parse request
            data, error, status = validate_json_request()
            if error:
                return safe_jsonify(error, status)
            
            if not data or 'strategy' not in data:
                return safe_jsonify({
                    'error': 'Missing required field: strategy',
                    'available_strategies': ['critical', 'high', 'medium', 'normal', 'low']
                }, 400)
            
            strategy_name = data['strategy']
            
            # Force strategy change
            result = load_aware_integration.load_manager.force_strategy_change(strategy_name)
            
            return safe_jsonify(result, 200 if result['success'] else 400)
            
        except Exception as e:
            logger.error(f"Error forcing strategy change: {str(e)}")
            return safe_jsonify({
                'success': False,
                'error': str(e)
            }, 500)

    @load_aware_bp.route('/load-management/history', methods=['GET'])
    def get_load_history():
        """Get load management history."""
        try:
            hours = int(request.args.get('hours', 1))
            history = load_aware_integration.load_manager.get_load_history(hours)
            return safe_jsonify(history)
            
        except Exception as e:
            logger.error(f"Error getting load history: {str(e)}")
            return safe_jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500)

# =============================================================================
# AUTO-SCALING ENDPOINTS
# =============================================================================

if FLASK_AVAILABLE:
    @load_aware_bp.route('/auto-scaling/evaluate', methods=['POST'])
    def evaluate_scaling():
        """Evaluate current scaling needs."""
        try:
            scaling_action = load_aware_integration.scaling_service.evaluate_scaling_need(
                load_aware_integration.load_manager
            )
            
            return safe_jsonify({
                'timestamp': datetime.utcnow().isoformat(),
                'scaling_evaluation': scaling_action.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Error evaluating scaling: {str(e)}")
            return safe_jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500)

    @load_aware_bp.route('/auto-scaling/execute', methods=['POST'])
    def execute_scaling():
        """Execute a scaling action."""
        try:
            # Evaluate scaling need
            scaling_action = load_aware_integration.scaling_service.evaluate_scaling_need(
                load_aware_integration.load_manager
            )
            
            # Execute the action
            result = load_aware_integration.scaling_service.execute_scaling_action(scaling_action)
            
            return safe_jsonify(result, 200 if result['success'] else 500)
            
        except Exception as e:
            logger.error(f"Error executing scaling: {str(e)}")
            return safe_jsonify({
                'success': False,
                'error': str(e)
            }, 500)

    @load_aware_bp.route('/auto-scaling/configuration', methods=['GET'])
    def get_scaling_configuration():
        """Get auto-scaling configuration."""
        try:
            environment = request.args.get('environment')
            config = load_aware_integration.scaling_service.get_scaling_configuration(environment)
            return safe_jsonify(config)
            
        except Exception as e:
            logger.error(f"Error getting scaling configuration: {str(e)}")
            return safe_jsonify({
                'error': str(e)
            }, 500)

    @load_aware_bp.route('/auto-scaling/configuration', methods=['PUT'])
    def update_scaling_configuration():
        """Update auto-scaling configuration."""
        try:
            # Parse request
            data, error, status = validate_json_request()
            if error:
                return safe_jsonify(error, status)
            
            if not data or 'environment' not in data or 'configuration' not in data:
                return safe_jsonify({
                    'error': 'Missing required fields: environment, configuration'
                }, 400)
            
            environment = data['environment']
            configuration = data['configuration']
            
            # Update configuration
            result = load_aware_integration.scaling_service.update_scaling_configuration(
                environment, configuration
            )
            
            return safe_jsonify(result, 200 if result['success'] else 400)
            
        except Exception as e:
            logger.error(f"Error updating scaling configuration: {str(e)}")
            return safe_jsonify({
                'success': False,
                'error': str(e)
            }, 500)

    @load_aware_bp.route('/auto-scaling/status', methods=['GET'])
    def get_scaling_status():
        """Get current auto-scaling status."""
        try:
            status = load_aware_integration.scaling_service.get_scaling_status()
            return safe_jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting scaling status: {str(e)}")
            return safe_jsonify({
                'error': str(e)
            }, 500)

# =============================================================================
# COORDINATION ENDPOINTS
# =============================================================================

if FLASK_AVAILABLE:
    @load_aware_bp.route('/coordination/decision', methods=['POST'])
    def force_coordination_decision():
        """Force an immediate coordinated processing decision."""
        try:
            result = load_aware_integration.force_coordination_decision()
            return safe_jsonify(result, 200 if result['success'] else 500)
            
        except Exception as e:
            logger.error(f"Error forcing coordination decision: {str(e)}")
            return safe_jsonify({
                'success': False,
                'error': str(e)
            }, 500)

    @load_aware_bp.route('/coordination/start', methods=['POST'])
    def start_coordination():
        """Start load-aware processing coordination."""
        try:
            load_aware_integration.start_coordination()
            
            return safe_jsonify({
                'success': True,
                'message': 'Load-aware processing coordination started',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error starting coordination: {str(e)}")
            return safe_jsonify({
                'success': False,
                'error': str(e)
            }, 500)

    @load_aware_bp.route('/coordination/stop', methods=['POST'])
    def stop_coordination():
        """Stop load-aware processing coordination."""
        try:
            load_aware_integration.stop_coordination()
            
            return safe_jsonify({
                'success': True,
                'message': 'Load-aware processing coordination stopped',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error stopping coordination: {str(e)}")
            return safe_jsonify({
                'success': False,
                'error': str(e)
            }, 500)

    @load_aware_bp.route('/coordination/history', methods=['GET'])
    def get_coordination_history():
        """Get coordination decision history."""
        try:
            limit = int(request.args.get('limit', 10))
            
            history = load_aware_integration.coordination_history[-limit:] if load_aware_integration.coordination_history else []
            
            return safe_jsonify({
                'timestamp': datetime.utcnow().isoformat(),
                'coordination_history': history,
                'total_decisions': len(load_aware_integration.coordination_history),
                'returned_count': len(history)
            })
            
        except Exception as e:
            logger.error(f"Error getting coordination history: {str(e)}")
            return safe_jsonify({
                'error': str(e)
            }, 500)

# =============================================================================
# MONITORING AND ALERTING ENDPOINTS
# =============================================================================

if FLASK_AVAILABLE:
    @load_aware_bp.route('/alerts', methods=['GET'])
    def get_current_alerts():
        """Get current system alerts and warnings."""
        try:
            current_time = datetime.utcnow()
            alerts = []
            
            # Get current load status
            load_status = load_aware_integration.load_manager.get_current_load_status()
            current_metrics = load_status.get('current_metrics', {})
            
            # Check for alert conditions
            if current_metrics.get('cpu_usage', 0) > 90:
                alerts.append({
                    'type': 'critical',
                    'category': 'resource',
                    'message': f"Critical CPU usage: {current_metrics['cpu_usage']:.1f}%",
                    'timestamp': current_time.isoformat(),
                    'metric': 'cpu_usage',
                    'value': current_metrics['cpu_usage'],
                    'threshold': 90
                })
            
            if current_metrics.get('memory_usage', 0) > 85:
                alerts.append({
                    'type': 'warning' if current_metrics['memory_usage'] < 90 else 'critical',
                    'category': 'resource',
                    'message': f"High memory usage: {current_metrics['memory_usage']:.1f}%",
                    'timestamp': current_time.isoformat(),
                    'metric': 'memory_usage',
                    'value': current_metrics['memory_usage'],
                    'threshold': 85
                })
            
            if current_metrics.get('queue_length', 0) > 20:
                alerts.append({
                    'type': 'warning',
                    'category': 'performance',
                    'message': f"High queue backlog: {current_metrics['queue_length']} items",
                    'timestamp': current_time.isoformat(),
                    'metric': 'queue_length',
                    'value': current_metrics['queue_length'],
                    'threshold': 20
                })
            
            if current_metrics.get('response_time_avg', 0) > 3.0:
                alerts.append({
                    'type': 'warning',
                    'category': 'performance',
                    'message': f"High response time: {current_metrics['response_time_avg']:.2f}s",
                    'timestamp': current_time.isoformat(),
                    'metric': 'response_time_avg',
                    'value': current_metrics['response_time_avg'],
                    'threshold': 3.0
                })
            
            if current_metrics.get('error_rate', 0) > 0.05:
                alerts.append({
                    'type': 'critical',
                    'category': 'reliability',
                    'message': f"High error rate: {current_metrics['error_rate']:.1%}",
                    'timestamp': current_time.isoformat(),
                    'metric': 'error_rate',
                    'value': current_metrics['error_rate'],
                    'threshold': 0.05
                })
            
            return safe_jsonify({
                'timestamp': current_time.isoformat(),
                'alerts_count': len(alerts),
                'alerts': alerts,
                'system_health_status': load_aware_integration.system_health_status
            })
            
        except Exception as e:
            logger.error(f"Error getting current alerts: {str(e)}")
            return safe_jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500)

    @load_aware_bp.route('/performance-summary', methods=['GET'])
    def get_performance_summary():
        """Get performance summary over specified time period."""
        try:
            hours = int(request.args.get('hours', 1))
            
            # Get metrics history
            load_history = load_aware_integration.load_manager.get_load_history(hours)
            scaling_history = load_aware_integration.scaling_service.get_scaling_metrics_history(hours)
            
            # Calculate summary statistics
            load_metrics = load_history.get('load_metrics', [])
            scaling_metrics = scaling_history.get('metrics', [])
            
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'time_period_hours': hours,
                'load_management': {
                    'total_decisions': len(load_metrics),
                    'load_distribution': {},
                    'avg_cpu_usage': 0,
                    'avg_memory_usage': 0,
                    'avg_queue_length': 0,
                    'avg_response_time': 0
                },
                'auto_scaling': {
                    'total_evaluations': len(scaling_metrics),
                    'scaling_actions': 0,
                    'avg_instances': 0
                },
                'coordination': {
                    'total_coordinated_decisions': len([d for d in load_aware_integration.coordination_history 
                                                       if datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')) 
                                                       >= datetime.utcnow() - timedelta(hours=hours)])
                }
            }
            
            # Calculate load management summary
            if load_metrics:
                summary['load_management']['avg_cpu_usage'] = sum(m['cpu_usage'] for m in load_metrics) / len(load_metrics)
                summary['load_management']['avg_memory_usage'] = sum(m['memory_usage'] for m in load_metrics) / len(load_metrics)
                summary['load_management']['avg_queue_length'] = sum(m['queue_length'] for m in load_metrics) / len(load_metrics)
                summary['load_management']['avg_response_time'] = sum(m['response_time_avg'] for m in load_metrics) / len(load_metrics)
                
                # Load distribution
                for metric in load_metrics:
                    load_class = metric['load_classification']
                    summary['load_management']['load_distribution'][load_class] = summary['load_management']['load_distribution'].get(load_class, 0) + 1
            
            # Calculate scaling summary
            if scaling_metrics:
                # Count scaling actions (simplified)
                summary['auto_scaling']['scaling_actions'] = 0  # Would need to track actual actions
                summary['auto_scaling']['avg_instances'] = load_aware_integration.scaling_service.current_instances
            
            return safe_jsonify(summary)
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {str(e)}")
            return safe_jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500)

# =============================================================================
# BLUEPRINT REGISTRATION HELPER
# =============================================================================

def register_load_aware_blueprint(app):
    """Register the load-aware processing blueprint with the Flask app."""
    try:
        if not FLASK_AVAILABLE:
            logger.warning("Flask not available, cannot register load-aware blueprint")
            return False
        
        if load_aware_bp is None:
            logger.warning("Load-aware blueprint not created, cannot register")
            return False
        
        app.register_blueprint(load_aware_bp)
        logger.info("Load-aware processing API blueprint registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error registering load-aware blueprint: {str(e)}")
        return False
