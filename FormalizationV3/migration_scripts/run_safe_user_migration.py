#!/usr/bin/env python3
"""
SAFE Railway PostgreSQL User Schema Migration
Only adds missing essential tables and columns for user endpoints
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from railway_database import RailwayPostgreSQL
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print('🚀 Starting SAFE Railway PostgreSQL User Schema Migration...')
    print('📋 Only adding essential missing pieces for user endpoints')
    
    try:
        railway_db = RailwayPostgreSQL()
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                
                # Enable UUID extension
                print('🔧 Enabling UUID extension...')
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
                
                # ==================================================
                # PHASE 1: USER PROFILE EXTENSIONS (ESSENTIAL)
                # ==================================================
                print('📊 Phase 1: Essential User Profile Extensions...')
                
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'user_profiles' AND table_schema = 'public'
                """)
                existing_columns = [row[0] for row in cursor.fetchall()]
                
                # Only essential columns for user endpoints
                essential_columns = [
                    ('phone', 'VARCHAR(20)'),
                    ('avatar_url', 'TEXT'),
                    ('professional_info', 'JSONB'),  
                    ('preferences', 'JSONB'),
                    ('timezone', 'VARCHAR(50) DEFAULT \'UTC\''),
                    ('last_active', 'TIMESTAMP WITH TIME ZONE')
                ]
                
                for column_name, column_type in essential_columns:
                    if column_name not in existing_columns:
                        try:
                            cursor.execute(f"ALTER TABLE user_profiles ADD COLUMN {column_name} {column_type}")
                            print(f'  ✅ Added column: {column_name}')
                        except Exception as e:
                            print(f'  ⚠️  Could not add column {column_name}: {e}')
                    else:
                        print(f'  ⏭️  Column exists: {column_name}')
                
                # ==================================================
                # PHASE 2: USER SESSIONS (ESSENTIAL FOR AUTH)
                # ==================================================
                print('📊 Phase 2: User Sessions Table...')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        session_token VARCHAR(500) UNIQUE NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        ip_address INET,
                        user_agent TEXT,
                        is_active BOOLEAN DEFAULT true,
                        device_fingerprint VARCHAR(255),
                        revoked_at TIMESTAMP WITH TIME ZONE
                    )
                ''')
                
                session_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active)'
                ]
                
                for index in session_indexes:
                    try:
                        cursor.execute(index)
                    except Exception as e:
                        print(f'  ⚠️  Could not create session index: {e}')
                
                # ==================================================
                # PHASE 3: USER SUBSCRIPTIONS (ESSENTIAL FOR PAYMENTS)
                # ==================================================
                print('📊 Phase 3: User Subscriptions Table...')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_subscriptions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        plan_id VARCHAR(100) NOT NULL DEFAULT 'trial',
                        plan_name VARCHAR(255) NOT NULL DEFAULT 'Trial Plan',
                        status VARCHAR(50) DEFAULT 'active',
                        billing_cycle VARCHAR(20) DEFAULT 'monthly',
                        amount DECIMAL(10,2) DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'INR',
                        current_period_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        current_period_end TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days'),
                        monthly_resume_limit INTEGER DEFAULT 100,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(user_id)
                    )
                ''')
                
                subscription_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status)',
                    'CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_id ON user_subscriptions(plan_id)'
                ]
                
                for index in subscription_indexes:
                    try:
                        cursor.execute(index)
                    except Exception as e:
                        print(f'  ⚠️  Could not create subscription index: {e}')
                
                # ==================================================
                # PHASE 4: ENHANCED RESUMES TABLE
                # ==================================================
                print('📊 Phase 4: Enhance Resumes Table...')
                
                # Check existing resume columns
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'resumes' AND table_schema = 'public'
                """)
                resume_columns = [row[0] for row in cursor.fetchall()]
                
                # Essential resume enhancements
                resume_essential_columns = [
                    ('tags', 'TEXT[] DEFAULT \'{}\''),
                    ('category', 'VARCHAR(100) DEFAULT \'general\''),
                    ('is_favorite', 'BOOLEAN DEFAULT false'),
                    ('notes', 'TEXT'),
                    ('visibility', 'VARCHAR(20) DEFAULT \'private\''),
                    ('last_viewed_at', 'TIMESTAMP WITH TIME ZONE')
                ]
                
                for column_name, column_type in resume_essential_columns:
                    if column_name not in resume_columns:
                        try:
                            cursor.execute(f"ALTER TABLE resumes ADD COLUMN {column_name} {column_type}")
                            print(f'  ✅ Added resumes column: {column_name}')
                        except Exception as e:
                            print(f'  ⚠️  Could not add resumes column {column_name}: {e}')
                    else:
                        print(f'  ⏭️  Resume column exists: {column_name}')
                
                # Essential resume indexes
                resume_essential_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_resumes_tags ON resumes USING GIN(tags)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_category ON resumes(category)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_visibility ON resumes(visibility)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_is_favorite ON resumes(is_favorite)'
                ]
                
                for index in resume_essential_indexes:
                    try:
                        cursor.execute(index)
                    except Exception as e:
                        print(f'  ⚠️  Could not create resume index: {e}')
                
                # ==================================================
                # PHASE 5: UPDATE TRIGGERS
                # ==================================================
                print('📊 Phase 5: Essential Update Triggers...')
                
                # Update trigger function
                cursor.execute('''
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                ''')
                
                # Apply to user_subscriptions
                cursor.execute('''
                    DROP TRIGGER IF EXISTS update_user_subscriptions_updated_at ON user_subscriptions;
                    CREATE TRIGGER update_user_subscriptions_updated_at 
                    BEFORE UPDATE ON user_subscriptions 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                ''')
                
                print('  ✅ Created update triggers')
            
            conn.commit()
        
        print('\n🎉 SAFE DATABASE SCHEMA MIGRATION COMPLETED! 🎉')
        print('=' * 60)
        print('✅ Essential user profile extensions added')
        print('✅ User sessions table ready for authentication')
        print('✅ User subscriptions table ready for payment integration')
        print('✅ Resume table enhanced for user management')
        print('✅ Essential indexes and triggers created')
        print('=' * 60)
        print('🚀 Ready for user endpoint implementation!')
        
        # Verify essential tables
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                essential_tables = ['user_profiles', 'user_sessions', 'user_subscriptions', 'resumes']
                print(f'\n📊 Verifying essential tables:')
                
                for table in essential_tables:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_name = '{table}' AND table_schema = 'public'
                    """)
                    exists = cursor.fetchone()[0] > 0
                    status = '✅' if exists else '❌'
                    print(f'  {status} {table}')
        
        return True
        
    except Exception as e:
        print(f'❌ Migration failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
