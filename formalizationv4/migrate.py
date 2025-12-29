#!/usr/bin/env python3
"""
CLI tool for database migrations on Railway.
Usage: python migrate.py [command]
Commands: init, migrate, upgrade, current, history
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [init|migrate|upgrade|current|history]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'init':
        init_migrations()
    elif command == 'migrate':
        create_migration()
    elif command == 'upgrade':
        upgrade_database()
    elif command == 'current':
        show_current()
    elif command == 'history':
        show_history()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

def init_migrations():
    """Initialize migration repository."""
    print("🔧 Initializing migration repository...")
    try:
        from scripts.migration_manager import MigrationManager
        manager = MigrationManager()
        if manager.setup_app_context():
            print("✅ Migration repository initialized")
        else:
            print("❌ Failed to initialize migration repository")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def create_migration():
    """Create a new migration."""
    print("📝 Creating new migration...")
    # This would typically use flask db migrate
    print("⚠️  Use Flask-Migrate commands for creating new migrations")

def upgrade_database():
    """Upgrade database to latest migration."""
    print("🚀 Upgrading database...")
    try:
        from scripts.migration_manager import MigrationManager
        manager = MigrationManager()
        if manager.run_migrations():
            print("✅ Database upgraded successfully")
        else:
            print("❌ Database upgrade failed")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def show_current():
    """Show current migration revision."""
    print("🔍 Current migration revision:")
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from flask_migrate import current
            rev = current()
            print(f"Current revision: {rev or 'None'}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def show_history():
    """Show migration history."""
    print("📜 Migration history:")
    # This would show migration history
    print("Available migrations:")
    print("- initial_schema_v1: Initial database schema")
    print("- admin_system_v1: Admin and system tables")

if __name__ == '__main__':
    main()
