"""
HR Communication Templates Migration Script.
Creates the necessary tables for AI-powered HR communication templates.
"""
from app import db
from app.models.communication import HRTemplate, TemplateGeneration, ComplianceRule
import logging

logger = logging.getLogger(__name__)

def create_communication_tables():
    """Create communication tables with proper indexing."""
    try:
        logger.info("Creating HR Communication Templates tables...")
        
        # Create all tables
        db.create_all()
        
        logger.info("✓ Communication tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create communication tables: {str(e)}")
        return False

def initialize_compliance_rules():
    """Initialize basic compliance rules for Indian employment law."""
    try:
        logger.info("Initializing compliance rules...")
        
        # Check if rules already exist
        existing_rules = ComplianceRule.query.filter_by(jurisdiction='India').count()
        if existing_rules > 0:
            logger.info(f"Compliance rules already exist ({existing_rules} rules)")
            return True
        
        # Indian employment law compliance rules
        india_rules = [
            {
                'name': 'Equal Opportunity Employment',
                'description': 'Ensure equal opportunity and non-discrimination in hiring communications',
                'jurisdiction': 'India',
                'rule_text': 'All hiring communications must maintain equal opportunity principles and avoid discrimination based on gender, religion, caste, nationality, or other protected characteristics.',
                'required_clauses': [
                    'Equal opportunity employer',
                    'Merit-based selection'
                ],
                'prohibited_content': [
                    'gender preference',
                    'religion requirement',
                    'caste requirement',
                    'matrimonial status'
                ],
                'applicable_categories': ['screening', 'phone_interview', 'technical_interview', 'offer', 'rejection'],
                'compliance_level': 'standard',
                'source': 'Equal Opportunity Employment Guidelines, India'
            },
            {
                'name': 'Offer Letter Legal Requirements',
                'description': 'Legal requirements for job offer letters in India',
                'jurisdiction': 'India',
                'rule_text': 'Job offers must include clear terms of employment, probation period, notice period, and termination clauses as per Indian labor laws.',
                'required_clauses': [
                    'probation period',
                    'notice period',
                    'terms and conditions',
                    'background verification requirement'
                ],
                'prohibited_content': [
                    'unreasonable bond',
                    'excessive notice period',
                    'discriminatory conditions'
                ],
                'applicable_categories': ['offer'],
                'compliance_level': 'strict',
                'source': 'Indian Contract Act, 1872 and Labour Laws'
            },
            {
                'name': 'Data Privacy and Confidentiality',
                'description': 'Personal data protection requirements in recruitment',
                'jurisdiction': 'India',
                'rule_text': 'Personal data collected during recruitment must be handled in compliance with data protection laws and used only for legitimate business purposes.',
                'required_clauses': [
                    'data privacy notice',
                    'confidentiality assurance'
                ],
                'prohibited_content': [
                    'unauthorized data sharing',
                    'personal data misuse'
                ],
                'applicable_categories': ['screening', 'phone_interview', 'technical_interview', 'on_site_interview', 'final_interview', 'reference_request'],
                'compliance_level': 'standard',
                'source': 'Personal Data Protection Bill and IT Act, 2000'
            },
            {
                'name': 'Professional Communication Standards',
                'description': 'Minimum professional standards for HR communications',
                'jurisdiction': 'Global',
                'rule_text': 'All HR communications must maintain professional tone, clear language, and respectful approach towards candidates.',
                'required_clauses': [
                    'professional greeting',
                    'clear purpose statement',
                    'respectful closure'
                ],
                'prohibited_content': [
                    'unprofessional language',
                    'misleading information',
                    'threatening tone'
                ],
                'applicable_categories': ['screening', 'phone_interview', 'technical_interview', 'on_site_interview', 'final_interview', 'offer', 'offer_followup', 'rejection', 'onboarding', 'reference_request', 'feedback_request', 'general_update'],
                'compliance_level': 'basic',
                'source': 'Professional HR Best Practices'
            }
        ]
        
        # Import ComplianceLevel enum
        from app.models.communication import ComplianceLevel
        
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
        logger.info(f"✓ Created {created_count} compliance rules")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize compliance rules: {str(e)}")
        db.session.rollback()
        return False

def run_migration():
    """Run the complete communication templates migration."""
    logger.info("="*60)
    logger.info("STARTING HR COMMUNICATION TEMPLATES MIGRATION")
    logger.info("="*60)
    
    success = True
    
    # Step 1: Create tables
    if not create_communication_tables():
        success = False
    
    # Step 2: Initialize compliance rules
    if not initialize_compliance_rules():
        success = False
    
    if success:
        logger.info("="*60)
        logger.info("✓ HR COMMUNICATION TEMPLATES MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("="*60)
    else:
        logger.error("="*60)
        logger.error("✗ HR COMMUNICATION TEMPLATES MIGRATION FAILED")
        logger.error("="*60)
    
    return success

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    # Run migration
    success = run_migration()
    exit(0 if success else 1)
