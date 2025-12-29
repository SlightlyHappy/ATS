"""
HR Communication Template Models.
Manages AI-powered template generation for HR communications.
"""
from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Index
import uuid
from enum import Enum

class TemplateCategory(Enum):
    """Template category enumeration for different HR communication types."""
    SCREENING = "screening"
    PHONE_INTERVIEW = "phone_interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    ON_SITE_INTERVIEW = "on_site_interview"
    FINAL_INTERVIEW = "final_interview"
    OFFER = "offer"
    OFFER_FOLLOWUP = "offer_followup"
    REJECTION = "rejection"
    ONBOARDING = "onboarding"
    REFERENCE_REQUEST = "reference_request"
    FEEDBACK_REQUEST = "feedback_request"
    GENERAL_UPDATE = "general_update"

class TemplateType(Enum):
    """Template type enumeration."""
    EMAIL = "email"
    SMS = "sms"
    LETTER = "letter"
    SYSTEM_NOTIFICATION = "system_notification"

class ComplianceLevel(Enum):
    """Legal compliance level enumeration."""
    BASIC = "basic"               # Basic professional standards
    STANDARD = "standard"         # Industry standard compliance
    STRICT = "strict"            # Full legal compliance with audit trail
    CUSTOM = "custom"            # Custom compliance requirements

class TemplateStatus(Enum):
    """Template status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    REVIEW_REQUIRED = "review_required"

class HRTemplate(db.Model):
    """
    HR Communication Template model.
    Stores AI-generated and customized templates for various HR communications.
    """
    __tablename__ = 'hr_templates'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)  # Nullable for system templates
    
    # Template identification
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.Enum(TemplateCategory), nullable=False, index=True)
    template_type = db.Column(db.Enum(TemplateType), nullable=False, default=TemplateType.EMAIL)
    
    # Template content
    subject_template = db.Column(db.Text)  # For emails
    content_template = db.Column(db.Text, nullable=False)
    variables = db.Column(JSONB)  # Available variables for personalization
    
    # Legal and compliance
    compliance_level = db.Column(db.Enum(ComplianceLevel), nullable=False, default=ComplianceLevel.STANDARD)
    legal_notes = db.Column(db.Text)  # Legal guidance and requirements
    compliance_tags = db.Column(JSONB)  # Legal compliance tags
    
    # Personalization settings
    personalization_enabled = db.Column(db.Boolean, default=True)
    ai_enhancement_enabled = db.Column(db.Boolean, default=True)
    
    # Template metadata
    status = db.Column(db.Enum(TemplateStatus), default=TemplateStatus.DRAFT, index=True)
    version = db.Column(db.String(20), default='1.0')
    is_system_template = db.Column(db.Boolean, default=False)  # System vs user templates
    
    # Usage statistics
    usage_count = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime)
    
    # AI generation metadata
    ai_model_used = db.Column(db.String(50))
    generation_prompt = db.Column(db.Text)  # Store the prompt used for AI generation
    ai_confidence_score = db.Column(db.Float)  # AI confidence in template quality
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    generations = db.relationship('TemplateGeneration', backref='template', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<HRTemplate {self.name} - {self.category.value}>'
    
    def to_dict(self, include_content=True):
        """Convert template to dictionary."""
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'template_type': self.template_type.value,
            'compliance_level': self.compliance_level.value,
            'personalization_enabled': self.personalization_enabled,
            'ai_enhancement_enabled': self.ai_enhancement_enabled,
            'status': self.status.value,
            'version': self.version,
            'is_system_template': self.is_system_template,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'variables': self.variables or [],
            'compliance_tags': self.compliance_tags or []
        }
        
        if include_content:
            data.update({
                'subject_template': self.subject_template,
                'content_template': self.content_template,
                'legal_notes': self.legal_notes
            })
        
        return data
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used_at = datetime.utcnow()
        db.session.commit()


class TemplateGeneration(db.Model):
    """
    Template Generation History model.
    Tracks AI-generated template instances for personalization and audit.
    """
    __tablename__ = 'template_generations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = db.Column(UUID(as_uuid=True), db.ForeignKey('hr_templates.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    candidate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('candidates.id'), nullable=True)
    
    # Generated content
    subject = db.Column(db.String(500))  # Generated subject for emails
    content = db.Column(db.Text, nullable=False)  # Generated content
    personalization_data = db.Column(JSONB)  # Data used for personalization
    
    # Generation metadata
    ai_model_used = db.Column(db.String(50))
    generation_time = db.Column(db.Float)  # Time taken to generate
    quality_score = db.Column(db.Float)  # AI-assessed quality score
    
    # Usage tracking
    sent_at = db.Column(db.DateTime)  # When the communication was sent
    delivery_status = db.Column(db.String(50))  # email_sent, sms_sent, etc.
    
    # Feedback and effectiveness
    recipient_feedback = db.Column(JSONB)  # Feedback from recipients
    effectiveness_score = db.Column(db.Float)  # Measured effectiveness
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TemplateGeneration {self.id} for Template {self.template_id}>'
    
    def to_dict(self):
        """Convert template generation to dictionary."""
        return {
            'id': str(self.id),
            'template_id': str(self.template_id),
            'user_id': str(self.user_id),
            'candidate_id': str(self.candidate_id) if self.candidate_id else None,
            'subject': self.subject,
            'content': self.content,
            'personalization_data': self.personalization_data or {},
            'ai_model_used': self.ai_model_used,
            'generation_time': self.generation_time,
            'quality_score': self.quality_score,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivery_status': self.delivery_status,
            'recipient_feedback': self.recipient_feedback or {},
            'effectiveness_score': self.effectiveness_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ComplianceRule(db.Model):
    """
    Compliance Rules model.
    Defines legal and regulatory requirements for HR communications.
    """
    __tablename__ = 'compliance_rules'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    jurisdiction = db.Column(db.String(100))  # e.g., "India", "US", "EU", "Global"
    
    # Rule content
    rule_text = db.Column(db.Text, nullable=False)
    required_clauses = db.Column(JSONB)  # Must-include clauses
    prohibited_content = db.Column(JSONB)  # Content that must be avoided
    
    # Application scope
    applicable_categories = db.Column(JSONB)  # Which template categories this applies to
    compliance_level = db.Column(db.Enum(ComplianceLevel), nullable=False)
    
    # Rule metadata
    source = db.Column(db.String(255))  # Legal source or regulation
    effective_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ComplianceRule {self.name} - {self.jurisdiction}>'
    
    def to_dict(self):
        """Convert compliance rule to dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'jurisdiction': self.jurisdiction,
            'rule_text': self.rule_text,
            'required_clauses': self.required_clauses or [],
            'prohibited_content': self.prohibited_content or [],
            'applicable_categories': self.applicable_categories or [],
            'compliance_level': self.compliance_level.value,
            'source': self.source,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Create indexes for better performance
Index('idx_hr_templates_user_category', HRTemplate.user_id, HRTemplate.category)
Index('idx_hr_templates_status_created', HRTemplate.status, HRTemplate.created_at)
Index('idx_template_generations_template_user', TemplateGeneration.template_id, TemplateGeneration.user_id)
Index('idx_template_generations_candidate', TemplateGeneration.candidate_id)
Index('idx_compliance_rules_jurisdiction_active', ComplianceRule.jurisdiction, ComplianceRule.is_active)
