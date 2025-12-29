# Railway Production Dockerfile
# Optimized exclusively for Railway cloud platform deployment
FROM python:3.11-slim AS base

# Railway production environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    PYTHONIOENCODING=utf-8 \
    PYTHONFAULTHANDLER=1 \
    RAILWAY_DEPLOYMENT=true

# Install Railway-optimized system dependencies
RUN echo " Installing Railway production dependencies..." && \
    apt-get update && apt-get install -y --no-install-recommends \
    bash curl wget ca-certificates build-essential pkg-config libpq-dev \
    tesseract-ocr tesseract-ocr-eng \
    poppler-utils \
    procps htop net-tools dnsutils \
    && echo " Railway system dependencies installed" \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Install Python dependencies with Railway optimization
COPY requirements.txt /app/
RUN echo " Installing Railway-optimized Python packages..." && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --verbose -r requirements.txt && \
    echo " Python packages installed for Railway" && \
    echo " Key packages installed:" && \
    pip list | grep -E "(flask|gunicorn|celery|sqlalchemy|redis|boto3|alembic)" || true

# Copy Railway application structure
COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY entrypoint.sh /app/entrypoint.sh
COPY gunicorn.conf.py /app/gunicorn.conf.py

# Verify Railway application structure and set permissions
RUN echo " Verifying Railway application structure..." && \
    ls -la /app/ && \
    echo " Application modules:" && \
    find /app/app -name "*.py" | head -10 && \
    echo " Alembic migrations:" && \
    ls -la /app/alembic/versions/ 2>/dev/null | head -5 || echo "No migrations found" && \
    chmod +x /app/entrypoint.sh && \
    echo " Railway application structure verified"

# Railway production environment
ENV ALEMBIC_CONFIG=/app/alembic.ini \
    PYTHONPATH=/app \
    GUNICORN_CMD_ARGS="--access-logfile=- --error-logfile=- --capture-output" \
    OLLAMA_HOST=http://127.0.0.1:11434 \
    OLLAMA_ORIGINS=* \
    OLLAMA_KEEP_ALIVE=5m \
    OLLAMA_NUM_PARALLEL=4 \
    OLLAMA_MAX_LOADED_MODELS=3

# Railway health check configuration
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD curl -f http://127.0.0.1:$PORT/api/health || exit 1

# Railway port exposure
EXPOSE $PORT

# Railway production entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
