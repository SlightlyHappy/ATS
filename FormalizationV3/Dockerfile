# Optimized Dockerfile for Enhanced HR ATS with Legal RAG System
# Railway deployment ready - models downloaded at runtime for efficiency

FROM python:3.11-slim

# Set environment variables with memory optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    NUMEXPR_NUM_THREADS=4 \
    SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2 \
    RAILWAY_MEMORY_OPTIMIZED=true

# Install system dependencies (optimized for Railway)
RUN apt-get update && apt-get install -y \
    # Essential system tools
    curl \
    wget \
    # OCR dependencies
    tesseract-ocr \
    tesseract-ocr-eng \
    # Document processing
    poppler-utils \
    # Image processing
    libgl1-mesa-glx \
    libglib2.0-0 \
    # ML dependencies
    libblas3 \
    liblapack3 \
    # Build tools (minimal)
    gcc \
    # Additional libraries
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Ollama for Railway deployment
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with correct permissions
RUN mkdir -p /app/uploads /app/processed /app/temp /app/logs /app/models \
    /app/hr_legal_faiss_data /app/query_cache /app/model_cache \
    /app/faiss_indexes /app/legal_knowledge && \
    chmod -R 755 /app && \
    touch /app/logs/app.log && \
    chmod 666 /app/logs/app.log

# Copy and setup Railway startup script
COPY railway_start.sh /app/railway_start.sh
RUN chmod +x /app/railway_start.sh

# Add modern startup script
COPY start_modern.py /app/start_modern.py

# Health check - Extended for Railway deployment with model downloads
HEALTHCHECK --interval=45s --timeout=30s --start-period=300s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8000}/startup/health || curl -f http://localhost:${PORT:-8000}/health || exit 1

# Expose port
EXPOSE 8000

# Use Railway startup script that handles Ollama + app
CMD ["/app/railway_start.sh"]
