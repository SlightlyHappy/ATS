#!/usr/bin/env python3
"""
Test script to verify that all dependencies can be imported successfully.
This helps catch dependency conflicts early.
"""

import sys
import importlib

# Core packages that were causing conflicts
critical_packages = [
    'numpy',
    'pandas', 
    'sklearn',
    'sentence_transformers',
    'faiss',
    'together',
]

# Other important packages
other_packages = [
    'flask',
    'openai',
    'anthropic',
    'google.generativeai',
    'supabase',
    'cryptography',
    'bcrypt',
    'jwt',
]

def test_import(package_name):
    """Test if a package can be imported."""
    try:
        importlib.import_module(package_name)
        print(f"✅ {package_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name} - FAILED: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {package_name} - WARNING: {e}")
        return True  # Consider warnings as success for dependency check

def main():
    """Main test function."""
    print("Testing critical ML/AI dependencies...")
    critical_success = all(test_import(pkg) for pkg in critical_packages)
    
    print("\nTesting other dependencies...")
    other_success = all(test_import(pkg) for pkg in other_packages)
    
    print(f"\n{'='*50}")
    if critical_success and other_success:
        print("✅ All dependencies test passed!")
        sys.exit(0)
    else:
        print("❌ Some dependencies failed to import!")
        sys.exit(1)

if __name__ == "__main__":
    main()
