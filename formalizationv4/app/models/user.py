from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class User(db.Model):
    """User model for authentication and access control."""
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Credit system
    credits_balance = db.Column(db.Integer, default=10)  # Default 10 credits for new users
    total_credits_purchased = db.Column(db.Integer, default=0)
    total_credits_used = db.Column(db.Integer, default=0)
    last_credit_transaction = db.Column(db.DateTime)
    
    # Subscription info (for future implementation)
    subscription_tier = db.Column(db.String(20), default='free')  # free, basic, premium
    subscription_expires = db.Column(db.DateTime)
    
    # Authentication tracking
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resumes = db.relationship('Resume', backref='user', lazy='dynamic')
    credit_transactions = db.relationship('CreditTransaction', backref='user', lazy='dynamic')
    admin_profile = db.relationship('AdminUser', uselist=False, lazy='select', back_populates='user')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def has_sufficient_credits(self, required_credits=1):
        """Check if user has enough credits for an operation."""
        if self.is_admin:
            return True
        return self.credits_balance >= required_credits
    
    def deduct_credits(self, amount=1, description="Resume analysis"):
        """Deduct credits from user balance."""
        if self.is_admin:
            return True
            
        if not self.has_sufficient_credits(amount):
            return False
            
        self.credits_balance -= amount
        self.total_credits_used += amount
        self.last_credit_transaction = datetime.utcnow()
        
        # Record transaction
        transaction = CreditTransaction(
            user_id=self.id,
            transaction_type='debit',
            amount=amount,
            description=description,
            balance_after=self.credits_balance
        )
        db.session.add(transaction)
        return True
    
    def add_credits(self, amount, description="Credit purchase"):
        """Add credits to user balance."""
        self.credits_balance += amount
        self.total_credits_purchased += amount
        self.last_credit_transaction = datetime.utcnow()
        
        # Record transaction
        transaction = CreditTransaction(
            user_id=self.id,
            transaction_type='credit',
            amount=amount,
            description=description,
            balance_after=self.credits_balance
        )
        db.session.add(transaction)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'credits_balance': self.credits_balance,
            'subscription_tier': self.subscription_tier,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }


class CreditTransaction(db.Model):
    """Model to track credit transactions."""
    __tablename__ = 'credit_transactions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    transaction_type = db.Column(db.String(10), nullable=False)  # credit, debit
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    balance_after = db.Column(db.Integer, nullable=False)
    
    # Reference to what caused this transaction
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=True)
    analysis_id = db.Column(UUID(as_uuid=True), db.ForeignKey('analyses.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CreditTransaction {self.transaction_type} {self.amount}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'description': self.description,
            'balance_after': self.balance_after,
            'created_at': self.created_at.isoformat()
        }
