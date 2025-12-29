#!/usr/bin/env python3
"""
Safe Backup System Migration Script
Safely migrates database to include backup system tables and functions

Created: August 3, 2025
Author: Production Engineering Team
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_backup_system_migration():
    """
    Execute backup system database migration safely
    """
    logger.info("🚀 Starting Backup System Database Migration")
    
    try:
        # Get database connection - check multiple environment variable formats
        database_url = (
            os.getenv('DATABASE_URL') or 
            os.getenv('POSTGRES_URL') or 
            os.getenv('DATABASE_PUBLIC_URL')
        )
        
        if not database_url:
            # Try to construct from individual components
            host = os.getenv('PGHOST')
            port = os.getenv('PGPORT', '5432')
            database = os.getenv('PGDATABASE') or os.getenv('POSTGRES_DB')
            user = os.getenv('PGUSER') or os.getenv('POSTGRES_USER')
            password = os.getenv('PGPASSWORD') or os.getenv('POSTGRES_PASSWORD')
            
            if all([host, database, user, password]):
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                logger.info(f"Constructed database URL from individual components")
            else:
                logger.error("❌ Database connection details not found in environment variables")
                logger.error("Required: DATABASE_URL or (PGHOST, PGDATABASE, PGUSER, PGPASSWORD)")
                return False
        
        logger.info("📊 Connecting to Railway PostgreSQL database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Read the backup system schema file
        schema_file = 'migration_scripts/create_backup_system_schema.sql'
        if not os.path.exists(schema_file):
            logger.error(f"❌ Schema file not found: {schema_file}")
            return False
        
        logger.info(f"📖 Reading backup system schema from {schema_file}...")
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute the schema creation
        logger.info("🔨 Creating backup system tables and functions...")
        cursor.execute(schema_sql)
        conn.commit()
        
        # Verify the migration
        logger.info("✅ Verifying backup system migration...")
        verification_queries = [
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'backup_metadata'",
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'system_health_logs'",
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'backup_restore_logs'",
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'system_alerts'",
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'backup_configurations'",
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'performance_metrics'",
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'data_retention_policies'"
        ]
        
        created_tables = []
        for query in verification_queries:
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                created_tables.append(result[0])
        
        logger.info(f"✅ Successfully created {len(created_tables)} backup system tables:")
        for table in created_tables:
            logger.info(f"  - {table}")
        
        # Verify functions
        logger.info("🔍 Verifying backup system functions...")
        cursor.execute("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_name IN ('cleanup_old_records', 'get_backup_health_summary', 'check_and_create_alerts')
            AND routine_type = 'FUNCTION'
        """)
        
        created_functions = [row[0] for row in cursor.fetchall()]
        logger.info(f"✅ Successfully created {len(created_functions)} backup system functions:")
        for func in created_functions:
            logger.info(f"  - {func}()")
        
        # Check default configuration
        cursor.execute("SELECT config_name FROM backup_configurations WHERE is_active = true")
        active_config = cursor.fetchone()
        if active_config:
            logger.info(f"✅ Default backup configuration active: {active_config[0]}")
        
        # Check retention policies
        cursor.execute("SELECT COUNT(*) FROM data_retention_policies WHERE is_active = true")
        policy_count = cursor.fetchone()[0]
        logger.info(f"✅ Data retention policies configured: {policy_count}")
        
        # Log the migration
        cursor.execute("""
            INSERT INTO system_health_logs (health_status, metrics, checked_by)
            VALUES ('healthy', %s, 'migration_script')
        """, (
            '{"migration": "backup_system", "tables_created": ' + str(len(created_tables)) + 
            ', "functions_created": ' + str(len(created_functions)) + '}',
        ))
        conn.commit()
        
        # Close connections
        cursor.close()
        conn.close()
        
        logger.info("🎉 Backup System Migration completed successfully!")
        logger.info("📋 Migration Summary:")
        logger.info(f"  - Tables created: {len(created_tables)}")
        logger.info(f"  - Functions created: {len(created_functions)}")
        logger.info(f"  - Retention policies: {policy_count}")
        logger.info(f"  - Default configuration: {'Active' if active_config else 'Not found'}")
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ Database error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during migration: {e}")
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

def check_backup_system_status():
    """
    Check if backup system is already installed
    """
    try:
        # Get database connection using same logic as main function
        database_url = (
            os.getenv('DATABASE_URL') or 
            os.getenv('POSTGRES_URL') or 
            os.getenv('DATABASE_PUBLIC_URL')
        )
        
        if not database_url:
            # Try to construct from individual components
            host = os.getenv('PGHOST')
            port = os.getenv('PGPORT', '5432')
            database = os.getenv('PGDATABASE') or os.getenv('POSTGRES_DB')
            user = os.getenv('PGUSER') or os.getenv('POSTGRES_USER')
            password = os.getenv('PGPASSWORD') or os.getenv('POSTGRES_PASSWORD')
            
            if all([host, database, user, password]):
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'backup_metadata'
        """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result is not None
        
    except Exception:
        return False

def main():
    """Main migration execution"""
    logger.info("🔍 Checking backup system status...")
    
    if check_backup_system_status():
        logger.info("✅ Backup system tables already exist - migration not required")
        logger.info("Use --force flag to re-run migration if needed")
        return True
    
    logger.info("📋 Backup system not found - proceeding with migration")
    
    # Confirm migration in interactive mode
    if len(sys.argv) > 1 and '--confirm' not in sys.argv:
        logger.info("💡 Add --confirm flag to run migration automatically")
        response = input("Proceed with backup system migration? (y/N): ")
        if response.lower() != 'y':
            logger.info("Migration cancelled by user")
            return False
    
    # Run the migration
    success = run_backup_system_migration()
    
    if success:
        logger.info("✅ Backup system migration completed successfully!")
        logger.info("🚀 You can now use the backup management endpoints:")
        logger.info("  - POST /api/admin/backup/create")
        logger.info("  - GET /api/admin/backup/list")
        logger.info("  - GET /api/admin/backup/health")
        logger.info("  - POST /api/admin/backup/restore")
        logger.info("  - GET /api/admin/backup/alerts")
    else:
        logger.error("❌ Backup system migration failed!")
        logger.error("Please check the error messages above and try again")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
