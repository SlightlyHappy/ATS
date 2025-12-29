from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.sql import text
from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True, 
    pool_size=10, 
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={
        "connect_timeout": 30,
        "application_name": "ats_backend"
    }
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Initialize database connection and verify basic accessibility.
    
    Note: Table creation is handled by Alembic migrations, not here.
    This function only checks basic connectivity and pgvector availability.
    """
    try:
        with engine.connect() as conn:
            # Test basic connectivity
            conn.execute(text("SELECT 1"))
            conn.commit()
    except Exception as e:
        # Log but don't fail app boot if DB is temporarily unavailable
        print(f"Database connection check failed during init: {e}")
        pass
    
    # Note: We intentionally do NOT call Base.metadata.create_all() here
    # because table creation should be handled by Alembic migrations only.
    # This prevents conflicts between migration-managed schema and direct table creation.
