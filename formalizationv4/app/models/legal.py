"""
Legal Knowledge Base Models for HR-Legal RAG System
"""
import uuid
import hashlib
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app import db

class DocumentType(Enum):
    """Legal document categories"""
    TEXTBOOK = "textbook"
    LEGAL_CODE = "legal_code"
    CASE_LAW = "case_law"
    REGULATION = "regulation"
    POLICY = "policy"
    GUIDANCE = "guidance"
    OTHER = "other"

class ProcessingStatus(Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UPDATED = "updated"

class LegalDocument(db.Model):
    """Legal documents in the knowledge base"""
    __tablename__ = 'legal_documents'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False, unique=True)
    title = Column(String(500))
    document_type = Column(db.Enum(DocumentType), default=DocumentType.OTHER)
    
    # Content tracking
    content_hash = Column(String(64), unique=True, nullable=False)  # SHA256 of content
    file_size = Column(Integer)  # File size in bytes
    total_chunks = Column(Integer, default=0)
    
    # Processing metadata
    processing_status = Column(db.Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_error = Column(Text)  # Error message if processing failed
    
    # Statistics
    query_count = Column(Integer, default=0)  # How many times this doc was referenced
    last_queried_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    @classmethod
    def generate_content_hash(cls, content: str) -> str:
        """Generate SHA256 hash of document content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'filename': self.filename,
            'title': self.title,
            'document_type': self.document_type.value if self.document_type else None,
            'total_chunks': self.total_chunks,
            'processing_status': self.processing_status.value,
            'query_count': self.query_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DocumentChunk(db.Model):
    """Text chunks from legal documents with embeddings"""
    __tablename__ = 'document_chunks'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('legal_documents.id'), nullable=False)
    
    # Chunk information
    chunk_index = Column(Integer, nullable=False)  # Sequential index within document
    content = Column(Text, nullable=False)  # Actual text content
    content_hash = Column(String(64), nullable=False)  # SHA256 of chunk content
    
    # Vector embeddings (stored as JSONB for PostgreSQL compatibility)
    embedding_vector = Column(JSONB)  # Dense vector representation
    embedding_model = Column(String(100))  # Model used for embedding generation
    
    # Document metadata
    doc_metadata = Column(JSONB)  # Page numbers, section titles, context info
    word_count = Column(Integer)
    character_count = Column(Integer)
    
    # Performance tracking
    retrieval_count = Column(Integer, default=0)  # How often this chunk was retrieved
    last_retrieved_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("LegalDocument", back_populates="chunks")
    
    # Composite index for efficient querying
    __table_args__ = (
        db.Index('idx_document_chunk', 'document_id', 'chunk_index'),
        db.Index('idx_chunk_hash', 'content_hash'),
    )
    
    @classmethod
    def generate_content_hash(cls, content: str) -> str:
        """Generate SHA256 hash of chunk content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'chunk_index': self.chunk_index,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'word_count': self.word_count,
            'metadata': self.doc_metadata,
            'retrieval_count': self.retrieval_count
        }

class LegalQuery(db.Model):
    """Legal RAG queries and responses"""
    __tablename__ = 'legal_queries'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=False)  # For caching similar queries
    
    # Response information
    response = Column(Text)
    confidence_score = Column(Float)  # AI confidence in response quality
    
    # Retrieved context
    retrieved_chunks = Column(JSONB)  # List of chunk IDs and similarity scores
    source_documents = Column(JSONB)  # List of source document info
    total_context_length = Column(Integer)  # Total characters in context
    
    # Performance metrics
    processing_time = Column(Float)  # Time taken to process query
    embedding_time = Column(Float)  # Time to generate query embedding
    retrieval_time = Column(Float)  # Time to retrieve relevant chunks
    generation_time = Column(Float)  # Time to generate response
    
    # Quality metrics
    user_rating = Column(Integer)  # User feedback (1-5 stars)
    user_feedback = Column(Text)  # Optional user feedback text
    
    # Status
    status = Column(String(20), default='completed')  # completed, failed, pending
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_user_queries', 'user_id', 'created_at'),
        db.Index('idx_query_hash', 'query_hash'),
    )
    
    @classmethod
    def generate_query_hash(cls, query_text: str) -> str:
        """Generate hash for query caching"""
        return hashlib.sha256(query_text.lower().strip().encode('utf-8')).hexdigest()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'query_text': self.query_text,
            'response': self.response,
            'confidence_score': self.confidence_score,
            'source_documents': self.source_documents,
            'processing_time': self.processing_time,
            'user_rating': self.user_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status
        }

class KnowledgeBaseUpdate(db.Model):
    """Track knowledge base updates and rebuilds"""
    __tablename__ = 'knowledge_base_updates'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Update information
    update_type = Column(String(50), nullable=False)  # 'full_rebuild', 'incremental', 'document_added'
    trigger = Column(String(100))  # 'deployment', 'manual', 'scheduled'
    
    # Processing metrics
    documents_processed = Column(Integer, default=0)
    chunks_created = Column(Integer, default=0)
    chunks_updated = Column(Integer, default=0)
    processing_time = Column(Float)
    
    # Status
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    error_message = Column(Text)
    
    # Statistics
    total_documents = Column(Integer)
    total_chunks = Column(Integer)
    vector_db_size = Column(Integer)  # Size in bytes if applicable
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'update_type': self.update_type,
            'trigger': self.trigger,
            'documents_processed': self.documents_processed,
            'chunks_created': self.chunks_created,
            'processing_time': self.processing_time,
            'status': self.status,
            'total_documents': self.total_documents,
            'total_chunks': self.total_chunks,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
