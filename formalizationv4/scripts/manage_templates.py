"""
HR Communication Templates Management Script.
Provides CLI commands for template management and initialization.
"""
import asyncio
import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.communication import HRTemplate, TemplateGeneration, ComplianceRule
from app.services.hr_template_service import HRTemplateService, TemplateLibraryService

logger = logging.getLogger(__name__)

class TemplateManager:
    """Manager class for HR communication templates operations."""
    
    def __init__(self):
        self.app = create_app()
        self.template_service = HRTemplateService()
        self.library_service = TemplateLibraryService()
    
    def run_migration(self):
        """Run database migration for communication templates."""
        with self.app.app_context():
            try:
                logger.info("Running HR Communication Templates migration...")
                
                # Import the migration script
                from scripts.hr_communication_migration import run_migration
                success = run_migration()
                
                if success:
                    logger.info("✓ Migration completed successfully")
                else:
                    logger.error("✗ Migration failed")
                
                return success
                
            except Exception as e:
                logger.error(f"Migration error: {str(e)}")
                return False
    
    def initialize_system_templates(self):
        """Initialize system templates."""
        with self.app.app_context():
            try:
                logger.info("Initializing system templates...")
                
                templates = asyncio.run(self.library_service.initialize_system_templates())
                
                logger.info(f"✓ Initialized {len(templates)} system templates")
                
                # Display created templates
                for template in templates:
                    logger.info(f"  - {template.name} ({template.category.value})")
                
                return True
                
            except Exception as e:
                logger.error(f"Template initialization error: {str(e)}")
                return False
    
    def list_templates(self, user_id=None):
        """List all templates in the system."""
        with self.app.app_context():
            try:
                if user_id:
                    templates = HRTemplate.query.filter_by(user_id=user_id).all()
                    logger.info(f"Templates for user {user_id}:")
                else:
                    templates = HRTemplate.query.all()
                    logger.info("All templates in system:")
                
                if not templates:
                    logger.info("  No templates found")
                    return True
                
                # Group by category
                by_category = {}
                for template in templates:
                    category = template.category.value
                    if category not in by_category:
                        by_category[category] = []
                    by_category[category].append(template)
                
                for category, cat_templates in by_category.items():
                    logger.info(f"\n  {category.upper()}:")
                    for template in cat_templates:
                        status_icon = "📝" if template.status.value == "draft" else "✅" if template.status.value == "active" else "📁"
                        system_icon = "🔧" if template.is_system_template else "👤"
                        usage = template.usage_count or 0
                        logger.info(f"    {status_icon} {system_icon} {template.name} (used {usage} times)")
                
                logger.info(f"\nTotal: {len(templates)} templates")
                return True
                
            except Exception as e:
                logger.error(f"List templates error: {str(e)}")
                return False
    
    def test_template_generation(self, category="screening"):
        """Test template generation functionality."""
        with self.app.app_context():
            try:
                logger.info(f"Testing template generation for category: {category}")
                
                # Import required enums
                from app.models.communication import TemplateCategory, TemplateType, ComplianceLevel
                
                # Create a test user if needed
                from app.models.user import User
                test_user = User.query.filter_by(email='test@template.com').first()
                if not test_user:
                    test_user = User(
                        email='test@template.com',
                        username='test_template_user',
                        password_hash='test_hash',
                        is_admin=False,
                        credits_remaining=10
                    )
                    db.session.add(test_user)
                    db.session.commit()
                    logger.info("Created test user for template generation")
                
                # Generate template
                template_category = TemplateCategory(category)
                template = asyncio.run(self.template_service.generate_template(
                    user_id=str(test_user.id),
                    category=template_category,
                    template_type=TemplateType.EMAIL,
                    compliance_level=ComplianceLevel.STANDARD,
                    custom_requirements="This is a test template generation"
                ))
                
                logger.info("✓ Template generated successfully")
                logger.info(f"  Name: {template.name}")
                logger.info(f"  Category: {template.category.value}")
                logger.info(f"  Variables: {template.variables}")
                logger.info(f"  Subject: {template.subject_template}")
                logger.info(f"  Content preview: {template.content_template[:200]}...")
                
                return True
                
            except Exception as e:
                logger.error(f"Template generation test error: {str(e)}")
                return False
    
    def test_template_personalization(self, template_id):
        """Test template personalization functionality."""
        with self.app.app_context():
            try:
                logger.info(f"Testing template personalization for template: {template_id}")
                
                # Get template
                template = HRTemplate.query.filter_by(id=template_id).first()
                if not template:
                    logger.error("Template not found")
                    return False
                
                # Sample personalization data
                personalization_data = {
                    "candidate_name": "Rajesh Kumar",
                    "first_name": "Rajesh",
                    "last_name": "Kumar",
                    "position_title": "Senior Software Engineer",
                    "company_name": "TechCorp India",
                    "hiring_manager": "Priya Sharma",
                    "recruiter": "Amit Singh",
                    "interview_date": "2024-01-15",
                    "interview_time": "10:00 AM",
                    "phone_number": "+91-9876543210"
                }
                
                # Generate personalized content
                generation = asyncio.run(self.template_service.personalize_template(
                    template_id=template_id,
                    user_id=template.user_id or str(template.id),  # Handle system templates
                    personalization_data=personalization_data
                ))
                
                logger.info("✓ Template personalized successfully")
                logger.info(f"  Template: {template.name}")
                logger.info(f"  Subject: {generation.subject}")
                logger.info(f"  Content preview: {generation.content[:300]}...")
                logger.info(f"  Quality score: {generation.quality_score}")
                
                return True
                
            except Exception as e:
                logger.error(f"Template personalization test error: {str(e)}")
                return False
    
    def validate_compliance(self, template_id):
        """Test compliance validation for a template."""
        with self.app.app_context():
            try:
                logger.info(f"Testing compliance validation for template: {template_id}")
                
                # Get template
                template = HRTemplate.query.filter_by(id=template_id).first()
                if not template:
                    logger.error("Template not found")
                    return False
                
                # Validate compliance
                is_compliant, issues = asyncio.run(
                    self.template_service.validate_compliance(template)
                )
                
                logger.info("✓ Compliance validation completed")
                logger.info(f"  Template: {template.name}")
                logger.info(f"  Compliant: {'Yes' if is_compliant else 'No'}")
                logger.info(f"  Compliance Level: {template.compliance_level.value}")
                
                if issues:
                    logger.info("  Issues found:")
                    for issue in issues:
                        logger.info(f"    - {issue}")
                else:
                    logger.info("  No compliance issues found")
                
                return True
                
            except Exception as e:
                logger.error(f"Compliance validation test error: {str(e)}")
                return False
    
    def cleanup_test_data(self):
        """Clean up test data created during testing."""
        with self.app.app_context():
            try:
                logger.info("Cleaning up test data...")
                
                # Remove test user and their templates
                from app.models.user import User
                test_user = User.query.filter_by(email='test@template.com').first()
                if test_user:
                    # Delete user's templates
                    user_templates = HRTemplate.query.filter_by(user_id=test_user.id).all()
                    for template in user_templates:
                        db.session.delete(template)
                    
                    # Delete user
                    db.session.delete(test_user)
                    db.session.commit()
                    
                    logger.info(f"✓ Cleaned up test user and {len(user_templates)} templates")
                else:
                    logger.info("No test data found to clean up")
                
                return True
                
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")
                db.session.rollback()
                return False

def main():
    """Main CLI function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python manage_templates.py <command> [args]")
        print("\nCommands:")
        print("  migrate              - Run database migration")
        print("  init-system          - Initialize system templates")
        print("  list [user_id]       - List templates (optionally for specific user)")
        print("  test-generate [category] - Test template generation")
        print("  test-personalize <template_id> - Test template personalization")
        print("  validate <template_id> - Test compliance validation")
        print("  cleanup              - Clean up test data")
        print("  full-test            - Run complete test suite")
        return
    
    command = sys.argv[1]
    manager = TemplateManager()
    
    if command == "migrate":
        success = manager.run_migration()
        
    elif command == "init-system":
        success = manager.initialize_system_templates()
        
    elif command == "list":
        user_id = sys.argv[2] if len(sys.argv) > 2 else None
        success = manager.list_templates(user_id)
        
    elif command == "test-generate":
        category = sys.argv[2] if len(sys.argv) > 2 else "screening"
        success = manager.test_template_generation(category)
        
    elif command == "test-personalize":
        if len(sys.argv) < 3:
            print("Error: template_id required")
            return
        template_id = sys.argv[2]
        success = manager.test_template_personalization(template_id)
        
    elif command == "validate":
        if len(sys.argv) < 3:
            print("Error: template_id required")
            return
        template_id = sys.argv[2]
        success = manager.validate_compliance(template_id)
        
    elif command == "cleanup":
        success = manager.cleanup_test_data()
        
    elif command == "full-test":
        logger.info("Running full test suite...")
        
        # Run migration
        if not manager.run_migration():
            logger.error("Migration failed")
            return
        
        # Initialize system templates
        if not manager.initialize_system_templates():
            logger.error("System template initialization failed")
            return
        
        # List templates
        manager.list_templates()
        
        # Test generation
        if not manager.test_template_generation("screening"):
            logger.error("Template generation test failed")
            return
        
        # Get a template for personalization test
        with manager.app.app_context():
            template = HRTemplate.query.first()
            if template:
                manager.test_template_personalization(str(template.id))
                manager.validate_compliance(str(template.id))
        
        logger.info("✓ Full test suite completed successfully")
        success = True
        
    else:
        print(f"Unknown command: {command}")
        return
    
    if success:
        logger.info("✓ Command completed successfully")
    else:
        logger.error("✗ Command failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
