#!/bin/bash
# Fix eventlet conflicts for Railway deployment

echo "🔧 Removing eventlet to prevent RLock conflicts..."

# Remove eventlet if it's installed
pip uninstall -y eventlet

echo "✅ Eventlet removed - Gunicorn will now respect --worker-class gthread"
echo "🚀 Ready for deployment with threading mode"
