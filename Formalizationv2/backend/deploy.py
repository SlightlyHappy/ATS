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
    """Setup environment for Railway deployment without HRlaw folder"""
    
    logger.info("🚀 Setting up Railway deployment environment...")
    
    # Check if HRlaw exists
    hrlaw_path = Path("HRlaw")
    if not hrlaw_path.exists():
        logger.warning("⚠️  HRlaw folder not found - creating fallback structure")
        
        # Create minimal fallback structure
        fallback_path = Path("hr_legal/fallback_data")
        fallback_path.mkdir(parents=True, exist_ok=True)
        
        # Create a notice file
        notice_file = fallback_path / "NOTICE.txt"
        notice_file.write_text("""
HR LEGAL SYSTEM - FALLBACK MODE

The full legal knowledge base (HRlaw folder) is not available in this deployment.
The system will operate in fallback mode with basic legal assistance.

To enable full legal capabilities:
1. Ensure the HRlaw folder with legal documents is available
2. The system will automatically detect and use the full knowledge base

Current status: Basic legal assistance available
Full legal database: Not available
        """)
        
        logger.info("✅ Fallback environment created")
    else:
        logger.info("✅ HRlaw folder found - full legal system available")
    
    # Set environment variable for HR Legal system
    os.environ["HR_LEGAL_FALLBACK_MODE"] = "true" if not hrlaw_path.exists() else "false"
    
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
