"""initial schema

Revision ID: 20250810_00
Revises: 
Create Date: 2025-08-10

"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import time
import os

# revision identifiers, used by Alembic.
revision = '20250810_00'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    try:
        return bool(bind.execute(sa.text("SELECT to_regclass(:n) IS NOT NULL"), {"n": name}).scalar())
    except Exception:
        return False


def _index_exists(name: str) -> bool:
    bind = op.get_bind()
    try:
        return bool(bind.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n"), {"n": name}).fetchone())
    except Exception:
        return False


def _column_udt(table: str, column: str) -> str | None:
    bind = op.get_bind()
    try:
        row = bind.execute(sa.text(
            """
            SELECT udt_name FROM information_schema.columns
            WHERE table_name = :t AND column_name = :c
            """
        ), {"t": table, "c": column}).fetchone()
        return row[0] if row else None
    except Exception:
        return None


def _attempt_pgvector_creation():
    """Attempt to create pgvector extension with retry logic using autocommit to prevent transaction poisoning.
    Production-safe: if pgvector isn't available on the server, do not fail migration by default.
    """
    # Get configuration from environment
    retry_count = int(os.getenv("PGVECTOR_RETRY_COUNT", "3"))
    retry_delay = int(os.getenv("PGVECTOR_RETRY_DELAY", "5"))
    force_creation = os.getenv("FORCE_PGVECTOR_CREATION", "true").lower() == "true"
    # Default to false to match Settings default - fail if pgvector creation fails on pgvector service
    skip_on_failure = os.getenv("SKIP_PGVECTOR_ON_FAILURE", "false").lower() == "true"
    
    if not force_creation:
        print("⚠️  FORCE_PGVECTOR_CREATION=false, skipping pgvector extension creation")
        return False
    
    # Best-effort detection: if server doesn't even list the extension as available, skip attempts
    try:
        bind = op.get_bind()
        print("🔍 Railway pgvector service debugging:")
        
        # Check server version
        version_result = bind.execute(sa.text("SELECT version()")).scalar()
        print(f"   📊 PostgreSQL version: {version_result}")
        
        # Check current database
        db_result = bind.execute(sa.text("SELECT current_database()")).scalar()
        print(f"   🗄️  Current database: {db_result}")
        
        # Check if we're superuser (needed for extension creation)
        superuser_result = bind.execute(sa.text("SELECT current_setting('is_superuser')")).scalar()
        print(f"   🔑 Is superuser: {superuser_result}")
        
        # Check available extensions
        available = bind.execute(sa.text("SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name='vector')")).scalar()
        print(f"   🧬 pgvector available: {available}")
        
        if available:
            # Get extension details
            ext_details = bind.execute(sa.text("SELECT version, comment FROM pg_available_extensions WHERE name='vector'")).fetchone()
            if ext_details:
                print(f"   📦 pgvector version: {ext_details[0]}, comment: {ext_details[1]}")
        
        # Check if extension is already installed
        installed = bind.execute(sa.text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar()
        print(f"   ✅ pgvector installed: {installed}")
        
        if installed:
            print("   🎉 pgvector extension already installed, skipping creation")
            return True
            
        if not available:
            print("   ❌ pgvector not available on server (pg_available_extensions)")
            if skip_on_failure:
                print("   ⚠️  Continuing without vector support")
                return False
            else:
                raise Exception("pgvector extension not available on Railway pgvector service")
                
    except Exception as e:
        # If we cannot introspect availability, proceed to attempts (will be caught below)
        print(f"   ⚠️  Could not query extension status: {str(e)}")
    
    print(f"🔄 Attempting to create pgvector extension (retries: {retry_count}, delay: {retry_delay}s)")
    
    last_error = None
    for attempt in range(1, retry_count + 1):
        try:
            print(f"   Attempt {attempt}/{retry_count}: CREATE EXTENSION IF NOT EXISTS vector")
            # Use autocommit to prevent transaction poisoning
            with op.get_context().autocommit_block():
                op.execute('CREATE EXTENSION IF NOT EXISTS vector')
            print("✅ pgvector extension created successfully")
            return True
        except Exception as e:
            last_error = str(e)
            print(f"❌ Attempt {attempt}/{retry_count} failed:")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {last_error}")
            
            # If it's the classic "extension is not available" error, don't burn retries unnecessarily
            if 'extension "vector" is not available' in last_error:
                print("ℹ️  Server does not have pgvector installed; will not retry further")
                break
            
            # Check for permission errors
            if 'permission denied' in last_error.lower() or 'must be owner' in last_error.lower():
                print("ℹ️  Permission error - user may not have rights to create extensions")
                break
            
            if attempt < retry_count:
                print(f"⏳ Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
            else:
                print(f"🚫 All {retry_count} attempts failed")
    
    if skip_on_failure:
        print("⚠️  SKIP_PGVECTOR_ON_FAILURE=true, continuing without vector support")
        if last_error:
            print(f"   Last error: {last_error}")
        return False
    else:
        print("💥 SKIP_PGVECTOR_ON_FAILURE=false, failing migration")
        raise Exception(f"Failed to create pgvector extension after {retry_count} attempts. Last error: {last_error}")


def _create_tables_without_vector():
    """Create tables without vector columns as fallback."""
    print("🔄 Creating tables without vector support...")
    
    # Create resumes table
    if not _table_exists('resumes'):
        op.create_table('resumes',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('original_filename', sa.String(length=512), nullable=False),
            sa.Column('mime', sa.String(length=100), nullable=False),
            sa.Column('size', sa.Integer(), nullable=False),
            sa.Column('content_hash', sa.String(length=64), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.PrimaryKeyConstraint('id')
        )
    if not _index_exists(op.f('ix_resumes_content_hash')):
        try:
            op.create_index(op.f('ix_resumes_content_hash'), 'resumes', ['content_hash'], unique=False)
        except Exception:
            pass

    # Create resume_text table
    if not _table_exists('resume_text'):
        op.create_table('resume_text',
            sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('full_text', sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
            sa.PrimaryKeyConstraint('resume_id')
        )

    # Create resume_chunks table WITHOUT vector embedding (fallback)
    if not _table_exists('resume_chunks'):
        op.create_table('resume_chunks',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('idx', sa.Integer(), nullable=False),
            sa.Column('text', sa.Text(), nullable=False),
            sa.Column('embedding', sa.Text(), nullable=True),  # Text field as fallback
            sa.Column('section', sa.String(length=64), nullable=False, server_default='unknown'),
            sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    if not _index_exists(op.f('ix_resume_chunks_resume_id')):
        try:
            op.create_index(op.f('ix_resume_chunks_resume_id'), 'resume_chunks', ['resume_id'], unique=False)
        except Exception:
            pass
    if not _index_exists(op.f('ix_resume_chunks_section')):
        try:
            op.create_index(op.f('ix_resume_chunks_section'), 'resume_chunks', ['section'], unique=False)
        except Exception:
            pass

    # Create resume_facts table
    if not _table_exists('resume_facts'):
        op.create_table('resume_facts',
            sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('extracted_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.Column('scores', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
            sa.PrimaryKeyConstraint('resume_id')
        )

    # Create jobs table
    if not _table_exists('jobs'):
        op.create_table('jobs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('finished_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    print("✅ Tables ensured without vector support")


def _create_tables_with_vector():
    """Create tables with vector columns."""
    print("🔄 Creating tables with vector support...")
    
    # Create resumes table
    if not _table_exists('resumes'):
        op.create_table('resumes',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('original_filename', sa.String(length=512), nullable=False),
            sa.Column('mime', sa.String(length=100), nullable=False),
            sa.Column('size', sa.Integer(), nullable=False),
            sa.Column('content_hash', sa.String(length=64), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.PrimaryKeyConstraint('id')
        )
    if not _index_exists(op.f('ix_resumes_content_hash')):
        try:
            op.create_index(op.f('ix_resumes_content_hash'), 'resumes', ['content_hash'], unique=False)
        except Exception:
            pass

    # Create resume_text table
    if not _table_exists('resume_text'):
        op.create_table('resume_text',
            sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('full_text', sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
            sa.PrimaryKeyConstraint('resume_id')
        )

    # Create resume_chunks table with vector embedding (create as text then convert)
    if not _table_exists('resume_chunks'):
        op.create_table('resume_chunks',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('idx', sa.Integer(), nullable=False),
            sa.Column('text', sa.Text(), nullable=False),
            sa.Column('embedding', sa.Text(), nullable=False),  # Will be converted to VECTOR(1024) after creation
            sa.Column('section', sa.String(length=64), nullable=False, server_default='unknown'),
            sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Convert embedding column to vector type with retry if not already vector
    current_udt = _column_udt('resume_chunks', 'embedding')
    if current_udt != 'vector':
        retry_count = int(os.getenv("PGVECTOR_RETRY_COUNT", "5"))
        retry_delay = int(os.getenv("PGVECTOR_RETRY_DELAY", "10"))
        
        for attempt in range(1, retry_count + 1):
            try:
                print(f"   Attempt {attempt}/{retry_count}: Converting embedding column to VECTOR(1024)")
                # Use autocommit to prevent transaction poisoning
                with op.get_context().autocommit_block():
                    op.execute('ALTER TABLE resume_chunks ALTER COLUMN embedding TYPE VECTOR(1024) USING embedding::VECTOR(1024)')
                print("✅ Embedding column converted to VECTOR(1024)")
                break
            except Exception as e:
                print(f"❌ Attempt {attempt}/{retry_count} failed: {str(e)}")
                if attempt < retry_count:
                    print(f"⏳ Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"Failed to convert embedding column after {retry_count} attempts: {str(e)}")
    else:
        print("ℹ️  Embedding column already VECTOR type; skipping conversion")
    
    if not _index_exists(op.f('ix_resume_chunks_resume_id')):
        try:
            op.create_index(op.f('ix_resume_chunks_resume_id'), 'resume_chunks', ['resume_id'], unique=False)
        except Exception:
            pass
    if not _index_exists(op.f('ix_resume_chunks_section')):
        try:
            op.create_index(op.f('ix_resume_chunks_section'), 'resume_chunks', ['section'], unique=False)
        except Exception:
            pass

    # Create resume_facts table
    if not _table_exists('resume_facts'):
        op.create_table('resume_facts',
            sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('extracted_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.Column('scores', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
            sa.PrimaryKeyConstraint('resume_id')
        )

    # Create jobs table
    if not _table_exists('jobs'):
        op.create_table('jobs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('finished_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    print("✅ Tables ensured with vector support")


def upgrade() -> None:
    print("🚀 Starting database schema upgrade...")
    
    # Attempt to create pgvector extension
    vector_success = _attempt_pgvector_creation()
    
    if vector_success:
        # Create tables with vector support
        _create_tables_with_vector()
    else:
        # Create tables without vector support
        _create_tables_without_vector()

    # Add FTS column and index to resume_text (works with or without vector)
    print("🔄 Setting up full-text search...")
    try:
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'resume_text' AND column_name = 'fts') THEN
                    ALTER TABLE resume_text ADD COLUMN fts tsvector;
                    UPDATE resume_text SET fts = to_tsvector('english', full_text);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE tablename='resume_text' AND indexname='resume_text_fts'
                ) THEN
                    CREATE INDEX resume_text_fts ON resume_text USING GIN (fts);
                END IF;
            END
            $$;
            """
        )
        print("✅ Full-text search setup completed")
    except Exception as e:
        print(f"⚠️  Full-text search setup failed (will be handled by runtime): {str(e)}")
    
    print("🎉 Database schema upgrade completed")


def downgrade() -> None:
    # Best-effort drops; ignore if already gone
    try:
        op.drop_table('jobs')
    except Exception:
        pass
    try:
        op.drop_table('resume_facts')
    except Exception:
        pass
    try:
        op.drop_index(op.f('ix_resume_chunks_resume_id'), table_name='resume_chunks')
    except Exception:
        pass
    try:
        op.drop_table('resume_chunks')
    except Exception:
        pass
    try:
        op.drop_table('resume_text')
    except Exception:
        pass
    try:
        op.drop_index(op.f('ix_resumes_content_hash'), table_name='resumes')
    except Exception:
        pass
    try:
        op.drop_table('resumes')
    except Exception:
        pass
    try:
        op.execute('DROP EXTENSION IF EXISTS vector')
    except Exception:
        pass
