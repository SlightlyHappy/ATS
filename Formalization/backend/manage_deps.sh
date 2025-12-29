#!/bin/bash

# Dependency Management Script for Resume Screening App Backend

set -e

echo "🔧 Resume Screening App - Dependency Management"
echo "=============================================="

# Function to create virtual environment
create_venv() {
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    echo "✅ Virtual environment created and activated"
}

# Function to install production dependencies
install_prod() {
    echo "📦 Installing production dependencies..."
    pip install --no-cache-dir -r requirements.txt
    echo "✅ Production dependencies installed"
}

# Function to install development dependencies
install_dev() {
    echo "📦 Installing development dependencies..."
    pip install --no-cache-dir -r requirements.txt
    pip install --no-cache-dir -r requirements-dev.txt
    echo "✅ Development dependencies installed"
}

# Function to update dependencies
update_deps() {
    echo "🔄 Updating dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install --upgrade -r requirements.txt
    if [ -f "requirements-dev.txt" ]; then
        pip install --upgrade -r requirements-dev.txt
    fi
    echo "✅ Dependencies updated"
}

# Function to freeze current dependencies
freeze_deps() {
    echo "❄️ Freezing current dependencies..."
    pip freeze > requirements-frozen.txt
    echo "✅ Dependencies frozen to requirements-frozen.txt"
}

# Function to check for security vulnerabilities
security_check() {
    echo "🔒 Running security checks..."
    if command -v safety &> /dev/null; then
        safety check
    else
        echo "⚠️ Safety not installed. Install with: pip install safety"
    fi
    echo "✅ Security check completed"
}

# Main menu
case "$1" in
    "venv")
        create_venv
        ;;
    "prod")
        install_prod
        ;;
    "dev")
        install_dev
        ;;
    "update")
        update_deps
        ;;
    "freeze")
        freeze_deps
        ;;
    "security")
        security_check
        ;;
    "clean")
        echo "🧹 Cleaning up..."
        pip cache purge
        echo "✅ Cache cleaned"
        ;;
    *)
        echo "Usage: $0 {venv|prod|dev|update|freeze|security|clean}"
        echo ""
        echo "Commands:"
        echo "  venv     - Create and activate virtual environment"
        echo "  prod     - Install production dependencies only"
        echo "  dev      - Install both production and development dependencies"
        echo "  update   - Update all dependencies to latest versions"
        echo "  freeze   - Freeze current dependencies to requirements-frozen.txt"
        echo "  security - Run security vulnerability checks"
        echo "  clean    - Clean pip cache"
        echo ""
        echo "Example: ./manage_deps.sh dev"
        exit 1
        ;;
esac
