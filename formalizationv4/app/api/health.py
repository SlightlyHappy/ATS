from flask import jsonify, current_app
import asyncio
import threading
from datetime import datetime, timedelta
from app.api import api_bp
from app.services.ollama_service import OllamaService
from app import db
import logging
import os

logger = logging.getLogger(__name__)

def run_async_in_thread(coro):
    """Run async function in a new thread with its own event loop."""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    # Run in thread to avoid event loop conflicts
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result(timeout=current_app.config.get('HEALTH_CHECK_TIMEOUT', 10))

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint."""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Check database connectivity
        try:
            db.session.execute(db.text('SELECT 1'))
            health_status['services']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['services']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        # Check Ollama service (skip if SIMPLE_HEALTH_ONLY is enabled)
        if not current_app.config.get('SIMPLE_HEALTH_ONLY', False):
            try:
                async def check_ollama():
                    async with OllamaService() as ollama:
                        is_healthy = await ollama.check_health()
                        if is_healthy:
                            models = await ollama.list_models()
                            return {
                                'status': 'healthy',
                                'message': 'Ollama service accessible',
                                'available_models': models
                            }
                        else:
                            return {
                                'status': 'unhealthy',
                                'message': 'Ollama service not responding'
                            }
                
                ollama_result = run_async_in_thread(check_ollama())
                health_status['services']['ollama'] = ollama_result
                
                if ollama_result['status'] != 'healthy':
                    health_status['status'] = 'degraded'
                    
            except Exception as e:
                health_status['services']['ollama'] = {
                    'status': 'unhealthy',
                    'message': f'Ollama service check failed: {str(e)}'
                }
                health_status['status'] = 'degraded'
        else:
            health_status['services']['ollama'] = {
                'status': 'skipped',
                'message': 'Simple health check mode - Ollama check skipped'
            }
        
        # Check upload directory
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if os.path.exists(upload_folder) and os.access(upload_folder, os.W_OK):
                health_status['services']['file_storage'] = {
                    'status': 'healthy',
                    'message': 'Upload directory accessible',
                    'path': upload_folder
                }
            else:
                health_status['services']['file_storage'] = {
                    'status': 'unhealthy',
                    'message': 'Upload directory not accessible'
                }
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['services']['file_storage'] = {
                'status': 'unhealthy',
                'message': f'File storage check failed: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        # Check HR Templates system
        try:
            from app.services.hr_templates_autofix import HRTemplatesAutoFixService
            from app.models.communication import HRTemplate
            
            # Check for issues
            issues = HRTemplatesAutoFixService.detect_issues()
            has_issues = any(issues.values())
            
            # Count system templates
            try:
                system_template_count = HRTemplate.query.filter_by(is_system_template=True).count()
            except Exception:
                system_template_count = 0
            
            if has_issues:
                health_status['services']['hr_templates'] = {
                    'status': 'degraded',
                    'message': 'HR templates have configuration issues',
                    'issues': issues,
                    'system_templates': system_template_count,
                    'auto_fix_available': True
                }
                health_status['status'] = 'degraded'
            else:
                health_status['services']['hr_templates'] = {
                    'status': 'healthy',
                    'message': 'HR templates system operational',
                    'system_templates': system_template_count
                }
        except Exception as e:
            health_status['services']['hr_templates'] = {
                'status': 'unhealthy',
                'message': f'HR templates check failed: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        # Overall status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'message': f'Health check failed: {str(e)}'
        }), 503

@api_bp.route('/health/simple', methods=['GET'])
def simple_health_check():
    """Simple health check endpoint for Railway - just checks basic app availability."""
    try:
        # Only check database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Service is running and database is accessible'
        }), 200
    except Exception as e:
        logger.error(f"Simple health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@api_bp.route('/health/database', methods=['GET'])
def database_health():
    """Database-specific health check."""
    try:
        # Test database connection and get some stats
        db.session.execute(db.text('SELECT 1'))
        
        # Get table counts
        from app.models import Resume, Analysis, User
        
        stats = {
            'status': 'healthy',
            'connection': 'successful',
            'statistics': {
                'total_resumes': Resume.query.count(),
                'total_analyses': Analysis.query.count(),
                'total_users': User.query.count(),
                'completed_analyses': Analysis.query.filter_by(status='completed').count(),
                'pending_analyses': Analysis.query.filter_by(status='pending').count()
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@api_bp.route('/health/ollama', methods=['GET'])
def ollama_health():
    """Ollama service health check."""
    try:
        async def check_ollama_detailed():
            async with OllamaService() as ollama:
                # Check if service is responding
                is_healthy = await ollama.check_health()
                
                if not is_healthy:
                    return {
                        'status': 'unhealthy',
                        'message': 'Ollama service not responding'
                    }
                
                # Get available models
                models = await ollama.list_models()
                
                # Test a simple generation
                test_response = await ollama.generate(
                    prompt="Hello, this is a test.",
                    max_tokens=10
                )
                
                return {
                    'status': 'healthy',
                    'service_url': ollama.base_url,
                    'available_models': models,
                    'configured_model': ollama.model,
                    'test_generation': {
                        'prompt': "Hello, this is a test.",
                        'response': test_response[:50] + "..." if len(test_response) > 50 else test_response
                    }
                }
        
        result = run_async_in_thread(check_ollama_detailed())
        status_code = 200 if result['status'] == 'healthy' else 503
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Ollama health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@api_bp.route('/health/agents', methods=['GET'])
def agents_health():
    """Test agent functionality."""
    try:
        # Sample resume text for testing
        test_resume = """
        John Doe
        Software Engineer
        
        Experience:
        - Senior Developer at Tech Corp (2020-2023)
        - Built web applications using Python and React
        
        Education:
        - BS Computer Science, University of Technology (2018)
        
        Skills:
        - Python, JavaScript, React, PostgreSQL
        - AWS, Docker, Git
        """
        
        async def test_agents():
            from app.agents import TechnicalSkillsAgent, ExperienceAgent, EducationAgent, SoftSkillsAgent
            
            agent_results = {}
            
            async with OllamaService() as ollama:
                # Test each agent
                agents = {
                    'technical_skills': TechnicalSkillsAgent(ollama),
                    'experience': ExperienceAgent(ollama),
                    'education': EducationAgent(ollama),
                    'soft_skills': SoftSkillsAgent(ollama)
                }
                
                for agent_name, agent in agents.items():
                    try:
                        # Test with short timeout
                        result = await asyncio.wait_for(
                            agent.analyze(test_resume),
                            timeout=30
                        )
                        
                        agent_results[agent_name] = {
                            'status': 'healthy',
                            'score': result.score,
                            'confidence': result.confidence,
                            'processing_time': result.processing_time
                        }
                        
                    except asyncio.TimeoutError:
                        agent_results[agent_name] = {
                            'status': 'timeout',
                            'message': 'Agent test timed out'
                        }
                    except Exception as e:
                        agent_results[agent_name] = {
                            'status': 'error',
                            'message': str(e)
                        }
            
            return agent_results
        
        agent_results = run_async_in_thread(test_agents())
        
        # Determine overall agent health
        healthy_agents = sum(1 for result in agent_results.values() if result.get('status') == 'healthy')
        total_agents = len(agent_results)
        
        overall_status = 'healthy' if healthy_agents == total_agents else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'healthy_agents': healthy_agents,
            'total_agents': total_agents,
            'agent_results': agent_results
        }), 200 if overall_status == 'healthy' else 503
        
    except Exception as e:
        logger.error(f"Agent health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@api_bp.route('/health/system', methods=['GET'])
def system_health():
    """Comprehensive system health check for production monitoring."""
    try:
        import psutil
        import platform
        
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get database pool info
        from app import db
        pool_info = {
            'pool_size': db.engine.pool.size(),
            'checked_in': db.engine.pool.checkedin(),
            'checked_out': db.engine.pool.checkedout(),
            'overflow': db.engine.pool.overflow(),
            'invalid': db.engine.pool.invalid()
        }
        
        # Get queue statistics
        from app.models.queue import AnalysisQueue, QueueStatus
        queue_stats = {
            'total_queued': AnalysisQueue.query.count(),
            'pending': AnalysisQueue.query.filter_by(status=QueueStatus.PENDING).count(),
            'processing': AnalysisQueue.query.filter_by(status=QueueStatus.PROCESSING).count(),
            'completed': AnalysisQueue.query.filter_by(status=QueueStatus.COMPLETED).count(),
            'failed': AnalysisQueue.query.filter_by(status=QueueStatus.FAILED).count()
        }
        
        # Get WebSocket connection stats
        from app.services.websocket_service import websocket_service
        ws_stats = websocket_service.get_connection_stats() if websocket_service else {
            'total_connections': 0,
            'current_connections': 0
        }
        
        # Determine overall health
        health_score = 100
        warnings = []
        
        if cpu_percent > 80:
            health_score -= 20
            warnings.append(f"High CPU usage: {cpu_percent}%")
        
        if memory.percent > 85:
            health_score -= 20
            warnings.append(f"High memory usage: {memory.percent}%")
        
        if disk.percent > 90:
            health_score -= 30
            warnings.append(f"High disk usage: {disk.percent}%")
        
        if queue_stats['failed'] > 10:
            health_score -= 15
            warnings.append(f"High queue failure rate: {queue_stats['failed']} failed jobs")
        
        system_info = {
            'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 60 else 'unhealthy',
            'health_score': health_score,
            'warnings': warnings,
            'system': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                }
            },
            'database': {
                'pool': pool_info,
                'connection_healthy': True
            },
            'queue': queue_stats,
            'websocket': ws_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        status_code = 200 if health_score >= 80 else 503
        return jsonify(system_info), status_code
        
    except ImportError:
        return jsonify({
            'status': 'limited',
            'message': 'psutil not available - limited system monitoring',
            'basic_health': 'operational'
        }), 200
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@api_bp.route('/health/performance', methods=['GET'])
def performance_metrics():
    """Performance metrics endpoint for monitoring."""
    try:
        # Get recent performance data
        from app.models.analysis import Analysis
        from sqlalchemy import func
        
        # Query performance statistics
        recent_analyses = Analysis.query.filter(
            Analysis.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        if recent_analyses:
            processing_times = [a.processing_time for a in recent_analyses if a.processing_time]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            success_rate = len([a for a in recent_analyses if a.status == 'completed']) / len(recent_analyses) * 100
        else:
            avg_processing_time = 0
            success_rate = 100
        
        metrics = {
            'status': 'healthy',
            'performance': {
                'avg_processing_time_seconds': round(avg_processing_time, 2),
                'success_rate_percent': round(success_rate, 2),
                'analyses_last_24h': len(recent_analyses),
                'queue_efficiency': 'high' if success_rate > 95 else 'medium' if success_rate > 85 else 'low'
            },
            'benchmarks': {
                'target_processing_time': 60,
                'target_success_rate': 95,
                'max_queue_size': 100
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Performance metrics check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503
