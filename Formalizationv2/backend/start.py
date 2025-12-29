"""
Application startup script for Railway deployment
"""

import os
import sys
import logging
from app import app

# Configure logging for production
if os.getenv('FLASK_ENV') == 'production':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/logs/application.log')
        ]
    )

# Ensure log directory exists
os.makedirs('/tmp/logs', exist_ok=True)

if __name__ == '__main__':
    # Get port from Railway environment
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🚀 Starting HR Resume Screening Backend")
    print(f"📊 Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"🌐 Port: {port}")
    print(f"🔗 Frontend URL: {os.getenv('FRONTEND_URL', 'https://hrtool-sable.vercel.app')}")
    
    # Run with Gunicorn in production, Flask dev server otherwise
    if os.getenv('FLASK_ENV') == 'production':
        import subprocess
        subprocess.run([
            'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '4',
            '--timeout', '300',
            '--worker-class', 'sync',
            '--max-requests', '1000',
            '--preload',
            'app:app'
        ])
    else:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True
        )
