#!/usr/bin/env python3
"""
Legal Documents Processing Script for Railway Deployment
Processes all legal documents during deployment and builds the RAG knowledge base
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.services.document_processor import DocumentProcessor
from app.services.legal_rag_service import LegalRAGService
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_legal_documents():
    """Main function to process legal documents during deployment"""
    
    logger.info("🚀 Starting Legal Knowledge Base Setup for Railway Deployment")
    
    try:
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            logger.info("📁 Checking for legal documents...")
            
            # Check if legal documents directory exists
            legal_docs_path = Config.LEGAL_DOCS_PATH
            if not os.path.exists(legal_docs_path):
                logger.warning(f"Legal documents directory not found: {legal_docs_path}")
                logger.info("Creating legal documents directory...")
                os.makedirs(legal_docs_path, exist_ok=True)
                
                # Create a sample document if none exist
                sample_doc_path = os.path.join(legal_docs_path, "sample_hr_law.txt")
                with open(sample_doc_path, 'w', encoding='utf-8') as f:
                    f.write("""Sample HR Legal Document
                    
This is a sample legal document for the HR Legal RAG system.
Replace this with your actual legal documents.

Key HR Legal Areas:
1. Employment Contracts
2. Labor Laws
3. Workplace Safety
4. Anti-Discrimination Policies
5. Employee Benefits

For production use, place your .txt legal documents in the legal_documents/ folder.
""")
                logger.info(f"Created sample document: {sample_doc_path}")
            
            # Count existing .txt files
            txt_files = list(Path(legal_docs_path).glob("*.txt"))
            logger.info(f"Found {len(txt_files)} .txt files to process")
            
            if len(txt_files) == 0:
                logger.warning("No .txt files found for processing")
                return
            
            # Start heartbeat logging for long-running operations
            import threading
            import time
            
            heartbeat_active = True
            
            def heartbeat():
                count = 0
                while heartbeat_active:
                    count += 1
                    logger.info(f"💓 Heartbeat {count}: Legal document processing still active...")
                    time.sleep(30)  # Log every 30 seconds
            
            heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
            heartbeat_thread.start()
            logger.info("💓 Started heartbeat monitoring")
            
            try:
                # Initialize document processor
                logger.info("🤖 Initializing document processor...")
                processor = DocumentProcessor()
                
                logger.info("🔧 About to initialize models - this may take several minutes...")
                logger.info("⏳ Please be patient, downloading embedding models can take 5-10 minutes...")
                await processor.initialize_models()
                logger.info("✅ Document processor models initialized successfully")
                
                # Process all documents
                logger.info("📚 Starting document processing pipeline...")
                result = await processor.process_all_documents(
                    update_type='deployment_build',
                    trigger='railway_deployment'
                )
                logger.info(f"📊 Document processing pipeline completed with result: {result}")
            finally:
                # Stop heartbeat
                heartbeat_active = False
                logger.info("💓 Stopped heartbeat monitoring")
            
            # Log results
            if result['status'] == 'completed':
                logger.info(f"✅ Document processing completed successfully!")
                logger.info(f"   📄 Documents processed: {result['processed']}")
                logger.info(f"   🧩 Chunks created: {result['total_chunks']}")
                logger.info(f"   ⏱️  Processing time: {result.get('processing_time', 0):.2f} seconds")
                
                if result.get('failed', 0) > 0:
                    logger.warning(f"   ⚠️  Failed documents: {result['failed']}")
            else:
                logger.error(f"❌ Document processing failed: {result}")
                return False
            
            # Initialize and test RAG service
            logger.info("🧠 Initializing Legal RAG service...")
            rag_service = LegalRAGService()
            await rag_service.initialize()
            
            # Get knowledge base statistics
            stats = await rag_service.get_knowledge_base_stats()
            logger.info(f"📊 Knowledge Base Statistics:")
            logger.info(f"   📚 Total documents: {stats.get('total_documents', 0)}")
            logger.info(f"   ✅ Processed documents: {stats.get('processed_documents', 0)}")
            logger.info(f"   🧩 Total chunks: {stats.get('total_chunks', 0)}")
            logger.info(f"   📈 Processing rate: {stats.get('processing_rate', 0)*100:.1f}%")
            
            # Test query (if documents are processed)
            if stats.get('total_chunks', 0) > 0:
                logger.info("🧪 Running test query...")
                test_result = await rag_service.query_legal_knowledge(
                    query_text="What are the key employment law requirements?",
                    user_id="test-deployment-user"
                )
                
                if test_result.get('status') == 'success':
                    logger.info("✅ Test query successful - RAG system is working!")
                    logger.info(f"   🎯 Confidence: {test_result.get('confidence_score', 0):.3f}")
                    logger.info(f"   📄 Sources: {len(test_result.get('source_documents', []))}")
                else:
                    logger.warning("⚠️  Test query failed - RAG system may have issues")
            
            logger.info("🎉 Legal Knowledge Base setup completed successfully!")
            logger.info("🚀 System is ready for legal consultations!")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Legal document processing failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point"""
    try:
        # Check environment
        if not Config.LEGAL_RAG_ENABLED:
            logger.info("Legal RAG is disabled - skipping document processing")
            return True
        
        # Run the async processing
        success = asyncio.run(process_legal_documents())
        
        if success:
            logger.info("✅ Legal Knowledge Base setup completed successfully!")
            return True
        else:
            logger.error("❌ Legal Knowledge Base setup failed!")
            return False
            
    except KeyboardInterrupt:
        logger.info("⏹️  Processing interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
