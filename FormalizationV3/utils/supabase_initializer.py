#!/usr/bin/env python3
"""
Supabase Database Initializer
Ensures Supabase schema matches Railway PostgreSQL for seamless sync
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseInitializer:
    """
    Initialize Supabase database schema to match Railway PostgreSQL
    Handles table creation, column synchronization, and schema compatibility
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.client: Optional[Client] = None
        self.initialization_log = []
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("⚠️ Supabase credentials not found - will run in Railway-only mode")
        
        self.required_schema = self._load_required_schema()
    
    def _load_required_schema(self) -> Dict[str, List[Dict]]:
        """
        Load the required schema to match Railway PostgreSQL
        Based on enhanced_schema_migrator.py schema definition
        """
        return {
            'user_profiles': [
                {'name': 'id', 'type': 'uuid', 'nullable': False, 'default': 'gen_random_uuid()'},
                {'name': 'email', 'type': 'text', 'nullable': False, 'unique': True},
                {'name': 'full_name', 'type': 'text', 'nullable': True},
                {'name': 'access_type', 'type': 'text', 'nullable': False, 'default': "'trial'"},
                {'name': 'created_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'},
                {'name': 'updated_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'}
            ],
            'user_credits': [
                {'name': 'id', 'type': 'uuid', 'nullable': False, 'default': 'gen_random_uuid()'},
                {'name': 'user_id', 'type': 'uuid', 'nullable': False},
                {'name': 'credit_type', 'type': 'text', 'nullable': False},
                {'name': 'credits_available', 'type': 'integer', 'nullable': False, 'default': '0'},
                {'name': 'trial_credits', 'type': 'integer', 'nullable': False, 'default': '0'},
                {'name': 'created_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'},
                {'name': 'updated_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'}
            ],
            'resumes': [
                {'name': 'id', 'type': 'uuid', 'nullable': False, 'default': 'gen_random_uuid()'},
                {'name': 'user_id', 'type': 'uuid', 'nullable': False},
                {'name': 'filename', 'type': 'text', 'nullable': False},
                {'name': 'analysis_results', 'type': 'jsonb', 'nullable': True},  # Critical: Must match Railway
                {'name': 'skills', 'type': 'jsonb', 'nullable': True},  # Critical: Must be jsonb, not text[]
                {'name': 'education', 'type': 'jsonb', 'nullable': True},
                {'name': 'experience', 'type': 'jsonb', 'nullable': True},
                {'name': 'ai_summary', 'type': 'text', 'nullable': True},
                {'name': 'created_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'},
                {'name': 'updated_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'},
                # Additional fields for full compatibility
                {'name': 'candidate_name', 'type': 'text', 'nullable': True},
                {'name': 'candidate_email', 'type': 'text', 'nullable': True},
                {'name': 'candidate_phone', 'type': 'text', 'nullable': True},
                {'name': 'overall_score', 'type': 'integer', 'nullable': True, 'default': '0'},
                {'name': 'technical_score', 'type': 'integer', 'nullable': True, 'default': '0'},
                {'name': 'experience_score', 'type': 'integer', 'nullable': True, 'default': '0'},
                {'name': 'education_score', 'type': 'integer', 'nullable': True, 'default': '0'},
                {'name': 'role_fit_score', 'type': 'integer', 'nullable': True, 'default': '0'},
                {'name': 'experience_years', 'type': 'integer', 'nullable': True, 'default': '0'},
                {'name': 'education_level', 'type': 'text', 'nullable': True},
                {'name': 'job_titles', 'type': 'jsonb', 'nullable': True},
                {'name': 'companies', 'type': 'jsonb', 'nullable': True},
                {'name': 'programming_languages', 'type': 'jsonb', 'nullable': True},
                {'name': 'certifications', 'type': 'jsonb', 'nullable': True},
                {'name': 'tags', 'type': 'jsonb', 'nullable': True},
                {'name': 'ai_feedback', 'type': 'text', 'nullable': True},
                {'name': 'category', 'type': 'text', 'nullable': True, 'default': "'general'"},
                {'name': 'priority', 'type': 'integer', 'nullable': True, 'default': '1'},
                {'name': 'is_shortlisted', 'type': 'boolean', 'nullable': True, 'default': 'false'},
                {'name': 'is_archived', 'type': 'boolean', 'nullable': True, 'default': 'false'},
                {'name': 'notes', 'type': 'text', 'nullable': True},
                {'name': 'similarity_score', 'type': 'real', 'nullable': True, 'default': '0.0'},
                {'name': 'processing_status', 'type': 'text', 'nullable': True, 'default': "'pending'"},
                {'name': 'processing_completed_at', 'type': 'timestamp', 'nullable': True},
                {'name': 'ai_model_used', 'type': 'text', 'nullable': True},
                {'name': 'ai_processing_time', 'type': 'real', 'nullable': True, 'default': '0.0'}
            ],
            'hr_legal_queries': [
                {'name': 'id', 'type': 'uuid', 'nullable': False, 'default': 'gen_random_uuid()'},
                {'name': 'user_id', 'type': 'uuid', 'nullable': False},
                {'name': 'query_text', 'type': 'text', 'nullable': False},
                {'name': 'response_text', 'type': 'text', 'nullable': True},
                {'name': 'status', 'type': 'text', 'nullable': False, 'default': "'pending'"},
                {'name': 'created_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'},
                {'name': 'updated_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'}
            ],
            'user_activity': [
                {'name': 'id', 'type': 'uuid', 'nullable': False, 'default': 'gen_random_uuid()'},
                {'name': 'user_id', 'type': 'uuid', 'nullable': False},
                {'name': 'activity_type', 'type': 'text', 'nullable': False},
                {'name': 'activity_data', 'type': 'jsonb', 'nullable': True},
                {'name': 'created_at', 'type': 'timestamp', 'nullable': False, 'default': 'NOW()'}
            ]
        }
    
    def initialize_client(self) -> bool:
        """Initialize Supabase client"""
        try:
            if not self.supabase_url or not self.supabase_key:
                logger.warning("⚠️ Supabase credentials missing - skipping initialization")
                return False
            
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("✅ Supabase client initialized")
            return True
            
        except Exception as e:
            logger.error(f"💥 Failed to initialize Supabase client: {e}")
            return False
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists in Supabase"""
        try:
            if not self.client:
                return False
            
            # Try to query the table with limit 0 to check existence
            result = self.client.table(table_name).select("*").limit(0).execute()
            return True
            
        except Exception as e:
            logger.debug(f"Table {table_name} does not exist: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> Dict[str, str]:
        """Get existing columns in a Supabase table"""
        try:
            if not self.client:
                return {}
            
            # Use Supabase's built-in system tables to get column info
            result = self.client.rpc('get_table_columns', {'table_name': table_name}).execute()
            
            if result.data:
                return {col['column_name']: col['data_type'] for col in result.data}
            else:
                # Fallback: try to get a sample record to infer columns
                sample = self.client.table(table_name).select("*").limit(1).execute()
                if sample.data:
                    return {col: 'unknown' for col in sample.data[0].keys()}
                
            return {}
            
        except Exception as e:
            logger.debug(f"Could not get columns for {table_name}: {e}")
            return {}
    
    def create_missing_tables_via_sql(self) -> bool:
        """
        Create missing tables using Supabase SQL editor approach
        This generates SQL that can be run manually in Supabase dashboard
        """
        try:
            missing_tables = []
            
            for table_name in self.required_schema.keys():
                if not self.check_table_exists(table_name):
                    missing_tables.append(table_name)
            
            if not missing_tables:
                logger.info("✅ All required tables exist in Supabase")
                return True
            
            # Generate SQL for missing tables
            sql_statements = []
            
            for table_name in missing_tables:
                columns = self.required_schema[table_name]
                column_defs = []
                
                for col in columns:
                    col_def = f"{col['name']} {col['type'].upper()}"
                    if not col.get('nullable', True):
                        col_def += " NOT NULL"
                    if col.get('default'):
                        col_def += f" DEFAULT {col['default']}"
                    if col.get('unique'):
                        col_def += " UNIQUE"
                    column_defs.append(col_def)
                
                # Add primary key
                column_defs.append("PRIMARY KEY (id)")
                
                create_sql = f"""
-- Create table {table_name}
CREATE TABLE IF NOT EXISTS {table_name} (
    {',\n    '.join(column_defs)}
);
"""
                
                # Add indexes
                indexes = self._get_table_indexes(table_name)
                for index_sql in indexes:
                    create_sql += f"\n{index_sql};"
                
                sql_statements.append(create_sql)
            
            # Write SQL to file for manual execution
            sql_file_path = "supabase_schema_setup.sql"
            with open(sql_file_path, 'w') as f:
                f.write("-- Supabase Schema Setup SQL\n")
                f.write("-- Run this in Supabase SQL Editor\n\n")
                f.write("-- Enable necessary extensions\n")
                f.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n\n")
                f.write('\n\n'.join(sql_statements))
                
                # Add RLS policies
                f.write("\n\n-- Row Level Security Policies\n")
                for table_name in missing_tables:
                    f.write(f"""
-- Enable RLS for {table_name}
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;

-- Policy for {table_name}
CREATE POLICY "Users can access their own {table_name}" ON {table_name}
    FOR ALL USING (user_id = auth.uid());
""")
            
            logger.info(f"✅ Generated SQL file: {sql_file_path}")
            logger.info(f"📝 Please run the SQL in Supabase dashboard to create {len(missing_tables)} tables")
            
            self.initialization_log.append(f"Generated SQL for {len(missing_tables)} missing tables")
            return True
            
        except Exception as e:
            logger.error(f"💥 Failed to generate table creation SQL: {e}")
            return False
    
    def _get_table_indexes(self, table_name: str) -> List[str]:
        """Get index creation SQL for table"""
        index_map = {
            'user_profiles': [
                "CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email)",
                "CREATE INDEX IF NOT EXISTS idx_user_profiles_access_type ON user_profiles(access_type)"
            ],
            'user_credits': [
                "CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_credits_type ON user_credits(credit_type)",
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_credits_user_type ON user_credits(user_id, credit_type)"
            ],
            'resumes': [
                "CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_resumes_filename ON resumes(filename)",
                "CREATE INDEX IF NOT EXISTS idx_resumes_analysis_results ON resumes USING GIN(analysis_results)",
                "CREATE INDEX IF NOT EXISTS idx_resumes_skills ON resumes USING GIN(skills)",
                "CREATE INDEX IF NOT EXISTS idx_resumes_overall_score ON resumes(overall_score)",
                "CREATE INDEX IF NOT EXISTS idx_resumes_processing_status ON resumes(processing_status)"
            ],
            'hr_legal_queries': [
                "CREATE INDEX IF NOT EXISTS idx_hr_legal_queries_user_id ON hr_legal_queries(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_hr_legal_queries_status ON hr_legal_queries(status)"
            ],
            'user_activity': [
                "CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type)",
                "CREATE INDEX IF NOT EXISTS idx_user_activity_data ON user_activity USING GIN(activity_data)"
            ]
        }
        
        return index_map.get(table_name, [])
    
    def add_missing_columns_via_sql(self) -> bool:
        """
        Generate SQL to add missing columns to existing tables
        """
        try:
            missing_columns_sql = []
            
            for table_name, required_columns in self.required_schema.items():
                if not self.check_table_exists(table_name):
                    continue  # Table doesn't exist, will be created separately
                
                existing_columns = self.get_table_columns(table_name)
                
                for col in required_columns:
                    col_name = col['name']
                    if col_name not in existing_columns:
                        col_type = col['type']
                        nullable = col.get('nullable', True)
                        default = col.get('default')
                        
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type.upper()}"
                        
                        if not nullable:
                            alter_sql += " NOT NULL"
                        
                        if default:
                            alter_sql += f" DEFAULT {default}"
                        
                        missing_columns_sql.append(alter_sql)
            
            if missing_columns_sql:
                # Append to SQL file
                sql_file_path = "supabase_schema_setup.sql"
                with open(sql_file_path, 'a') as f:
                    f.write("\n\n-- Add Missing Columns\n")
                    for sql in missing_columns_sql:
                        f.write(f"{sql};\n")
                
                logger.info(f"✅ Added {len(missing_columns_sql)} column additions to SQL file")
                self.initialization_log.append(f"Added {len(missing_columns_sql)} missing columns to SQL")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Failed to generate missing columns SQL: {e}")
            return False
    
    def create_default_admin_user(self) -> bool:
        """Create default admin user in Supabase"""
        try:
            if not self.client:
                return False
            
            admin_email = os.getenv('ADMIN_EMAILS', 'admin@bearsystems.co.in').split(',')[0]
            admin_id = 'b8f7c9e6-1234-5678-9abc-def012345678'
            
            # Check if admin user exists
            existing_user = self.client.table('user_profiles').select('*').eq('email', admin_email).execute()
            
            if existing_user.data:
                logger.info(f"✅ Admin user already exists: {admin_email}")
                return True
            
            # Create admin user
            admin_data = {
                'id': admin_id,
                'email': admin_email,
                'full_name': 'System Administrator',
                'access_type': 'enterprise'
            }
            
            user_result = self.client.table('user_profiles').insert(admin_data).execute()
            
            if user_result.data:
                # Create admin credits
                credits_data = {
                    'user_id': admin_id,
                    'credit_type': 'trial',
                    'credits_available': 1000,
                    'trial_credits': 1000
                }
                
                self.client.table('user_credits').insert(credits_data).execute()
                
                logger.info(f"✅ Created admin user in Supabase: {admin_email}")
                self.initialization_log.append(f"Created admin user: {admin_email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"💥 Failed to create admin user in Supabase: {e}")
            return False
    
    def run_comprehensive_initialization(self) -> Dict[str, Any]:
        """
        Run comprehensive Supabase initialization
        Returns detailed results
        """
        start_time = datetime.now()
        logger.info("🚀 Starting Supabase initialization...")
        
        results = {
            'started_at': start_time.isoformat(),
            'supabase_available': False,
            'client_initialized': False,
            'sql_generated': False,
            'admin_created': False,
            'initialization_log': [],
            'success': False,
            'errors': []
        }
        
        try:
            # Step 1: Initialize client
            client_success = self.initialize_client()
            results['client_initialized'] = client_success
            results['supabase_available'] = client_success
            
            if not client_success:
                results['errors'].append("Supabase client initialization failed")
                logger.warning("⚠️ Supabase not available - application will use Railway only")
                results['success'] = True  # Not a failure if Supabase is optional
                return results
            
            # Step 2: Generate SQL for missing tables and columns
            sql_success = self.create_missing_tables_via_sql()
            self.add_missing_columns_via_sql()
            results['sql_generated'] = sql_success
            
            # Step 3: Try to create admin user (if tables exist)
            admin_success = self.create_default_admin_user()
            results['admin_created'] = admin_success
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results.update({
                'completed_at': end_time.isoformat(),
                'duration_seconds': duration,
                'initialization_log': self.initialization_log,
                'success': True
            })
            
            logger.info(f"✅ Supabase initialization completed in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"💥 Supabase initialization failed: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        return results

def initialize_supabase() -> Dict[str, Any]:
    """
    Global function to initialize Supabase
    """
    initializer = SupabaseInitializer()
    return initializer.run_comprehensive_initialization()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    results = initialize_supabase()
    
    print("\n" + "="*80)
    print("🚀 SUPABASE INITIALIZATION RESULTS")
    print("="*80)
    print(f"Success: {'✅ YES' if results['success'] else '❌ NO'}")
    print(f"Supabase Available: {'✅ YES' if results['supabase_available'] else '❌ NO'}")
    print(f"SQL Generated: {'✅ YES' if results['sql_generated'] else '❌ NO'}")
    
    if results['initialization_log']:
        print("\n📝 Initialization Log:")
        for log_entry in results['initialization_log']:
            print(f"   {log_entry}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"   {error}")
