#!/usr/bin/env python3
"""
Check current Railway PostgreSQL database state
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from railway_database import RailwayPostgreSQL
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print('🔍 Checking Railway PostgreSQL Database State...')
    
    try:
        railway_db = RailwayPostgreSQL()
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check existing tables
                print('\n📊 Existing Tables:')
                cursor.execute("""
                    SELECT table_name, table_type 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                
                if not tables:
                    print('  No tables found in database')
                else:
                    for table_name, table_type in tables:
                        print(f'  - {table_name} ({table_type})')
                
                # Check if user_profiles exists and its structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'user_profiles' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                user_profile_columns = cursor.fetchall()
                
                if user_profile_columns:
                    print(f'\n📋 user_profiles table structure ({len(user_profile_columns)} columns):')
                    for col_name, data_type, nullable, default in user_profile_columns:
                        nullable_str = 'NULL' if nullable == 'YES' else 'NOT NULL'
                        default_str = f' DEFAULT {default}' if default else ''
                        print(f'  - {col_name}: {data_type} {nullable_str}{default_str}')
                else:
                    print('\n❌ user_profiles table does not exist')
                
                # Check foreign key constraints
                print('\n🔗 Foreign Key Constraints:')
                cursor.execute("""
                    SELECT 
                        tc.constraint_name,
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name 
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='public'
                """)
                
                fks = cursor.fetchall()
                if fks:
                    for constraint_name, table_name, column_name, foreign_table, foreign_column in fks:
                        print(f'  - {table_name}.{column_name} -> {foreign_table}.{foreign_column}')
                else:
                    print('  No foreign key constraints found')
                
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
