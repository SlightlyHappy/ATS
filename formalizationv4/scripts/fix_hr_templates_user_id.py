#!/usr/bin/env python3
"""
Fix HR Templates user_id column to allow NULL for system templates
"""
import os
import sys
import logging
from sqlalchemy import text

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_hr_templates_schema():
    """Fix the HR templates schema to allow NULL user_id for system templates."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔧 Fixing HR templates schema...")
            
            # Check if the table exists and has the constraint
            result = db.session.execute(text("""
                SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'hr_templates' 
                AND column_name = 'user_id'
            """)).fetchone()
            
            if result and result[1] == 'NO':  # is_nullable = 'NO'
                logger.info("  📝 Making user_id column nullable...")
                
                # Drop the foreign key constraint temporarily
                db.session.execute(text("""
                    ALTER TABLE hr_templates 
                    DROP CONSTRAINT IF EXISTS hr_templates_user_id_fkey
                """))
                
                # Alter the column to allow NULL
                db.session.execute(text("""
                    ALTER TABLE hr_templates 
                    ALTER COLUMN user_id DROP NOT NULL
                """))
                
                # Re-add the foreign key constraint
                db.session.execute(text("""
                    ALTER TABLE hr_templates 
                    ADD CONSTRAINT hr_templates_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(id)
                """))
                
                db.session.commit()
                logger.info("  ✅ HR templates schema fixed successfully")
                
            else:
                logger.info("  ℹ️  user_id column is already nullable or table doesn't exist")
                
        except Exception as e:
            logger.error(f"  ❌ Error fixing HR templates schema: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    fix_hr_templates_schema()
