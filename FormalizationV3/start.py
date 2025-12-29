#!/usr/bin/env python3
"""
Main startup script for HR ATS Application
Uses the modern startup orchestrator system
"""

import os
import sys
import asyncio
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from startup import StartupOrchestrator, StartupConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Main startup function using orchestrator"""
    try:
        logger.info("🚀 Starting HR ATS Application...")
        
        # Create startup configuration
        config = StartupConfig()
        
        # Create and run orchestrator
        orchestrator = StartupOrchestrator(config)
        success = await orchestrator.start_all_services()
        
        if success:
            logger.info("✅ All services started successfully")
            
            # Start the main Flask application
            from app import app
            
            # Get port from environment or default to 5000
            port = int(os.environ.get('PORT', 5000))
            host = os.environ.get('HOST', '0.0.0.0')
            
            logger.info(f"🌐 Starting Flask app on {host}:{port}")
            app.run(host=host, port=port, debug=False)
            
        else:
            logger.error("❌ Failed to start services")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)

def run_sync():
    """Synchronous wrapper for async main function"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_sync()
