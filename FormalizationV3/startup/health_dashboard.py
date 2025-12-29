"""
Health Dashboard for HR ATS Application
Provides comprehensive health monitoring and status information
"""

import os
import time
import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template_string
from typing import Dict, Any

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/health')

def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system metrics"""
    try:
        import psutil
        
        # Memory info
        memory = psutil.virtual_memory()
        
        # CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Disk info
        disk = psutil.disk_usage('/')
        
        return {
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            },
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            }
        }
    except ImportError:
        return {'error': 'psutil not available'}

def get_environment_info() -> Dict[str, Any]:
    """Get environment information"""
    return {
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        'platform': os.sys.platform,
        'railway_environment': os.getenv('RAILWAY_ENVIRONMENT'),
        'port': os.getenv('PORT'),
        'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true',
        'ollama_available': os.getenv('OLLAMA_AVAILABLE', 'false') == 'true',
        'database_configured': bool(os.getenv('DATABASE_URL')),
        'supabase_configured': bool(os.getenv('SUPABASE_URL')),
    }

@health_bp.route('/')
def basic_health():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'hr-ats'
    })

@health_bp.route('/detailed')
def detailed_health():
    """Detailed health check with system metrics"""
    try:
        # Try to get orchestrator status
        from startup import get_orchestrator
        orchestrator = get_orchestrator()
        startup_status = orchestrator.get_status()
        health_status = orchestrator.get_health_status()
    except:
        startup_status = {'error': 'Orchestrator not available'}
        health_status = {'error': 'Health monitoring not available'}
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'hr-ats',
        'system_metrics': get_system_metrics(),
        'environment': get_environment_info(),
        'startup_status': startup_status,
        'health_status': health_status
    })

@health_bp.route('/dashboard')
def health_dashboard():
    """HTML dashboard for health monitoring"""
    
    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>HR ATS Health Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5;
        }
        .header { 
            background: #fff; padding: 20px; border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { 
            background: #fff; padding: 20px; border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-healthy { color: #22c55e; }
        .status-warning { color: #f59e0b; }
        .status-error { color: #ef4444; }
        .metric { margin-bottom: 10px; }
        .metric-label { font-weight: 600; color: #374151; }
        .metric-value { color: #6b7280; }
        .progress-bar {
            width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;
        }
        .progress-fill { height: 100%; background: #3b82f6; transition: width 0.3s; }
        .refresh-btn {
            background: #3b82f6; color: white; border: none; padding: 10px 20px;
            border-radius: 6px; cursor: pointer; font-size: 14px;
        }
        .refresh-btn:hover { background: #2563eb; }
        pre { background: #f9fafb; padding: 15px; border-radius: 6px; font-size: 12px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 HR ATS Health Dashboard</h1>
        <p>Real-time system monitoring and health status</p>
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
    </div>
    
    <div class="grid">
        <div class="card">
            <h3>📊 System Overview</h3>
            <div id="system-overview">Loading...</div>
        </div>
        
        <div class="card">
            <h3>🔧 Services Status</h3>
            <div id="services-status">Loading...</div>
        </div>
        
        <div class="card">
            <h3>💾 System Metrics</h3>
            <div id="system-metrics">Loading...</div>
        </div>
        
        <div class="card">
            <h3>🌍 Environment</h3>
            <div id="environment-info">Loading...</div>
        </div>
    </div>
    
    <script>
        async function loadHealthData() {
            try {
                const response = await fetch('/health/detailed');
                const data = await response.json();
                
                // System Overview
                document.getElementById('system-overview').innerHTML = `
                    <div class="metric">
                        <span class="metric-label">Status:</span>
                        <span class="status-healthy">✅ Healthy</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Last Check:</span>
                        <span class="metric-value">${new Date(data.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Service:</span>
                        <span class="metric-value">${data.service}</span>
                    </div>
                `;
                
                // Services Status
                let servicesHtml = '';
                if (data.startup_status && data.startup_status.services) {
                    for (const [name, service] of Object.entries(data.startup_status.services)) {
                        const status = service.is_running ? '✅ Running' : '❌ Stopped';
                        servicesHtml += `
                            <div class="metric">
                                <span class="metric-label">${name}:</span>
                                <span class="metric-value">${status}</span>
                            </div>
                        `;
                    }
                } else {
                    servicesHtml = '<p>Service status not available</p>';
                }
                document.getElementById('services-status').innerHTML = servicesHtml;
                
                // System Metrics
                let metricsHtml = '';
                if (data.system_metrics && !data.system_metrics.error) {
                    const metrics = data.system_metrics;
                    metricsHtml = `
                        <div class="metric">
                            <span class="metric-label">Memory Usage:</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${metrics.memory.percent}%"></div>
                            </div>
                            <span class="metric-value">${metrics.memory.percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">CPU Usage:</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${metrics.cpu.percent}%"></div>
                            </div>
                            <span class="metric-value">${metrics.cpu.percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Disk Usage:</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${metrics.disk.percent}%"></div>
                            </div>
                            <span class="metric-value">${metrics.disk.percent.toFixed(1)}%</span>
                        </div>
                    `;
                } else {
                    metricsHtml = '<p>System metrics not available</p>';
                }
                document.getElementById('system-metrics').innerHTML = metricsHtml;
                
                // Environment Info
                let envHtml = '';
                if (data.environment) {
                    for (const [key, value] of Object.entries(data.environment)) {
                        envHtml += `
                            <div class="metric">
                                <span class="metric-label">${key.replace(/_/g, ' ')}:</span>
                                <span class="metric-value">${value}</span>
                            </div>
                        `;
                    }
                }
                document.getElementById('environment-info').innerHTML = envHtml;
                
            } catch (error) {
                console.error('Failed to load health data:', error);
                document.getElementById('system-overview').innerHTML = 
                    '<p class="status-error">❌ Failed to load health data</p>';
            }
        }
        
        // Load data on page load
        loadHealthData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadHealthData, 30000);
    </script>
</body>
</html>
    """
    
    return dashboard_html

@health_bp.route('/startup/status')
def startup_status():
    """Get startup orchestrator status"""
    try:
        from startup import get_orchestrator
        orchestrator = get_orchestrator()
        return jsonify(orchestrator.get_status())
    except Exception as e:
        return jsonify({'error': str(e), 'available': False}), 503

@health_bp.route('/startup/health')
def startup_health():
    """Get startup orchestrator health"""
    try:
        from startup import get_orchestrator
        orchestrator = get_orchestrator()
        return jsonify(orchestrator.get_health_status())
    except Exception as e:
        return jsonify({'error': str(e), 'available': False}), 503

def register_health_routes(app):
    """Register health monitoring routes with Flask app"""
    app.register_blueprint(health_bp)
    
    # Legacy health endpoint for backwards compatibility
    @app.route('/health')
    def legacy_health():
        return basic_health()
    
    # Startup endpoints for compatibility
    @app.route('/startup/status')
    def legacy_startup_status():
        return startup_status()
    
    @app.route('/startup/health')
    def legacy_startup_health():
        return startup_health()
