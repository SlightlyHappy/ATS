"""
Vector Support Detection Service

Provides runtime detection of vector search capabilities and fallback strategies.
"""
from __future__ import annotations
import functools
from sqlalchemy.sql import text
from app.db.session import SessionLocal
from app.core.logging import get_logger

log = get_logger("vector_support")

# Cache the detection result to avoid repeated database queries
_vector_support_cache: bool | None = None


@functools.lru_cache(maxsize=1)
def detect_vector_support() -> bool:
    """
    Detect if vector operations are available at runtime.
    
    Returns:
        bool: True if pgvector extension is installed and embedding column is VECTOR type
    """
    global _vector_support_cache
    
    if _vector_support_cache is not None:
        return _vector_support_cache
    
    try:
        # Check if pgvector package is available
        try:
            import pgvector  # noqa: F401
        except ImportError:
            log.info("vector_support_check", available=False, reason="pgvector package not installed")
            _vector_support_cache = False
            return False
        
        with SessionLocal() as session:
            # Check if pgvector extension is installed
            result = session.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')"))
            has_extension = result.scalar()
            
            if not has_extension:
                log.info("vector_support_check", available=False, reason="pgvector extension not installed")
                _vector_support_cache = False
                return False
            
            # Check if resume_chunks table exists
            result = session.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='resume_chunks')"))
            has_table = result.scalar()
            
            if not has_table:
                log.info("vector_support_check", available=False, reason="resume_chunks table not found")
                _vector_support_cache = False
                return False
            
            # Check if embedding column is VECTOR type
            result = session.execute(text("""
                SELECT udt_name FROM information_schema.columns 
                WHERE table_name='resume_chunks' AND column_name='embedding'
            """))
            row = result.fetchone()
            
            if not row or row[0] != 'vector':
                log.info("vector_support_check", available=False, reason=f"embedding column type: {row[0] if row else 'not found'}")
                _vector_support_cache = False
                return False
            
            log.info("vector_support_check", available=True, reason="all requirements met")
            _vector_support_cache = True
            return True
            
    except Exception as e:
        log.warning("vector_support_check", available=False, reason=f"error: {str(e)}")
        _vector_support_cache = False
        return False


def invalidate_vector_support_cache():
    """Invalidate the vector support cache (useful after migrations)."""
    global _vector_support_cache
    _vector_support_cache = None
    detect_vector_support.cache_clear()


def require_vector_support():
    """
    Decorator to ensure vector support is available before calling a function.
    
    Raises:
        RuntimeError: If vector support is not available
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not detect_vector_support():
                raise RuntimeError(f"Vector support required for {func.__name__} but not available")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def vector_fallback(fallback_func):
    """
    Decorator to provide a fallback function when vector support is not available.
    
    Args:
        fallback_func: Function to call when vector support is not available
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if detect_vector_support():
                return func(*args, **kwargs)
            else:
                log.debug("vector_fallback", function=func.__name__, reason="vector support not available")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator


class VectorSupportError(Exception):
    """Raised when vector operations are attempted without proper support."""
    pass
