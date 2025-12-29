#!/usr/bin/env python3
"""
Setup script for development environment.
Installs dependencies, sets up database, and downloads Ollama model.
"""
import os
import sys
import subprocess
import time

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def check_requirements():
    """Check if required tools are installed."""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        return False
    
    # Check if pip is available
    try:
        subprocess.run(['pip', '--version'], check=True, capture_output=True)
        print("✅ pip is available")
    except subprocess.CalledProcessError:
        print("❌ pip is not available")
        return False
    
    # Check if PostgreSQL is available (optional warning)
    try:
        subprocess.run(['psql', '--version'], check=True, capture_output=True)
        print("✅ PostgreSQL is available")
    except subprocess.CalledProcessError:
        print("⚠️  PostgreSQL not found - you'll need a database connection")
    
    return True

def setup_python_environment():
    """Set up Python virtual environment and install dependencies."""
    # Create virtual environment if it doesn't exist
    if not os.path.exists('venv'):
        run_command('python -m venv venv', 'Creating virtual environment')
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate'
        pip_cmd = 'venv\\Scripts\\pip'
    else:  # Unix/Linux/macOS
        activate_cmd = 'source venv/bin/activate'
        pip_cmd = 'venv/bin/pip'
    
    # Install dependencies
    run_command(f'{pip_cmd} install --upgrade pip', 'Upgrading pip')
    run_command(f'{pip_cmd} install -r requirements.txt', 'Installing Python dependencies')

def setup_environment_file():
    """Create .env file from example if it doesn't exist."""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            run_command('copy .env.example .env' if os.name == 'nt' else 'cp .env.example .env', 
                       'Creating .env file from example')
            print("⚠️  Please update .env file with your actual configuration values")
        else:
            print("⚠️  No .env.example found - please create .env file manually")
    else:
        print("✅ .env file already exists")

def create_directories():
    """Create necessary directories."""
    directories = ['uploads', 'logs', 'migrations']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory already exists: {directory}")

def check_ollama():
    """Check if Ollama is available and has the required model."""
    print("\n🔍 Checking Ollama setup...")
    
    # Check if Ollama is installed
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ollama is installed and running")
            
            # Check if qwen2.5:7b model is available
            if 'qwen2.5:7b' in result.stdout:
                print("✅ QWEN2.5 7B model is available")
            else:
                print("⚠️  QWEN2.5 7B model not found")
                pull_model = input("Would you like to pull the QWEN2.5 7B model? (y/n): ")
                if pull_model.lower() == 'y':
                    print("🔄 Pulling QWEN2.5 7B model (this may take a while)...")
                    result = run_command('ollama pull qwen2.5:7b', 'Pulling QWEN2.5 7B model')
                    if result:
                        print("✅ QWEN2.5 7B model pulled successfully")
        else:
            print("❌ Ollama is not running or not accessible")
            
    except subprocess.TimeoutExpired:
        print("❌ Ollama command timed out - service may not be running")
    except FileNotFoundError:
        print("❌ Ollama not found - please install Ollama first")
        print("   Visit: https://ollama.ai/download")

def main():
    """Main setup function."""
    print("🚀 Setting up ResumeAI Pro development environment")
    print("="*50)
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements check failed")
        return
    
    # Setup steps
    setup_environment_file()
    create_directories()
    setup_python_environment()
    check_ollama()
    
    print("\n" + "="*50)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Update .env file with your database and other configurations")
    print("2. Start your PostgreSQL database")
    print("3. Start Ollama service")
    print("4. Run: python scripts/init_db.py --seed")
    print("5. Run: python run.py")
    print("\nFor Docker setup, run: docker-compose up")

if __name__ == '__main__':
    main()
