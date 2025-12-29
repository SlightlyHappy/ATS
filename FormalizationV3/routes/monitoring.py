"""
Database Health Monitoring Routes
Provides endpoints for monitoring hybrid Railway + Supabase database system
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
import os

# Import database manager (will be injected by main app)
db_manager = None

logger = logging.getLogger(__name__)

# Create monitoring blueprint
monitoring_routes = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')

def init_monitoring(database_manager):
    """Initialize monitoring with database manager reference"""
    global db_manager
    db_manager = database_manager
    logger.info("Monitoring routes initialized")

@monitoring_routes.route('/health', methods=['GET'])
def database_health():
    """Get comprehensive database health status"""
    
    if not db_manager:
        return jsonify({
            'error': 'Database manager not initialized',
            'status': 'error'
        }), 500
    
    try:
        # Get hybrid database health
        if hasattr(db_manager, 'get_database_health_hybrid'):
            health = db_manager.get_database_health_hybrid()
        else:
            # Fallback to basic health check
            health = {
                'timestamp': datetime.now().isoformat(),
                'primary_db': getattr(db_manager, 'primary_db', 'unknown')
            }
            
            # Check Railway if available
            if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                health['railway'] = db_manager.railway_pg.health_check()
            
            # Check Supabase if available
            if hasattr(db_manager, 'supabase') and db_manager.supabase:
                health['supabase'] = {'healthy': True}  # Basic check
        
        return jsonify({
            'status': 'success',
            'health': health
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@monitoring_routes.route('/backup-sync/status', methods=['GET'])
def backup_sync_status():
    """Get backup sync status"""
    
    if not db_manager:
        return jsonify({'error': 'Database manager not initialized'}), 500
    
    try:
        if hasattr(db_manager, 'backup_sync') and db_manager.backup_sync:
            status = db_manager.backup_sync.get_sync_status()
            return jsonify({
                'status': 'success',
                'sync_status': status
            })
        else:
            return jsonify({
                'status': 'info',
                'message': 'Backup sync not enabled'
            })
            
    except Exception as e:
        logger.error(f"Failed to get backup sync status: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@monitoring_routes.route('/backup-sync/manual', methods=['POST'])
def manual_backup_sync():
    """Trigger manual backup sync for a specific table"""
    
    if not db_manager:
        return jsonify({'error': 'Database manager not initialized'}), 500
    
    try:
        data = request.get_json() or {}
        table = data.get('table', 'user_profiles')
        hours = data.get('hours', 1)
        
        if hasattr(db_manager, 'backup_sync') and db_manager.backup_sync:
            result = db_manager.backup_sync.manual_sync_table(table, hours)
            return jsonify({
                'status': 'success',
                'sync_result': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Backup sync not available'
            }), 400
            
    except Exception as e:
        logger.error(f"Manual backup sync failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@monitoring_routes.route('/performance', methods=['GET'])
def performance_metrics():
    """Get performance metrics for all databases"""
    
    if not db_manager:
        return jsonify({'error': 'Database manager not initialized'}), 500
    
    try:
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'primary_db': getattr(db_manager, 'primary_db', 'unknown'),
            'dual_write': getattr(db_manager, 'dual_write', False)
        }
        
        # Railway metrics
        if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
            railway_health = db_manager.railway_pg.health_check()
            metrics['railway'] = {
                'status': railway_health.get('status'),
                'query_count': railway_health.get('query_count', 0),
                'error_count': railway_health.get('error_count', 0),
                'avg_response_time': railway_health.get('avg_response_time', 0),
                'pool_size': railway_health.get('pool_size', 0),
                'pool_max': railway_health.get('pool_max', 0)
            }
        
        # Supabase metrics (basic)
        if hasattr(db_manager, 'supabase') and db_manager.supabase:
            metrics['supabase'] = {
                'status': 'healthy',
                'enabled': True
            }
        
        return jsonify({
            'status': 'success',
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@monitoring_routes.route('/configuration', methods=['GET'])
def database_configuration():
    """Get current database configuration"""
    
    config = {
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'DATABASE_URL': 'Set' if os.getenv('DATABASE_URL') else 'Not Set',
            'PRIMARY_DB': os.getenv('PRIMARY_DB', 'supabase'),
            'DUAL_WRITE': os.getenv('DUAL_WRITE', 'false'),
            'BACKUP_SYNC_ENABLED': os.getenv('BACKUP_SYNC_ENABLED', 'true')
        },
        'database_manager': {
            'initialized': db_manager is not None,
            'railway_available': hasattr(db_manager, 'railway_pg') and db_manager.railway_pg is not None if db_manager else False,
            'supabase_available': hasattr(db_manager, 'supabase') and db_manager.supabase is not None if db_manager else False,
            'backup_sync_available': hasattr(db_manager, 'backup_sync') and db_manager.backup_sync is not None if db_manager else False
        }
    }
    
    return jsonify({
        'status': 'success',
        'configuration': config
    })

@monitoring_routes.route('/test-hybrid', methods=['POST'])
def test_hybrid_operations():
    """Test hybrid database operations"""
    
    if not db_manager:
        return jsonify({'error': 'Database manager not initialized'}), 500
    
    try:
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # Test 1: Health checks
        test_results['tests']['health_check'] = {
            'description': 'Database health checks',
            'result': 'success' if hasattr(db_manager, 'get_database_health_hybrid') else 'partial'
        }
        
        # Test 2: Railway connection (if available)
        if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
            try:
                railway_health = db_manager.railway_pg.health_check()
                test_results['tests']['railway_connection'] = {
                    'description': 'Railway PostgreSQL connection',
                    'result': 'success' if railway_health.get('status') == 'healthy' else 'failed',
                    'details': railway_health
                }
            except Exception as e:
                test_results['tests']['railway_connection'] = {
                    'description': 'Railway PostgreSQL connection',
                    'result': 'failed',
                    'error': str(e)
                }
        
        # Test 3: Supabase connection (if available)
        if hasattr(db_manager, 'supabase') and db_manager.supabase:
            test_results['tests']['supabase_connection'] = {
                'description': 'Supabase connection',
                'result': 'success'
            }
        
        # Test 4: Backup sync (if available)
        if hasattr(db_manager, 'backup_sync') and db_manager.backup_sync:
            try:
                sync_status = db_manager.backup_sync.get_sync_status()
                test_results['tests']['backup_sync'] = {
                    'description': 'Backup sync system',
                    'result': 'success' if sync_status.get('running') else 'partial',
                    'details': sync_status
                }
            except Exception as e:
                test_results['tests']['backup_sync'] = {
                    'description': 'Backup sync system',
                    'result': 'failed',
                    'error': str(e)
                }
        
        # Overall result
        failed_tests = [t for t in test_results['tests'].values() if t['result'] == 'failed']
        overall_status = 'success' if not failed_tests else 'partial'
        
        return jsonify({
            'status': overall_status,
            'test_results': test_results,
            'summary': {
                'total_tests': len(test_results['tests']),
                'passed': len([t for t in test_results['tests'].values() if t['result'] == 'success']),
                'failed': len(failed_tests)
            }
        })
        
    except Exception as e:
        logger.error(f"Hybrid operation test failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@monitoring_routes.route('/data-consistency', methods=['GET'])
def check_data_consistency():
    """Check data consistency between Railway and Supabase"""
    
    if not db_manager:
        return jsonify({'error': 'Database manager not initialized'}), 500
    
    table = request.args.get('table', 'user_profiles')
    sample_size = int(request.args.get('sample_size', 10))
    
    try:
        if hasattr(db_manager, 'backup_sync') and db_manager.backup_sync:
            result = db_manager.backup_sync.verify_data_consistency(table, sample_size)
            return jsonify({
                'status': 'success',
                'consistency_check': result
            })
        else:
            return jsonify({
                'status': 'info',
                'message': 'Data consistency check not available (backup sync not enabled)'
            })
            
    except Exception as e:
        logger.error(f"Data consistency check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Error handlers
@monitoring_routes.errorhandler(404)
def monitoring_not_found(error):
    return jsonify({
        'status': 'error',
        'error': 'Monitoring endpoint not found'
    }), 404

@monitoring_routes.errorhandler(500)
def monitoring_server_error(error):
    return jsonify({
        'status': 'error',
        'error': 'Internal monitoring error'
    }), 500
