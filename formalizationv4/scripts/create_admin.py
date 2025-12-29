#!/usr/bin/env python3
"""
Script to create or update admin user with specific credentials.
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import User, AdminUser
from app.services.auth_manager import auth_manager

def create_admin_user(email, password, force_update=False):
    """Create or update admin user with specified credentials."""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email=email).first()
        
        if existing_admin and not force_update:
            print(f"Admin user {email} already exists. Use --force to update.")
            return False
        
        if existing_admin:
            print(f"Updating existing admin user: {email}")
            # Update existing user
            existing_admin.password_hash = auth_manager.hash_password(password)
            existing_admin.username = email.split('@')[0] if not existing_admin.username else existing_admin.username
            existing_admin.is_admin = True
            existing_admin.is_active = True
            
            # Ensure admin profile exists
            admin_profile = AdminUser.query.filter_by(user_id=existing_admin.id).first()
            if not admin_profile:
                admin_profile = AdminUser(
                    user_id=existing_admin.id,
                    role='super_admin',
                    access_level=100,
                    can_access_all_users=True,
                    can_modify_credits=True,
                    can_manage_queue=True,
                    can_view_analytics=True,
                    can_manage_system=True,
                    can_access_sales_intelligence=True
                )
                db.session.add(admin_profile)
            
            db.session.commit()
            print(f"✅ Admin user {email} updated successfully")
            
        else:
            print(f"Creating new admin user: {email}")
            # Create new admin user
            admin_user = User(
                email=email,
                username=email.split('@')[0],
                password_hash=auth_manager.hash_password(password),
                first_name='System',
                last_name='Administrator',
                is_admin=True,
                is_active=True,
                credits_balance=10000  # High credit limit for admin
            )
            db.session.add(admin_user)
            db.session.flush()  # Get the user ID
            
            # Create admin profile
            admin_profile = AdminUser(
                user_id=admin_user.id,
                role='super_admin',
                access_level=100,
                can_access_all_users=True,
                can_modify_credits=True,
                can_manage_queue=True,
                can_view_analytics=True,
                can_manage_system=True,
                can_access_sales_intelligence=True
            )
            db.session.add(admin_profile)
            db.session.commit()
            
            print(f"✅ Admin user {email} created successfully")
        
        return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Create or update admin user')
    parser.add_argument('--email', default='admin@bearsystems.co.in', help='Admin email address')
    parser.add_argument('--password', default='Benzie1!Benzie1!Benzie1!Benzie1!', help='Admin password')
    parser.add_argument('--force', action='store_true', help='Force update existing user')
    
    args = parser.parse_args()
    
    success = create_admin_user(args.email, args.password, args.force)
    if success:
        print(f"\n🎉 Admin setup complete!")
        print(f"Email: {args.email}")
        print(f"Password: {args.password}")
        print("\nYou can now use these credentials to log in to the admin dashboard.")
