"""
SQLAlchemy Python 3.13 Compatibility Patch
This module provides compatibility fixes for SQLAlchemy with Python 3.13+
"""

import sys
import warnings
import logging

logger = logging.getLogger(__name__)

def apply_sqlalchemy_patches():
    """Apply patches for SQLAlchemy compatibility with Python 3.13+"""
    # Skip patches in Railway environment to avoid threading issues
    import os
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        logger.info('Skipping SQLAlchemy patches in Railway environment')
        return
        
    if sys.version_info >= (3, 13):
        logger.info('Applying SQLAlchemy compatibility patches for Python 3.13+')
        
        # Suppress specific warnings that don't affect functionality
        warnings.filterwarnings('ignore', 
                              message='.*TypingOnly.*',
                              category=UserWarning)
        
        warnings.filterwarnings('ignore',
                              message='.*directly inherits TypingOnly.*',
                              category=UserWarning)
        
        # Apply monkey patches if needed
        try:
            import sqlalchemy.sql.elements
            # The TypingOnly issue doesn't affect runtime functionality,
            # so we just suppress the warnings
            logger.info('✓ SQLAlchemy compatibility patches applied')
        except ImportError:
            logger.warning('SQLAlchemy not available for patching')

def apply_eventlet_patches():
    """Apply patches for eventlet compatibility issues - DISABLED FOR RAILWAY"""
    # EVENTLET COMPLETELY DISABLED FOR RAILWAY DEPLOYMENT
    # Railway uses gthread workers, eventlet conflicts with Flask/Werkzeug
    # Never import eventlet in production to prevent Gunicorn auto-detection
    logger.info('Eventlet patches disabled for Railway deployment')
    return

def apply_database_patches():
    """Apply patches for database metadata handling"""
    try:
        import sqlalchemy
        from sqlalchemy import event
        from sqlalchemy.schema import MetaData
        
        # Monkey patch to handle table redefinition gracefully
        original_create_all = MetaData.create_all
        
        def patched_create_all(self, bind=None, tables=None, checkfirst=True):
            """Patched create_all that handles existing tables gracefully"""
            try:
                return original_create_all(self, bind=bind, tables=tables, checkfirst=checkfirst)
            except Exception as e:
                if 'already defined' in str(e):
                    logger.warning(f'Table already exists, continuing: {e}')
                    return
                else:
                    raise
        
        MetaData.create_all = patched_create_all
        logger.info('✓ Database metadata patches applied')
        
    except ImportError:
        logger.warning('SQLAlchemy not available for database patching')

# Apply patches on import
try:
    apply_sqlalchemy_patches()
    apply_eventlet_patches()
    apply_database_patches()
    logger.info('✓ All compatibility patches applied successfully')
except Exception as e:
    logger.error(f'Failed to apply compatibility patches: {e}')
