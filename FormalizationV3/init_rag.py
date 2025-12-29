#!/usr/bin/env python3
"""
RAG System Initialization Script for Railway Deployment
Gracefully handles initialization failures and provides fallback
"""

import sys
import os
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the builder directory to Python path
sys.path.append('/app/builder')

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer
        logger.info("All ML dependencies are available")
        return True
    except ImportError as e:
        logger.warning(f"Missing ML dependencies: {e}")
        return False

def initialize_rag_system():
    """Initialize RAG system with graceful error handling and lazy loading"""
    try:
        logger.info("Attempting to initialize RAG system with lazy loading...")
        
        # Check dependencies first
        if not check_dependencies():
            logger.warning("ML dependencies not available, RAG will run in fallback mode")
            return True  # Still successful, just in fallback mode
        
        # Import RAG system (this will initialize in lazy mode)
        from modules.hr_legal_rag.hr_legal_rag import HRLegalRAGSystem
        
        # Create RAG system instance with lazy loading
        logger.info("Creating RAG system instance with lazy loading...")
        rag = HRLegalRAGSystem()  # This now uses lazy loading
        
        # Perform health check (doesn't trigger model loading)
        logger.info("Performing health check...")
        health = rag.health_check()
        logger.info(f"RAG system initialized: {health.get('system_status', 'unknown')}")
        
        if health.get('system_status') == 'fallback':
            logger.info("RAG system running in fallback mode (expected for missing dependencies)")
        elif health.get('system_status') == 'operational':
            logger.info("RAG system ready for lazy loading of ML capabilities")
        
        # Log lazy loading status
        logger.info(f"Models will be loaded on-demand: lazy_loading_enabled={health.get('lazy_loading_enabled', False)}")
        
        # Log basic stats
        if hasattr(rag, 'document_metadata'):
            logger.info(f"Documents available for indexing: {len(rag.document_metadata)}")
        
        return True
        
    except ImportError as e:
        logger.warning(f"Import error during RAG initialization: {e}")
        logger.info("RAG system will be initialized at runtime in fallback mode")
        return True  # Don't fail the build
        
    except Exception as e:
        logger.error(f"Error during RAG initialization: {e}")
        logger.info("RAG system will be initialized at runtime")
        return True  # Don't fail the build

if __name__ == "__main__":
    logger.info("Starting RAG system pre-build initialization")
    success = initialize_rag_system()
    if success:
        logger.info("RAG pre-build completed successfully")
        sys.exit(0)
    else:
        logger.warning("RAG pre-build failed, continuing with deployment")
        sys.exit(0)  # Don't fail the build, just continue
