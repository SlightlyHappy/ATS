#!/usr/bin/env python3
"""
Migration management script for Railway deployment.
Handles database schema creation and migrations automatically.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages database migrations for Railway deployment."""
    
    def __init__(self):
        self.app = None
        self.db = None
        
    def setup_app_context(self):
        """Setup Flask app context for migrations."""
        try:
            from app import create_app, db
            self.app = create_app()
            self.db = db
            return True
        except Exception as e:
            logger.error(f"Failed to setup app context: {str(e)}")
            return False
    
    def run_migrations(self):
        """Run database migrations with comprehensive error handling."""
        if not self.app:
            if not self.setup_app_context():
                return False
                
        with self.app.app_context():
            try:
                # Method 1: Try Flask-Migrate
                return self._try_flask_migrate()
            except Exception as e:
                logger.warning(f"Flask-Migrate failed: {str(e)}")
                
            try:
                # Method 2: Try direct Alembic
                return self._try_alembic_direct()
            except Exception as e:
                logger.warning(f"Direct Alembic failed: {str(e)}")
                
            # Method 3: Fallback to SQLAlchemy create_all
            return self._fallback_create_all()
    
    def _try_flask_migrate(self):
        """Try using Flask-Migrate for migrations."""
        logger.info("🔄 Attempting Flask-Migrate...")
        
        from flask_migrate import upgrade, current, stamp, init, migrate
        
        # Check if migration directory exists
        migration_dir = Path('migrations')
        if not migration_dir.exists():
            logger.info("Initializing migration repository...")
            init()
            
        # Check current migration state
        try:
            current_rev = current()
            logger.info(f"Current migration revision: {current_rev}")
            
            if current_rev is None:
                # No migrations applied, stamp with initial
                logger.info("Stamping database with initial migration...")
                stamp('initial_schema_v1')
            
            # Run upgrade
            logger.info("Running migration upgrade...")
            upgrade()
            logger.info("✅ Flask-Migrate completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Flask-Migrate execution failed: {str(e)}")
            raise
    
    def _try_alembic_direct(self):
        """Try using Alembic directly."""
        logger.info("🔄 Attempting direct Alembic...")
        
        from alembic.config import Config
        from alembic import command
        
        # Setup Alembic config
        alembic_cfg = Config('migrations/alembic.ini')
        alembic_cfg.set_main_option('script_location', 'migrations')
        alembic_cfg.set_main_option('sqlalchemy.url', str(self.db.engine.url))
        
        # Run upgrade
        command.upgrade(alembic_cfg, 'head')
        logger.info("✅ Direct Alembic completed successfully")
        return True
    
    def _fallback_create_all(self):
        """Fallback to SQLAlchemy create_all."""
        logger.info("🔄 Falling back to SQLAlchemy create_all...")
        
        # Import all models to ensure they're registered
        self._import_all_models()
        
        # Create all tables
        self.db.create_all()
        
        # Verify tables were created
        inspector = self.db.inspect(self.db.engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            # Core tables
            'users', 'credit_transactions', 'resumes', 
            'analyses', 'analysis_queue', 'batch_uploads',
            # Admin tables
            'admin_users', 'admin_actions', 'system_configurations', 'admin_notifications',
            # Sales tables
            'leads', 'lead_score_history', 'lead_activities', 'sales_metrics', 'roi_calculations',
            # Candidate tables
            'candidates', 'candidate_activities', 'pipeline_stage_history', 'interviews', 
            'candidate_alerts', 'hiring_analytics',
            # Analytics tables
            'performance_metrics', 'usage_insights', 'error_tracking', 'system_alerts', 'analytics_snapshots',
            # Communication tables
            'hr_templates', 'template_generations', 'compliance_rules',
            # Legal tables
            'legal_documents', 'document_chunks', 'legal_queries', 'knowledge_base_updates'
        ]
        
        missing_tables = []
        for table in expected_tables:
            if table in tables:
                logger.info(f"  ✅ Table '{table}' created successfully")
            else:
                missing_tables.append(table)
                
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
            
        logger.info("✅ SQLAlchemy create_all completed successfully")
        return True
    
    def _import_all_models(self):
        """Import all models to ensure they're registered with SQLAlchemy."""
        try:
            from app.models import (
                User, CreditTransaction, Resume, Analysis, 
                AnalysisQueue, BatchUpload, AdminUser, AdminAction,
                SystemConfiguration, AdminNotification
            )
            logger.info("✅ All core models imported")
            
            # Try to import additional models (don't fail if they don't exist)
            try:
                from app.models import (
                    Lead, LeadScoreHistory, LeadActivity, SalesMetrics, ROICalculation,
                    PerformanceMetric, UsageInsight, ErrorTracking, SystemAlert,
                    Candidate, CandidateActivity, PipelineStageHistory, Interview,
                    HRTemplate, TemplateGeneration, ComplianceRule,
                    LegalDocument, DocumentChunk, LegalQuery, KnowledgeBaseUpdate
                )
                logger.info("✅ Extended models imported")
            except ImportError as e:
                logger.info(f"Some extended models not available: {str(e)}")
                
        except Exception as e:
            logger.warning(f"Error importing models: {str(e)}")
    
    def verify_database_schema(self):
        """Verify the database schema is correct."""
        if not self.app:
            if not self.setup_app_context():
                return False
                
        with self.app.app_context():
            try:
                inspector = self.db.inspect(self.db.engine)
                tables = inspector.get_table_names()
                
                logger.info(f"Found {len(tables)} tables in database:")
                for table in sorted(tables):
                    logger.info(f"  - {table}")
                
                # Test basic connectivity
                result = self.db.session.execute(self.db.text('SELECT 1')).scalar()
                if result == 1:
                    logger.info("✅ Database connectivity verified")
                    return True
                else:
                    logger.error("❌ Database connectivity test failed")
                    return False
                    
            except Exception as e:
                logger.error(f"Database schema verification failed: {str(e)}")
                return False

def main():
    """Main function for migration management."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting Railway Database Migration Manager...")
    
    manager = MigrationManager()
    
    # Run migrations
    if manager.run_migrations():
        print("✅ Database migrations completed successfully!")
        
        # Verify schema
        if manager.verify_database_schema():
            print("✅ Database schema verification passed!")
            return True
        else:
            print("⚠️  Database schema verification had issues")
            return False
    else:
        print("❌ Database migrations failed!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
