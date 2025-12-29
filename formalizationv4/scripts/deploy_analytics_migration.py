#!/usr/bin/env python3
"""
Production-ready database migration script for analytics tables.
Safe deployment with rollback support.
"""
import os
import sys
import time
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AnalyticsMigration:
    """Safe analytics database migration with rollback support."""
    
    def __init__(self, database_url=None):
        """Initialize migration with database connection."""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.engine = create_engine(self.database_url)
        
    def check_connection(self):
        """Verify database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def table_exists(self, table_name):
        """Check if table exists."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
                ), {"table_name": table_name})
                return result.scalar()
        except Exception as e:
            logger.error(f"Error checking table {table_name}: {e}")
            return False
    
    def create_performance_metrics_table(self):
        """Create performance_metrics table."""
        sql = """
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id BIGSERIAL PRIMARY KEY,
            metric_type VARCHAR(50) NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            component VARCHAR(100) NOT NULL,
            value DECIMAL(10,4) NOT NULL,
            unit VARCHAR(20) NOT NULL,
            warning_threshold DECIMAL(10,4),
            critical_threshold DECIMAL(10,4),
            tags JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_performance_metrics_type 
            ON performance_metrics(metric_type);
        CREATE INDEX IF NOT EXISTS idx_performance_metrics_component 
            ON performance_metrics(component);
        CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp 
            ON performance_metrics(timestamp);
        CREATE INDEX IF NOT EXISTS idx_performance_metrics_tags 
            ON performance_metrics USING GIN(tags);
        """
        return sql
    
    def create_usage_insights_table(self):
        """Create usage_insights table."""
        sql = """
        CREATE TABLE IF NOT EXISTS usage_insights (
            id BIGSERIAL PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            event_category VARCHAR(50) NOT NULL,
            event_action VARCHAR(100) NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            session_id VARCHAR(100),
            resource_type VARCHAR(50),
            resource_id VARCHAR(100),
            duration_seconds DECIMAL(8,3),
            success BOOLEAN DEFAULT TRUE,
            error_code VARCHAR(50),
            error_message TEXT,
            metadata JSONB DEFAULT '{}',
            ip_address INET,
            user_agent TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_usage_insights_user_id 
            ON usage_insights(user_id);
        CREATE INDEX IF NOT EXISTS idx_usage_insights_event_type 
            ON usage_insights(event_type);
        CREATE INDEX IF NOT EXISTS idx_usage_insights_timestamp 
            ON usage_insights(timestamp);
        CREATE INDEX IF NOT EXISTS idx_usage_insights_success 
            ON usage_insights(success);
        CREATE INDEX IF NOT EXISTS idx_usage_insights_metadata 
            ON usage_insights USING GIN(metadata);
        """
        return sql
    
    def create_error_tracking_table(self):
        """Create error_tracking table."""
        sql = """
        CREATE TABLE IF NOT EXISTS error_tracking (
            id BIGSERIAL PRIMARY KEY,
            error_type VARCHAR(100) NOT NULL,
            error_category VARCHAR(50) NOT NULL,
            error_code VARCHAR(50),
            error_message TEXT NOT NULL,
            stack_trace TEXT,
            severity VARCHAR(20) DEFAULT 'medium',
            component VARCHAR(100),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            session_id VARCHAR(100),
            request_id VARCHAR(100),
            occurrence_count INTEGER DEFAULT 1,
            first_occurrence TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_occurrence TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP WITH TIME ZONE,
            resolution_notes TEXT,
            metadata JSONB DEFAULT '{}',
            context JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_error_tracking_type 
            ON error_tracking(error_type);
        CREATE INDEX IF NOT EXISTS idx_error_tracking_category 
            ON error_tracking(error_category);
        CREATE INDEX IF NOT EXISTS idx_error_tracking_severity 
            ON error_tracking(severity);
        CREATE INDEX IF NOT EXISTS idx_error_tracking_resolved 
            ON error_tracking(resolved_at);
        CREATE INDEX IF NOT EXISTS idx_error_tracking_user_id 
            ON error_tracking(user_id);
        CREATE INDEX IF NOT EXISTS idx_error_tracking_first_occurrence 
            ON error_tracking(first_occurrence);
        """
        return sql
    
    def create_system_alerts_table(self):
        """Create system_alerts table."""
        sql = """
        CREATE TABLE IF NOT EXISTS system_alerts (
            id BIGSERIAL PRIMARY KEY,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            component VARCHAR(100),
            metric_name VARCHAR(100),
            threshold_value DECIMAL(10,4),
            actual_value DECIMAL(10,4),
            acknowledged BOOLEAN DEFAULT FALSE,
            acknowledged_by UUID REFERENCES users(id) ON DELETE SET NULL,
            acknowledged_at TIMESTAMP WITH TIME ZONE,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMP WITH TIME ZONE,
            resolution_notes TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_system_alerts_type 
            ON system_alerts(alert_type);
        CREATE INDEX IF NOT EXISTS idx_system_alerts_severity 
            ON system_alerts(severity);
        CREATE INDEX IF NOT EXISTS idx_system_alerts_acknowledged 
            ON system_alerts(acknowledged);
        CREATE INDEX IF NOT EXISTS idx_system_alerts_resolved 
            ON system_alerts(resolved);
        CREATE INDEX IF NOT EXISTS idx_system_alerts_created_at 
            ON system_alerts(created_at);
        """
        return sql
    
    def create_analytics_snapshots_table(self):
        """Create analytics_snapshots table."""
        sql = """
        CREATE TABLE IF NOT EXISTS analytics_snapshots (
            id BIGSERIAL PRIMARY KEY,
            snapshot_type VARCHAR(50) NOT NULL,
            time_period VARCHAR(20) NOT NULL,
            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
            end_time TIMESTAMP WITH TIME ZONE NOT NULL,
            metrics JSONB NOT NULL DEFAULT '{}',
            summary JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_type 
            ON analytics_snapshots(snapshot_type);
        CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_period 
            ON analytics_snapshots(time_period);
        CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_start_time 
            ON analytics_snapshots(start_time);
        CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_end_time 
            ON analytics_snapshots(end_time);
        """
        return sql
    
    def execute_migration(self):
        """Execute the full migration."""
        if not self.check_connection():
            logger.error("Cannot proceed without database connection")
            return False
        
        tables = [
            ('performance_metrics', self.create_performance_metrics_table()),
            ('usage_insights', self.create_usage_insights_table()),
            ('error_tracking', self.create_error_tracking_table()),
            ('system_alerts', self.create_system_alerts_table()),
            ('analytics_snapshots', self.create_analytics_snapshots_table())
        ]
        
        try:
            with self.engine.begin() as conn:
                for table_name, sql in tables:
                    logger.info(f"Creating table: {table_name}")
                    conn.execute(text(sql))
                    logger.info(f"Successfully created table: {table_name}")
            
            logger.info("All analytics tables created successfully")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def verify_migration(self):
        """Verify that all tables were created correctly."""
        required_tables = [
            'performance_metrics',
            'usage_insights', 
            'error_tracking',
            'system_alerts',
            'analytics_snapshots'
        ]
        
        for table in required_tables:
            if not self.table_exists(table):
                logger.error(f"Table {table} was not created")
                return False
            logger.info(f"Table {table} verified")
        
        logger.info("Migration verification successful")
        return True
    
    def rollback_migration(self):
        """Rollback the migration (drop tables)."""
        tables = [
            'analytics_snapshots',
            'system_alerts',
            'error_tracking',
            'usage_insights',
            'performance_metrics'
        ]
        
        try:
            with self.engine.begin() as conn:
                for table in tables:
                    logger.info(f"Dropping table: {table}")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            logger.info("Migration rollback completed")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Rollback failed: {e}")
            return False

def main():
    """Main migration script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analytics Database Migration')
    parser.add_argument('--action', choices=['migrate', 'verify', 'rollback'], 
                       default='migrate', help='Migration action to perform')
    parser.add_argument('--database-url', help='Database URL (optional)')
    
    args = parser.parse_args()
    
    try:
        migration = AnalyticsMigration(args.database_url)
        
        if args.action == 'migrate':
            logger.info("Starting analytics database migration...")
            if migration.execute_migration():
                if migration.verify_migration():
                    logger.info("Migration completed successfully!")
                    sys.exit(0)
                else:
                    logger.error("Migration verification failed")
                    sys.exit(1)
            else:
                logger.error("Migration failed")
                sys.exit(1)
        
        elif args.action == 'verify':
            logger.info("Verifying migration...")
            if migration.verify_migration():
                logger.info("Verification successful!")
                sys.exit(0)
            else:
                logger.error("Verification failed")
                sys.exit(1)
        
        elif args.action == 'rollback':
            logger.info("Rolling back migration...")
            if migration.rollback_migration():
                logger.info("Rollback completed successfully!")
                sys.exit(0)
            else:
                logger.error("Rollback failed")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
