# Backend Dockerfile - Complete Production Setup with Ollama Support
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app \
    OLLAMA_HOST=0.0.0.0 \
    OLLAMA_ORIGINS=* \
    OLLAMA_MODELS=/app/.ollama/models

# Install system dependencies for OCR, document processing, utilities, and Ollama
RUN apt-get update && apt-get install -y \
    # OCR dependencies
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    # Document processing
    poppler-utils \
    libpoppler-cpp-dev \
    # Image processing
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    # System utilities
    pkg-config \
    curl \
    wget \
    gcc \
    g++ \
    ca-certificates \
    gnupg \
    lsb-release \
    # Additional libraries for better performance
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Verify Ollama installation
RUN which ollama && ollama --version

# Set working directory
WORKDIR /app

# Create necessary directories including Ollama data directory
RUN mkdir -p \
    /app/data/uploads \
    /app/data/processed \
    /app/data/resume_storage \
    /app/logs \
    /app/temp \
    /app/.ollama/models \
    /app/.ollama/logs

# Copy requirements first for better layer caching
COPY requirements.txt .

# Debug: Show Python and system info
RUN echo "=== BACKEND BUILD DEBUG ===" && \
    echo "Python version: $(python --version)" && \
    echo "Pip version: $(pip --version)" && \
    echo "Ollama version: $(ollama --version || echo 'Ollama check failed')" && \
    echo "Working directory: $(pwd)" && \
    echo "Requirements file contents:" && \
    head -20 requirements.txt && \
    echo "=== INSTALLING DEPENDENCIES ==="

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Debug: Verify critical packages
RUN echo "=== DEPENDENCY VERIFICATION ===" && \
    python -c "import flask; print(f'Flask: {flask.__version__}')" && \
    python -c "import requests; print(f'Requests: {requests.__version__}')" && \
    python -c "import PIL; print(f'Pillow: {PIL.__version__}')" && \
    python -c "import gunicorn; print(f'Gunicorn: {gunicorn.__version__}')" && \
    python -c "import numpy; print(f'NumPy: {numpy.__version__}')" && \
    python -c "import pandas; print(f'Pandas: {pandas.__version__}')" && \
    python -c "import sklearn; print(f'Scikit-learn: {sklearn.__version__}')" && \
    python -c "import faiss; print('FAISS-CPU: Available')" && \
    echo "Critical packages verified successfully" || echo "Some packages missing!"

# Copy application code
COPY . .

# Run comprehensive dependency test
RUN echo "=== COMPREHENSIVE DEPENDENCY TEST ===" && \
    python test_dependencies.py && \
    echo "All dependencies verified successfully!"

# Debug: Verify application structure and make scripts executable
RUN echo "=== APPLICATION STRUCTURE DEBUG ===" && \
    echo "Application files:" && \
    ls -la && \
    echo "Key files check:" && \
    test -f app.py && echo "✓ app.py exists" || echo "✗ app.py missing" && \
    test -f start.py && echo "✓ start.py exists" || echo "✗ start.py missing" && \
    test -f config.py && echo "✓ config.py exists" || echo "✗ config.py missing" && \
    test -f start_with_ollama.sh && echo "✓ start_with_ollama.sh exists" || echo "✗ startup script missing" && \
    echo "Making startup script executable..." && \
    chmod +x /app/start_with_ollama.sh && \
    echo "Python syntax check:" && \
    python -m py_compile app.py && echo "✓ app.py syntax OK" || echo "✗ app.py syntax error" && \
    python -m py_compile multi_provider_ai.py && echo "✓ multi_provider_ai.py syntax OK" || echo "✗ multi_provider_ai.py syntax error" && \
    echo "=== APPLICATION DEBUG COMPLETE ==="

# Set proper permissions
RUN chmod +x /app/data && \
    chmod 755 /app/logs && \
    chmod 755 /app/.ollama && \
    chown -R nobody:nogroup /app/data /app/logs /app/temp /app/.ollama

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Expose ports (Flask app and Ollama)
EXPOSE 8000 11434

# Health check that verifies Flask is running (Ollama is optional)
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || \
        curl -f http://localhost:${PORT:-8000}/ || exit 1

# Use the comprehensive startup script
CMD ["/app/start_with_ollama.sh"]
