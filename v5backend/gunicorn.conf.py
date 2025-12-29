# Railway Production Gunicorn Configuration
# Optimized for Railway cloud platform deployment with enhanced debugging
import os
import multiprocessing
import sys

# Railway server socket configuration
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Railway-optimized worker configuration
workers = int(os.getenv('WEB_CONCURRENCY', '4'))  # Railway container optimized
worker_class = "sync"
worker_connections = 1000
max_requests = 1500  # Increased for Railway efficiency
max_requests_jitter = 200

# Railway-optimized timeout settings
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))  # Railway load balancer compatible
graceful_timeout = 30
keepalive = 5  # Slightly increased for Railway

# Railway application preloading
preload_app = True

# Railway logging configuration with enhanced debugging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s [Railway:%(p)s]'
error_log_format = '[%(asctime)s] [%(levelname)s] [Railway:%(process)d] %(message)s'

# Railway process configuration
proc_name = 'railway_ats_backend'
daemon = False
pidfile = None
tmp_upload_dir = None

# Railway performance optimizations
worker_tmp_dir = "/dev/shm" if os.path.exists("/dev/shm") else None  # Shared memory for Railway containers
max_worker_memory = 256 * 1024 * 1024  # 256MB per worker for Railway

# Railway security settings
limit_request_line = 8192
limit_request_fields = 100
limit_request_field_size = 8190

# Enhanced Railway deployment hooks with debugging
def post_fork(server, worker):
    """Called after a worker is forked - Railway optimized."""
    server.log.info("🚂 Railway worker spawned (pid: %s, deployment: %s, service: %s)", 
                    worker.pid, 
                    os.getenv('RAILWAY_DEPLOYMENT_ID', 'unknown'),
                    os.getenv('RAILWAY_SERVICE_NAME', 'unknown'))
    
    # Log worker environment for debugging
    server.log.info("🔧 Worker environment - Memory: %s, Replica: %s", 
                    os.getenv('RAILWAY_MEMORY_GB', 'unknown'),
                    os.getenv('RAILWAY_REPLICA_ID', 'unknown'))

def pre_fork(server, worker):
    """Called before worker fork - Railway preparation."""
    server.log.info("🔄 Railway worker pre-fork preparation for worker %s", worker)

def when_ready(server):
    """Called when Railway server is ready."""
    server.log.info("🚂 Railway ATS Backend ready - Service: %s, Environment: %s, Deployment: %s", 
                    os.getenv('RAILWAY_SERVICE_NAME', 'unknown'),
                    os.getenv('RAILWAY_ENVIRONMENT_NAME', 'unknown'),
                    os.getenv('RAILWAY_DEPLOYMENT_ID', 'unknown'))
    server.log.info("🌐 Listening on %s with %d workers", bind, workers)

def worker_int(worker):
    """Called when Railway worker receives signal."""
    worker.log.info("🛑 Railway worker %s received shutdown signal", worker.pid)

def on_exit(server):
    """Called when Railway server shuts down."""
    server.log.info("🔚 Railway ATS Backend shutting down - Deployment: %s", 
                    os.getenv('RAILWAY_DEPLOYMENT_ID', 'unknown'))

def on_reload(server):
    """Called when Railway server reloads."""
    server.log.info("🔄 Railway ATS Backend reloading configuration")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.error("❌ Railway worker %s aborted (SIGABRT) - potential memory issue or crash", worker.pid)

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("🚀 Railway master process pre-exec - preparing new master")

def post_worker_init(worker):
    """Called just after a worker has been forked."""
    worker.log.info("🔧 Railway worker %s initialization complete", worker.pid)
