#!/bin/bash
echo "🚀 Railway Container Starting with Modern Orchestrator..."

# Step 1: Setup Railway Database (if needed)
echo "🛠️ Checking database setup..."
cd /app

# The new orchestrator handles database initialization
# But we can run a quick check here if needed
if [ -n "$DATABASE_URL" ]; then
    echo "✅ Database URL configured"
else
    echo "⚠️ No DATABASE_URL found"
fi

# Step 2: Start Ollama service in background (the orchestrator will manage it)
echo "🤖 Pre-starting Ollama service..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!
echo "Ollama pre-started with PID: $OLLAMA_PID"

# Step 3: Start the modern application with orchestrator
echo "🌟 Starting application with modern orchestrator..."
python start_modern.py

# If we reach here, the app has stopped
echo "📋 Application stopped"
            ollama pull qwen2.5:14b > /tmp/ollama_pull_14b.log 2>&1 &
            ollama pull qwen2.5:7b > /tmp/ollama_pull_7b.log 2>&1 &
            break
        fi
        echo "Waiting for Ollama... ($i/30)"
        sleep 2
    done
    
    if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        echo "⚠️ Warning: Ollama failed to start properly"
    fi
} &

# Wait for the main application
wait $APP_PID
