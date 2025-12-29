"""
Smart Resource Scaling API endpoints for monitoring and control.
Provides comprehensive monitoring dashboard and system control endpoints.
"""
import logging
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

# Create blueprint
scaling_api = Blueprint('scaling_api', __name__, url_prefix='/api/v1/scaling')

@scaling_api.route('/status', methods=['GET'])
@login_required
def get_scaling_status():
    """Get comprehensive Smart Resource Scaling system status."""
    try:
        # Check if user has admin privileges
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_info': {
                'scaling_enabled': os.getenv('ENABLE_SMART_SCALING', 'true').lower() == 'true',
                'environment': os.getenv('ENVIRONMENT', 'development'),
                'railway_environment': bool(os.getenv('RAILWAY_ENVIRONMENT')),
                'max_workers': int(os.getenv('MAX_WORKERS', '8')),
                'min_workers': int(os.getenv('MIN_WORKERS', '2'))
            },
            'components': {}
        }
        
        # Try to get Smart Resource Scaler status
        try:
            from app.services.smart_resource_scaler import smart_resource_scaler
            status['components']['smart_resource_scaler'] = smart_resource_scaler.get_scaling_status()
        except ImportError:
            status['components']['smart_resource_scaler'] = {'status': 'not_available'}
        except Exception as e:
            status['components']['smart_resource_scaler'] = {'status': 'error', 'error': str(e)}
        
        # Try to get Enhanced Queue Service status
        try:
            from app.services.queue_service import QueueService
            queue_service = QueueService()
            if hasattr(queue_service, 'get_enhanced_status'):
                status['components']['queue_service'] = queue_service.get_enhanced_status()
            else:
                # Basic queue status
                from app.models.queue import AnalysisQueue, QueueStatus
                status['components']['queue_service'] = {
                    'pending': AnalysisQueue.query.filter_by(status=QueueStatus.PENDING.value).count(),
                    'processing': AnalysisQueue.query.filter_by(status=QueueStatus.PROCESSING.value).count(),
                    'completed': AnalysisQueue.query.filter_by(status=QueueStatus.COMPLETED.value).count(),
                    'failed': AnalysisQueue.query.filter_by(status=QueueStatus.FAILED.value).count(),
                }
        except Exception as e:
            status['components']['queue_service'] = {'status': 'error', 'error': str(e)}
        
        # Try to get system metrics
        try:
            import psutil
            status['system_metrics'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'active_processes': len(psutil.pids()),
                'network_connections': len(psutil.net_connections())
            }
        except ImportError:
            status['system_metrics'] = {'error': 'psutil not available'}
        except Exception as e:
            status['system_metrics'] = {'error': str(e)}
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting scaling status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@scaling_api.route('/metrics', methods=['GET'])
@login_required
def get_performance_metrics():
    """Get detailed performance metrics."""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'performance': {},
            'queue_analytics': {},
            'resource_usage': {}
        }
        
        # Get enhanced queue metrics
        try:
            from app.services.queue_service import QueueService
            queue_service = QueueService()
            if hasattr(queue_service, 'get_enhanced_status'):
                queue_status = queue_service.get_enhanced_status()
                metrics['performance'] = queue_status.get('performance_metrics', {})
        except Exception:
            pass
        
        # Get queue analytics
        try:
            from app.services.queue_service import QueueService
            queue_service = QueueService()
            if hasattr(queue_service, 'get_enhanced_status'):
                queue_status = queue_service.get_enhanced_status()
                metrics['queue_analytics'] = queue_status.get('performance_metrics', {})
        except Exception:
            pass
        
        # Get resource usage
        try:
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            metrics['resource_usage'] = {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg': list(load_avg)
                },
                'memory': {
                    'total_gb': round(memory.total / 1024**3, 2),
                    'available_gb': round(memory.available / 1024**3, 2),
                    'percent': memory.percent,
                    'swap_percent': swap.percent
                },
                'disk': {
                    'total_gb': round(disk.total / 1024**3, 2),
                    'free_gb': round(disk.free / 1024**3, 2),
                    'percent': round((disk.used / disk.total) * 100, 2),
                    'read_mb': round(disk_io.read_bytes / 1024**2, 2) if disk_io else 0,
                    'write_mb': round(disk_io.write_bytes / 1024**2, 2) if disk_io else 0
                },
                'network': {
                    'bytes_sent_mb': round(network_io.bytes_sent / 1024**2, 2) if network_io else 0,
                    'bytes_recv_mb': round(network_io.bytes_recv / 1024**2, 2) if network_io else 0
                }
            }
            
        except ImportError:
            metrics['resource_usage'] = {'error': 'psutil not available'}
        except Exception as e:
            metrics['resource_usage'] = {'error': str(e)}
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@scaling_api.route('/logs', methods=['GET'])
@login_required
def get_deployment_logs():
    """Get recent deployment and scaling logs."""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        lines = int(request.args.get('lines', 100))
        log_type = request.args.get('type', 'all')  # all, worker, scaling, deployment
        
        logs = {
            'timestamp': datetime.utcnow().isoformat(),
            'logs': [],
            'log_files_checked': []
        }
        
        # Log files to check
        log_files = []
        
        if log_type in ['all', 'worker']:
            log_files.extend(['enhanced_worker.log', 'queue_worker.log'])
        
        if log_type in ['all', 'scaling']:
            log_files.extend(['smart_scaling_system.log'])
        
        if log_type in ['all', 'deployment']:
            log_files.extend(['deployment.log'])
        
        # Default fallback logs
        if not log_files:
            log_files = ['enhanced_worker.log', 'queue_worker.log']
        
        # Read log files
        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    logs['log_files_checked'].append(log_file)
                    with open(log_file, 'r') as f:
                        log_lines = f.readlines()
                        # Get last N lines
                        recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
                        
                        for line in recent_lines:
                            logs['logs'].append({
                                'source': log_file,
                                'content': line.strip(),
                                'timestamp': 'extracted_from_log'
                            })
            except Exception as e:
                logs['logs'].append({
                    'source': 'system',
                    'content': f"Error reading {log_file}: {str(e)}",
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Sort logs by timestamp (best effort)
        logs['logs'] = logs['logs'][-lines:]  # Limit to requested lines
        
        return jsonify(logs)
        
    except Exception as e:
        logger.error(f"Error getting deployment logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@scaling_api.route('/control/restart', methods=['POST'])
@login_required
async def restart_scaling_system():
    """Restart the Smart Resource Scaling system."""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        result = {'timestamp': datetime.utcnow().isoformat(), 'actions': []}
        
        # Try to restart Smart Resource Scaler
        try:
            from app.services.smart_resource_scaler import smart_resource_scaler
            
            if smart_resource_scaler.running:
                await smart_resource_scaler.stop()
                result['actions'].append('Stopped Smart Resource Scaler')
            
            await smart_resource_scaler.start()
            result['actions'].append('Started Smart Resource Scaler')
            
        except ImportError:
            result['actions'].append('Smart Resource Scaler not available')
        except Exception as e:
            result['actions'].append(f'Error restarting Smart Resource Scaler: {str(e)}')
        
        result['status'] = 'completed' if result['actions'] else 'no_actions'
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error restarting scaling system: {str(e)}")
        return jsonify({'error': str(e)}), 500

@scaling_api.route('/health', methods=['GET'])
def health_check():
    """Public health check endpoint for monitoring."""
    try:
        health = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'healthy',
            'version': '1.2',
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'components': {}
        }
        
        # Check queue service
        try:
            from app.models.queue import AnalysisQueue
            pending_count = AnalysisQueue.query.filter_by(status='pending').count()
            health['components']['queue'] = {
                'status': 'healthy',
                'pending_items': pending_count
            }
        except Exception as e:
            health['components']['queue'] = {
                'status': 'error',
                'error': str(e)
            }
            health['status'] = 'degraded'
        
        # Check database
        try:
            from app import db
            db.session.execute('SELECT 1')
            health['components']['database'] = {'status': 'healthy'}
        except Exception as e:
            health['components']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health['status'] = 'unhealthy'
        
        # Return appropriate HTTP status
        if health['status'] == 'healthy':
            return jsonify(health), 200
        elif health['status'] == 'degraded':
            return jsonify(health), 200  # Still operational
        else:
            return jsonify(health), 503  # Service unavailable
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'unhealthy',
            'error': str(e)
        }), 503

def register_scaling_api(app):
    """Register the scaling API blueprint with the Flask app."""
    app.register_blueprint(scaling_api)
    logger.info("Smart Resource Scaling API endpoints registered")
