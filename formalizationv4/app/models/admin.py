from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class AdminUser(db.Model):
    """Enhanced admin model with comprehensive access control and monitoring capabilities."""
    __tablename__ = 'admin_users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Admin privileges
    role = db.Column(db.String(20), nullable=False, default='admin')  # admin, super_admin, system_admin
    permissions = db.Column(JSONB, default=lambda: {
        "users": {"create": True, "read": True, "update": True, "delete": True},
        "resumes": {"create": True, "read": True, "update": True, "delete": True},
        "analyses": {"create": True, "read": True, "update": True, "delete": True},
        "queue": {"manage": True, "priority": True, "reorder": True, "cancel": True},
        "credits": {"add": True, "deduct": True, "view_all": True, "purchase": True},
        "system": {"health": True, "logs": True, "config": True, "backup": True},
        "analytics": {"view": True, "export": True, "dashboard": True},
        "sales": {"leads": True, "campaigns": True, "roi": True, "reports": True}
    })
    
    # Admin-specific features
    access_level = db.Column(db.Integer, default=100)  # 0-100, higher = more access
    can_access_all_users = db.Column(db.Boolean, default=True)
    can_modify_credits = db.Column(db.Boolean, default=True)
    can_manage_queue = db.Column(db.Boolean, default=True)
    can_view_analytics = db.Column(db.Boolean, default=True)
    can_manage_system = db.Column(db.Boolean, default=True)
    can_access_sales_intelligence = db.Column(db.Boolean, default=True)
    
    # Security and audit
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    ip_restrictions = db.Column(JSONB)  # List of allowed IP addresses/ranges
    session_timeout = db.Column(db.Integer, default=480)  # Minutes
    
    # Activity tracking
    last_activity = db.Column(db.DateTime)
    actions_performed = db.Column(db.Integer, default=0)
    
    # Status and validity
    is_active = db.Column(db.Boolean, default=True)
    access_expires = db.Column(db.DateTime)  # Optional expiration
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id'))
    
    # Relationships
    user = db.relationship('User', back_populates='admin_profile')
    admin_actions = db.relationship(
        'AdminAction',
        backref=db.backref('admin_user', passive_deletes=True),
        cascade='all, delete-orphan',
        passive_deletes=True,
        lazy='dynamic'
    )
    created_admins = db.relationship('AdminUser', remote_side=[id], backref='creator')
    
    def __repr__(self):
        return f'<AdminUser {self.user.email if self.user else "Unknown"} - {self.role}>'
    
    def has_permission(self, resource, action):
        """Check if admin has specific permission."""
        if not self.is_active:
            return False
            
        if self.access_expires and self.access_expires < datetime.utcnow():
            return False
            
        permissions = self.permissions or {}
        resource_perms = permissions.get(resource, {})
        return resource_perms.get(action, False)
    
    def can_access_user(self, user_id):
        """Check if admin can access specific user."""
        if not self.can_access_all_users:
            # Add logic for restricted access if needed
            return False
        return True
    
    def log_action(self, action_type, description, target_resource=None, target_id=None, metadata=None):
        """Log admin action for audit trail."""
        action = AdminAction(
            admin_user_id=self.id,
            action_type=action_type,
            description=description,
            target_resource=target_resource,
            target_id=target_id,
            action_metadata=metadata or {},
            ip_address=None,  # Would be set from request context
        )
        db.session.add(action)
        self.actions_performed += 1
        self.last_activity = datetime.utcnow()
        return action
    
    def update_login_info(self, success=True, ip_address=None):
        """Update login tracking information."""
        if success:
            self.last_login = datetime.utcnow()
            self.login_count += 1
            self.failed_login_attempts = 0
        else:
            self.failed_login_attempts += 1
            self.last_failed_login = datetime.utcnow()
    
    def is_session_valid(self):
        """Check if admin session is still valid."""
        if not self.last_activity:
            return False
            
        timeout_minutes = self.session_timeout or 480
        session_expiry = self.last_activity.timestamp() + (timeout_minutes * 60)
        return datetime.utcnow().timestamp() < session_expiry
    
    def get_dashboard_permissions(self):
        """Get permissions formatted for dashboard use."""
        return {
            "user_management": self.has_permission("users", "read"),
            "resume_management": self.has_permission("resumes", "read"),
            "analysis_management": self.has_permission("analyses", "read"),
            "queue_management": self.can_manage_queue,
            "credit_management": self.can_modify_credits,
            "system_health": self.has_permission("system", "health"),
            "analytics_dashboard": self.can_view_analytics,
            "sales_intelligence": self.can_access_sales_intelligence,
        }
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'email': self.user.email if self.user else None,
            'role': self.role,
            'access_level': self.access_level,
            'permissions': self.get_dashboard_permissions(),
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'actions_performed': self.actions_performed,
            'created_at': self.created_at.isoformat()
        }


class AdminAction(db.Model):
    """Audit log for admin actions."""
    __tablename__ = 'admin_actions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('admin_users.id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Action details
    action_type = db.Column(db.String(50), nullable=False)  # create, update, delete, view, etc.
    description = db.Column(db.String(500), nullable=False)
    
    # Target information
    target_resource = db.Column(db.String(50))  # user, resume, analysis, system, etc.
    target_id = db.Column(UUID(as_uuid=True))  # ID of the target resource
    
    # Context and metadata
    action_metadata = db.Column(JSONB, default=dict)  # Additional context data
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    
    # Status and result
    status = db.Column(db.String(20), default='success')  # success, failed, partial
    error_message = db.Column(db.String(1000))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminAction {self.action_type} on {self.target_resource}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'admin_user_id': str(self.admin_user_id),
            'action_type': self.action_type,
            'description': self.description,
            'target_resource': self.target_resource,
            'target_id': str(self.target_id) if self.target_id else None,
            'metadata': self.action_metadata,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class SystemConfiguration(db.Model):
    """System-wide configuration that admins can modify."""
    __tablename__ = 'system_configurations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(JSONB, nullable=False)
    description = db.Column(db.String(500))
    category = db.Column(db.String(50), default='general')  # general, ai, queue, credits, etc.
    
    # Admin who last modified
    modified_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id', ondelete='SET NULL'))
    
    # Validation and constraints
    is_sensitive = db.Column(db.Boolean, default=False)  # Hide value in UI
    requires_restart = db.Column(db.Boolean, default=False)  # Requires system restart
    validation_schema = db.Column(JSONB)  # JSON schema for value validation
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    modifier = db.relationship('AdminUser', backref='system_configs_modified')
    
    def __repr__(self):
        return f'<SystemConfiguration {self.key}>'
    
    def to_dict(self, show_sensitive=False):
        return {
            'id': str(self.id),
            'key': self.key,
            'value': self.value if not self.is_sensitive or show_sensitive else "[HIDDEN]",
            'description': self.description,
            'category': self.category,
            'is_sensitive': self.is_sensitive,
            'requires_restart': self.requires_restart,
            'updated_at': self.updated_at.isoformat()
        }


class AdminNotification(db.Model):
    """Notifications for admin users about system events."""
    __tablename__ = 'admin_notifications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id', ondelete='CASCADE'))
    
    # Notification details
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, warning, error, success
    category = db.Column(db.String(50), default='system')  # system, user, queue, sales, etc.
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    
    # Metadata
    notification_metadata = db.Column(JSONB, default=dict)  # Additional data
    action_url = db.Column(db.String(500))  # Optional link for action
    
    # Expiration
    expires_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    admin_user = db.relationship('AdminUser', backref='notifications')
    
    def __repr__(self):
        return f'<AdminNotification {self.title}>'
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
    
    def is_expired(self):
        """Check if notification is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'category': self.category,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'metadata': self.notification_metadata,
            'action_url': self.action_url,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
