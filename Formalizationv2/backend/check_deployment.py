#!/usr/bin/env python3
"""
Environment Configuration Helper for Railway Deployment
Helps set up environment variables for the enhanced HR backend
"""

import os
import sys
from pathlib import Path

def check_env_vars():
    """Check which environment variables are configured"""
    print("🔍 Checking Environment Variables\n")
    
    required_vars = {
        'SUPABASE_URL': 'Database connection URL',
        'SUPABASE_KEY': 'Database authentication key',
        'SECRET_KEY': 'Flask application secret key',
        'FRONTEND_URL': 'Frontend application URL'
    }
    
    ai_providers = {
        'OPENAI_API_KEY': 'OpenAI API access',
        'GEMINI_API_KEY': 'Google Gemini API access',
        'ANTHROPIC_API_KEY': 'Anthropic Claude API access',
        'TOGETHER_API_KEY': 'Together AI API access',
        'OLLAMA_URL': 'Ollama server URL'
    }
    
    optional_vars = {
        'DEFAULT_AI_PROVIDER': 'Primary AI provider (openai, gemini, etc.)',
        'MAX_CONCURRENT_PROCESSING': 'Max concurrent resume processing',
        'HR_LEGAL_ENABLED': 'Enable HR Legal system (true/false)',
        'ENABLE_AGENTIC_ANALYSIS': 'Enable advanced AI analysis'
    }
    
    print("📋 REQUIRED VARIABLES:")
    all_required_set = True
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var} - {desc}")
        else:
            print(f"  ❌ {var} - {desc} (NOT SET)")
            all_required_set = False
    
    print("\n🤖 AI PROVIDER VARIABLES (at least one needed):")
    ai_provider_set = False
    for var, desc in ai_providers.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var} - {desc}")
            ai_provider_set = True
        else:
            print(f"  ⚪ {var} - {desc}")
    
    print("\n⚙️ OPTIONAL VARIABLES:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var} = {value} - {desc}")
        else:
            print(f"  ⚪ {var} - {desc} (using default)")
    
    print("\n" + "="*50)
    
    if all_required_set and ai_provider_set:
        print("🎉 READY FOR DEPLOYMENT!")
        print("All required variables are set and at least one AI provider is configured.")
        return True
    else:
        print("⚠️  MISSING REQUIRED VARIABLES")
        if not all_required_set:
            print("Please set all required variables before deployment.")
        if not ai_provider_set:
            print("Please set at least one AI provider API key.")
        return False

def generate_railway_commands():
    """Generate Railway CLI commands to set environment variables"""
    print("\n🚀 Railway CLI Commands to Set Variables:")
    print("Copy and run these commands to set your environment variables:\n")
    
    print("# Required variables")
    print("npx @railway/cli variables set SUPABASE_URL=your_supabase_url")
    print("npx @railway/cli variables set SUPABASE_KEY=your_supabase_key")
    print("npx @railway/cli variables set SECRET_KEY=your_secret_key")
    print("npx @railway/cli variables set FRONTEND_URL=https://hrtool-sable.vercel.app")
    
    print("\n# AI Provider (choose at least one)")
    print("npx @railway/cli variables set OPENAI_API_KEY=your_openai_key")
    print("npx @railway/cli variables set GEMINI_API_KEY=your_gemini_key")
    
    print("\n# Optional configuration")
    print("npx @railway/cli variables set DEFAULT_AI_PROVIDER=openai")
    print("npx @railway/cli variables set HR_LEGAL_ENABLED=true")

def check_files():
    """Check if required files are present"""
    print("\n📁 Checking Required Files:")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'railway.toml',
        'railway_start.py',
        'hr_legal/__init__.py',
        'HRlaw/README.md'
    ]
    
    all_files_present = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (MISSING)")
            all_files_present = False
    
    return all_files_present

def main():
    print("🎯 Railway Deployment Environment Checker")
    print("=" * 50)
    
    # Check files
    files_ok = check_files()
    
    # Check environment variables
    env_ok = check_env_vars()
    
    if not files_ok:
        print("\n❌ Some required files are missing!")
        return False
    
    if not env_ok:
        generate_railway_commands()
        print("\n📖 See RAILWAY_DEPLOYMENT_GUIDE.md for detailed setup instructions.")
        return False
    
    print("\n🚀 Ready to deploy! Run: npx @railway/cli up")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
