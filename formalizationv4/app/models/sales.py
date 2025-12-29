"""
Sales Intelligence Models for Lead Scoring and CRM functionality.
Integrates with existing user and analytics infrastructure.
"""
from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import func, and_
import uuid
from enum import Enum

class LeadStatus(Enum):
    """Lead status enumeration."""
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"

class LeadSource(Enum):
    """Lead source enumeration."""
    ORGANIC = "organic"
    REFERRAL = "referral"
    DEMO = "demo"
    MARKETING = "marketing"
    API = "api"
    DIRECT = "direct"

class Lead(db.Model):
    """Lead model for tracking potential customers and their journey."""
    __tablename__ = 'leads'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Lead classification
    status = db.Column(db.String(20), nullable=False, default=LeadStatus.COLD.value)
    source = db.Column(db.String(20), nullable=False, default=LeadSource.ORGANIC.value)
    
    # Scoring
    overall_score = db.Column(db.Integer, default=0)  # 0-100
    engagement_score = db.Column(db.Integer, default=0)  # 0-40
    usage_score = db.Column(db.Integer, default=0)  # 0-30
    potential_score = db.Column(db.Integer, default=0)  # 0-30
    
    # Lead details
    company_name = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))  # startup, small, medium, large, enterprise
    estimated_monthly_analyses = db.Column(db.Integer, default=0)
    budget_range = db.Column(db.String(50))  # low, medium, high, enterprise
    
    # Activity tracking
    first_activity = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    last_score_update = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Qualification data
    qualification_notes = db.Column(db.Text)
    qualification_metadata = db.Column(JSONB, default=dict)
    
    # Conversion tracking
    converted_at = db.Column(db.DateTime)
    conversion_value = db.Column(db.Float)  # Monthly subscription value
    conversion_source = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('lead_profile', uselist=False))
    score_history = db.relationship('LeadScoreHistory', backref='lead', lazy='dynamic', 
                                  cascade='all, delete-orphan')
    activities = db.relationship('LeadActivity', backref='lead', lazy='dynamic',
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lead {self.user.email if self.user else "Unknown"} - {self.status}>'
    
    def update_score(self, force_recalculate=False):
        """Calculate and update lead score based on user behavior."""
        from app.services.lead_scoring_service import LeadScoringService
        
        # Only recalculate if enough time has passed or forced
        if not force_recalculate and self.last_score_update:
            time_since_update = datetime.utcnow() - self.last_score_update
            if time_since_update < timedelta(hours=1):
                return self.overall_score
        
        scorer = LeadScoringService()
        scores = scorer.calculate_lead_score(self.user_id)
        
        # Update scores
        old_score = self.overall_score
        self.engagement_score = scores['engagement']
        self.usage_score = scores['usage']
        self.potential_score = scores['potential']
        self.overall_score = scores['total']
        self.last_score_update = datetime.utcnow()
        
        # Update status based on score
        self._update_status_from_score()
        
        # Record score history if changed significantly
        if abs(old_score - self.overall_score) >= 5:
            self._record_score_change(old_score, self.overall_score)
        
        return self.overall_score
    
    def _update_status_from_score(self):
        """Update lead status based on current score."""
        if self.overall_score >= 80:
            self.status = LeadStatus.HOT.value
        elif self.overall_score >= 60:
            self.status = LeadStatus.WARM.value
        else:
            self.status = LeadStatus.COLD.value
    
    def _record_score_change(self, old_score, new_score):
        """Record significant score changes."""
        score_history = LeadScoreHistory(
            lead_id=self.id,
            old_score=old_score,
            new_score=new_score,
            change_reason='automatic_update',
            score_breakdown={
                'engagement': self.engagement_score,
                'usage': self.usage_score,
                'potential': self.potential_score
            }
        )
        db.session.add(score_history)
    
    def log_activity(self, activity_type, description, metadata=None):
        """Log lead activity."""
        activity = LeadActivity(
            lead_id=self.id,
            activity_type=activity_type,
            description=description,
            activity_metadata=metadata or {}
        )
        db.session.add(activity)
        self.last_activity = datetime.utcnow()
        return activity
    
    def get_conversion_probability(self):
        """Calculate conversion probability based on score and behavior."""
        if self.overall_score >= 90:
            return 0.8
        elif self.overall_score >= 80:
            return 0.6
        elif self.overall_score >= 60:
            return 0.3
        elif self.overall_score >= 40:
            return 0.1
        else:
            return 0.05
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'status': self.status,
            'source': self.source,
            'overall_score': self.overall_score,
            'engagement_score': self.engagement_score,
            'usage_score': self.usage_score,
            'potential_score': self.potential_score,
            'company_name': self.company_name,
            'industry': self.industry,
            'company_size': self.company_size,
            'estimated_monthly_analyses': self.estimated_monthly_analyses,
            'budget_range': self.budget_range,
            'conversion_probability': self.get_conversion_probability(),
            'first_activity': self.first_activity.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'created_at': self.created_at.isoformat(),
            'user_email': self.user.email if self.user else None
        }

class LeadScoreHistory(db.Model):
    """Track lead score changes over time."""
    __tablename__ = 'lead_score_history'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False)
    
    old_score = db.Column(db.Integer, nullable=False)
    new_score = db.Column(db.Integer, nullable=False)
    change_reason = db.Column(db.String(100))  # automatic_update, manual_adjustment, etc.
    
    score_breakdown = db.Column(JSONB)  # Detailed score components
    score_metadata = db.Column(JSONB, default=dict)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeadScoreHistory {self.lead_id} {self.old_score}->{self.new_score}>'

class LeadActivity(db.Model):
    """Track lead activities and touchpoints."""
    __tablename__ = 'lead_activities'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False)
    
    activity_type = db.Column(db.String(50), nullable=False)  # login, analysis, batch_upload, etc.
    description = db.Column(db.String(500))
    activity_metadata = db.Column(JSONB, default=dict)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeadActivity {self.activity_type} for {self.lead_id}>'

class SalesMetrics(db.Model):
    """Store aggregated sales metrics for reporting."""
    __tablename__ = 'sales_metrics'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    metric_date = db.Column(db.Date, nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly
    
    # Lead metrics
    total_leads = db.Column(db.Integer, default=0)
    new_leads = db.Column(db.Integer, default=0)
    hot_leads = db.Column(db.Integer, default=0)
    qualified_leads = db.Column(db.Integer, default=0)
    converted_leads = db.Column(db.Integer, default=0)
    
    # Conversion metrics
    conversion_rate = db.Column(db.Float, default=0.0)
    average_score = db.Column(db.Float, default=0.0)
    average_time_to_conversion = db.Column(db.Float)  # Days
    
    # Revenue metrics
    total_conversion_value = db.Column(db.Float, default=0.0)
    average_deal_size = db.Column(db.Float, default=0.0)
    
    # Additional metrics
    metrics_data = db.Column(JSONB, default=dict)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SalesMetrics {self.metric_date} - {self.metric_type}>'

class ROICalculation(db.Model):
    """Store ROI calculations for prospects."""
    __tablename__ = 'roi_calculations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=True)
    
    # Input parameters
    monthly_analyses = db.Column(db.Integer, nullable=False)
    time_saved_per_analysis = db.Column(db.Float, default=2.0)  # Hours
    hourly_rate = db.Column(db.Float, nullable=False)
    current_process_cost = db.Column(db.Float)
    
    # Calculated results
    monthly_time_savings = db.Column(db.Float)  # Hours
    monthly_cost_savings = db.Column(db.Float)  # USD
    platform_cost = db.Column(db.Float)  # USD
    net_savings = db.Column(db.Float)  # USD
    roi_percentage = db.Column(db.Float)
    payback_period_days = db.Column(db.Float)
    
    # Additional calculations
    annual_savings = db.Column(db.Float)
    three_year_savings = db.Column(db.Float)
    
    calculation_metadata = db.Column(JSONB, default=dict)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ROICalculation {self.id} - ROI: {self.roi_percentage}%>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'monthly_analyses': self.monthly_analyses,
            'monthly_time_savings': self.monthly_time_savings,
            'monthly_cost_savings': self.monthly_cost_savings,
            'platform_cost': self.platform_cost,
            'net_savings': self.net_savings,
            'roi_percentage': self.roi_percentage,
            'payback_period_days': self.payback_period_days,
            'annual_savings': self.annual_savings,
            'three_year_savings': self.three_year_savings,
            'created_at': self.created_at.isoformat()
        }
