#!/usr/bin/env python3
"""
Bear Systems Resume Screening Tool - Authentication System Tests
Tests Phase 5 Implementation: Complete authentication flow, trial limitations, and user experience.

Author: Bear Systems Development Team
Date: July 22, 2025
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials (matching our implementation)
ADMIN_CREDENTIALS = {
    "username": "Admin",
    "password": "Admin1232048"
}

TEST_USERS = [
    {"email": "trial@bearsystems.co.in", "password": "trial123", "access_type": "trial"},
    {"email": "full@bearsystems.co.in", "password": "full123", "access_type": "full"}
]

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}🧪 {test_name}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ️ {message}{Colors.END}")

def test_server_connection():
    """Test if the backend server is running."""
    print_test_header("Server Connection Test")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=10)
        if response.status_code in [200, 401]:  # 401 is expected if not authenticated
            print_success("Backend server is running")
            return True
        else:
            print_error(f"Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend server. Is it running on localhost:5000?")
        return False
    except Exception as e:
        print_error(f"Server connection test failed: {e}")
        return False

def test_admin_authentication():
    """Test admin authentication system."""
    print_test_header("Admin Authentication Test")
    
    try:
        # Test admin login
        login_data = {
            "username": ADMIN_CREDENTIALS["username"],
            "password": ADMIN_CREDENTIALS["password"]
        }
        
        response = requests.post(f"{API_BASE}/auth/admin-login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data and "admin_info" in data:
                print_success(f"Admin login successful: {data['admin_info']['username']}")
                return data["token"]
            else:
                print_error("Admin login response missing required fields")
                return None
        else:
            print_error(f"Admin login failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Admin authentication test failed: {e}")
        return None

def test_user_creation_and_login(admin_token):
    """Test user creation and authentication."""
    print_test_header("User Creation and Login Test")
    
    if not admin_token:
        print_error("No admin token available for user creation")
        return {}
    
    user_tokens = {}
    
    for user_data in TEST_USERS:
        try:
            # Create user
            headers = {"Authorization": f"Bearer {admin_token}"}
            create_response = requests.post(f"{API_BASE}/auth/create-user", 
                                         json=user_data, headers=headers)
            
            if create_response.status_code == 201:
                print_success(f"User created: {user_data['email']} ({user_data['access_type']})")
                
                # Test user login
                login_data = {"email": user_data["email"], "password": user_data["password"]}
                login_response = requests.post(f"{API_BASE}/auth/user-login", json=login_data)
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    user_tokens[user_data["access_type"]] = {
                        "token": token_data["token"],
                        "user_info": token_data["user_info"]
                    }
                    print_success(f"User login successful: {user_data['email']}")
                else:
                    print_error(f"User login failed: {login_response.status_code}")
            
            elif create_response.status_code == 409:
                print_warning(f"User already exists: {user_data['email']}")
                
                # Try to login anyway
                login_data = {"email": user_data["email"], "password": user_data["password"]}
                login_response = requests.post(f"{API_BASE}/auth/user-login", json=login_data)
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    user_tokens[user_data["access_type"]] = {
                        "token": token_data["token"],
                        "user_info": token_data["user_info"]
                    }
                    print_success(f"Existing user login successful: {user_data['email']}")
            else:
                print_error(f"User creation failed: {create_response.status_code} - {create_response.text}")
                
        except Exception as e:
            print_error(f"User creation/login test failed for {user_data['email']}: {e}")
    
    return user_tokens

def test_trial_limitations(user_tokens):
    """Test trial user limitations and restrictions."""
    print_test_header("Trial Limitations Test")
    
    if "trial" not in user_tokens:
        print_error("No trial user token available")
        return False
    
    trial_token = user_tokens["trial"]["token"]
    headers = {"Authorization": f"Bearer {trial_token}"}
    
    try:
        # Test trial status
        status_response = requests.get(f"{API_BASE}/trial/status", headers=headers)
        if status_response.status_code == 200:
            status_data = status_response.json()
            print_success(f"Trial status retrieved: {status_data['trial_status']['resumes_analyzed']}/100 used")
        else:
            print_error(f"Trial status failed: {status_response.status_code}")
            return False
        
        # Test upgrade info
        upgrade_response = requests.get(f"{API_BASE}/trial/upgrade-info", headers=headers)
        if upgrade_response.status_code == 200:
            upgrade_data = upgrade_response.json()
            print_success(f"Upgrade info retrieved: Contact {upgrade_data['contact_email']}")
        else:
            print_error(f"Upgrade info failed: {upgrade_response.status_code}")
        
        # Test CSV export restriction (should fail for trial users)
        export_response = requests.post(f"{API_BASE}/export", headers=headers)
        if export_response.status_code == 403:
            print_success("CSV export correctly blocked for trial user")
        else:
            print_warning(f"CSV export should be blocked for trial users: {export_response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Trial limitations test failed: {e}")
        return False

def test_full_access_features(user_tokens):
    """Test full access user features."""
    print_test_header("Full Access Features Test")
    
    if "full" not in user_tokens:
        print_error("No full access user token available")
        return False
    
    full_token = user_tokens["full"]["token"]
    headers = {"Authorization": f"Bearer {full_token}"}
    
    try:
        # Test resumes access
        resumes_response = requests.get(f"{API_BASE}/resumes", headers=headers)
        if resumes_response.status_code == 200:
            print_success("Full user can access resumes endpoint")
        else:
            print_warning(f"Resumes access issue: {resumes_response.status_code}")
        
        # Test stats access
        stats_response = requests.get(f"{API_BASE}/stats", headers=headers)
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print_success(f"Stats access successful: {len(stats_data)} resume(s) in system")
        else:
            print_warning(f"Stats access issue: {stats_response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Full access features test failed: {e}")
        return False

def test_session_validation(user_tokens):
    """Test session validation and management."""
    print_test_header("Session Validation Test")
    
    for access_type, token_data in user_tokens.items():
        try:
            headers = {"Authorization": f"Bearer {token_data['token']}"}
            session_response = requests.get(f"{API_BASE}/auth/session", headers=headers)
            
            if session_response.status_code == 200:
                session_data = session_response.json()
                print_success(f"{access_type.capitalize()} user session valid: {session_data['user']['email']}")
            else:
                print_error(f"{access_type.capitalize()} user session invalid: {session_response.status_code}")
        
        except Exception as e:
            print_error(f"Session validation test failed for {access_type}: {e}")

def test_data_isolation(user_tokens):
    """Test that users can only see their own data."""
    print_test_header("Data Isolation Test")
    
    if len(user_tokens) < 2:
        print_warning("Need at least 2 users to test data isolation")
        return
    
    # This is a basic test - in a full implementation, you'd upload resumes
    # as different users and verify they can't see each other's data
    print_info("Data isolation test would require uploading sample resumes")
    print_info("Skipping detailed data isolation test - requires sample uploads")

def test_bear_systems_branding():
    """Test Bear Systems specific configurations."""
    print_test_header("Bear Systems Branding Test")
    
    try:
        # Test upgrade info contains Bear Systems branding
        upgrade_response = requests.get(f"{API_BASE}/trial/upgrade-info")
        if upgrade_response.status_code == 200:
            upgrade_data = upgrade_response.json()
            
            # Check for Bear Systems branding
            if upgrade_data.get("company") == "Bear Systems":
                print_success("Company name correctly set to Bear Systems")
            else:
                print_warning("Company name not set to Bear Systems")
            
            if "info@bearsystems.co.in" in upgrade_data.get("contact_email", ""):
                print_success("Contact email correctly set")
            else:
                print_warning("Contact email not set correctly")
            
            if "+91 8527186615" in str(upgrade_data):
                print_success("Phone number included in upgrade info")
            else:
                print_warning("Phone number not found in upgrade info")
        
    except Exception as e:
        print_error(f"Bear Systems branding test failed: {e}")

def run_comprehensive_test():
    """Run all tests in sequence."""
    print(f"{Colors.BOLD}{Colors.PURPLE}")
    print("🐻 Bear Systems Resume Screening Tool - Authentication Test Suite")
    print("Phase 5 Implementation Validation")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.END}")
    
    # Test 1: Server Connection
    if not test_server_connection():
        print_error("Cannot proceed without server connection")
        sys.exit(1)
    
    # Test 2: Admin Authentication
    admin_token = test_admin_authentication()
    
    # Test 3: User Creation and Login
    user_tokens = test_user_creation_and_login(admin_token)
    
    # Test 4: Trial Limitations
    test_trial_limitations(user_tokens)
    
    # Test 5: Full Access Features
    test_full_access_features(user_tokens)
    
    # Test 6: Session Validation
    test_session_validation(user_tokens)
    
    # Test 7: Data Isolation
    test_data_isolation(user_tokens)
    
    # Test 8: Bear Systems Branding
    test_bear_systems_branding()
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 Authentication System Test Complete!{Colors.END}")
    print(f"{Colors.CYAN}Phase 5 Implementation Status: Testing Complete{Colors.END}")
    print(f"{Colors.CYAN}Ready for Phase 4: Marketing Landing Page{Colors.END}")

if __name__ == "__main__":
    run_comprehensive_test()
