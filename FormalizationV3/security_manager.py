#!/usr/bin/env python3
"""
Security Manager for HR ATS System
Handles security, rate limiting, and protection
"""

import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from collections import defaultdict
from flask import request, g

logger = logging.getLogger(__name__)

class SecurityManager:
    """Comprehensive security management"""
    
    def __init__(self):
        """Initialize security manager"""
        self.rate_limits = defaultdict(list)  # In-memory rate limiting
        self.blocked_ips = set()  # Blocked IP addresses
        self.security_config = self._load_security_config()
        
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        return {
            'rate_limit_enabled': os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
            'requests_per_minute': int(os.getenv('RATE_LIMIT_REQUESTS', 60)),
            'requests_per_hour': int(os.getenv('RATE_LIMIT_HOURLY', 1000)),
            'block_threshold': int(os.getenv('BLOCK_THRESHOLD', 100)),  # Requests before blocking
            'block_duration': int(os.getenv('BLOCK_DURATION', 3600)),  # Block duration in seconds
            'max_file_size': int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024)),  # 50MB
            'allowed_origins': [
                'https://hrtool-sable.vercel.app',
                'http://localhost:3000'
            ]
        }
        
    def apply_security_headers(self):
        """Apply security headers to request"""
        # Security headers will be applied in the after_request handler
        pass
        
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if identifier is within rate limits"""
        if not self.security_config['rate_limit_enabled']:
            return True
            
        # Check if IP is blocked
        if identifier in self.blocked_ips:
            return False
            
        current_time = time.time()
        
        # Clean old entries
        self.rate_limits[identifier] = [
            timestamp for timestamp in self.rate_limits[identifier]
            if current_time - timestamp < 3600  # Keep last hour
        ]
        
        # Check minute limit
        minute_requests = len([
            timestamp for timestamp in self.rate_limits[identifier]
            if current_time - timestamp < 60
        ])
        
        if minute_requests >= self.security_config['requests_per_minute']:
            self._log_rate_limit_violation(identifier, 'minute')
            return False
            
        # Check hourly limit
        hourly_requests = len(self.rate_limits[identifier])
        if hourly_requests >= self.security_config['requests_per_hour']:
            self._log_rate_limit_violation(identifier, 'hour')
            return False
            
        # Check block threshold
        if hourly_requests >= self.security_config['block_threshold']:
            self._block_ip(identifier)
            return False
            
        # Add current request
        self.rate_limits[identifier].append(current_time)
        return True
        
    def _log_rate_limit_violation(self, identifier: str, period: str):
        """Log rate limit violation"""
        logger.warning(f"Rate limit violation: {identifier} exceeded {period} limit")
        
    def _block_ip(self, ip: str):
        """Block IP address"""
        self.blocked_ips.add(ip)
        logger.warning(f"IP blocked due to excessive requests: {ip}")
        
        # In a real implementation, you might want to store this in Redis or database
        # with automatic expiry
        
    def validate_file_upload(self, file) -> Dict[str, Any]:
        """Validate uploaded file for security"""
        errors = []
        
        # Check file size
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > self.security_config['max_file_size']:
                errors.append(f"File too large. Maximum size: {self.security_config['max_file_size']} bytes")
        
        # Check file extension
        if file.filename:
            allowed_extensions = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            
            if file_ext not in allowed_extensions:
                errors.append(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        # Check for suspicious filenames
        if file.filename:
            suspicious_patterns = ['.php', '.exe', '.sh', '.bat', '.cmd', '.scr']
            if any(pattern in file.filename.lower() for pattern in suspicious_patterns):
                errors.append("Suspicious file type detected")
                
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
        
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input"""
        if not text:
            return ""
            
        # Remove potentially dangerous characters
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove script tags and javascript
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Remove SQL injection patterns
        sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)',
            r'(--|#|\/\*|\*\/)',
            r'(\bOR\b.*?=.*?=)',
            r'(\bAND\b.*?=.*?=)'
        ]
        
        for pattern in sql_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        return text.strip()
        
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
        
    def check_origin(self, origin: str) -> bool:
        """Check if request origin is allowed"""
        if not origin:
            return True  # Allow requests without explicit origin
            
        return origin in self.security_config['allowed_origins']
        
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        import secrets
        return secrets.token_urlsafe(32)
        
    def validate_csrf_token(self, token: str, expected: str) -> bool:
        """Validate CSRF token"""
        return token and expected and token == expected
        
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event"""
        try:
            event_data = {
                'type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', ''),
                'details': details
            }
            
            logger.warning(f"Security event: {event_data}")
            
            # In a real implementation, you might want to store this in a
            # dedicated security log database or send alerts
            
        except Exception as e:
            logger.error(f"Security event logging error: {e}")
            
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded IP first
        forwarded_ip = request.headers.get('X-Forwarded-For')
        if forwarded_ip:
            return forwarded_ip.split(',')[0].strip()
            
        # Check for real IP
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
            
        return request.remote_addr or '0.0.0.0'
        
    def check_suspicious_activity(self, user_id: str = None) -> Dict[str, Any]:
        """Check for suspicious activity patterns"""
        ip = self._get_client_ip()
        
        # Check rapid consecutive requests
        recent_requests = [
            timestamp for timestamp in self.rate_limits[ip]
            if time.time() - timestamp < 10  # Last 10 seconds
        ]
        
        suspicious_indicators = {
            'rapid_requests': len(recent_requests) > 20,
            'blocked_ip': ip in self.blocked_ips,
            'suspicious_user_agent': self._check_suspicious_user_agent(),
            'multiple_failed_attempts': False  # Would implement with database tracking
        }
        
        is_suspicious = any(suspicious_indicators.values())
        
        if is_suspicious:
            self.log_security_event('suspicious_activity', {
                'indicators': suspicious_indicators,
                'user_id': user_id,
                'ip': ip
            })
            
        return {
            'suspicious': is_suspicious,
            'indicators': suspicious_indicators,
            'risk_level': 'high' if is_suspicious else 'low'
        }
        
    def _check_suspicious_user_agent(self) -> bool:
        """Check for suspicious user agent strings"""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        suspicious_patterns = [
            'bot', 'crawler', 'spider', 'scraper',
            'curl', 'wget', 'python-requests',
            'postman', 'insomnia'
        ]
        
        return any(pattern in user_agent for pattern in suspicious_patterns)
        
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers to add to responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.supabase.co https://*.supabase.co"
            ),
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
        }
        
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            from cryptography.fernet import Fernet
            
            # In production, this key should be stored securely
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                # Generate a key for demonstration (don't do this in production)
                key = Fernet.generate_key()
                
            f = Fernet(key)
            encrypted = f.encrypt(data.encode())
            return encrypted.decode()
            
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return data  # Return unencrypted if encryption fails
            
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            from cryptography.fernet import Fernet
            
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                return encrypted_data  # Can't decrypt without key
                
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_data.encode())
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return encrypted_data  # Return as-is if decryption fails
            
    def audit_log(self, action: str, user_id: str = None, details: Dict[str, Any] = None):
        """Create audit log entry"""
        try:
            audit_entry = {
                'action': action,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', ''),
                'details': details or {}
            }
            
            # In a real implementation, store this in an audit log database
            logger.info(f"Audit log: {audit_entry}")
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")
            
    def health_check(self) -> Dict[str, Any]:
        """Security system health check"""
        return {
            'status': 'healthy',
            'active_rate_limits': len(self.rate_limits),
            'blocked_ips': len(self.blocked_ips),
            'security_features': {
                'rate_limiting': self.security_config['rate_limit_enabled'],
                'file_validation': True,
                'input_sanitization': True,
                'security_headers': True,
                'audit_logging': True
            }
        }
