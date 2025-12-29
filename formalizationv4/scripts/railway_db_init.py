#!/usr/bin/env python3
"""
Comprehensive database initialization for Railway deployment.
This script ensures all tables, indexes, constraints, and default data are created.
"""
import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    User, CreditTransaction, Resume, Analysis, 
    AnalysisQueue, BatchUpload
)
from app.models.admin import AdminUser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Handles complete database initialization for Railway deployment."""
    
    def __init__(self):
        self.app = create_app()
        
    def initialize_database(self):
        """Main initialization method with migration support."""
        with self.app.app_context():
            try:
                logger.info("🚀 Starting database initialization for Railway...")
                
                # Step 1: Handle migrations and table creation
                self._handle_database_schema()
                
                # Step 2: Create indexes for performance
                self._create_indexes()
                
                # Step 3: Create default admin user
                self._create_default_users()
                
                # Step 4: Initialize HR Communication Templates
                self._initialize_hr_templates()
                
                # Step 5: Verify database integrity
                self._verify_database()
                
                logger.info("✅ Database initialization completed successfully!")
                return True
                
            except Exception as e:
                logger.error(f"❌ Database initialization failed: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
    def _handle_database_schema(self):
        """Handle database schema creation via migrations or fallback."""
        logger.info("🔧 Setting up database schema...")
        
        # The migration_manager handles this now, but we still need
        # to ensure all models are imported and tables exist
        self._import_all_models()
        
        # Check if tables exist, create if they don't
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            logger.info("No existing tables found, creating schema...")
            db.create_all()
        else:
            logger.info(f"Found {len(existing_tables)} existing tables")
            
        # Verify core tables exist
        expected_tables = [
            'users', 'credit_transactions', 'resumes', 
            'analyses', 'analysis_queue', 'batch_uploads'
        ]
        
        missing_tables = []
        for table in expected_tables:
            if table not in existing_tables:
                missing_tables.append(table)
                
        if missing_tables:
            logger.warning(f"Missing core tables: {missing_tables}")
            logger.info("Creating missing tables...")
            db.create_all()
            
        logger.info("✅ Database schema setup complete")
        
    def _import_all_models(self):
        """Import all models to ensure they're registered with SQLAlchemy."""
        try:
            from app.models import (
                User, CreditTransaction, Resume, Analysis, 
                AnalysisQueue, BatchUpload
            )
            logger.info("✅ Core models imported")
            
            # Try to import additional models (don't fail if they don't exist)
            try:
                from app.models.admin import AdminUser, AdminAction, SystemConfiguration, AdminNotification
                logger.info("✅ Admin models imported")
            except ImportError:
                logger.info("Admin models not available")
                
            try:
                from app.models.sales import Lead, LeadScoreHistory, LeadActivity, SalesMetrics, ROICalculation
                logger.info("✅ Sales models imported")
            except ImportError:
                logger.info("Sales models not available")
                
            try:
                from app.models.analytics import PerformanceMetric, UsageInsight, ErrorTracking, SystemAlert
                logger.info("✅ Analytics models imported")
            except ImportError:
                logger.info("Analytics models not available")
                
            try:
                from app.models.candidate import Candidate, CandidateActivity, PipelineStageHistory, Interview
                logger.info("✅ Candidate models imported")
            except ImportError:
                logger.info("Candidate models not available")
                
            try:
                from app.models.communication import HRTemplate, TemplateGeneration, ComplianceRule
                logger.info("✅ Communication models imported")
            except ImportError:
                logger.info("Communication models not available")
                
            try:
                from app.models.legal import LegalDocument, DocumentChunk, LegalQuery, KnowledgeBaseUpdate
                logger.info("✅ Legal models imported")
            except ImportError:
                logger.info("Legal models not available")
                
        except Exception as e:
            logger.warning(f"Error importing models: {str(e)}")

    def _create_indexes(self):
        """Create database indexes for optimal performance."""
        logger.info("🔍 Creating database indexes...")
        
        try:
            # Performance indexes for frequent queries
            indexes = [
                # User email lookup (for authentication)
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
                
                # Resume queries by user
                "CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_resumes_status ON resumes(processing_status);",
                "CREATE INDEX IF NOT EXISTS idx_resumes_batch ON resumes(batch_upload_id);",
                
                # Analysis queries
                "CREATE INDEX IF NOT EXISTS idx_analyses_resume_id ON analyses(resume_id);",
                "CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);",
                "CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);",
                
                # Queue management indexes
                "CREATE INDEX IF NOT EXISTS idx_queue_status ON analysis_queue(status);",
                "CREATE INDEX IF NOT EXISTS idx_queue_priority ON analysis_queue(priority, created_at);",
                "CREATE INDEX IF NOT EXISTS idx_queue_user ON analysis_queue(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_queue_position ON analysis_queue(queue_position);",
                
                # Credit transaction tracking
                "CREATE INDEX IF NOT EXISTS idx_credits_user_id ON credit_transactions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_credits_created ON credit_transactions(created_at);",
                
                # Batch upload tracking
                "CREATE INDEX IF NOT EXISTS idx_batch_user_id ON batch_uploads(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_batch_status ON batch_uploads(status);",
                
                # HR Communication Templates indexes
                "CREATE INDEX IF NOT EXISTS idx_hr_templates_user_category ON hr_templates(user_id, category);",
                "CREATE INDEX IF NOT EXISTS idx_hr_templates_status_created ON hr_templates(status, created_at);",
                "CREATE INDEX IF NOT EXISTS idx_template_generations_template_user ON template_generations(template_id, user_id);",
                "CREATE INDEX IF NOT EXISTS idx_template_generations_candidate ON template_generations(candidate_id);",
                "CREATE INDEX IF NOT EXISTS idx_compliance_rules_jurisdiction_active ON compliance_rules(jurisdiction, is_active);",
            ]
            
            for index_sql in indexes:
                try:
                    db.session.execute(db.text(index_sql))
                    logger.info(f"  ✅ Index created: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.warning(f"  ⚠️  Index creation warning: {str(e)}")
            
            db.session.commit()
            logger.info("🔍 Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {str(e)}")
            db.session.rollback()
            raise
    
    def _create_default_users(self):
        """Create default admin and test users."""
        logger.info("👤 Creating default users...")
        
        try:
            from app.services.auth_manager import auth_manager
            from app.models.admin import AdminUser
            
            # Get admin credentials from environment
            admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@bearsystems.co.in')
            admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'Benzie1!Benzie1!Benzie1!Benzie1!')
            admin_username = admin_email.split('@')[0]  # 'admin'
            
            # Check if admin already exists by email OR username
            existing_admin = User.query.filter(
                (User.email == admin_email) | (User.username == admin_username)
            ).first()
            
            if existing_admin:
                logger.info(f"  ✅ Admin user already exists: {admin_email} (username: {existing_admin.username})")
                
                # Update password if not set or ensure admin privileges
                if not existing_admin.password_hash:
                    existing_admin.password_hash = auth_manager.hash_password(admin_password)
                    logger.info(f"  🔐 Password set for existing admin: {admin_email}")
                
                # Ensure admin status
                if not existing_admin.is_admin:
                    existing_admin.is_admin = True
                    logger.info(f"  👑 Admin privileges granted to: {admin_email}")
                
                # Ensure active status
                if not existing_admin.is_active:
                    existing_admin.is_active = True
                    logger.info(f"  ✅ Activated admin user: {admin_email}")
                
                # Update other fields if needed
                if existing_admin.credits_balance < 1000:
                    existing_admin.credits_balance = 10000
                    logger.info(f"  � Credits updated for admin: {admin_email}")
                
                db.session.commit()
                return
            
            # Create default admin user with password
            admin_user = User(
                email=admin_email,
                username=admin_username,
                password_hash=auth_manager.hash_password(admin_password),
                first_name='System',
                last_name='Administrator',
                is_admin=True,
                is_active=True,
                credits_balance=10000,  # Lots of credits for admin
                subscription_tier='admin'
            )
            
            db.session.add(admin_user)
            db.session.flush()  # Get the user ID
            
            # Create admin profile
            admin_profile = AdminUser(
                user_id=admin_user.id,
                role='super_admin',
                access_level=100,
                can_access_all_users=True,
                can_modify_credits=True,
                can_manage_queue=True,
                can_view_analytics=True,
                can_manage_system=True,
                can_access_sales_intelligence=True
            )
            db.session.add(admin_profile)
            db.session.commit()
            
            logger.info(f"  ✅ Admin user created: {admin_email} with password (10,000 credits)")
            
            # Create initial credit transaction for admin
            admin_credit_transaction = CreditTransaction(
                user_id=admin_user.id,
                transaction_type='credit',
                amount=10000,
                description='Initial admin credits',
                balance_after=10000
            )
            
            db.session.add(admin_credit_transaction)
            db.session.commit()
            
            logger.info("👤 Default users created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating default users: {str(e)}")
            db.session.rollback()
            raise
    
    def _initialize_hr_templates(self):
        """Initialize HR Communication Templates system."""
        logger.info("📧 Initializing HR Communication Templates...")
        
        try:
            # Import HR Communication models and services
            from app.models.communication import (HRTemplate, TemplateGeneration, ComplianceRule,
                                                TemplateCategory, TemplateType, ComplianceLevel, TemplateStatus)
            
            logger.info("  📋 Creating HR communication tables...")
            # Create HR communication tables
            db.create_all()
            
            # Initialize compliance rules
            self._create_compliance_rules()
            
            # Initialize system templates
            self._create_system_templates()
            
            logger.info("📧 HR Communication Templates initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing HR templates: {str(e)}")
            
            # Check if this is the user_id constraint issue
            if 'null value in column "user_id"' in str(e) and 'violates not-null constraint' in str(e):
                logger.warning("⚠️  HR templates failed due to user_id constraint issue")
                logger.info("💡 This can be fixed by running: python scripts/fix_hr_templates_user_id.py")
                logger.warning("⚠️  Continuing deployment - HR templates can be initialized later")
            else:
                logger.warning("⚠️  Continuing deployment without HR templates - can be initialized later")
    
    def _create_compliance_rules(self):
        """Create initial compliance rules for HR communications."""
        logger.info("  ⚖️  Creating compliance rules...")
        
        try:
            from app.models.communication import ComplianceRule, ComplianceLevel
            
            # Check if rules already exist
            existing_rules = ComplianceRule.query.filter_by(jurisdiction='India').count()
            if existing_rules > 0:
                logger.info(f"    ✅ Compliance rules already exist ({existing_rules} rules)")
                return
            
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
            logger.info(f"    ✅ Created {created_count} compliance rules")
            
        except Exception as e:
            logger.error(f"    ❌ Error creating compliance rules: {str(e)}")
            db.session.rollback()
            raise
    
    def _auto_fix_hr_templates_schema(self):
        """Auto-fix HR templates schema to allow NULL user_id for system templates."""
        try:
            from sqlalchemy import text
            
            logger.info("    🔧 Checking HR templates schema...")
            
            # Check if the table exists and has the constraint
            result = db.session.execute(text("""
                SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'hr_templates' 
                AND column_name = 'user_id'
            """)).fetchone()
            
            if result and result[1] == 'NO':  # is_nullable = 'NO'
                logger.info("    📝 Making user_id column nullable for system templates...")
                
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
                logger.info("    ✅ HR templates schema fixed successfully")
                return True
                
            else:
                logger.info("    ℹ️  user_id column is already nullable or table doesn't exist")
                return True
                
        except Exception as e:
            logger.error(f"    ❌ Error fixing HR templates schema: {str(e)}")
            db.session.rollback()
            return False
    
    def _create_system_templates_retry(self):
        """Retry creating system templates after schema fix."""
        from app.models.communication import (HRTemplate, TemplateCategory, TemplateType, 
                                            ComplianceLevel, TemplateStatus)
        
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

In the meantime, feel free to explore more about our company and culture on our website.

Best regards,
{{recruiter}}
{{company_name}} HR Team

Note: This is an automated message. Please do not reply to this email. For any queries, contact us at hr@{{company_domain}}.''',
                'variables': ["candidate_name", "position_title", "company_name", "recruiter", "company_domain"]
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
- Phone Number: {{phone_number}}

During this interview, we will discuss your background, experience, and answer any questions you may have about the role.

Please confirm your availability by replying to this email.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
                'variables': ["candidate_name", "position_title", "company_name", "interview_date", "interview_time", "interviewer_name", "interviewer_title", "phone_number", "recruiter"]
            },
            {
                'category': TemplateCategory.REJECTION,
                'name': 'Professional Rejection Email',
                'description': 'Respectful candidate rejection communication',
                'subject': 'Update on Your Application - {{position_title}} Position',
                'content': '''Dear {{candidate_name}},

Thank you for your interest in the {{position_title}} position at {{company_name}} and for taking the time to participate in our recruitment process.

After careful consideration of all applications, we have decided to move forward with other candidates whose qualifications more closely match our current requirements.

{{positive_feedback}}

We appreciate your time and interest in {{company_name}}. We wish you all the best in your career endeavors.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
                'variables': ["candidate_name", "position_title", "company_name", "positive_feedback", "recruiter"]
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
        logger.info(f"    ✅ Created {created_count} system templates")
    
    def _create_system_templates(self):
        """Create initial system templates."""
        logger.info("  📝 Creating system templates...")
        
        try:
            from app.models.communication import (HRTemplate, TemplateCategory, TemplateType, 
                                                ComplianceLevel, TemplateStatus)
            
            # Check if system templates already exist
            existing_templates = HRTemplate.query.filter_by(is_system_template=True).count()
            if existing_templates > 0:
                logger.info(f"    ✅ System templates already exist ({existing_templates} templates)")
                return
            
            # Auto-fix HR templates schema if needed
            self._auto_fix_hr_templates_schema()
            
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
            logger.info(f"    ✅ Created {created_count} system templates")
            
        except Exception as e:
            logger.error(f"    ❌ Error creating system templates: {str(e)}")
            db.session.rollback()
            
            # Check if this is the user_id constraint violation
            if 'null value in column "user_id"' in str(e) and 'violates not-null constraint' in str(e):
                logger.info("    🔧 Detected user_id constraint issue, attempting automatic fix...")
                if self._auto_fix_hr_templates_schema():
                    logger.info("    🔄 Schema fixed, retrying template creation...")
                    try:
                        # Retry template creation after schema fix
                        self._create_system_templates_retry()
                        logger.info("    ✅ System templates created successfully after schema fix")
                        return
                    except Exception as retry_e:
                        logger.error(f"    ❌ Failed to create templates even after schema fix: {str(retry_e)}")
                        raise retry_e
                else:
                    logger.error("    ❌ Failed to fix schema automatically")
                    raise e
            else:
                raise e
    
    def _verify_database(self):
        """Verify database integrity and configuration."""
        logger.info("🔍 Verifying database integrity...")
        
        try:
            # Test basic queries
            user_count = User.query.count()
            logger.info(f"  ✅ Users table accessible: {user_count} users")
            
            # Verify admin user exists
            admin = User.query.filter_by(is_admin=True).first()
            if admin:
                logger.info(f"  ✅ Admin user verified: {admin.email}")
            else:
                raise Exception("No admin user found")
            
            # Test all table access
            table_tests = [
                (Resume, "resumes"),
                (Analysis, "analyses"),
                (AnalysisQueue, "analysis_queue"),
                (BatchUpload, "batch_uploads"),
                (CreditTransaction, "credit_transactions")
            ]
            
            for model, table_name in table_tests:
                count = model.query.count()
                logger.info(f"  ✅ {table_name} table accessible: {count} records")
            
            # Test HR communication tables if they exist
            try:
                from app.models.communication import HRTemplate, ComplianceRule
                template_count = HRTemplate.query.count()
                rule_count = ComplianceRule.query.count()
                logger.info(f"  ✅ hr_templates table accessible: {template_count} templates")
                logger.info(f"  ✅ compliance_rules table accessible: {rule_count} rules")
            except Exception as hr_error:
                logger.warning(f"  ⚠️  HR templates tables not available: {str(hr_error)}")
            
            # Test foreign key relationships
            if user_count > 0:
                test_user = User.query.first()
                # Test relationship access
                _ = test_user.credit_transactions.count()
                _ = test_user.resumes.count()
                logger.info("  ✅ Foreign key relationships working")
            
            logger.info("🔍 Database verification completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Database verification failed: {str(e)}")
            raise
    
    def reset_database(self):
        """Reset database (drop and recreate all tables)."""
        logger.warning("⚠️  RESETTING DATABASE - ALL DATA WILL BE LOST!")
        
        with self.app.app_context():
            try:
                # Drop all tables
                db.drop_all()
                logger.info("🗑️  All tables dropped")
                
                # Recreate everything
                self.initialize_database()
                
            except Exception as e:
                logger.error(f"❌ Database reset failed: {str(e)}")
                raise

def main():
    """Main entry point for database initialization."""
    
    # Check if we're in Railway environment
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("🚂 Running in Railway environment")
    
    # Check for reset flag
    reset_flag = '--reset' in sys.argv or os.getenv('RESET_DATABASE', '').lower() == 'true'
    
    initializer = DatabaseInitializer()
    
    try:
        if reset_flag:
            logger.warning("⚠️  Database reset requested")
            initializer.reset_database()
        else:
            success = initializer.initialize_database()
            
            if success:
                logger.info("🎉 Database is ready for Railway deployment!")
                sys.exit(0)
            else:
                logger.error("💥 Database initialization failed")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("⏹️  Database initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
