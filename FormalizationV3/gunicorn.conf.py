#!/usr/bin/env python3
"""
Production Gunicorn Configuration for Railway Deployment
Memory-optimized for 32GB RAM environment with ML models
Updated for modern startup orchestrator
"""

import os
import multiprocessing
import logging

# Railway environment detection
is_railway = os.getenv('RAILWAY_ENVIRONMENT') == 'production'
port = int(os.getenv('PORT', 8000))

# Memory-optimized worker configuration for Railway Pro (32GB RAM, 32 cores)
if is_railway:
    # Railway Pro: OPTIMIZED CONFIGURATION for 32-core, 32GB setup
    workers = 4  # Reduced workers but more memory per worker
    worker_class = "sync"  # Sync for stability and reduced CPU overhead
    worker_connections = 1000  # Can handle more connections with 32 cores
    max_requests = 1000  # Process more requests per worker
    max_requests_jitter = 50  # Add jitter to prevent thundering herd
    preload_app = True  # CRITICAL: Share memory between workers for 32GB RAM
    worker_tmp_dir = "/dev/shm"  # Use shared memory for tmp files
    
    # CPU optimization for 32 cores
    worker_rlimit_as = 8000000000  # 8GB per worker (4 workers × 8GB = 32GB total)
    
else:
    # Development/other environments
    workers = 2
    worker_class = "sync"
    worker_connections = 500
    max_requests = 500
    max_requests_jitter = 50
    preload_app = False

# Binding and networking
bind = f"0.0.0.0:{port}"
backlog = 2048

# Memory and timeout settings - Extended for AI processing
timeout = 300  # Extended to 5 minutes for AI processing (was 120)
graceful_timeout = 120  # Extended graceful timeout
keepalive = 5  # Reduced to save memory

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process management
pidfile = "/tmp/gunicorn.pid"
daemon = False
user = None
group = None
tmp_upload_dir = None

# Memory optimization for Railway Pro
worker_rlimit_as = 8000000000  # 8GB memory limit per worker (optimized for 4 workers)
worker_rlimit_core = 0
worker_rlimit_data = 8000000000
worker_rlimit_fsize = 2147483648
worker_rlimit_memlock = -1
worker_rlimit_nofile = 65536
worker_rlimit_nproc = 65536

# SSL (disabled for Railway internal routing)
keyfile = None
certfile = None

# Application
module = "start:app"

# Hooks for memory monitoring
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("🚀 Starting Gunicorn with WebSocket support for Railway")
    server.log.info(f"Workers: {workers}, Worker class: {worker_class}, Connections: {worker_connections}")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("🔄 Reloading workers with memory optimization")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"💭 Worker {worker.pid} interrupted - memory will be released")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"🍴 Forking worker {worker.pid} with memory optimization")

def post_fork(server, worker):
    """Called just after worker processes are forked."""
    worker.log.info(f"👶 Worker {worker.pid} spawned with PID and memory optimization")

def pre_exec(server):
    """Called just before new application is executed."""
    server.log.info("🔄 Pre-exec: Preparing for application execution")

def when_ready(server):
    """Called just after the master process is initialized."""
    server.log.info("✅ Gunicorn master ready with WebSocket and real-time support")
    server.log.info(f"Listening on: {bind}")
    server.log.info(f"Workers: {workers} (eventlet async workers)")
    server.log.info(f"WebSocket support: {'Enabled' if worker_class == 'eventlet' else 'Disabled'}")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info(f"💥 Worker {worker.pid} aborted - likely memory issue")

# Environment-specific configurations
if is_railway:
    # Railway-specific optimizations
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Prevent tokenizer threading issues
    os.environ['OMP_NUM_THREADS'] = '4'  # Limit OpenMP threads
    os.environ['MKL_NUM_THREADS'] = '4'  # Limit MKL threads
    os.environ['NUMEXPR_NUM_THREADS'] = '4'  # Limit NumExpr threads
