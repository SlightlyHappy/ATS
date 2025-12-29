#!/usr/bin/env python3
"""
Reset Admin User Script
=======================

This script safely resets the admin user to the default credentials:
- Email: admin@bearsystems.co.in  
- Password: Benzie1!Benzie1!Benzie1!Benzie1!
- Username: admin

It handles the cascade deletion of AdminUser records properly to avoid
foreign key constraint violations.

Usage:
    python scripts/reset_admin.py
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

def reset_admin_user():
    """Reset the admin user with proper cascade handling"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import Flask app and models
        from app import create_app, db
        from app.models import User
        from app.models.admin import AdminUser
        from app.services.auth_manager import auth_manager
        
        # Create app context
        app = create_app('production')
        
        with app.app_context():
            logger.info('🔄 Resetting admin user...')
            
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
            
            # Remove existing admin users and their AdminUser records
            for user in existing_users:
                logger.info(f'🗑️ Removing existing admin user: {user.email} (username: {user.username})')
                
                # First, remove any AdminUser records that reference this user
                # Try using the relationship first
                try:
                    if hasattr(user, 'admin_profile') and user.admin_profile:
                        logger.info(f'🗑️ Removing AdminUser record for user via relationship: {user.email}')
                        db.session.delete(user.admin_profile)
                except Exception:
                    # Fallback to direct query
                    admin_user_record = AdminUser.query.filter_by(user_id=user.id).first()
                    if admin_user_record:
                        logger.info(f'🗑️ Removing AdminUser record for user via query: {user.email}')
                        db.session.delete(admin_user_record)
                
                # Then remove the user
                db.session.delete(user)
            
            # Commit deletions
            if existing_users:
                db.session.commit()
                logger.info('✅ Existing admin users and AdminUser records removed')
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
            
            logger.info('✅ Admin user reset completed successfully!')
            logger.info(f'📧 Email: {admin_email}')
            logger.info(f'👤 Username: {admin_username}')
            logger.info(f'🔑 Password: {admin_password}')
            logger.info(f'🎭 Role: super_admin')
            
            return True
            
    except Exception as e:
        logger.error(f'❌ Failed to reset admin user: {str(e)}')
        
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
    
    logger.info('🚀 Starting admin user reset script...')
    
    success = reset_admin_user()
    
    if success:
        logger.info('🎉 Admin user reset completed successfully!')
        sys.exit(0)
    else:
        logger.error('💥 Admin user reset failed!')
        sys.exit(1)
