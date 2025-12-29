"""add resume_facts_versions table

Revision ID: 20250810_03
Revises: 20250810_02
Create Date: 2025-08-10

"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250810_03'
down_revision = '20250810_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create resume_facts_versions if not exists
    conn = op.get_bind()
    exists = False
    try:
        # First try to recover from any failed transaction state
        try:
            conn.execute(sa.text("ROLLBACK"))
        except Exception:
            pass
        
        # Start a fresh transaction
        try:
            conn.execute(sa.text("BEGIN"))
        except Exception:
            pass
            
        exists = bool(conn.execute(sa.text("SELECT to_regclass('resume_facts_versions') IS NOT NULL")).scalar())
    except Exception as e:
        # If we still can't query, assume table doesn't exist
        print(f"Warning: Could not check table existence: {e}")
        exists = False
    
    if not exists:
        # Check if resumes table exists first
        resumes_exists = False
        try:
            resumes_exists = bool(conn.execute(sa.text("SELECT to_regclass('resumes') IS NOT NULL")).scalar())
        except Exception as e:
            print(f"Warning: Could not check resumes table existence: {e}")
            resumes_exists = False
        
        if not resumes_exists:
            print("❌ resumes table does not exist, creating it first...")
            # Create the resumes table if it doesn't exist
            try:
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
                print("✅ Successfully created resumes table")
            except Exception as e:
                print(f"❌ Error creating resumes table: {e}")
                raise
        
        try:
            op.create_table(
                'resume_facts_versions',
                sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
                sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id'), nullable=False, index=True),
                sa.Column('pass_no', sa.Integer(), nullable=False),
                sa.Column('pipeline', sa.String(length=50), nullable=False, server_default=''),
                sa.Column('extracted_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
                sa.Column('scores', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
                sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            )
            print("✅ Successfully created resume_facts_versions table")
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            # Try to recover the transaction
            try:
                conn.execute(sa.text("ROLLBACK"))
                conn.execute(sa.text("BEGIN"))
            except Exception:
                pass
            raise
            
        # Create indexes only if they don't exist
        try:
            # Check if resume_id index exists
            resume_id_index_exists = bool(conn.execute(sa.text(
                "SELECT 1 FROM pg_indexes WHERE indexname = 'ix_resume_facts_versions_resume_id'"
            )).scalar())
            
            if not resume_id_index_exists:
                op.create_index('ix_resume_facts_versions_resume_id', 'resume_facts_versions', ['resume_id'], unique=False)
                print("Successfully created resume_id index")
            else:
                print("Resume_id index already exists, skipping")
        except Exception as e:
            print(f"Warning: Could not create resume_id index: {e}")
            # Recover transaction after failed index creation
            try:
                conn.execute(sa.text("ROLLBACK"))
                conn.execute(sa.text("BEGIN"))
            except Exception:
                pass
            
        try:
            # Check if pass_no index exists
            pass_no_index_exists = bool(conn.execute(sa.text(
                "SELECT 1 FROM pg_indexes WHERE indexname = 'ix_resume_facts_versions_pass_no'"
            )).scalar())
            
            if not pass_no_index_exists:
                op.create_index('ix_resume_facts_versions_pass_no', 'resume_facts_versions', ['pass_no'], unique=False)
                print("Successfully created pass_no index")
            else:
                print("Pass_no index already exists, skipping")
        except Exception as e:
            print(f"Warning: Could not create pass_no index: {e}")
            # Recover transaction after failed index creation
            try:
                conn.execute(sa.text("ROLLBACK"))
                conn.execute(sa.text("BEGIN"))
            except Exception:
                pass


def downgrade() -> None:
    # Ensure we have a clean transaction state
    conn = op.get_bind()
    try:
        # Try to recover from any failed transaction state
        try:
            conn.execute(sa.text("ROLLBACK"))
        except Exception:
            pass
        
        # Start a fresh transaction
        try:
            conn.execute(sa.text("BEGIN"))
        except Exception:
            pass
    except Exception:
        pass
        
    try:
        op.drop_index('ix_resume_facts_versions_resume_id', table_name='resume_facts_versions')
    except Exception:
        pass
    try:
        op.drop_index('ix_resume_facts_versions_pass_no', table_name='resume_facts_versions')
    except Exception:
        pass
    try:
        op.drop_table('resume_facts_versions')
    except Exception:
        pass
