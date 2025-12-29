#!/usr/bin/env python3
"""
Admin User Setup Migration
==========================

This script handles the admin user setup migration including:
1. Adding CASCADE DELETE to foreign key constraints
2. Safely removing and recreating admin users
3. Testing the admin login

Usage:
    python scripts/admin_setup_migration.py
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """Setup logging for the script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def migrate_admin_setup():
    """Run the admin setup migration"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import Flask app and models
        from app import create_app, db
        from app.models import User
        from app.models.admin import AdminUser
        from app.services.auth_manager import auth_manager
        from sqlalchemy import text
        
        # Create app context
        app = create_app('production')
        
        with app.app_context():
            logger.info('🔧 Starting admin setup migration...')
            
            # Step 1: Update foreign key constraint to include CASCADE DELETE
            logger.info('📊 Updating database schema...')
            try:
                # Check if the constraint needs updating
                result = db.session.execute(text("""
                    SELECT conname 
                    FROM pg_constraint 
                    WHERE conrelid = 'admin_users'::regclass 
                    AND confrelid = 'users'::regclass
                """))
                constraint_name = result.fetchone()
                
                if constraint_name:
                    constraint_name = constraint_name[0]
                    logger.info(f'Found foreign key constraint: {constraint_name}')
                    
                    # Drop the old constraint
                    db.session.execute(text(f'ALTER TABLE admin_users DROP CONSTRAINT {constraint_name}'))
                    
                    # Add the new constraint with CASCADE DELETE
                    db.session.execute(text('''
                        ALTER TABLE admin_users 
                        ADD CONSTRAINT admin_users_user_id_fkey 
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    '''))
                    
                    db.session.commit()
                    logger.info('✅ Foreign key constraint updated with CASCADE DELETE')
                else:
                    logger.info('ℹ️ No existing foreign key constraint found')
                    
            except Exception as schema_error:
                logger.warning(f'⚠️ Schema update issue (continuing): {str(schema_error)}')
                db.session.rollback()
            
            # Step 2: Reset admin user
            logger.info('👤 Resetting admin user...')
            
            # Define admin credentials
            admin_email = 'admin@bearsystems.co.in'
            admin_password = 'Benzie1!Benzie1!Benzie1!Benzie1!'
            admin_username = 'admin'
            
            # Find all existing admin users
            existing_users = User.query.filter(
                db.or_(
                    User.email == admin_email,
                    User.username == admin_username,
                    User.is_admin == True
                )
            ).all()
            
            # Remove existing admin users (this should now cascade to admin_users table)
            for user in existing_users:
                logger.info(f'🗑️ Removing existing admin user: {user.email} (username: {user.username})')
                db.session.delete(user)
            
            # Commit deletions
            if existing_users:
                db.session.commit()
                logger.info('✅ Existing admin users removed (with cascade)')
            else:
                logger.info('ℹ️ No existing admin users found')
            
            # Create the new admin user
            logger.info('👤 Creating new admin user...')
            admin = User(
                email=admin_email,
                username=admin_username,
                password_hash=auth_manager.hash_password(admin_password),
                first_name='System',
                last_name='Administrator',
                is_admin=True,
                is_active=True,
                credits_balance=10000
            )
            
            db.session.add(admin)
            db.session.flush()  # Flush to get the ID before creating AdminUser
            
            # Create corresponding AdminUser record
            logger.info('🔐 Creating AdminUser record...')
            admin_user = AdminUser(
                user_id=admin.id,
                role='super_admin',
                access_level=100,
                can_access_all_users=True,
                can_modify_credits=True,
                can_manage_queue=True,
                can_view_analytics=True,
                can_manage_system=True,
                can_access_sales_intelligence=True,
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Step 3: Test admin login
            logger.info('🧪 Testing admin login...')
            test_user = auth_manager.authenticate_user(admin_email, admin_password)
            if test_user:
                logger.info('✅ Admin login test successful!')
            else:
                logger.error('❌ Admin login test failed!')
                return False
            
            logger.info('🎉 Admin setup migration completed successfully!')
            logger.info(f'📧 Email: {admin_email}')
            logger.info(f'👤 Username: {admin_username}')
            logger.info(f'🔑 Password: {admin_password}')
            logger.info(f'🎭 Role: super_admin')
            
            return True
            
    except Exception as e:
        logger.error(f'❌ Failed to run admin setup migration: {str(e)}')
        
        # Try to rollback
        try:
            db.session.rollback()
            logger.info('🔄 Database session rolled back')
        except:
            pass
            
        import traceback
        logger.error(f'Traceback: {traceback.format_exc()}')
        return False

if __name__ == '__main__':
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info('🚀 Starting admin setup migration...')
    
    success = migrate_admin_setup()
    
    if success:
        logger.info('🎉 Admin setup migration completed successfully!')
        sys.exit(0)
    else:
        logger.error('💥 Admin setup migration failed!')
        sys.exit(1)
