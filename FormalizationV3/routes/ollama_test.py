#!/usr/bin/env python3
"""
Ollama Test Routes for Railway Deployment
Provides endpoints to test Ollama functionality and real-time progress monitoring
"""

from flask import Blueprint, jsonify, request, render_template
import logging
import asyncio
import os
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Create blueprint
ollama_test_bp = Blueprint('ollama_test', __name__, url_prefix='/api/test')

@ollama_test_bp.route('/ollama/progress-monitor', methods=['GET'])
def ollama_progress_monitor():
    """Serve the Ollama progress monitoring page"""
    try:
        return render_template('ollama_progress_monitor.html')
    except Exception as e:
        logger.error(f"Error serving progress monitor: {e}")
        return jsonify({
            'error': 'Could not serve progress monitor',
            'details': str(e)
        }), 500

@ollama_test_bp.route('/ollama/status', methods=['GET'])
def test_ollama_status():
    """Test Ollama service status"""
    try:
        import requests
        
        # Check if Ollama service is running
        response = requests.get('http://localhost:11434/api/version', timeout=5)
        
        if response.status_code == 200:
            version_info = response.json()
            return jsonify({
                'success': True,
                'status': 'running',
                'version': version_info,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'status': 'error',
                'error': f'Service returned status {response.status_code}',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@ollama_test_bp.route('/ollama/models', methods=['GET'])
def test_ollama_models():
    """List available Ollama models"""
    try:
        # Try official client first
        try:
            import ollama
            models = ollama.list()
            model_list = []
            
            for model in models.get('models', []):
                model_list.append({
                    'name': model.get('name'),
                    'size': model.get('size'),
                    'modified_at': model.get('modified_at')
                })
            
            return jsonify({
                'success': True,
                'models': model_list,
                'count': len(model_list),
                'method': 'ollama_client',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except ImportError:
            # Fallback to HTTP API
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    'success': True,
                    'models': data.get('models', []),
                    'count': len(data.get('models', [])),
                    'method': 'http_api',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'HTTP API returned status {response.status_code}',
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@ollama_test_bp.route('/ollama/generate', methods=['POST'])
def test_ollama_generation():
    """Test Ollama text generation"""
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', 'Hello! Please respond with "Ollama is working on Railway"')
        model = data.get('model', os.getenv('OLLAMA_MODEL', 'qwen2.5:7b'))
        
        logger.info(f"Testing generation with model: {model}")
        
        # Try official client first
        try:
            import ollama
            start_time = time.time()
            
            response = ollama.generate(
                model=model,
                prompt=prompt,
                options={
                    'temperature': 0.1,
                    'num_predict': 200
                }
            )
            
            generation_time = time.time() - start_time
            
            return jsonify({
                'success': True,
                'response': response.get('response', ''),
                'model_used': model,
                'generation_time': round(generation_time, 2),
                'method': 'ollama_client',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except ImportError:
            # Fallback to HTTP API
            import requests
            import json
            
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,
                    'num_predict': 200
                }
            }
            
            start_time = time.time()
            response = requests.post(
                'http://localhost:11434/api/generate',
                json=payload,
                timeout=60
            )
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    'success': True,
                    'response': result.get('response', ''),
                    'model_used': model,
                    'generation_time': round(generation_time, 2),
                    'method': 'http_api',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Generation failed with status {response.status_code}',
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@ollama_test_bp.route('/ai-processor', methods=['GET'])
def test_ai_processor():
    """Test the unified AI processor"""
    try:
        from utils.unified_ai_processor import UnifiedAIProcessor, AIProvider
        
        # Create processor
        processor = UnifiedAIProcessor()
        
        # Get available providers
        providers = processor.get_available_providers()
        
        # Check Ollama specifically
        ollama_status = {
            'available': AIProvider.OLLAMA in processor.providers,
            'healthy': False,
            'model': None
        }
        
        if AIProvider.OLLAMA in processor.providers:
            ollama_status['healthy'] = processor._check_provider_health(AIProvider.OLLAMA)
            ollama_status['model'] = processor.providers[AIProvider.OLLAMA].model
        
        return jsonify({
            'success': True,
            'providers': providers,
            'ollama_status': ollama_status,
            'total_providers': len(processor.providers),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@ollama_test_bp.route('/full-test', methods=['GET'])
def run_full_test():
    """Run comprehensive Ollama test suite"""
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'tests': {}
    }
    
    # Test 1: Service Status
    try:
        import requests
        response = requests.get('http://localhost:11434/api/version', timeout=5)
        results['tests']['service_status'] = {
            'passed': response.status_code == 200,
            'details': response.json() if response.status_code == 200 else f"Status: {response.status_code}"
        }
    except Exception as e:
        results['tests']['service_status'] = {
            'passed': False,
            'details': str(e)
        }
    
    # Test 2: Client Import
    try:
        import ollama
        results['tests']['client_import'] = {
            'passed': True,
            'details': "Ollama client imported successfully"
        }
    except ImportError:
        results['tests']['client_import'] = {
            'passed': False,
            'details': "Ollama client not available"
        }
    
    # Test 3: Model Availability
    try:
        import ollama
        models = ollama.list()
        model_names = [m.get('name', '') for m in models.get('models', [])]
        qwen_models = [name for name in model_names if 'qwen' in name.lower()]
        
        results['tests']['models'] = {
            'passed': len(qwen_models) > 0,
            'details': {
                'total_models': len(model_names),
                'qwen_models': qwen_models,
                'all_models': model_names
            }
        }
    except Exception as e:
        results['tests']['models'] = {
            'passed': False,
            'details': str(e)
        }
    
    # Test 4: AI Processor
    try:
        from utils.unified_ai_processor import UnifiedAIProcessor, AIProvider
        processor = UnifiedAIProcessor()
        
        results['tests']['ai_processor'] = {
            'passed': AIProvider.OLLAMA in processor.providers,
            'details': {
                'ollama_available': AIProvider.OLLAMA in processor.providers,
                'total_providers': len(processor.providers),
                'provider_list': [p.value for p in processor.providers.keys()]
            }
        }
    except Exception as e:
        results['tests']['ai_processor'] = {
            'passed': False,
            'details': str(e)
        }
    
    # Calculate overall success
    passed_tests = sum(1 for test in results['tests'].values() if test['passed'])
    total_tests = len(results['tests'])
    
    results['summary'] = {
        'passed': passed_tests,
        'total': total_tests,
        'success_rate': round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
        'overall_status': 'PASS' if passed_tests == total_tests else 'PARTIAL' if passed_tests > 0 else 'FAIL'
    }
    
    return jsonify(results)

@ollama_test_bp.route('/admin-analysis/<resume_id>', methods=['POST'])
def test_admin_analysis(resume_id):
    """Test admin analysis endpoint with the specific resume that was failing"""
    try:
        # This endpoint tests the admin analysis function directly
        from routes.admin import admin_unlimited_resume_analysis
        from flask import request as flask_request
        
        # Create mock request data
        test_data = {
            'job_requirements': {
                'title': 'Test Position',
                'required_skills': ['Python', 'Data Analysis'],
                'experience_level': 'mid',
                'department': 'Technology'
            },
            'analysis_type': 'comprehensive'
        }
        
        # Mock the request JSON
        original_get_json = flask_request.get_json
        flask_request.get_json = lambda: test_data
        
        try:
            # Call the admin analysis function
            result = admin_unlimited_resume_analysis(resume_id)
            
            return jsonify({
                'success': True,
                'test_result': 'admin_analysis_test_completed',
                'resume_id': resume_id,
                'endpoint_response': result.get_json() if hasattr(result, 'get_json') else str(result),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            # Restore original get_json
            flask_request.get_json = original_get_json
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'test_result': 'admin_analysis_test_failed',
            'resume_id': resume_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@ollama_test_bp.route('/database-migration', methods=['POST'])
def test_database_migration():
    """Test database migration functionality"""
    try:
        # Test the migration script
        import subprocess
        import os
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrate_resumes_to_railway.py')
        
        if os.path.exists(script_path):
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            return jsonify({
                'success': result.returncode == 0,
                'migration_output': result.stdout,
                'migration_errors': result.stderr,
                'return_code': result.returncode,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Migration script not found',
                'script_path': script_path,
                'timestamp': datetime.utcnow().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
