#!/usr/bin/env python3
"""
Railway Production Startup Script
Enhanced HR Resume Screening Backend with Enterprise Features
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available"""
    required_packages = [
        'flask', 'flask_cors', 'flask_limiter', 'gunicorn',
        'supabase', 'requests', 'numpy', 'pandas',
        'sentence_transformers', 'faiss', 'openai', 
        'google.generativeai', 'anthropic', 'together'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'faiss':
                import faiss
            elif package == 'google.generativeai':
                import google.generativeai
            else:
                __import__(package.replace('_', '.'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.error("Please install missing packages with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required dependencies are available")
    return True

def initialize_directories():
    """Create necessary directories for Railway deployment"""
    directories = [
        '/tmp/uploads',
        '/tmp/processed', 
        '/tmp/logs',
        'hr_legal/vector_db',
        'HRlaw'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directory created/verified: {directory}")

def verify_environment():
    """Verify critical environment variables"""
    critical_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work properly")
    else:
        logger.info("✅ All critical environment variables are set")
    
    # Log AI provider configuration
    ai_providers = ['OLLAMA_URL', 'OPENAI_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY', 'TOGETHER_API_KEY']
    available_providers = [var for var in ai_providers if os.getenv(var)]
    
    if available_providers:
        logger.info(f"✅ Available AI providers: {len(available_providers)}/5")
    else:
        logger.warning("⚠️ No AI provider API keys configured")

def main():
    """Main startup function"""
    logger.info("🚀 Starting Enhanced HR Resume Screening Backend")
    logger.info("=" * 60)
    
    # Environment info
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"Port: {os.getenv('PORT', '8000')}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize directories
    initialize_directories()
    
    # Verify environment
    verify_environment()
    
    # Import and start the Flask app
    try:
        logger.info("🔧 Loading application modules...")
        from app import app
        
        logger.info("✅ Application modules loaded successfully")
        logger.info("🌟 Enhanced features available:")
        logger.info("   - Multi-provider AI system")
        logger.info("   - HR Legal RAG engine")
        logger.info("   - Market-based scoring")
        logger.info("   - Email template system")
        logger.info("   - Enhanced admin dashboard")
        logger.info("=" * 60)
        
        # Start the application
        port = int(os.getenv('PORT', 8000))
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False  # Always False in production
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
