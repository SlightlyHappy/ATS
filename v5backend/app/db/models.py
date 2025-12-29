from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import text
from typing import Union, Any
import uuid
from app.db.session import Base

try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-not-found]
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Fallback Vector class that acts like Text
    class Vector:
        def __init__(self, dim):
            self.dim = dim
        def __call__(self):
            return Text


def get_embedding_column_type():
    """Determine the appropriate column type for embeddings based on runtime detection.
    - If the resume_chunks.embedding column exists, use its UDT to decide.
    - Else, if pgvector extension is installed and library available, use Vector(1024).
    - Else, fall back to Text.
    """
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            # If table/column already exists, trust the database type
            row = conn.execute(text(
                """
                SELECT udt_name FROM information_schema.columns
                WHERE table_name='resume_chunks' AND column_name='embedding'
                """
            )).fetchone()
            if row and row[0]:
                return Vector(1024) if (row[0] == 'vector' and PGVECTOR_AVAILABLE) else Text

            # Otherwise, check extension availability
            has_pgvector = bool(conn.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar())
            if has_pgvector and PGVECTOR_AVAILABLE:
                return Vector(1024)
            return Text
    except Exception:
        # Fallback to Text if we can't determine
        return Text


def has_vector_support() -> bool:
    """Check if vector operations are available at runtime."""
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            # Check if pgvector extension is available
            result = conn.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')"))
            has_pgvector = result.scalar()
            
            if not has_pgvector or not PGVECTOR_AVAILABLE:
                return False
                
            # Check if the embedding column is actually VECTOR type
            result = conn.execute(text("""
                SELECT udt_name FROM information_schema.columns 
                WHERE table_name='resume_chunks' AND column_name='embedding'
            """))
            row = result.fetchone()
            return row is not None and row[0] == 'vector'
    except Exception:
        return False


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    text: Mapped["ResumeText"] = relationship("ResumeText", back_populates="resume", uselist=False)
    facts: Mapped["ResumeFacts"] = relationship("ResumeFacts", back_populates="resume", uselist=False)
    chunks: Mapped[list["ResumeChunk"]] = relationship("ResumeChunk", back_populates="resume", cascade="all,delete")


class ResumeText(Base):
    __tablename__ = "resume_text"
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), primary_key=True)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)

    resume: Mapped[Resume] = relationship("Resume", back_populates="text")


class ResumeChunk(Base):
    __tablename__ = "resume_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), index=True)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # embedding column type will be determined dynamically (Vector(1024) or Text) at import time
    embedding: Mapped[Any] = mapped_column(get_embedding_column_type(), nullable=True)
    section: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown", server_default="unknown", index=True)

    resume: Mapped[Resume] = relationship("Resume", back_populates="chunks")
    
    @property
    def has_vector_embedding(self) -> bool:
        """Check if this chunk has a vector embedding (vs text fallback)."""
        if isinstance(self.embedding, list) and len(self.embedding) > 0:
            return True
        # Check if it's a serialized vector string
        if isinstance(self.embedding, str) and self.embedding.startswith('[') and self.embedding.endswith(']'):
            try:
                import json
                parsed = json.loads(self.embedding)
                return isinstance(parsed, list) and len(parsed) > 0
            except Exception:
                return False
        return False
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of the vector embedding, or 0 if not a vector."""
        if isinstance(self.embedding, list):
            return len(self.embedding)
        if isinstance(self.embedding, str) and self.embedding.startswith('['):
            try:
                import json
                parsed = json.loads(self.embedding)
                return len(parsed) if isinstance(parsed, list) else 0
            except Exception:
                return 0
        return 0
    
    def get_embedding_vector(self) -> list[float] | None:
        """Get the embedding as a list of floats, regardless of storage format."""
        if isinstance(self.embedding, list):
            return self.embedding
        if isinstance(self.embedding, str) and self.embedding.startswith('['):
            try:
                import json
                parsed = json.loads(self.embedding)
                return parsed if isinstance(parsed, list) else None
            except Exception:
                return None
        return None


class ResumeFacts(Base):
    __tablename__ = "resume_facts"
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), primary_key=True)
    extracted_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    resume: Mapped[Resume] = relationship("Resume", back_populates="facts")


class ResumeFactsVersion(Base):
    """Versioned snapshots of resume facts across multi-pass analysis."""
    __tablename__ = "resume_facts_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), index=True, nullable=False)
    pass_no: Mapped[int] = mapped_column(Integer, nullable=False)
    pipeline: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    extracted_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
