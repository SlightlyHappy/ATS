"""
Candidate and HR Pipeline Management Models.
Tracks candidates through the hiring process with scoring and analytics.
"""
from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import func, and_, or_
import uuid
from enum import Enum

class PipelineStage(Enum):
    """Pipeline stage enumeration for candidate journey."""
    APPLIED = "applied"
    SCREENING = "screening"
    PHONE_INTERVIEW = "phone_interview"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    ON_SITE_INTERVIEW = "on_site_interview"
    FINAL_INTERVIEW = "final_interview"
    REFERENCE_CHECK = "reference_check"
    OFFER_MADE = "offer_made"
    OFFER_ACCEPTED = "offer_accepted"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class CandidateStatus(Enum):
    """Candidate status enumeration."""
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"
    HIRED = "hired"
    WITHDRAWN = "withdrawn"

class Priority(Enum):
    """Candidate priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Candidate(db.Model):
    """Candidate model for tracking individuals through the hiring pipeline."""
    __tablename__ = 'candidates'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=True)
    
    # Basic candidate information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    linkedin_url = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(500))
    
    # Position and company details
    position_title = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100))
    hiring_manager = db.Column(db.String(200))
    recruiter = db.Column(db.String(200))
    job_req_id = db.Column(db.String(50))
    
    # Pipeline management
    current_stage = db.Column(db.String(30), nullable=False, default=PipelineStage.APPLIED.value)
    status = db.Column(db.String(20), nullable=False, default=CandidateStatus.ACTIVE.value)
    priority = db.Column(db.String(10), nullable=False, default=Priority.MEDIUM.value)
    
    # Scoring and qualification
    overall_score = db.Column(db.Float, default=0.0)  # 0-100
    technical_score = db.Column(db.Float, default=0.0)  # 0-100
    cultural_fit_score = db.Column(db.Float, default=0.0)  # 0-100
    experience_score = db.Column(db.Float, default=0.0)  # 0-100
    qualification_notes = db.Column(db.Text)
    
    # AI-powered insights
    ai_match_score = db.Column(db.Float)  # From resume analysis
    ai_strengths = db.Column(JSONB)  # Array of strengths from AI analysis
    ai_concerns = db.Column(JSONB)  # Array of concerns from AI analysis
    ai_recommendations = db.Column(JSONB)  # Array of AI recommendations
    
    # Timeline and progress
    expected_start_date = db.Column(db.Date)
    salary_expectation = db.Column(db.Integer)
    offer_amount = db.Column(db.Integer)
    notice_period = db.Column(db.Integer)  # days
    
    # Communication tracking
    last_contact_date = db.Column(db.DateTime)
    next_followup_date = db.Column(db.DateTime)
    communication_notes = db.Column(db.Text)
    
    # Source and referral tracking
    source = db.Column(db.String(50))  # job_board, referral, linkedin, etc.
    referrer_name = db.Column(db.String(200))
    referrer_email = db.Column(db.String(255))
    
    # Timestamps
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    hired_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    
    # Relationships
    activities = db.relationship('CandidateActivity', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    interviews = db.relationship('Interview', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    stage_history = db.relationship('PipelineStageHistory', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('CandidateAlert', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Candidate {self.first_name} {self.last_name} - {self.position_title}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def days_in_pipeline(self):
        return (datetime.utcnow() - self.applied_at).days
    
    @property
    def days_in_current_stage(self):
        latest_stage = self.stage_history.order_by(PipelineStageHistory.changed_at.desc()).first()
        if latest_stage:
            return (datetime.utcnow() - latest_stage.changed_at).days
        return self.days_in_pipeline
    
    def calculate_overall_score(self):
        """Calculate overall score based on various factors."""
        scores = []
        weights = []
        
        if self.ai_match_score is not None:
            scores.append(self.ai_match_score)
            weights.append(0.4)  # 40% weight for AI analysis
        
        if self.technical_score > 0:
            scores.append(self.technical_score)
            weights.append(0.3)  # 30% weight for technical assessment
        
        if self.cultural_fit_score > 0:
            scores.append(self.cultural_fit_score)
            weights.append(0.2)  # 20% weight for cultural fit
        
        if self.experience_score > 0:
            scores.append(self.experience_score)
            weights.append(0.1)  # 10% weight for experience
        
        if scores and weights:
            weighted_score = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            self.overall_score = weighted_score / total_weight
        
        return self.overall_score
    
    def move_to_stage(self, new_stage: str, notes: str = None, moved_by: str = None):
        """Move candidate to a new pipeline stage."""
        if self.current_stage != new_stage:
            # Record stage history
            stage_history = PipelineStageHistory(
                candidate_id=self.id,
                from_stage=self.current_stage,
                to_stage=new_stage,
                notes=notes,
                moved_by=moved_by,
                changed_at=datetime.utcnow()
            )
            db.session.add(stage_history)
            
            # Update current stage
            self.current_stage = new_stage
            self.updated_at = datetime.utcnow()
            
            # Update status based on stage
            if new_stage in [PipelineStage.REJECTED.value, PipelineStage.WITHDRAWN.value]:
                self.status = CandidateStatus.REJECTED.value if new_stage == PipelineStage.REJECTED.value else CandidateStatus.WITHDRAWN.value
                self.rejected_at = datetime.utcnow()
            elif new_stage == PipelineStage.HIRED.value:
                self.status = CandidateStatus.HIRED.value
                self.hired_at = datetime.utcnow()
    
    def add_activity(self, activity_type: str, description: str, details: dict = None, created_by: str = None):
        """Add an activity record for this candidate."""
        activity = CandidateActivity(
            candidate_id=self.id,
            activity_type=activity_type,
            description=description,
            details=details,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        db.session.add(activity)
        return activity
    
    def to_dict(self, include_sensitive=False):
        """Convert candidate to dictionary representation."""
        data = {
            'id': str(self.id),
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone if include_sensitive else None,
            'position_title': self.position_title,
            'department': self.department,
            'current_stage': self.current_stage,
            'status': self.status,
            'priority': self.priority,
            'overall_score': round(self.overall_score, 2) if self.overall_score else 0,
            'technical_score': self.technical_score,
            'cultural_fit_score': self.cultural_fit_score,
            'experience_score': self.experience_score,
            'ai_match_score': self.ai_match_score,
            'days_in_pipeline': self.days_in_pipeline,
            'days_in_current_stage': self.days_in_current_stage,
            'applied_at': self.applied_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'next_followup_date': self.next_followup_date.isoformat() if self.next_followup_date else None,
            'hiring_manager': self.hiring_manager,
            'recruiter': self.recruiter,
            'source': self.source
        }
        
        if include_sensitive:
            data.update({
                'salary_expectation': self.salary_expectation,
                'offer_amount': self.offer_amount,
                'notice_period': self.notice_period,
                'linkedin_url': self.linkedin_url,
                'portfolio_url': self.portfolio_url,
                'ai_strengths': self.ai_strengths,
                'ai_concerns': self.ai_concerns,
                'ai_recommendations': self.ai_recommendations,
                'qualification_notes': self.qualification_notes,
                'communication_notes': self.communication_notes
            })
        
        return data

class CandidateActivity(db.Model):
    """Activity tracking for candidate interactions."""
    __tablename__ = 'candidate_activities'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('candidates.id'), nullable=False)
    
    activity_type = db.Column(db.String(50), nullable=False)  # email, call, interview, note, etc.
    description = db.Column(db.Text, nullable=False)
    details = db.Column(JSONB)  # Additional structured data
    
    created_by = db.Column(db.String(200))  # Name or ID of person who created the activity
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'activity_type': self.activity_type,
            'description': self.description,
            'details': self.details,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

class PipelineStageHistory(db.Model):
    """Track candidate movement through pipeline stages."""
    __tablename__ = 'pipeline_stage_history'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('candidates.id'), nullable=False)
    
    from_stage = db.Column(db.String(30))
    to_stage = db.Column(db.String(30), nullable=False)
    notes = db.Column(db.Text)
    moved_by = db.Column(db.String(200))
    
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'from_stage': self.from_stage,
            'to_stage': self.to_stage,
            'notes': self.notes,
            'moved_by': self.moved_by,
            'changed_at': self.changed_at.isoformat()
        }

class Interview(db.Model):
    """Interview scheduling and tracking."""
    __tablename__ = 'interviews'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('candidates.id'), nullable=False)
    
    interview_type = db.Column(db.String(50), nullable=False)  # phone, video, on_site, technical
    interviewer_name = db.Column(db.String(200))
    interviewer_email = db.Column(db.String(255))
    
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    location = db.Column(db.String(500))  # Room, video link, phone number
    
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    feedback = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-10 scale
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'interview_type': self.interview_type,
            'interviewer_name': self.interviewer_name,
            'interviewer_email': self.interviewer_email,
            'scheduled_at': self.scheduled_at.isoformat(),
            'duration_minutes': self.duration_minutes,
            'location': self.location,
            'status': self.status,
            'feedback': self.feedback,
            'rating': self.rating,
            'created_at': self.created_at.isoformat()
        }

class CandidateAlert(db.Model):
    """High-priority alerts for candidates."""
    __tablename__ = 'candidate_alerts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('candidates.id'), nullable=False)
    
    alert_type = db.Column(db.String(50), nullable=False)  # high_score, stalled, follow_up, offer_deadline
    priority = db.Column(db.String(10), nullable=False, default=Priority.MEDIUM.value)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    auto_generated = db.Column(db.Boolean, default=True)
    
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    dismissed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'candidate_id': str(self.candidate_id),
            'alert_type': self.alert_type,
            'priority': self.priority,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'auto_generated': self.auto_generated,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'candidate_name': self.candidate.full_name if hasattr(self, 'candidate') else None
        }

class HiringAnalytics(db.Model):
    """Aggregate hiring analytics and metrics."""
    __tablename__ = 'hiring_analytics'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    # Time period for analytics
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    period_type = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, quarterly
    
    # Pipeline metrics
    total_candidates = db.Column(db.Integer, default=0)
    active_candidates = db.Column(db.Integer, default=0)
    hired_candidates = db.Column(db.Integer, default=0)
    rejected_candidates = db.Column(db.Integer, default=0)
    
    # Conversion metrics
    application_to_screening_rate = db.Column(db.Float, default=0.0)
    screening_to_interview_rate = db.Column(db.Float, default=0.0)
    interview_to_offer_rate = db.Column(db.Float, default=0.0)
    offer_to_hire_rate = db.Column(db.Float, default=0.0)
    overall_conversion_rate = db.Column(db.Float, default=0.0)
    
    # Time metrics
    avg_time_to_hire = db.Column(db.Float, default=0.0)  # days
    avg_time_per_stage = db.Column(JSONB)  # stage -> average days
    
    # Quality metrics
    avg_candidate_score = db.Column(db.Float, default=0.0)
    high_priority_candidates = db.Column(db.Integer, default=0)
    ai_match_score_avg = db.Column(db.Float, default=0.0)
    
    # Source analytics
    source_breakdown = db.Column(JSONB)  # source -> count
    top_performing_sources = db.Column(JSONB)  # source -> conversion rate
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'period_type': self.period_type,
            'total_candidates': self.total_candidates,
            'active_candidates': self.active_candidates,
            'hired_candidates': self.hired_candidates,
            'rejected_candidates': self.rejected_candidates,
            'application_to_screening_rate': self.application_to_screening_rate,
            'screening_to_interview_rate': self.screening_to_interview_rate,
            'interview_to_offer_rate': self.interview_to_offer_rate,
            'offer_to_hire_rate': self.offer_to_hire_rate,
            'overall_conversion_rate': self.overall_conversion_rate,
            'avg_time_to_hire': self.avg_time_to_hire,
            'avg_time_per_stage': self.avg_time_per_stage,
            'avg_candidate_score': self.avg_candidate_score,
            'high_priority_candidates': self.high_priority_candidates,
            'ai_match_score_avg': self.ai_match_score_avg,
            'source_breakdown': self.source_breakdown,
            'top_performing_sources': self.top_performing_sources,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
