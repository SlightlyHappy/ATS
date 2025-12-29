# Use Python 3.11 slim image for better compatibility with PyTorch ecosystem
# Python 3.11 provides optimal compatibility with scientific packages and pre-built wheels
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies optimized for ML packages and OCR
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    python3-dev \
    gcc \
    g++ \
    make \
    libpq-dev \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    antiword \
    unrar-free \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    wget \
    ca-certificates \
    libblas-dev \
    liblapack-dev \
    libopenblas-dev \
    gfortran \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and build tools
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch CPU with matching torchvision (required by sentence-transformers)
RUN pip install torch==2.1.0+cpu torchvision==0.16.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install numpy first as it's required by many other packages
RUN pip install numpy==1.26.4

# Install core ML packages needed by the RAG system
RUN pip install tiktoken==0.5.2 faiss-cpu==1.7.4

# Install sentencepiece (required by some sentence-transformer models like all-mpnet-base-v2)
RUN pip install --no-cache-dir --prefer-binary sentencepiece

# Set environment variables for better compilation
ENV SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=False
ENV NPY_NUM_BUILD_JOBS=1
ENV CFLAGS="-Wno-error"
ENV CPPFLAGS="-Wno-error"

# Install remaining application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads processed logs

# Set environment variables for Railway
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PORT=8000
ENV OLLAMA_HOST=0.0.0.0

# Expose ports (Railway uses PORT environment variable, Ollama uses 11434)
EXPOSE $PORT
EXPOSE 11434

# Create startup script that launches both Ollama and the Flask app
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starting Railway deployment..."\n\
echo "Starting Ollama service in background..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
echo "Waiting for Ollama to be ready..."\n\
sleep 15\n\
echo "Testing Ollama connection..."\n\
for i in {1..30}; do\n\
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then\n\
        echo "✅ Ollama is ready!"\n\
        break\n\
    fi\n\
    echo "⏳ Waiting for Ollama... ($i/30)"\n\
    sleep 2\n\
done\n\
echo "Pulling AI model: ${OLLAMA_MODEL:-qwen2.5:7b}..."\n\
ollama pull ${OLLAMA_MODEL:-qwen2.5:7b} || echo "⚠️ Failed to pull model, continuing..."\n\
echo "🌐 Starting Flask application..."\n\
exec python start.py' > /app/start_combined.sh && chmod +x /app/start_combined.sh

# Health check for both services (simplified for Railway)
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/v1/health/simple || exit 1

# Run both Ollama and the application
CMD ["/app/start_combined.sh"]
