#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables and optionally seeds with sample data.
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import User, CreditTransaction, Resume, Analysis, AnalysisQueue, BatchUpload

def init_database(seed_data=False):
    """Initialize database tables."""
    app = create_app()
    
    with app.app_context():
        # Drop all tables if they exist
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating tables...")
        db.create_all()
        
        if seed_data:
            print("Seeding sample data...")
            seed_sample_data()
        
        print("Database initialization completed!")

def seed_sample_data():
    """Create sample data for testing."""
    # Create sample admin user
    admin = User(
        email='admin@example.com',
        username='admin',
        first_name='Admin',
        last_name='User',
        is_admin=True,
        credits_balance=1000  # Admin gets lots of credits
    )
    db.session.add(admin)
    
    # Create sample regular user
    user = User(
        email='user@example.com',
        username='user',
        first_name='Test',
        last_name='User',
        is_admin=False,
        credits_balance=10  # Regular user gets default credits
    )
    db.session.add(user)
    
    db.session.commit()
    
    print(f"Created sample admin: {admin.email} (Credits: {admin.credits_balance})")
    print(f"Created sample user: {user.email} (Credits: {user.credits_balance})")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize database')
    parser.add_argument('--seed', action='store_true', help='Seed with sample data')
    
    args = parser.parse_args()
    init_database(seed_data=args.seed)
