#!/bin/bash

# Initialize Ollama models for the resume screening application

echo "Waiting for Ollama service to be ready..."

# Wait for Ollama to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://ollama:11434/api/version > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    echo "Waiting for Ollama... (attempt $((attempt + 1))/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "Ollama failed to start within the expected time"
    exit 1
fi

# Pull required models
echo "Pulling Ollama models..."

# Pull the main models used by the application
models=("qwen2.5:3b" "qwen2.5:7b" "llama3.2:3b")

for model in "${models[@]}"; do
    echo "Pulling model: $model"
    curl -X POST http://ollama:11434/api/pull \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$model\"}" \
        --max-time 1800  # 30 minutes timeout per model
    
    if [ $? -eq 0 ]; then
        echo "Successfully pulled $model"
    else
        echo "Failed to pull $model, but continuing..."
    fi
done

echo "Ollama initialization complete!"
