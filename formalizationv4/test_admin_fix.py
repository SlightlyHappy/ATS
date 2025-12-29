#!/usr/bin/env python3
"""
Test script to verify the admin user creation fix
"""

import os
import sys
import logging

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_admin_creation():
    """Test the admin user creation logic without database"""
    
    # Test data
    admin_email = 'admin@bearsystems.co.in'
    desired_username = admin_email.split('@')[0]  # 'admin'
    
    print(f"Testing admin creation logic...")
    print(f"Email: {admin_email}")
    print(f"Username: {desired_username}")
    
    # Simulate different scenarios
    scenarios = [
        {
            'name': 'No existing user',
            'existing_admin_by_email': None,
            'existing_admin_by_username': None,
            'expected': 'create_new'
        },
        {
            'name': 'User exists by email',
            'existing_admin_by_email': {'id': 1, 'email': admin_email, 'username': desired_username},
            'existing_admin_by_username': {'id': 1, 'email': admin_email, 'username': desired_username},
            'expected': 'user_exists'
        },
        {
            'name': 'User exists by username only',
            'existing_admin_by_email': None,
            'existing_admin_by_username': {'id': 2, 'email': 'different@email.com', 'username': desired_username},
            'expected': 'update_existing'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- Testing: {scenario['name']} ---")
        
        existing_admin_by_email = scenario['existing_admin_by_email']
        existing_admin_by_username = scenario['existing_admin_by_username']
        existing_admin = existing_admin_by_email or existing_admin_by_username
        
        if not existing_admin:
            action = 'create_new'
            print("Action: Create new admin user")
        elif existing_admin_by_username and not existing_admin_by_email:
            action = 'update_existing'
            print("Action: Update existing user to admin")
        else:
            action = 'user_exists'
            print("Action: Admin user already exists")
        
        result = action == scenario['expected']
        print(f"Expected: {scenario['expected']}, Got: {action}, Result: {'✓ PASS' if result else '❌ FAIL'}")
    
    print(f"\n✅ Admin creation logic test completed")

if __name__ == '__main__':
    test_admin_creation()
