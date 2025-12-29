from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Resume(db.Model):
    """Resume model to store uploaded resume data."""
    __tablename__ = 'resumes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    batch_upload_id = db.Column(UUID(as_uuid=True), db.ForeignKey('batch_uploads.id'), nullable=True)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    
    # Extracted content
    raw_text = db.Column(db.Text)
    structured_data = db.Column(JSONB)  # Parsed resume data
    
    # Processing status
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    analyses = db.relationship('Analysis', backref='resume', lazy='dynamic', cascade='all, delete-orphan')
    batch_upload = db.relationship('BatchUpload', backref='resumes')
    
    def __repr__(self):
        return f'<Resume {self.filename}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'processing_status': self.processing_status,
            'batch_upload_id': str(self.batch_upload_id) if self.batch_upload_id else None,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'analyses_count': self.analyses.count()
        }
