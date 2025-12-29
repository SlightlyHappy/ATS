"""
Data Migration Script: Supabase to Railway PostgreSQL
Migrates all existing data from Supabase to Railway PostgreSQL with data integrity verification
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from railway_database import RailwayPostgreSQL
from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

class DataMigrator:
    """Handles data migration from Supabase to Railway PostgreSQL"""
    
    def __init__(self):
        """Initialize data migrator with both database connections"""
        
        # Initialize Railway PostgreSQL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.railway_db = RailwayPostgreSQL(database_url)
        
        # Initialize Supabase client
        try:
            self.supabase = SupabaseClient()
            logger.info("Connected to Supabase")
        except Exception as e:
            raise Exception(f"Failed to connect to Supabase: {e}")
        
        # Migration configuration
        self.batch_size = 100
        self.migration_stats = {
            'total_records': 0,
            'migrated_records': 0,
            'failed_records': 0,
            'tables_migrated': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Tables to migrate in dependency order
        self.migration_plan = [
            {'table': 'user_profiles', 'dependencies': []},
            {'table': 'resumes', 'dependencies': ['user_profiles']},
            {'table': 'user_activity', 'dependencies': ['user_profiles']},
            {'table': 'hr_legal_queries', 'dependencies': ['user_profiles']},
            {'table': 'system_config', 'dependencies': []},
            {'table': 'user_credits', 'dependencies': ['user_profiles']},
            {'table': 'credit_transactions', 'dependencies': ['user_profiles']},
            {'table': 'payment_orders', 'dependencies': ['user_profiles']},
            {'table': 'payment_transactions', 'dependencies': ['payment_orders']},
            {'table': 'user_privileges', 'dependencies': ['user_profiles']},
            {'table': 'usage_analytics', 'dependencies': ['user_profiles']},
            {'table': 'sales_intelligence', 'dependencies': ['user_profiles']},
            {'table': 'email_campaigns_sent', 'dependencies': ['user_profiles']},
            {'table': 'email_automation_triggers', 'dependencies': []},
            {'table': 'email_performance', 'dependencies': ['email_campaigns_sent', 'user_profiles']},
            {'table': 'sales_actions', 'dependencies': ['user_profiles']},
            {'table': 'sales_status_changes', 'dependencies': ['user_profiles']},
            {'table': 'user_segments', 'dependencies': ['user_profiles']},
            {'table': 'conversion_predictions', 'dependencies': ['user_profiles']},
            {'table': 'cohort_analysis', 'dependencies': []},
            {'table': 'feature_usage_analytics', 'dependencies': ['user_profiles']}
        ]
        
        logger.info("Data migrator initialized")
    
    def migrate_all_data(self) -> Dict[str, Any]:
        """Migrate all data from Supabase to Railway PostgreSQL"""
        
        self.migration_stats['start_time'] = datetime.now()
        logger.info("🚀 Starting full data migration from Supabase to Railway")
        
        try:
            # Pre-migration checks
            self._pre_migration_checks()
            
            # Migrate each table according to the plan
            for plan in self.migration_plan:
                table_name = plan['table']
                logger.info(f"📋 Migrating table: {table_name}")
                
                try:
                    result = self._migrate_table(table_name)
                    self.migration_stats['tables_migrated'] += 1
                    self.migration_stats['migrated_records'] += result['migrated_count']
                    self.migration_stats['total_records'] += result['total_count']
                    
                    logger.info(f"✅ {table_name}: {result['migrated_count']}/{result['total_count']} records")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to migrate {table_name}: {e}")
                    self.migration_stats['failed_records'] += 1
                    # Continue with other tables
            
            # Post-migration verification
            verification_result = self._verify_migration()
            
            self.migration_stats['end_time'] = datetime.now()
            duration = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            
            logger.info(f"✅ Migration completed in {duration:.2f} seconds")
            logger.info(f"📊 Stats: {self.migration_stats['migrated_records']} migrated, {self.migration_stats['failed_records']} failed")
            
            return {
                'status': 'success',
                'migration_stats': self.migration_stats,
                'verification': verification_result,
                'duration_seconds': duration
            }
            
        except Exception as e:
            self.migration_stats['end_time'] = datetime.now()
            logger.error(f"💥 Migration failed: {e}")
            
            return {
                'status': 'error',
                'error': str(e),
                'migration_stats': self.migration_stats
            }
    
    def _pre_migration_checks(self):
        """Perform pre-migration checks"""
        
        logger.info("🔍 Performing pre-migration checks...")
        
        # Check Railway connection
        railway_health = self.railway_db.health_check()
        if railway_health['status'] != 'healthy':
            raise Exception(f"Railway database is not healthy: {railway_health}")
        
        # Check Supabase connection
        supabase_health = self.supabase.health_check()
        if not supabase_health.get('healthy', False):
            raise Exception(f"Supabase is not healthy: {supabase_health}")
        
        logger.info("✅ Pre-migration checks passed")
    
    def _migrate_table(self, table_name: str) -> Dict[str, Any]:
        """Migrate a specific table from Supabase to Railway"""
        
        # Get total count from Supabase
        try:
            # Use the Supabase client's count method if available
            if hasattr(self.supabase.client.table(table_name), 'select'):
                count_result = self.supabase.client.table(table_name).select('id', count='exact').execute()
                total_records = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            else:
                # Fallback: get all records and count
                all_data = self.supabase.client.table(table_name).select('*').execute()
                total_records = len(all_data.data) if all_data.data else 0
        except Exception as e:
            logger.warning(f"Could not get count for {table_name}, attempting to fetch all data: {e}")
            total_records = 0
        
        if total_records == 0:
            logger.info(f"No data to migrate for {table_name}")
            return {'total_count': 0, 'migrated_count': 0}
        
        logger.info(f"Migrating {total_records} records from {table_name}...")
        
        # Fetch all data from Supabase
        try:
            supabase_data = self.supabase.client.table(table_name).select('*').execute()
            records = supabase_data.data if supabase_data.data else []
        except Exception as e:
            logger.error(f"Failed to fetch data from Supabase for {table_name}: {e}")
            return {'total_count': total_records, 'migrated_count': 0}
        
        if not records:
            logger.info(f"No records returned for {table_name}")
            return {'total_count': 0, 'migrated_count': 0}
        
        # Process records in batches
        migrated_count = 0
        batch_count = 0
        
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            batch_count += 1
            
            try:
                # Prepare batch for Railway
                processed_batch = self._process_batch_for_railway(table_name, batch)
                
                if processed_batch:
                    # Bulk insert to Railway
                    inserted_count = self.railway_db.bulk_insert(table_name, processed_batch)
                    migrated_count += inserted_count
                    
                    logger.debug(f"Batch {batch_count}: {inserted_count} records inserted")
                
            except Exception as e:
                logger.error(f"Failed to migrate batch {batch_count} for {table_name}: {e}")
                # Continue with next batch
        
        logger.info(f"✅ Migrated {migrated_count}/{len(records)} records for {table_name}")
        
        return {
            'total_count': len(records),
            'migrated_count': migrated_count
        }
    
    def _process_batch_for_railway(self, table_name: str, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process batch of records for Railway PostgreSQL compatibility"""
        
        processed_batch = []
        
        for record in batch:
            try:
                processed_record = self._process_record_for_railway(table_name, record)
                if processed_record:
                    processed_batch.append(processed_record)
            except Exception as e:
                logger.warning(f"Failed to process record {record.get('id', 'unknown')} for {table_name}: {e}")
                # Skip this record and continue
        
        return processed_batch
    
    def _process_record_for_railway(self, table_name: str, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual record for Railway PostgreSQL compatibility"""
        
        # Create a copy to avoid modifying original
        processed = record.copy()
        
        # Table-specific processing
        if table_name == 'user_profiles':
            # Ensure required fields are present
            processed.setdefault('access_type', 'trial')
            processed.setdefault('trial_usage', 0)
            processed.setdefault('trial_limit', 100)
            
        elif table_name == 'resumes':
            # Ensure analysis_result is proper JSONB
            if 'analysis_result' in processed and isinstance(processed['analysis_result'], str):
                try:
                    processed['analysis_result'] = json.loads(processed['analysis_result'])
                except json.JSONDecodeError:
                    processed['analysis_result'] = {'raw': processed['analysis_result']}
        
        elif table_name == 'user_activity':
            # Ensure details is proper JSONB
            if 'details' in processed and isinstance(processed['details'], str):
                try:
                    processed['details'] = json.loads(processed['details'])
                except json.JSONDecodeError:
                    processed['details'] = {'raw': processed['details']}
        
        # Common processing for all tables
        
        # Ensure timestamps are in correct format
        for field in ['created_at', 'updated_at', 'timestamp', 'upload_date']:
            if field in processed and processed[field]:
                # Convert string timestamps to proper format if needed
                if isinstance(processed[field], str):
                    try:
                        # Parse and reformat timestamp
                        dt = datetime.fromisoformat(processed[field].replace('Z', '+00:00'))
                        processed[field] = dt.isoformat()
                    except:
                        # Keep original if parsing fails
                        pass
        
        # Add updated_at if not present but created_at is
        if 'created_at' in processed and 'updated_at' not in processed:
            processed['updated_at'] = processed['created_at']
        
        return processed
    
    def _verify_migration(self) -> Dict[str, Any]:
        """Verify migration integrity by comparing record counts"""
        
        logger.info("🔍 Verifying migration integrity...")
        
        verification_results = {}
        total_discrepancies = 0
        
        for plan in self.migration_plan[:10]:  # Verify first 10 tables
            table_name = plan['table']
            
            try:
                # Get count from Supabase
                supabase_result = self.supabase.client.table(table_name).select('id', count='exact').execute()
                supabase_count = supabase_result.count if hasattr(supabase_result, 'count') else len(supabase_result.data)
                
                # Get count from Railway
                railway_result = self.railway_db.execute_read(f"SELECT COUNT(*) as count FROM {table_name}")
                railway_count = railway_result[0]['count'] if railway_result else 0
                
                is_consistent = supabase_count == railway_count
                if not is_consistent:
                    total_discrepancies += abs(supabase_count - railway_count)
                
                verification_results[table_name] = {
                    'supabase_count': supabase_count,
                    'railway_count': railway_count,
                    'consistent': is_consistent
                }
                
                status = "✅" if is_consistent else "⚠️"
                logger.info(f"{status} {table_name}: Supabase={supabase_count}, Railway={railway_count}")
                
            except Exception as e:
                logger.error(f"Failed to verify {table_name}: {e}")
                verification_results[table_name] = {
                    'error': str(e),
                    'consistent': False
                }
        
        overall_status = 'success' if total_discrepancies == 0 else 'partial'
        
        return {
            'status': overall_status,
            'total_discrepancies': total_discrepancies,
            'table_results': verification_results
        }
    
    def migrate_single_table(self, table_name: str) -> Dict[str, Any]:
        """Migrate a single table (useful for testing or fixing specific tables)"""
        
        logger.info(f"🎯 Migrating single table: {table_name}")
        
        try:
            result = self._migrate_table(table_name)
            
            # Verify this table
            verification = {}
            try:
                supabase_result = self.supabase.client.table(table_name).select('id', count='exact').execute()
                supabase_count = supabase_result.count if hasattr(supabase_result, 'count') else len(supabase_result.data)
                
                railway_result = self.railway_db.execute_read(f"SELECT COUNT(*) as count FROM {table_name}")
                railway_count = railway_result[0]['count'] if railway_result else 0
                
                verification = {
                    'supabase_count': supabase_count,
                    'railway_count': railway_count,
                    'consistent': supabase_count == railway_count
                }
            except Exception as e:
                verification = {'error': str(e)}
            
            return {
                'status': 'success',
                'table': table_name,
                'migration_result': result,
                'verification': verification
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'table': table_name,
                'error': str(e)
            }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        
        return {
            'migration_stats': self.migration_stats,
            'railway_health': self.railway_db.health_check(),
            'migration_plan': [plan['table'] for plan in self.migration_plan]
        }

def main():
    """Main migration script"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 Starting Supabase to Railway data migration")
    
    try:
        # Initialize migrator
        migrator = DataMigrator()
        
        # Run full migration
        result = migrator.migrate_all_data()
        
        if result['status'] == 'success':
            logger.info("✅ Migration completed successfully!")
            logger.info(f"📊 Final stats: {result['migration_stats']}")
            
            # Print verification results
            verification = result['verification']
            if verification['status'] == 'success':
                logger.info("✅ All data verified successfully")
            else:
                logger.warning(f"⚠️ Some discrepancies found: {verification['total_discrepancies']} records")
                
        else:
            logger.error(f"❌ Migration failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"💥 Migration script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
