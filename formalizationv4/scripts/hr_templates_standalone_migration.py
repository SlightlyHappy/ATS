#!/usr/bin/env python3
"""
Standalone HR Communication Templates Migration
This script can be run independently to add HR communication features to an existing deployment.
"""
import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_hr_templates_migration():
    """Run HR Communication Templates migration."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🚀 Starting HR Communication Templates migration...")
            
            # Import models to ensure tables are created
            from app.models.communication import (HRTemplate, TemplateGeneration, ComplianceRule,
                                                TemplateCategory, TemplateType, ComplianceLevel, TemplateStatus)
            
            # Create all tables
            logger.info("📋 Creating HR communication tables...")
            db.create_all()
            
            # Create compliance rules
            logger.info("⚖️  Creating compliance rules...")
            create_compliance_rules()
            
            # Create system templates
            logger.info("📝 Creating system templates...")
            create_system_templates()
            
            # Create indexes
            logger.info("🔍 Creating performance indexes...")
            create_hr_indexes()
            
            logger.info("✅ HR Communication Templates migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def create_compliance_rules():
    """Create initial compliance rules."""
    from app.models.communication import ComplianceRule, ComplianceLevel
    
    # Check if rules already exist
    existing_rules = ComplianceRule.query.filter_by(jurisdiction='India').count()
    if existing_rules > 0:
        logger.info(f"  ✅ Compliance rules already exist ({existing_rules} rules)")
        return
    
    # Indian employment law compliance rules
    india_rules = [
        {
            'name': 'Equal Opportunity Employment',
            'description': 'Ensure equal opportunity and non-discrimination in hiring communications',
            'jurisdiction': 'India',
            'rule_text': 'All hiring communications must maintain equal opportunity principles and avoid discrimination based on gender, religion, caste, nationality, or other protected characteristics.',
            'required_clauses': ['Equal opportunity employer', 'Merit-based selection'],
            'prohibited_content': ['gender preference', 'religion requirement', 'caste requirement', 'matrimonial status'],
            'applicable_categories': ['screening', 'phone_interview', 'technical_interview', 'offer', 'rejection'],
            'compliance_level': 'standard',
            'source': 'Equal Opportunity Employment Guidelines, India'
        },
        {
            'name': 'Offer Letter Legal Requirements',
            'description': 'Legal requirements for job offer letters in India',
            'jurisdiction': 'India',
            'rule_text': 'Job offers must include clear terms of employment, probation period, notice period, and termination clauses as per Indian labor laws.',
            'required_clauses': ['probation period', 'notice period', 'terms and conditions', 'background verification requirement'],
            'prohibited_content': ['unreasonable bond', 'excessive notice period', 'discriminatory conditions'],
            'applicable_categories': ['offer'],
            'compliance_level': 'strict',
            'source': 'Indian Contract Act, 1872 and Labour Laws'
        },
        {
            'name': 'Professional Communication Standards',
            'description': 'Minimum professional standards for HR communications',
            'jurisdiction': 'Global',
            'rule_text': 'All HR communications must maintain professional tone, clear language, and respectful approach towards candidates.',
            'required_clauses': ['professional greeting', 'clear purpose statement', 'respectful closure'],
            'prohibited_content': ['unprofessional language', 'misleading information', 'threatening tone'],
            'applicable_categories': ['screening', 'phone_interview', 'technical_interview', 'on_site_interview', 'final_interview', 'offer', 'offer_followup', 'rejection', 'onboarding', 'reference_request', 'feedback_request', 'general_update'],
            'compliance_level': 'basic',
            'source': 'Professional HR Best Practices'
        }
    ]
    
    created_count = 0
    for rule_data in india_rules:
        rule = ComplianceRule(
            name=rule_data['name'],
            description=rule_data['description'],
            jurisdiction=rule_data['jurisdiction'],
            rule_text=rule_data['rule_text'],
            required_clauses=rule_data['required_clauses'],
            prohibited_content=rule_data['prohibited_content'],
            applicable_categories=rule_data['applicable_categories'],
            compliance_level=ComplianceLevel(rule_data['compliance_level']),
            source=rule_data['source']
        )
        
        db.session.add(rule)
        created_count += 1
    
    db.session.commit()
    logger.info(f"  ✅ Created {created_count} compliance rules")

def create_system_templates():
    """Create initial system templates."""
    from app.models.communication import (HRTemplate, TemplateCategory, TemplateType, 
                                        ComplianceLevel, TemplateStatus)
    
    # Check if system templates already exist
    existing_templates = HRTemplate.query.filter_by(is_system_template=True).count()
    if existing_templates > 0:
        logger.info(f"  ✅ System templates already exist ({existing_templates} templates)")
        return
    
    # System templates data
    system_templates = [
        {
            'category': TemplateCategory.SCREENING,
            'name': 'Initial Screening Email',
            'description': 'Professional initial screening communication',
            'subject_template': 'Application Received - {{position_title}} at {{company_name}}',
            'content_template': '''Dear {{candidate_name}},

Thank you for your interest in the {{position_title}} position at {{company_name}}. We have received your application and are pleased to inform you that your profile meets our initial requirements.

Our hiring team will review your application within the next 2-3 business days. We will contact you shortly to discuss the next steps in our selection process.

We appreciate your patience and look forward to the possibility of working together.

Best regards,
{{recruiter}}
{{company_name}} HR Team

Note: This is an automated message. Please do not reply to this email. For any queries, contact us at hr@{{company_domain}}.''',
            'variables': ['candidate_name', 'position_title', 'company_name', 'recruiter', 'company_domain'],
            'compliance_level': ComplianceLevel.STANDARD
        },
        {
            'category': TemplateCategory.PHONE_INTERVIEW,
            'name': 'Phone Interview Invitation',
            'description': 'Professional phone interview scheduling email',
            'subject_template': 'Phone Interview Invitation - {{position_title}} Position',
            'content_template': '''Dear {{candidate_name}},

We are pleased to invite you for a phone interview for the {{position_title}} position at {{company_name}}.

Interview Details:
- Date: {{interview_date}}
- Time: {{interview_time}} (IST)
- Duration: Approximately 30-45 minutes
- Interviewer: {{interviewer_name}}, {{interviewer_title}}

We will call you at {{phone_number}}. Please ensure you are in a quiet location with good network connectivity.

Discussion Topics:
- Your background and experience
- Role requirements and expectations  
- Company culture and growth opportunities
- Your questions about the role

Please confirm your availability by replying to this email.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
            'variables': ['candidate_name', 'position_title', 'company_name', 'interview_date', 'interview_time', 'interviewer_name', 'interviewer_title', 'phone_number', 'recruiter'],
            'compliance_level': ComplianceLevel.STANDARD
        },
        {
            'category': TemplateCategory.REJECTION,
            'name': 'Professional Rejection Email',
            'description': 'Respectful candidate rejection communication',
            'subject_template': 'Update on Your Application - {{position_title}} Position',
            'content_template': '''Dear {{candidate_name}},

Thank you for your interest in the {{position_title}} position at {{company_name}} and for taking the time to participate in our selection process.

After careful consideration, we have decided to proceed with other candidates whose qualifications more closely match our current requirements for this role.

This decision was not easy, as we were impressed with {{positive_feedback}}. We encourage you to apply for future opportunities that align with your skills and career goals.

We will keep your profile on file for 12 months and may reach out if suitable positions become available.

Thank you again for your time and interest in {{company_name}}. We wish you all the best in your career endeavors.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
            'variables': ['candidate_name', 'position_title', 'company_name', 'positive_feedback', 'recruiter'],
            'compliance_level': ComplianceLevel.STANDARD
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
            subject_template=template_data['subject_template'],
            content_template=template_data['content_template'],
            variables=template_data['variables'],
            compliance_level=template_data['compliance_level'],
            status=TemplateStatus.ACTIVE,
            is_system_template=True,
            ai_model_used='system_generated',
            ai_confidence_score=1.0
        )
        
        db.session.add(template)
        created_count += 1
    
    db.session.commit()
    logger.info(f"  ✅ Created {created_count} system templates")

def create_hr_indexes():
    """Create performance indexes for HR communication tables."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_hr_templates_user_category ON hr_templates(user_id, category);",
        "CREATE INDEX IF NOT EXISTS idx_hr_templates_status_created ON hr_templates(status, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_template_generations_template_user ON template_generations(template_id, user_id);",
        "CREATE INDEX IF NOT EXISTS idx_template_generations_candidate ON template_generations(candidate_id);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_jurisdiction_active ON compliance_rules(jurisdiction, is_active);",
    ]
    
    for index_sql in indexes:
        try:
            db.session.execute(db.text(index_sql))
            index_name = index_sql.split('idx_')[1].split(' ')[0]
            logger.info(f"  ✅ Index created: {index_name}")
        except Exception as e:
            logger.warning(f"  ⚠️  Index creation warning: {str(e)}")
    
    db.session.commit()
    logger.info("  ✅ Performance indexes created")

def main():
    """Main entry point."""
    success = run_hr_templates_migration()
    
    if success:
        logger.info("🎉 HR Communication Templates are ready!")
        sys.exit(0)
    else:
        logger.error("💥 HR Communication Templates migration failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
