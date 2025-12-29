from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Analysis(db.Model):
    """Analysis model to store agent analysis results."""
    __tablename__ = 'analyses'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    # Analysis metadata
    analysis_type = db.Column(db.String(50), nullable=False)  # full, technical, experience, education, soft_skills
    agent_version = db.Column(db.String(20), default='1.0')
    
    # Individual agent results
    technical_skills_result = db.Column(JSONB)
    experience_result = db.Column(JSONB)
    education_result = db.Column(JSONB)
    soft_skills_result = db.Column(JSONB)
    
    # Consolidated results
    overall_score = db.Column(db.Float)
    scores_breakdown = db.Column(JSONB)  # Individual agent scores
    strengths = db.Column(JSONB)         # Array of identified strengths
    weaknesses = db.Column(JSONB)        # Array of identified weaknesses
    recommendations = db.Column(JSONB)   # Array of improvement recommendations
    
    # Processing details
    processing_time = db.Column(db.Float)  # Time in seconds
    model_used = db.Column(db.String(50))
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Analysis {self.id} - {self.analysis_type}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'resume_id': str(self.resume_id),
            'analysis_type': self.analysis_type,
            'overall_score': self.overall_score,
            'scores_breakdown': self.scores_breakdown,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations,
            'processing_time': self.processing_time,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def get_agent_results(self):
        """Get all agent results in a structured format."""
        return {
            'technical_skills': self.technical_skills_result,
            'experience': self.experience_result,
            'education': self.education_result,
            'soft_skills': self.soft_skills_result
        }
