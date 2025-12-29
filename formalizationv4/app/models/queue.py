from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum

class QueueStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AnalysisQueue(db.Model):
    """Model to manage resume analysis queue."""
    __tablename__ = 'analysis_queue'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    analysis_id = db.Column(UUID(as_uuid=True), db.ForeignKey('analyses.id'), nullable=True)
    
    status = db.Column(db.String(20), default=QueueStatus.PENDING.value, nullable=False)
    priority = db.Column(db.Integer, default=1)  # Higher number = higher priority, admins get higher priority
    
    # Queue metadata
    queue_position = db.Column(db.Integer)
    estimated_completion_time = db.Column(db.DateTime)
    
    # Processing info
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='queued_analyses')
    resume = db.relationship('Resume', backref='queue_entries')
    analysis = db.relationship('Analysis', backref='queue_entry', uselist=False)
    
    def __repr__(self):
        return f'<AnalysisQueue {self.id} - {self.status}>'
    
    def start_processing(self):
        """Mark the queue item as processing."""
        self.status = QueueStatus.PROCESSING.value
        self.started_at = datetime.utcnow()
        db.session.commit()
    
    def mark_completed(self, analysis_id):
        """Mark the queue item as completed."""
        self.status = QueueStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.analysis_id = analysis_id
        db.session.commit()
    
    def mark_failed(self, error_message):
        """Mark the queue item as failed."""
        self.status = QueueStatus.FAILED.value
        self.error_message = error_message
        self.retry_count += 1
        
        # If we haven't exceeded max retries, reset to pending
        if self.retry_count < self.max_retries:
            self.status = QueueStatus.PENDING.value
            self.started_at = None
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'resume_id': str(self.resume_id),
            'analysis_id': str(self.analysis_id) if self.analysis_id else None,
            'status': self.status,
            'priority': self.priority,
            'queue_position': self.queue_position,
            'estimated_completion_time': self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat()
        }

class BatchUpload(db.Model):
    """Model to track batch resume uploads."""
    __tablename__ = 'batch_uploads'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    batch_name = db.Column(db.String(255))
    total_resumes = db.Column(db.Integer, nullable=False)
    processed_resumes = db.Column(db.Integer, default=0)
    successful_analyses = db.Column(db.Integer, default=0)
    failed_analyses = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    credits_used = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='batch_uploads')
    
    def __repr__(self):
        return f'<BatchUpload {self.id} - {self.batch_name}>'
    
    def update_progress(self):
        """Update the progress counters."""
        # Count completed queue entries for this batch
        from app.models.resume import Resume
        
        completed_count = db.session.query(AnalysisQueue).join(Resume).filter(
            Resume.batch_upload_id == self.id,
            AnalysisQueue.status == QueueStatus.COMPLETED.value
        ).count()
        
        failed_count = db.session.query(AnalysisQueue).join(Resume).filter(
            Resume.batch_upload_id == self.id,
            AnalysisQueue.status == QueueStatus.FAILED.value
        ).count()
        
        self.successful_analyses = completed_count
        self.failed_analyses = failed_count
        self.processed_resumes = completed_count + failed_count
        
        # Check if batch is complete
        if self.processed_resumes >= self.total_resumes:
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
        
        db.session.commit()
    
    @property
    def progress(self):
        """Calculate progress percentage."""
        if self.total_resumes == 0:
            return 0
        return round((self.processed_resumes / self.total_resumes) * 100, 1)
    
    @property
    def completed_resumes(self):
        """Alias for processed_resumes for WebSocket compatibility."""
        return self.processed_resumes
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'batch_name': self.batch_name,
            'total_resumes': self.total_resumes,
            'processed_resumes': self.processed_resumes,
            'successful_analyses': self.successful_analyses,
            'failed_analyses': self.failed_analyses,
            'progress': self.progress,
            'status': self.status,
            'credits_used': self.credits_used,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
