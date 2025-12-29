"""
Phase 2 Status and Testing Utilities
Provides status endpoints and testing utilities for Phase 2 Load-Aware Processing System.
"""
import logging
from datetime import datetime
from typing import Dict, Any

try:
    from flask import Blueprint, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Blueprint = jsonify = request = None

logger = logging.getLogger(__name__)

# =============================================================================
# STATUS BLUEPRINT
# =============================================================================

if FLASK_AVAILABLE:
    phase2_status_bp = Blueprint('phase2_status', __name__, url_prefix='/api/v1/phase2')
else:
    phase2_status_bp = None

# =============================================================================
# STATUS ENDPOINTS
# =============================================================================

if FLASK_AVAILABLE:
    @phase2_status_bp.route('/status', methods=['GET'])
    def get_phase2_status():
        """Get comprehensive Phase 2 system status."""
        try:
            from app.phase2_integration import get_phase2_status
            from flask import current_app
            
            status = get_phase2_status(current_app)
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting Phase 2 status: {str(e)}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500

    @phase2_status_bp.route('/health', methods=['GET'])
    def get_phase2_health():
        """Get Phase 2 system health check."""
        try:
            from app.phase2_integration import phase2_health_check
            from flask import current_app
            
            health = phase2_health_check(current_app)
            status_code = 200 if health['overall_health'] in ['healthy', 'partial'] else 500
            return jsonify(health), status_code
            
        except Exception as e:
            logger.error(f"Error getting Phase 2 health: {str(e)}")
            return jsonify({
                'overall_health': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500

    @phase2_status_bp.route('/test-integration', methods=['POST'])
    def test_phase2_integration():
        """Test Phase 2 integration and functionality."""
        try:
            from flask import current_app
            
            test_results = {
                'timestamp': datetime.utcnow().isoformat(),
                'tests': [],
                'overall_result': 'unknown',
                'summary': {}
            }
            
            passed_tests = 0
            total_tests = 0
            
            # Test 1: Check service initialization
            total_tests += 1
            if hasattr(current_app, 'dynamic_load_manager'):
                test_results['tests'].append({
                    'name': 'Dynamic Load Manager Initialization',
                    'result': 'PASS',
                    'details': 'Service initialized and available'
                })
                passed_tests += 1
            else:
                test_results['tests'].append({
                    'name': 'Dynamic Load Manager Initialization',
                    'result': 'FAIL',
                    'details': 'Service not initialized'
                })
            
            # Test 2: Check auto-scaling service
            total_tests += 1
            if hasattr(current_app, 'auto_scaling_service'):
                test_results['tests'].append({
                    'name': 'Auto-Scaling Service Initialization',
                    'result': 'PASS',
                    'details': 'Service initialized and available'
                })
                passed_tests += 1
            else:
                test_results['tests'].append({
                    'name': 'Auto-Scaling Service Initialization',
                    'result': 'FAIL',
                    'details': 'Service not initialized'
                })
            
            # Test 3: Check integration service
            total_tests += 1
            if hasattr(current_app, 'load_aware_integration'):
                test_results['tests'].append({
                    'name': 'Load-Aware Integration Service',
                    'result': 'PASS',
                    'details': 'Service initialized and available'
                })
                passed_tests += 1
            else:
                test_results['tests'].append({
                    'name': 'Load-Aware Integration Service',
                    'result': 'FAIL',
                    'details': 'Service not initialized'
                })
            
            # Test 4: Check Phase 1 connections
            total_tests += 1
            phase1_connections = 0
            if hasattr(current_app, 'performance_monitor'):
                phase1_connections += 1
            if hasattr(current_app, 'enhanced_cache'):
                phase1_connections += 1
            
            if phase1_connections >= 1:
                test_results['tests'].append({
                    'name': 'Phase 1 Service Connections',
                    'result': 'PASS',
                    'details': f'Connected to {phase1_connections} Phase 1 services'
                })
                passed_tests += 1
            else:
                test_results['tests'].append({
                    'name': 'Phase 1 Service Connections',
                    'result': 'FAIL',
                    'details': 'No Phase 1 services connected'
                })
            
            # Test 5: Check configuration
            total_tests += 1
            if current_app.config.get('LOAD_AWARE_PROCESSING', False):
                test_results['tests'].append({
                    'name': 'Load-Aware Processing Configuration',
                    'result': 'PASS',
                    'details': 'Configuration enabled'
                })
                passed_tests += 1
            else:
                test_results['tests'].append({
                    'name': 'Load-Aware Processing Configuration',
                    'result': 'FAIL',
                    'details': 'Configuration not enabled'
                })
            
            # Test 6: Test API endpoints
            total_tests += 1
            try:
                from app.api.load_aware_routes import load_aware_bp
                if load_aware_bp is not None:
                    test_results['tests'].append({
                        'name': 'Load-Aware API Endpoints',
                        'result': 'PASS',
                        'details': 'API blueprint registered'
                    })
                    passed_tests += 1
                else:
                    test_results['tests'].append({
                        'name': 'Load-Aware API Endpoints',
                        'result': 'FAIL',
                        'details': 'API blueprint not available'
                    })
            except Exception as e:
                test_results['tests'].append({
                    'name': 'Load-Aware API Endpoints',
                    'result': 'FAIL',
                    'details': f'Error checking API: {str(e)}'
                })
            
            # Test 7: Test functional operations
            total_tests += 1
            if hasattr(current_app, 'dynamic_load_manager'):
                try:
                    load_status = current_app.dynamic_load_manager.get_current_load_status()
                    if load_status and 'current_metrics' in load_status:
                        test_results['tests'].append({
                            'name': 'Load Manager Functionality',
                            'result': 'PASS',
                            'details': 'Load metrics collected successfully'
                        })
                        passed_tests += 1
                    else:
                        test_results['tests'].append({
                            'name': 'Load Manager Functionality',
                            'result': 'FAIL',
                            'details': 'Load metrics collection failed'
                        })
                except Exception as e:
                    test_results['tests'].append({
                        'name': 'Load Manager Functionality',
                        'result': 'FAIL',
                        'details': f'Error testing functionality: {str(e)}'
                    })
            else:
                test_results['tests'].append({
                    'name': 'Load Manager Functionality',
                    'result': 'SKIP',
                    'details': 'Service not available'
                })
            
            # Calculate results
            test_results['summary'] = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0
            }
            
            if passed_tests == total_tests:
                test_results['overall_result'] = 'ALL_PASS'
            elif passed_tests >= total_tests * 0.7:
                test_results['overall_result'] = 'MOSTLY_PASS'
            elif passed_tests > 0:
                test_results['overall_result'] = 'PARTIAL_PASS'
            else:
                test_results['overall_result'] = 'ALL_FAIL'
            
            status_code = 200 if test_results['overall_result'] in ['ALL_PASS', 'MOSTLY_PASS'] else 500
            return jsonify(test_results), status_code
            
        except Exception as e:
            logger.error(f"Error testing Phase 2 integration: {str(e)}")
            return jsonify({
                'overall_result': 'ERROR',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500

    @phase2_status_bp.route('/metrics-summary', methods=['GET'])
    def get_metrics_summary():
        """Get summary of current Phase 2 metrics."""
        try:
            from flask import current_app
            
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'load_management': {},
                'auto_scaling': {},
                'integration': {},
                'system_health': 'unknown'
            }
            
            # Get load management metrics
            if hasattr(current_app, 'dynamic_load_manager'):
                try:
                    load_status = current_app.dynamic_load_manager.get_current_load_status()
                    summary['load_management'] = {
                        'current_load_level': load_status.get('current_metrics', {}).get('load_classification', 'unknown'),
                        'cpu_usage': load_status.get('current_metrics', {}).get('cpu_usage', 0),
                        'memory_usage': load_status.get('current_metrics', {}).get('memory_usage', 0),
                        'queue_length': load_status.get('current_metrics', {}).get('queue_length', 0),
                        'strategy': load_status.get('current_strategy', {}).get('name', 'unknown')
                    }
                except Exception as e:
                    summary['load_management']['error'] = str(e)
            
            # Get auto-scaling metrics
            if hasattr(current_app, 'auto_scaling_service'):
                try:
                    scaling_status = current_app.auto_scaling_service.get_scaling_status()
                    summary['auto_scaling'] = {
                        'current_instances': scaling_status.get('current_instances', 0),
                        'scaling_enabled': scaling_status.get('scaling_enabled', False),
                        'environment': scaling_status.get('current_environment', 'unknown'),
                        'instance_limits': scaling_status.get('instance_limits', {})
                    }
                except Exception as e:
                    summary['auto_scaling']['error'] = str(e)
            
            # Get integration metrics
            if hasattr(current_app, 'load_aware_integration'):
                try:
                    integration_status = current_app.load_aware_integration.get_integration_status()
                    summary['integration'] = {
                        'coordination_active': integration_status.get('integration_active', False),
                        'system_health_status': integration_status.get('system_health_status', 'unknown'),
                        'coordination_history_count': integration_status.get('coordination_history_count', 0)
                    }
                    summary['system_health'] = integration_status.get('system_health_status', 'unknown')
                except Exception as e:
                    summary['integration']['error'] = str(e)
            
            return jsonify(summary)
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {str(e)}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500

    @phase2_status_bp.route('/restart-coordination', methods=['POST'])
    def restart_coordination():
        """Restart load-aware processing coordination."""
        try:
            from flask import current_app
            
            if not hasattr(current_app, 'load_aware_integration'):
                return jsonify({
                    'success': False,
                    'error': 'Load-aware integration service not available'
                }), 400
            
            # Stop and restart coordination
            current_app.load_aware_integration.stop_coordination()
            current_app.load_aware_integration.start_coordination()
            
            return jsonify({
                'success': True,
                'message': 'Load-aware processing coordination restarted',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error restarting coordination: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

# =============================================================================
# BLUEPRINT REGISTRATION HELPER
# =============================================================================

def register_phase2_status_blueprint(app):
    """Register the Phase 2 status blueprint with the Flask app."""
    try:
        if not FLASK_AVAILABLE:
            logger.warning("Flask not available, cannot register Phase 2 status blueprint")
            return False
        
        if phase2_status_bp is None:
            logger.warning("Phase 2 status blueprint not created, cannot register")
            return False
        
        app.register_blueprint(phase2_status_bp)
        logger.info("Phase 2 status API blueprint registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error registering Phase 2 status blueprint: {str(e)}")
        return False
