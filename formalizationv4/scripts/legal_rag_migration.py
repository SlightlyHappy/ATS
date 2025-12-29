"""
Legal RAG Database Migration Script
Creates tables for legal knowledge base and RAG functionality
"""
import sys
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def upgrade():
    """Create legal RAG tables"""
    
    # Create legal_documents table
    op.create_table('legal_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('document_type', sa.Enum('TEXTBOOK', 'LEGAL_CODE', 'CASE_LAW', 'REGULATION', 'POLICY', 'GUIDANCE', 'OTHER', name='documenttype'), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('total_chunks', sa.Integer(), nullable=True),
        sa.Column('processing_status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'UPDATED', name='processingstatus'), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('query_count', sa.Integer(), nullable=True),
        sa.Column('last_queried_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash'),
        sa.UniqueConstraint('filename')
    )
    
    # Create document_chunks table
    op.create_table('document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('embedding_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('doc_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('character_count', sa.Integer(), nullable=True),
        sa.Column('retrieval_count', sa.Integer(), nullable=True),
        sa.Column('last_retrieved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['legal_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create legal_queries table
    op.create_table('legal_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('retrieved_chunks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_documents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('total_context_length', sa.Integer(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('embedding_time', sa.Float(), nullable=True),
        sa.Column('retrieval_time', sa.Float(), nullable=True),
        sa.Column('generation_time', sa.Float(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create knowledge_base_updates table
    op.create_table('knowledge_base_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('update_type', sa.String(length=50), nullable=False),
        sa.Column('trigger', sa.String(length=100), nullable=True),
        sa.Column('documents_processed', sa.Integer(), nullable=True),
        sa.Column('chunks_created', sa.Integer(), nullable=True),
        sa.Column('chunks_updated', sa.Integer(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_documents', sa.Integer(), nullable=True),
        sa.Column('total_chunks', sa.Integer(), nullable=True),
        sa.Column('vector_db_size', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_document_chunk', 'document_chunks', ['document_id', 'chunk_index'])
    op.create_index('idx_chunk_hash', 'document_chunks', ['content_hash'])
    op.create_index('idx_user_queries', 'legal_queries', ['user_id', 'created_at'])
    op.create_index('idx_query_hash', 'legal_queries', ['query_hash'])


def downgrade():
    """Drop legal RAG tables"""
    
    # Drop indexes
    op.drop_index('idx_query_hash', table_name='legal_queries')
    op.drop_index('idx_user_queries', table_name='legal_queries')
    op.drop_index('idx_chunk_hash', table_name='document_chunks')
    op.drop_index('idx_document_chunk', table_name='document_chunks')
    
    # Drop tables
    op.drop_table('knowledge_base_updates')
    op.drop_table('legal_queries')
    op.drop_table('document_chunks')
    op.drop_table('legal_documents')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS processingstatus')
    op.execute('DROP TYPE IF EXISTS documenttype')
