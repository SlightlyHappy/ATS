#!/usr/bin/env python3
"""
Deployment Helper for Railway - Handles HRlaw folder issue
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_deployment_environment():
    """Setup environment for Railway deployment with legal database initialization"""
    
    logger.info("🚀 Setting up Railway deployment environment...")
    
    # Initialize legal knowledge base
    try:
        from initialize_legal_db import LegalKnowledgeInitializer
        
        logger.info("🔧 Initializing legal knowledge base...")
        initializer = LegalKnowledgeInitializer()
        
        if initializer.initialize():
            logger.info("✅ Legal knowledge base ready!")
            os.environ["HR_LEGAL_ENABLED"] = "true"
            os.environ["HR_LEGAL_FALLBACK_MODE"] = "false"
        else:
            logger.warning("⚠️  Legal knowledge base initialization failed - using fallback mode")
            os.environ["HR_LEGAL_ENABLED"] = "true"
            os.environ["HR_LEGAL_FALLBACK_MODE"] = "true"
            
    except Exception as e:
        logger.error(f"❌ Legal database initialization error: {e}")
        logger.info("🔄 Continuing with fallback mode...")
        os.environ["HR_LEGAL_ENABLED"] = "true"
        os.environ["HR_LEGAL_FALLBACK_MODE"] = "true"
    
    return True

def main():
    """Main deployment setup"""
    
    print("🎯 Railway Deployment Setup")
    print("=" * 50)
    
    try:
        setup_deployment_environment()
        
        # Import and run the main application
        logger.info("🚀 Starting enhanced HR backend...")
        
        # Import the main app
        from app import app
        
        # Get port from environment
        port = int(os.environ.get("PORT", 8000))
        
        logger.info(f"🌐 Starting server on port {port}")
        
        # Run the Flask app
        app.run(
            host="0.0.0.0",
            port=port,
            debug=False
        )
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
