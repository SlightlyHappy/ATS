#!/bin/bash

# Script to restart the Resume Screening App with increased timeout settings
# For systems with limited resources (8GB RAM, 8 core CPU)

echo "🔄 Restarting Resume Screening App with increased timeout settings..."

# Stop any existing processes
echo "Stopping existing processes..."
pkill -f "python.*app.py" || true
pkill -f "python.*start.py" || true

# Set environment variables for increased timeouts
export AI_TIMEOUT=300
export OLLAMA_TIMEOUT=120
export DB_CONNECTION_TIMEOUT=60
export SESSION_TIMEOUT=7200  # 2 hours
export MAX_CONCURRENT_PROCESSING=1  # Single processing for limited resources

echo "✅ Environment variables set:"
echo "   AI_TIMEOUT=$AI_TIMEOUT seconds"
echo "   OLLAMA_TIMEOUT=$OLLAMA_TIMEOUT seconds"
echo "   DB_CONNECTION_TIMEOUT=$DB_CONNECTION_TIMEOUT seconds"
echo "   SESSION_TIMEOUT=$SESSION_TIMEOUT seconds"
echo "   MAX_CONCURRENT_PROCESSING=$MAX_CONCURRENT_PROCESSING"

# Navigate to backend directory
cd "$(dirname "$0")/backend" || exit 1

# Start the application
echo "🚀 Starting application with increased timeouts..."
python app.py

echo "✅ Application started with optimized timeout settings for limited hardware!"
