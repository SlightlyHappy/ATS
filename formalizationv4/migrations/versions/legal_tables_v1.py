"""Add legal RAG system tables

Revision ID: legal_tables_v1
Revises: communication_tables_v1
Create Date: 2025-08-05 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'legal_tables_v1'
down_revision = 'communication_tables_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Create legal_documents table
    op.create_table('legal_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('document_type', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_hash', sa.String(length=128), nullable=True),
        sa.Column('content_preview', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True, default='en'),
        sa.Column('jurisdiction', sa.String(length=100), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('last_updated_date', sa.Date(), nullable=True),
        sa.Column('source', sa.String(length=200), nullable=True),
        sa.Column('authority', sa.String(length=200), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True, default='pending'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_legal_documents_filename', 'legal_documents', ['filename'])
    op.create_index('idx_legal_documents_type', 'legal_documents', ['document_type'])
    op.create_index('idx_legal_documents_category', 'legal_documents', ['category'])
    op.create_index('idx_legal_documents_is_processed', 'legal_documents', ['is_processed'])
    op.create_index('idx_legal_documents_hash', 'legal_documents', ['file_hash'], unique=True)

    # Create document_chunks table
    op.create_table('document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_length', sa.Integer(), nullable=True),
        sa.Column('chunk_type', sa.String(length=50), nullable=True, default='text'),
        sa.Column('section_title', sa.String(length=500), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('start_char', sa.Integer(), nullable=True),
        sa.Column('end_char', sa.Integer(), nullable=True),
        sa.Column('embedding_vector', postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('keywords', postgresql.JSONB(), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('context_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['legal_documents.id'], ondelete='CASCADE')
    )
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_document_chunks_chunk_index', 'document_chunks', ['chunk_index'])
    op.create_index('idx_document_chunks_type', 'document_chunks', ['chunk_type'])

    # Create legal_queries table
    op.create_table('legal_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=True, default='general'),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('sources_count', sa.Integer(), nullable=True, default=0),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('embedding_similarity_threshold', sa.Float(), nullable=True),
        sa.Column('retrieved_chunks', postgresql.JSONB(), nullable=True),
        sa.Column('feedback_rating', sa.Integer(), nullable=True),
        sa.Column('feedback_comments', sa.Text(), nullable=True),
        sa.Column('is_helpful', sa.Boolean(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_legal_queries_user_id', 'legal_queries', ['user_id'])
    op.create_index('idx_legal_queries_type', 'legal_queries', ['query_type'])
    op.create_index('idx_legal_queries_created_at', 'legal_queries', ['created_at'])
    op.create_index('idx_legal_queries_session_id', 'legal_queries', ['session_id'])

    # Create knowledge_base_updates table
    op.create_table('knowledge_base_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('update_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_documents_count', sa.Integer(), nullable=True, default=0),
        sa.Column('new_chunks_count', sa.Integer(), nullable=True, default=0),
        sa.Column('updated_chunks_count', sa.Integer(), nullable=True, default=0),
        sa.Column('deleted_chunks_count', sa.Integer(), nullable=True, default=0),
        sa.Column('processing_duration_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('triggered_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trigger_reason', sa.String(length=200), nullable=True),
        sa.Column('version_before', sa.String(length=50), nullable=True),
        sa.Column('version_after', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_knowledge_base_updates_type', 'knowledge_base_updates', ['update_type'])
    op.create_index('idx_knowledge_base_updates_status', 'knowledge_base_updates', ['status'])
    op.create_index('idx_knowledge_base_updates_created_at', 'knowledge_base_updates', ['created_at'])


def downgrade():
    op.drop_table('knowledge_base_updates')
    op.drop_table('legal_queries')
    op.drop_table('document_chunks')
    op.drop_table('legal_documents')
