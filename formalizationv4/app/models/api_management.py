from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
import hashlib

class ApiKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    key_hash = db.Column(db.String(128), nullable=False, unique=True)
    permissions = db.Column(ARRAY(db.String), default=list)
    rate_limit = db.Column(db.Integer, default=0)  # requests per minute (0 = unlimited)
    requests_today = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active|revoked|expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    user = db.relationship('User')

    @staticmethod
    def hash_key(plain_key: str) -> str:
        return hashlib.sha256(plain_key.encode('utf-8')).hexdigest()

    def to_dict(self, include_key: bool = False, plain_key: str = None):
        # Only include plain_key when creating/rotating
        key_value = plain_key if include_key else None
        masked = None
        if not include_key:
            masked = '****'  # do not expose
        return {
            'id': str(self.id),
            'name': self.name,
            'key': key_value or masked,
            'permissions': self.permissions or [],
            'rate_limit': self.rate_limit or 0,
            'requests_today': self.requests_today or 0,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class RateLimitRule(db.Model):
    __tablename__ = 'rate_limit_rules'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint = db.Column(db.String(200), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    per_minute = db.Column(db.Integer, default=0)
    per_hour = db.Column(db.Integer, default=0)
    burst = db.Column(db.Integer, default=0)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'endpoint': self.endpoint,
            'method': self.method,
            'per_minute': self.per_minute or 0,
            'per_hour': self.per_hour or 0,
            'burst': self.burst or 0,
            'enabled': bool(self.enabled),
        }

class Webhook(db.Model):
    __tablename__ = 'webhooks'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = db.Column(db.String(500), nullable=False)
    events = db.Column(ARRAY(db.String), default=list)  # e.g., ['alert_created', 'backup_progress']
    secret = db.Column(db.String(128))
    status = db.Column(db.String(20), default='active')  # active|disabled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'url': self.url,
            'events': self.events or [],
            'secret': None,  # do not expose
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AccessLog(db.Model):
    __tablename__ = 'access_logs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_email = db.Column(db.String(255))
    user_name = db.Column(db.String(255))
    action = db.Column(db.String(50), nullable=False)  # Login|Logout|Failed Login|Password Reset
    ip_address = db.Column(db.String(45))
    location = db.Column(db.String(255))
    success = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_email': self.user_email,
            'user_name': self.user_name,
            'action': self.action,
            'ip_address': self.ip_address,
            'location': self.location,
            'success': self.success,
            'timestamp': self.timestamp.isoformat()
        }
