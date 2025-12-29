"""
HR Templates Auto-Fix Service
Automatically detects and fixes common HR templates database issues
"""
import logging
from typing import Dict, Any, Tuple
from sqlalchemy import text
from app import db
from app.models.communication import HRTemplate, TemplateCategory, TemplateType, ComplianceLevel, TemplateStatus

logger = logging.getLogger(__name__)

class HRTemplatesAutoFixService:
    """Service to automatically detect and fix HR templates issues."""
    
    @staticmethod
    def detect_issues() -> Dict[str, Any]:
        """
        Detect common issues with HR templates setup.
        
        Returns:
            Dict containing detected issues and their severity
        """
        issues = {
            'user_id_constraint': False,
            'missing_system_templates': False,
            'table_missing': False,
            'foreign_key_issues': False
        }
        
        try:
            # Check if table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'hr_templates'
                )
            """)).fetchone()
            
            if not result[0]:
                issues['table_missing'] = True
                return issues
            
            # Check user_id column constraint
            result = db.session.execute(text("""
                SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'hr_templates' 
                AND column_name = 'user_id'
            """)).fetchone()
            
            if result and result[1] == 'NO':  # is_nullable = 'NO'
                issues['user_id_constraint'] = True
            
            # Check if system templates exist
            try:
                system_template_count = HRTemplate.query.filter_by(is_system_template=True).count()
                if system_template_count == 0:
                    issues['missing_system_templates'] = True
            except Exception:
                # If query fails, likely a schema issue
                issues['foreign_key_issues'] = True
            
        except Exception as e:
            logger.error(f"Error detecting HR templates issues: {str(e)}")
            issues['detection_error'] = str(e)
        
        return issues
    
    @staticmethod
    def fix_user_id_constraint() -> Tuple[bool, str]:
        """
        Fix the user_id constraint to allow NULL values for system templates.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info("Fixing HR templates user_id constraint...")
            
            # Check if fix is needed
            result = db.session.execute(text("""
                SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'hr_templates' 
                AND column_name = 'user_id'
            """)).fetchone()
            
            if not result:
                return False, "hr_templates table or user_id column not found"
            
            if result[1] == 'YES':  # is_nullable = 'YES'
                return True, "user_id column is already nullable"
            
            # Drop the foreign key constraint temporarily
            db.session.execute(text("""
                ALTER TABLE hr_templates 
                DROP CONSTRAINT IF EXISTS hr_templates_user_id_fkey
            """))
            
            # Alter the column to allow NULL
            db.session.execute(text("""
                ALTER TABLE hr_templates 
                ALTER COLUMN user_id DROP NOT NULL
            """))
            
            # Re-add the foreign key constraint
            db.session.execute(text("""
                ALTER TABLE hr_templates 
                ADD CONSTRAINT hr_templates_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(id)
            """))
            
            db.session.commit()
            logger.info("HR templates user_id constraint fixed successfully")
            return True, "user_id constraint fixed successfully"
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to fix user_id constraint: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def create_system_templates() -> Tuple[bool, str]:
        """
        Create default system templates.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info("Creating system templates...")
            
            # Check if system templates already exist
            existing_count = HRTemplate.query.filter_by(is_system_template=True).count()
            if existing_count > 0:
                return True, f"System templates already exist ({existing_count} templates)"
            
            # System templates data
            system_templates = [
                {
                    'category': TemplateCategory.SCREENING,
                    'name': 'Initial Screening Email',
                    'description': 'Professional initial screening communication',
                    'subject': 'Application Received - {{position_title}} at {{company_name}}',
                    'content': '''Dear {{candidate_name}},

Thank you for your interest in the {{position_title}} position at {{company_name}}. We have received your application and are currently reviewing it.

Our recruitment team will evaluate your qualifications and experience. If your profile matches our requirements, we will contact you within the next 5-7 business days to discuss the next steps.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
                    'variables': ["candidate_name", "position_title", "company_name", "recruiter"]
                },
                {
                    'category': TemplateCategory.PHONE_INTERVIEW,
                    'name': 'Phone Interview Invitation',
                    'description': 'Professional phone interview scheduling email',
                    'subject': 'Phone Interview Invitation - {{position_title}} Position',
                    'content': '''Dear {{candidate_name}},

We are pleased to invite you for a phone interview for the {{position_title}} position at {{company_name}}.

Interview Details:
- Date: {{interview_date}}
- Time: {{interview_time}}
- Duration: Approximately 30-45 minutes
- Interviewer: {{interviewer_name}}, {{interviewer_title}}

Please confirm your availability by replying to this email.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
                    'variables': ["candidate_name", "position_title", "company_name", "interview_date", "interview_time", "interviewer_name", "interviewer_title", "recruiter"]
                },
                {
                    'category': TemplateCategory.REJECTION,
                    'name': 'Professional Rejection Email',
                    'description': 'Respectful candidate rejection communication',
                    'subject': 'Update on Your Application - {{position_title}} Position',
                    'content': '''Dear {{candidate_name}},

Thank you for your interest in the {{position_title}} position at {{company_name}} and for taking the time to participate in our recruitment process.

After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current requirements.

We appreciate your time and interest in {{company_name}}. We wish you all the best in your career endeavors.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
                    'variables': ["candidate_name", "position_title", "company_name", "recruiter"]
                }
            ]
            
            created_count = 0
            for template_data in system_templates:
                template = HRTemplate(
                    user_id=None,  # System template
                    name=template_data['name'],
                    description=template_data['description'],
                    category=template_data['category'],
                    template_type=TemplateType.EMAIL,
                    subject_template=template_data['subject'],
                    content_template=template_data['content'],
                    variables=template_data['variables'],
                    compliance_level=ComplianceLevel.STANDARD,
                    personalization_enabled=True,
                    ai_enhancement_enabled=True,
                    status=TemplateStatus.ACTIVE,
                    version='1.0',
                    is_system_template=True,
                    ai_model_used='system_generated',
                    ai_confidence_score=1.0
                )
                
                db.session.add(template)
                created_count += 1
            
            db.session.commit()
            message = f"Created {created_count} system templates successfully"
            logger.info(message)
            return True, message
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to create system templates: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @classmethod
    def auto_fix_all_issues(cls) -> Dict[str, Any]:
        """
        Automatically detect and fix all HR templates issues.
        
        Returns:
            Dict containing results of all fixes attempted
        """
        results = {
            'issues_detected': {},
            'fixes_attempted': {},
            'overall_success': False
        }
        
        try:
            # Detect issues
            issues = cls.detect_issues()
            results['issues_detected'] = issues
            
            fixes_successful = 0
            fixes_total = 0
            
            # Fix user_id constraint if needed
            if issues.get('user_id_constraint'):
                fixes_total += 1
                success, message = cls.fix_user_id_constraint()
                results['fixes_attempted']['user_id_constraint'] = {
                    'success': success,
                    'message': message
                }
                if success:
                    fixes_successful += 1
            
            # Create system templates if needed
            if issues.get('missing_system_templates') or issues.get('user_id_constraint'):
                fixes_total += 1
                success, message = cls.create_system_templates()
                results['fixes_attempted']['system_templates'] = {
                    'success': success,
                    'message': message
                }
                if success:
                    fixes_successful += 1
            
            # Determine overall success
            if fixes_total == 0:
                results['overall_success'] = True
                results['message'] = "No issues detected"
            else:
                results['overall_success'] = fixes_successful == fixes_total
                results['message'] = f"Fixed {fixes_successful}/{fixes_total} issues"
            
        except Exception as e:
            results['error'] = str(e)
            results['overall_success'] = False
            logger.error(f"Error in auto-fix process: {str(e)}")
        
        return results
