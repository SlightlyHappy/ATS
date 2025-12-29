#!/usr/bin/env bash
set -euo pipefail

# Railway Production Deployment Entrypoint
# Optimized exclusively for Railway cloud platform deployment
# This script handles API, worker, and beat roles

: "${LOG_LEVEL:=INFO}"
: "${PORT:=8000}"
: "${RUN_MIGRATIONS:=true}"
: "${ROLE:=api}"

resolve_database_url() {
    if [ -z "${DATABASE_URL:-}" ]; then
        # Prefer explicit PG* if available
        if [ -n "${PGHOST:-}" ] && [ -n "${PGPORT:-}" ] && [ -n "${PGPASSWORD:-}" ]; then
            local pguser
            pguser="${PGUSER:-${POSTGRES_USER:-postgres}}"
            local pgdb
            pgdb="${PGDATABASE:-${POSTGRES_DB:-railway}}"
            export DATABASE_URL="postgresql://${pguser}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${pgdb}"
        elif [ -n "${DATABASE_INTERNAL_URL:-}" ]; then
            export DATABASE_URL="${DATABASE_INTERNAL_URL}"
        elif [ -n "${DATABASE_PRIMARY_NODE:-}" ]; then
            export DATABASE_URL="${DATABASE_PRIMARY_NODE}"
        elif [ -n "${DATABASE_PUBLIC_URL:-}" ]; then
            export DATABASE_URL="${DATABASE_PUBLIC_URL}"
        fi
    fi
}

resolve_redis_url() {
    if [ -z "${REDIS_URL:-}" ] && [ -n "${CELERY_BROKER_URL:-}" ]; then
        export REDIS_URL="${CELERY_BROKER_URL}"
    fi
}

echo "🚂 Railway Production Deployment - ${ROLE} Service"
echo "⏰ Startup: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "🔧 Environment: ${ENV:-production}"
echo "📊 Log Level: ${LOG_LEVEL}"
echo "🌐 Port: ${PORT}"
echo "📋 Railway Service: ${RAILWAY_SERVICE_NAME:-'Unknown'}"
echo "🆔 Deployment ID: ${RAILWAY_DEPLOYMENT_ID:-'Unknown'}"
echo "🌍 Railway Environment: ${RAILWAY_ENVIRONMENT_NAME:-'Unknown'}"
echo "🚀 Railway Replica: ${RAILWAY_REPLICA_ID:-'Unknown'}"
echo "💾 Railway Memory: ${RAILWAY_MEMORY_GB:-'Unknown'}GB"
echo "🔄 Railway Static URL: ${RAILWAY_STATIC_URL:-'Unknown'}"
echo "🌐 Railway Public Domain: ${RAILWAY_PUBLIC_DOMAIN:-'Unknown'}"

# Configure database settings for Railway PostgreSQL service
export SKIP_PGVECTOR_ON_FAILURE="${SKIP_PGVECTOR_ON_FAILURE:-true}"
export FORCE_PGVECTOR_CREATION="${FORCE_PGVECTOR_CREATION:-false}"
export PGVECTOR_RETRY_COUNT="${PGVECTOR_RETRY_COUNT:-0}"
export PGVECTOR_RETRY_DELAY="${PGVECTOR_RETRY_DELAY:-0}"
echo "🗄️  Database Config: SKIP_PGVECTOR=${SKIP_PGVECTOR_ON_FAILURE}, FORCE_PGVECTOR=${FORCE_PGVECTOR_CREATION}, TEXT_SEARCH_MODE=enabled"

# Configure Railway-optimized Python environment
setup_python_env() {
    export PYTHONPATH="/app:${PYTHONPATH:-}"
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONFAULTHANDLER=1
    export PYTHONIOENCODING=utf-8
    echo "🐍 Python environment configured for Railway"
}

# Quick Railway service connectivity check
verify_core_services() {
    echo "🔗 Railway Core Service Check:"
    
    # Derive URLs if missing
    resolve_database_url
    resolve_redis_url
    
    # Determine whether dependencies are required for the given role
    local DB_REQUIRED="true"
    local REDIS_REQUIRED="false"
    if [ "${ROLE}" = "api" ]; then
        DB_REQUIRED="true"       # API needs database for proper functionality
        REDIS_REQUIRED="false"   # Redis never required for API
    elif [ "${ROLE}" = "worker" ] || [ "${ROLE}" = "beat" ]; then
        DB_REQUIRED="true"
        REDIS_REQUIRED="true"
    fi
    
    # Database connectivity with enhanced debugging
    if [ -n "${DATABASE_URL:-}" ]; then
        echo "   📊 Testing database connection..."
        echo "   🔗 Database URL pattern: ${DATABASE_URL:0:30}...***MASKED***"
        python -c "
import os
import sys
from sqlalchemy import create_engine, text
try:
    print('   🔄 Creating database engine...')
    engine = create_engine(
        os.environ['DATABASE_URL'], 
        pool_pre_ping=True, 
        connect_args={'connect_timeout': 15}
    )
    print('   🔄 Testing database connection...')
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        version = result.fetchone()[0]
        print(f'   ✅ Database: Connected - {version[:50]}...')
except Exception as e:
    print(f'   ❌ Database Error: {type(e).__name__}: {str(e)[:200]}...')
    import traceback
    print('   📋 Database Error Traceback:')
    traceback.print_exc()
    sys.exit(1)
" || {
            echo "   ❌ Database check failed and is required for ROLE=${ROLE}"
            echo "   💡 Check Railway PostgreSQL service status and connection variables"
            exit 1
        }
                echo "   ⚠️  Database check failed; continuing in degraded mode (ROLE=${ROLE})"
            fi
        }
    else
        if [ "${DB_REQUIRED}" = "true" ]; then
            echo "   ❌ DATABASE_URL not configured (required for ROLE=${ROLE})"
            exit 1
        else
            echo "   ⚠️  DATABASE_URL not configured; continuing (ROLE=${ROLE})"
        fi
    fi
    
    # Redis connectivity
    if [ "${ROLE}" != "api" ]; then
        # Required for worker/beat
        if [ -n "${REDIS_URL:-}" ]; then
            echo "   🔴 Testing Redis..."
            python -c "
import os
import redis
r = redis.from_url(os.environ['REDIS_URL'], socket_connect_timeout=15)
assert r.ping()
print('   ✅ Redis: Connected')
" >/dev/null 2>&1 || {
                echo "   ❌ Redis check failed (required for ROLE=${ROLE})"
                exit 1
            }
        else
            echo "   ❌ REDIS_URL not configured (required for ROLE=${ROLE})"
            exit 1
        fi
    else
        # Optional for API; do not fail on error
        if [ -n "${REDIS_URL:-}" ]; then
            echo "   🔴 Testing Redis (non-fatal for API)..."
            python -c "
import os
import redis
try:
    r = redis.from_url(os.environ['REDIS_URL'], socket_connect_timeout=10)
    r.ping()
    print('   ✅ Redis: Connected')
except Exception as e:
    print('   ⚠️  Redis check failed; continuing: ' + str(e)[:100])
" >/dev/null 2>&1 || echo "   ⚠️  Redis check failed; continuing (API)"
        else
            echo "   ℹ️  REDIS_URL not set for API; skipping"
        fi
    fi
}

# Railway Ollama setup for API service only
setup_ollama_for_api() {
    if [ "${ROLE}" != "api" ]; then
        echo "⏭️  Ollama not needed for ${ROLE} service"
        return 0
    fi
    
    echo "🤖 Railway Ollama Setup (API service only)"
    
    # Check if Ollama is already installed
    if ! command -v ollama >/dev/null 2>&1; then
        echo "   📥 Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh || {
            echo "   ⚠️  Ollama installation failed - using fallback mode"
            echo "   💡 Application will run without LLM features"
            export OLLAMA_HOST=""
            return 0
        }
    fi
    
    # Set Ollama configuration
    export OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
    export OLLAMA_ORIGINS="${OLLAMA_ORIGINS:-*}"
    
    # Start Ollama server in background
    echo "   🚀 Starting Ollama server..."
    ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    
    # Wait for Ollama to be ready (max 30 seconds)
    echo "   ⏳ Waiting for Ollama..."
    for i in {1..30}; do
        if curl -s "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
            echo "   ✅ Ollama ready after ${i} seconds"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "   ⚠️  Ollama timeout - continuing without LLM"
            export OLLAMA_HOST=""
            return 0
        fi
        sleep 1
    done
    
    # Pull essential models if specified
    if [ -n "${OLLAMA_MODELS:-}" ]; then
        echo "   📦 Pulling models: ${OLLAMA_MODELS}"
        IFS=',' read -ra MODELS <<< "${OLLAMA_MODELS}"
        for model in "${MODELS[@]}"; do
            model=$(echo "$model" | xargs) # trim whitespace
            echo "   📥 Pulling ${model}..."
            timeout 300 ollama pull "$model" || {
                echo "   ⚠️  Failed to pull ${model} - continuing"
                continue
            }
        done
    fi
    
    echo "   ✅ Ollama setup completed"
}

# Railway database migrations - BLOCKING for all services
run_railway_migrations() {
    if [ "${RUN_MIGRATIONS}" = "true" ]; then
        echo "🔄 Running Railway database migrations (BLOCKING for ${ROLE})..."
        echo "   - Database: ${DATABASE_URL:0:40}...***MASKED***"
        
        # Increase timeout for migrations and make it blocking for all services
        MIGRATION_TIMEOUT="${MIGRATION_TIMEOUT:-120}"
        echo "   - Timeout: ${MIGRATION_TIMEOUT}s"
        
        # Run database debug first to help troubleshoot issues
        echo "   - Running database connectivity debug..."
        TEMP_DEBUG=$(mktemp)
        if python debug_database.py > "$TEMP_DEBUG" 2>&1; then
            echo "   ✅ Database debug passed"
            # Show debug output with prefix
            while IFS= read -r line; do
                echo "   [DEBUG] $line"
            done < "$TEMP_DEBUG"
        else
            echo "   ❌ Database debug failed"
            # Show debug output with prefix
            while IFS= read -r line; do
                echo "   [DEBUG] $line"
            done < "$TEMP_DEBUG"
            rm -f "$TEMP_DEBUG"
            echo "🆘 Database debug failed - cannot proceed with migrations"
            exit 1
        fi
        rm -f "$TEMP_DEBUG"
        
        # Run migrations with proper error handling using temp file to capture exit code
        echo "   - Starting migration process..."
        TEMP_OUTPUT=$(mktemp)
        if timeout "${MIGRATION_TIMEOUT}" python -m app.core.preflight > "$TEMP_OUTPUT" 2>&1; then
            # Success - show output with prefix
            while IFS= read -r line; do
                echo "   [PREFLIGHT] $line"
            done < "$TEMP_OUTPUT"
            rm -f "$TEMP_OUTPUT"
            echo "✅ Railway migration phase (${ROLE}) completed successfully"
        else
            migration_exit_code=$?
            # Failure - show output with prefix and error details
            while IFS= read -r line; do
                echo "   [PREFLIGHT] $line"
            done < "$TEMP_OUTPUT"
            rm -f "$TEMP_OUTPUT"
            echo "❌ Preflight/migration failed for ${ROLE} (exit code: ${migration_exit_code})"
            echo "🔍 This usually means:"
            echo "   1. Database connection failed"
            echo "   2. Database permissions issue"
            echo "   3. Migration script error"
            echo "   4. pgvector extension not available"
            echo "💡 Check Railway dashboard for database service status"
            echo "🆘 Application cannot start without proper database schema"
            exit 1
        fi
    else
        echo "⏭️  Skipping migrations (RUN_MIGRATIONS=${RUN_MIGRATIONS}, ROLE=${ROLE})"
    fi
}

# Railway API server startup
start_railway_api() {
    echo "🌐 Starting Railway API server..."
    echo "   - Bind: 0.0.0.0:${PORT}"
    echo "   - Workers: 4 (Railway optimized)"
    echo "   - Timeout: 120s"
    
    # Verify Flask application can be imported with detailed error reporting
    echo "🧪 Testing Flask application import..."
    python -c "
import sys
import traceback
try:
    print('   🔄 Importing Flask application...')
    from app.main import app
    print('   ✅ Flask app import successful')
    
    print('   🔄 Checking application routes...')
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print(f'   🛣️  Routes: {len(routes)} endpoints registered')
    
    print('   🔄 Testing application config...')
    print(f'   ⚙️  App Name: {app.config.get(\"APP_NAME\", \"unknown\")}')
    print(f'   🌍 Environment: {app.config.get(\"ENV\", \"unknown\")}')
    
    print('   ✅ Flask application ready for Railway deployment')
    
except ImportError as e:
    print(f'   ❌ Import Error: {e}')
    print('   💡 Check Python path and dependencies')
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f'   ❌ Flask app error: {type(e).__name__}: {e}')
    print('   📋 Full traceback:')
    traceback.print_exc()
    sys.exit(1)
" || {
        echo "❌ Flask application import test failed - cannot start API server"
        echo "💡 Check Railway build logs and environment variables"
        exit 1
    }
    
    echo "🚀 Launching Railway API server with enhanced monitoring..."
    echo "   🌐 Binding to: 0.0.0.0:${PORT}"
    echo "   👥 Workers: ${WEB_CONCURRENCY:-4}"
    echo "   ⏰ Timeout: ${GUNICORN_TIMEOUT:-120}s"
    echo "   📊 Log Level: ${LOG_LEVEL}"
    
    exec gunicorn \
        --config /app/gunicorn.conf.py \
        --capture-output \
        --enable-stdio-inheritance \
        --preload \
        --log-file=- \
        --error-logfile=- \
        --access-logfile=- \
        "app.main:app"
}

# Railway Celery worker startup
start_railway_worker() {
    echo "👷 Starting Railway Celery worker..."
    echo "   - Concurrency: ${WORKER_CONCURRENCY:-8} processes"
    echo "   - Queues: io,llm"
    echo "   - Broker: ${CELERY_BROKER_URL:0:30}...***MASKED***"
    
    # Verify Celery application can be imported
    echo "🧪 Testing Celery app import..."
    python -c "
try:
    from app.workers.celery_app import celery_app
    print('   ✅ Celery app import successful')
    registered_tasks = list(celery_app.tasks.keys())
    app_tasks = [t for t in registered_tasks if t.startswith('app.')]
    print(f'   📦 App tasks: {len(app_tasks)}')
except Exception as e:
    print(f'   ❌ Celery app import failed: {e}')
    exit(1)
" || exit 1
    
    echo "🚀 Launching Railway Celery worker..."
    exec celery -A app.workers.celery_app worker \
        --loglevel="${LOG_LEVEL,,}" \
        --concurrency="${WORKER_CONCURRENCY:-8}" \
        --prefetch-multiplier="${CELERY_WORKER_PREFETCH_MULTIPLIER:-4}" \
        --queues="io,llm" \
        --without-heartbeat \
        --without-mingle \
        --without-gossip
}

# Railway Celery beat scheduler
start_railway_beat() {
    echo "⏰ Starting Railway Celery beat scheduler..."
    
    # Test beat scheduler configuration
    echo "🧪 Testing beat scheduler config..."
    python -c "
try:
    from app.workers.celery_app import celery_app
    schedule = celery_app.conf.beat_schedule or {}
    print(f'   ✅ Beat schedule: {len(schedule)} periodic tasks')
except Exception as e:
    print(f'   ❌ Beat configuration error: {e}')
    exit(1)
" || exit 1
    
    echo "🚀 Launching Railway Celery beat..."
    exec celery -A app.workers.celery_app beat \
        --loglevel="${LOG_LEVEL,,}" \
        --pidfile= \
        --schedule=/tmp/celerybeat-schedule
}

# Railway production main execution
main() {
    echo "🔧 Railway Production Service Initialization"
    echo "⏰ Start time: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    
    # Setup Python environment
    setup_python_env
    
    # Quick core service verification
    verify_core_services
    
    # Role-specific startup
    echo "🎯 Launching Railway ${ROLE} service..."
    case "${ROLE}" in
        "api")
            echo "📡 Railway API Server Mode"
            setup_ollama_for_api
            run_railway_migrations
            start_railway_api
            ;;
        "worker")
            echo "👷 Railway Worker Mode"
            start_railway_worker
            ;;
        "beat")
            echo "⏰ Railway Beat Scheduler Mode"
            start_railway_beat
            ;;
        *)
            echo "❌ Invalid ROLE for Railway deployment: ${ROLE}"
            echo "🔍 Supported Railway roles: api, worker, beat"
            echo "💡 Check ROLE environment variable in Railway dashboard"
            exit 1
            ;;
    esac
}

# Railway-specific error handler
railway_error_handler() {
    local line_number=$1
    local error_code=$2
    echo "❌ Railway deployment error at line $line_number (exit code: $error_code)"
    echo "⏰ Error timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "🔍 Railway service: ${RAILWAY_SERVICE_NAME:-'Unknown'} (${ROLE})"
    echo "📦 Deployment: ${RAILWAY_DEPLOYMENT_ID:-'Unknown'}"
    
    # Cleanup any background processes
    if [ -n "${OLLAMA_PID:-}" ]; then
        echo "🧹 Cleaning up Ollama processes..."
        kill ${OLLAMA_PID} 2>/dev/null || true
    fi
    
    echo "🆘 Railway troubleshooting:"
    echo "   1. Check Railway dashboard for service status"
    echo "   2. Verify environment variables in Railway dashboard"
    echo "   3. Check Railway service logs for this deployment"
    echo "   4. Ensure dependent services are running"
}

# Cleanup function for graceful shutdown
cleanup() {
    echo "🧹 Railway service shutdown - cleaning up..."
    if [ -n "${OLLAMA_PID:-}" ]; then
        echo "   🤖 Stopping Ollama server (PID: ${OLLAMA_PID})"
        kill ${OLLAMA_PID} 2>/dev/null || true
    fi
    echo "   ✅ Cleanup completed"
}

# Enhanced Railway error trapping
trap 'railway_error_handler $LINENO $?' ERR
trap 'cleanup; exit 0' SIGTERM SIGINT

# Railway production startup
echo "🚀 Railway Production Entrypoint - Starting..."
echo "📋 Service: ${RAILWAY_SERVICE_NAME:-'Unknown'} (${ROLE})"
echo "🔧 Project: ${RAILWAY_PROJECT_NAME:-'Unknown'}"
echo "🌐 Environment: ${RAILWAY_ENVIRONMENT_NAME:-'Unknown'}"

main "$@"
