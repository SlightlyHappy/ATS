#!/usr/bin/env python3
"""
Quick database debug script for Railway deployment troubleshooting.
Run this to check database connectivity and schema status.
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from urllib.parse import urlparse

def debug_database():
    print("🔍 Railway Database Debug")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Variables:")
    db_vars = [
        "DATABASE_URL", "DATABASE_INTERNAL_URL", "DATABASE_PUBLIC_URL", "DATABASE_PRIMARY_NODE",
        "PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE",
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"
    ]
    
    for var in db_vars:
        value = os.getenv(var)
        if value:
            if "password" in var.lower() or "PASSWORD" in var:
                masked = value[:8] + "***" if len(value) > 8 else "***"
                print(f"   {var}={masked}")
            else:
                print(f"   {var}={value}")
        else:
            print(f"   {var}=<not set>")
    
    # Try to determine DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Try to build from components
        pghost = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
        pgport = os.getenv("PGPORT") or os.getenv("POSTGRES_PORT")
        pguser = os.getenv("PGUSER") or os.getenv("POSTGRES_USER") or "postgres"
        pgpassword = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD") or ""
        pgdb = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB") or "railway"
        
        if pghost and pgport and pgpassword:
            database_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdb}"
        elif os.getenv("DATABASE_INTERNAL_URL"):
            database_url = os.getenv("DATABASE_INTERNAL_URL")
        elif os.getenv("DATABASE_PRIMARY_NODE"):
            database_url = os.getenv("DATABASE_PRIMARY_NODE")
        elif os.getenv("DATABASE_PUBLIC_URL"):
            database_url = os.getenv("DATABASE_PUBLIC_URL")
    
    if not database_url:
        print("❌ No DATABASE_URL found!")
        return False
    
    # Parse URL for display
    parsed = urlparse(database_url)
    print(f"\n🎯 Using DATABASE_URL:")
    print(f"   Host: {parsed.hostname}")
    print(f"   Port: {parsed.port}")
    print(f"   Database: {parsed.path.lstrip('/')}")
    print(f"   User: {parsed.username}")
    print(f"   Password: {'***' if parsed.password else '<none>'}")
    
    # Test connection
    print(f"\n🔗 Testing Database Connection...")
    try:
        engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 15})
        with engine.connect() as conn:
            # Basic connectivity test
            result = conn.execute(text("SELECT 1 as test"))
            test_result = result.scalar()
            if test_result == 1:
                print("   ✅ Basic connectivity: OK")
            else:
                print("   ❌ Basic connectivity: Failed")
                return False
            
            # Check PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            pg_version = result.scalar()
            print(f"   📊 PostgreSQL Version: {pg_version}")
            
            # Check current database
            result = conn.execute(text("SELECT current_database()"))
            current_db = result.scalar()
            print(f"   🗄️  Current Database: {current_db}")
            
            # Check if we have create privileges
            try:
                conn.execute(text("CREATE TABLE IF NOT EXISTS test_table_debug_temp (id INTEGER)"))
                conn.execute(text("DROP TABLE IF EXISTS test_table_debug_temp"))
                print("   ✅ Create/Drop privileges: OK")
            except Exception as e:
                print(f"   ❌ Create/Drop privileges: Failed ({str(e)[:50]}...)")
            
            # Check for pgvector extension
            try:
                result = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
                if result.fetchone():
                    print("   ✅ pgvector extension: Installed")
                else:
                    print("   ⚠️  pgvector extension: Not installed")
                    try:
                        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                        print("   ✅ pgvector extension: Successfully created")
                    except Exception as e:
                        print(f"   ❌ pgvector extension: Cannot create ({str(e)[:50]}...)")
            except Exception as e:
                print(f"   ❌ pgvector check failed: {str(e)[:50]}...")
            
            # Check for alembic_version table
            inspector = inspect(engine)
            if inspector.has_table("alembic_version"):
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                print(f"   ✅ Alembic version table: Exists (version: {version})")
            else:
                print("   ⚠️  Alembic version table: Does not exist (fresh database)")
            
            # List existing tables
            tables = inspector.get_table_names()
            print(f"   📋 Existing tables ({len(tables)}): {', '.join(tables[:10])}")
            if len(tables) > 10:
                print(f"      ... and {len(tables) - 10} more")
        
        engine.dispose()
        print("\n✅ Database debug completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = debug_database()
    sys.exit(0 if success else 1)
