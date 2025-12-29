#!/usr/bin/env python3
"""
Production start script for Railway deployment
"""

import os
import sys
import subprocess

# Set environment for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('NODE_ENV', 'production')

def main():
    try:
        # Get port from environment (Railway sets this automatically)
        port = int(os.environ.get('PORT', 8000))
        
        print(f"Starting Bear Systems ATS on port {port}")
        print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        
        # Check if Supabase variables are available
        supabase_url = os.environ.get('SUPABASE_URL') or os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
        if supabase_url:
            print(f"✅ Supabase URL configured: {supabase_url[:30]}...")
        else:
            print("⚠️  No Supabase URL found in environment variables")
        
        # Use gunicorn for production
        cmd = [
            'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '2',
            '--threads', '4',
            '--timeout', '300',
            '--keep-alive', '120',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--worker-class', 'sync',
            'app:app'
        ]
        
        print(f"Starting with command: {' '.join(cmd)}")
        
        # Execute gunicorn
        subprocess.run(cmd, check=True)
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()