"""pgvector recovery migration

Revision ID: 20250810_02
Revises: 20250810_01
Create Date: 2025-08-10

This migration attempts to recover from failed pgvector installations
by trying to add the extension and convert existing text embeddings to vector format.
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import time
import os

# revision identifiers, used by Alembic.
revision = '20250810_02'
down_revision = '20250810_01'
branch_labels = None
depends_on = None


def _attempt_pgvector_recovery():
    """Attempt to install pgvector and convert embedding column if needed."""
    retry_count = int(os.getenv("PGVECTOR_RETRY_COUNT", "5"))
    retry_delay = int(os.getenv("PGVECTOR_RETRY_DELAY", "10"))
    # Default to true for production safety
    skip_on_failure = os.getenv("SKIP_PGVECTOR_ON_FAILURE", "true").lower() == "true"
    
    print("🔄 Attempting pgvector recovery migration...")
    
    conn = op.get_bind()
    
    # Step 0: If server doesn't list pgvector in available extensions, skip early
    try:
        available = bool(conn.execute(sa.text("SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name='vector')")).scalar())
        if not available:
            print("ℹ️  pgvector not available on server (pg_available_extensions), skipping recovery")
            return False
    except Exception as e:
        print(f"ℹ️  Could not query pg_available_extensions: {str(e)}")
    
    # Step 1: Check if pgvector extension exists
    try:
        result = conn.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')"))
        has_pgvector = result.scalar()
        
        if has_pgvector:
            print("✅ pgvector extension already installed")
        else:
            print("❌ pgvector extension not found, attempting installation...")
            
            # Attempt to install pgvector with retries
            last_error = None
            for attempt in range(1, retry_count + 1):
                try:
                    print(f"   Attempt {attempt}/{retry_count}: CREATE EXTENSION vector")
                    # Use autocommit to prevent transaction poisoning
                    with op.get_context().autocommit_block():
                        op.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    print("✅ pgvector extension installed successfully")
                    has_pgvector = True
                    break
                except Exception as e:
                    last_error = str(e)
                    print(f"❌ Attempt {attempt}/{retry_count} failed: {last_error}")
                    # Stop retrying if it's the classic not-available error
                    if 'extension "vector" is not available' in last_error:
                        print("ℹ️  Server does not have pgvector installed; will not retry further")
                        break
                    if attempt < retry_count:
                        print(f"⏳ Waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
            
            if not has_pgvector:
                if skip_on_failure:
                    print(f"⚠️  Failed to install pgvector, but SKIP_PGVECTOR_ON_FAILURE=true")
                    print(f"   Continuing with text-based embeddings. Last error: {last_error}")
                    return False
                else:
                    raise Exception(f"Failed to install pgvector after {retry_count} attempts: {last_error}")
    
    except Exception as e:
        print(f"❌ Error checking pgvector status: {str(e)}")
        if skip_on_failure:
            print("⚠️  SKIP_PGVECTOR_ON_FAILURE=true, continuing without vector support")
            return False
        else:
            raise
    
    # Step 2: Check embedding column type and convert if needed
    if has_pgvector:
        try:
            # Check current embedding column type
            result = conn.execute(text("""
                SELECT data_type, udt_name
                FROM information_schema.columns
                WHERE table_name='resume_chunks' AND column_name='embedding'
            """))
            row = result.fetchone()
            
            if row:
                data_type, udt_name = row
                print(f"📊 Current embedding column: data_type={data_type}, udt_name={udt_name}")
                
                if udt_name != 'vector':
                    print("🔄 Converting embedding column from text to vector...")
                    
                    # First, clear any obviously invalid text data to minimize conversion errors
                    try:
                        conn.execute(text("UPDATE resume_chunks SET embedding = NULL WHERE embedding IS NOT NULL AND embedding !~ '^\\[.*\\]$'"))
                        conn.commit()
                    except Exception:
                        pass
                    
                    # Convert column to vector type
                    for attempt in range(1, retry_count + 1):
                        try:
                            print(f"   Attempt {attempt}/{retry_count}: Converting to VECTOR(1024)")
                            with op.get_context().autocommit_block():
                                op.execute(text("ALTER TABLE resume_chunks ALTER COLUMN embedding TYPE VECTOR(1024) USING embedding::VECTOR(1024)"))
                            print("✅ Embedding column converted to VECTOR(1024)")
                            break
                        except Exception as e:
                            print(f"❌ Conversion attempt {attempt}/{retry_count} failed: {str(e)}")
                            if attempt < retry_count:
                                print(f"⏳ Waiting {retry_delay}s before retry...")
                                time.sleep(retry_delay)
                            else:
                                if skip_on_failure:
                                    print("⚠️  Column conversion failed, but continuing with text format")
                                    return False
                                else:
                                    raise Exception(f"Failed to convert embedding column after {retry_count} attempts: {str(e)}")
                else:
                    print("✅ Embedding column is already VECTOR(1024) type")
            else:
                print("❌ resume_chunks table or embedding column not found")
                return False
                
        except Exception as e:
            print(f"❌ Error converting embedding column: {str(e)}")
            if skip_on_failure:
                print("⚠️  SKIP_PGVECTOR_ON_FAILURE=true, continuing with current column format")
                return False
            else:
                raise
    
    return True


def upgrade() -> None:
    """Attempt to recover pgvector functionality."""
    print("🚀 Starting pgvector recovery migration...")
    
    try:
        success = _attempt_pgvector_recovery()
        
        if success:
            print("🎉 pgvector recovery migration completed successfully")
            print("✅ Vector search functionality should now be available")
        else:
            print("⚠️  pgvector recovery migration completed with limitations")
            print("📝 System will continue with text-only search functionality")
            
    except Exception as e:
        print(f"💥 pgvector recovery migration failed: {str(e)}")
        print("💡 System may continue with degraded functionality")
        
        # Don't re-raise the exception if we're in skip mode
        skip_on_failure = os.getenv("SKIP_PGVECTOR_ON_FAILURE", "true").lower() == "true"
        if not skip_on_failure:
            raise


def downgrade() -> None:
    """Downgrade is not supported for this recovery migration."""
    print("⚠️  Downgrade not supported for pgvector recovery migration")
    pass
