#!/bin/bash
set -e

echo "=== STARTING FLASK + OLLAMA APPLICATION ==="

# Set environment variables
export FLASK_ENV=production
export PYTHONPATH=/app
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_ORIGINS="*"  
export OLLAMA_MODELS="/app/.ollama/models"
export OLLAMA_LOGS="/app/.ollama/logs"

# Get port from environment (Railway sets this)
PORT=${PORT:-8000}

echo "=== STEP 1: STARTING FLASK APPLICATION ==="
echo "Starting Flask on port $PORT..."

# Start Flask application in background
python start.py &
FLASK_PID=$!

echo "Flask PID: $FLASK_PID"

# Function to check if Flask is ready
check_flask() {
    curl -sf http://localhost:$PORT/health > /dev/null 2>&1 || \
    curl -sf http://localhost:$PORT/ > /dev/null 2>&1
}

# Wait for Flask to be ready
echo "Waiting for Flask to start (max 60 seconds)..."
flask_timeout=60
flask_counter=0
while ! check_flask; do
    if [ $flask_counter -ge $flask_timeout ]; then
        echo "ERROR: Flask failed to start within $flask_timeout seconds"
        echo "Checking if Flask process is still running..."
        if ! kill -0 $FLASK_PID 2>/dev/null; then
            echo "Flask process died. Exiting."
            exit 1
        fi
        echo "Flask process running but not responding. Continuing anyway..."
        break
    fi
    echo "Waiting for Flask... ($flask_counter/$flask_timeout)"
    sleep 2
    flask_counter=$((flask_counter + 2))
done

if check_flask; then
    echo "✅ Flask is ready and responding!"
else
    echo "⚠️  Flask may not be fully ready, but continuing..."
fi


echo "=== STEP 2: STARTING OLLAMA ==="

# Create log directories
mkdir -p /app/.ollama/logs
touch /app/.ollama/logs/ollama.log

echo "Starting Ollama server..."
# Start Ollama in the background with proper logging
ollama serve > /app/.ollama/logs/ollama.log 2>&1 &
OLLAMA_PID=$!

echo "Ollama PID: $OLLAMA_PID"

# Function to check if Ollama is ready
check_ollama() {
    curl -sf http://localhost:11434/api/version > /dev/null
}

# Wait for Ollama to be ready with timeout
echo "Waiting for Ollama to start (max 120 seconds)..."
timeout=120
counter=0
while ! check_ollama; do
    if [ $counter -ge $timeout ]; then
        echo "ERROR: Ollama failed to start within $timeout seconds"
        echo "Ollama logs:"
        cat /app/.ollama/logs/ollama.log
        exit 1
    fi
    echo "Waiting for Ollama... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

echo "✅ Ollama is ready!"

# Check available models
echo "Checking available models..."
ollama list || echo "No models installed yet"

# Function to pull model with retries
pull_model_with_retry() {
    local model=$1
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempting to pull model $model (attempt $attempt/$max_attempts)..."
        if ollama pull "$model"; then
            echo "✅ Successfully pulled model: $model"
            return 0
        else
            echo "❌ Failed to pull model $model (attempt $attempt/$max_attempts)"
            if [ $attempt -eq $max_attempts ]; then
                echo "ERROR: Failed to pull model after $max_attempts attempts"
                return 1
            fi
            sleep 10
        fi
        attempt=$((attempt + 1))
    done
}

# Pull the default model (with fallback options)
DEFAULT_MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
echo "Pulling default model: $DEFAULT_MODEL"

if ! pull_model_with_retry "$DEFAULT_MODEL"; then
    echo "⚠️  Failed to pull primary model, trying fallback models..."
    
    # Try smaller fallback models
    FALLBACK_MODELS="qwen2.5:3b llama3.2:3b phi3.5:3.8b"
    
    model_pulled=false
    for fallback_model in $FALLBACK_MODELS; do
        if pull_model_with_retry "$fallback_model"; then
            echo "✅ Using fallback model: $fallback_model"
            export OLLAMA_MODEL="$fallback_model"
            model_pulled=true
            break
        fi
    done
    
    if [ "$model_pulled" = false ]; then
        echo "❌ Failed to pull any model. Application may not work properly."
        echo "Available models:"
        ollama list
    fi
else
    echo "✅ Primary model ready: $DEFAULT_MODEL"
fi

# Verify Ollama is working with a test query
echo "Testing Ollama with a simple query..."
if echo '{"model":"'${OLLAMA_MODEL:-qwen2.5:7b}'","prompt":"Hello, respond with just: OK","stream":false}' | curl -s -X POST http://localhost:11434/api/generate -d @- | grep -q "OK"; then
    echo "✅ Ollama test successful"
else
    echo "⚠️  Ollama test failed, but continuing..."
fi

# Function to handle cleanup on exit
cleanup() {
    echo "Shutting down..."
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null || true
    fi
    if [ ! -z "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

echo "✅ Application stack started successfully!"
echo "Flask app available at: http://localhost:${PORT}"
echo "Ollama available at: http://localhost:11434"
echo "Both services are running. Monitoring Flask process..."

# Wait for Flask process (main application)
wait $FLASK_PID
