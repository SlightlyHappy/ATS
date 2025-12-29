"""
Bear Systems Resume Screening Tool - API Routes
"""

from .auth import auth_bp
from .trial import trial_bp

__all__ = ['auth_bp', 'trial_bp']
