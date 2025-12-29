"""
Enhanced error handling and logging system for production deployment.
Provides structured logging, error classification, and recovery procedures.
"""
import logging
import traceback
import uuid
from datetime import datetime
from enum import Enum
from functools import wraps
from flask import request, g, current_app, jsonify
import json
import os

class ErrorSeverity(Enum):
    """Error severity levels for proper categorization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better organization."""
    VALIDATION = "validation"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    AI_PROCESSING = "ai_processing"
    FILE_PROCESSING = "file_processing"
    QUEUE_MANAGEMENT = "queue_management"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"

class ApplicationError(Exception):
    """Base application error with enhanced context."""
    
    def __init__(self, message, error_code=None, category=ErrorCategory.SYSTEM, 
                 severity=ErrorSeverity.MEDIUM, details=None, user_message=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.generate_error_code()
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.user_message = user_message or "An error occurred. Please try again."
        self.timestamp = datetime.utcnow()
        
        # Safely get request_id
        try:
            self.request_id = getattr(g, 'request_id', None)
        except RuntimeError:
            # Outside request context (e.g., during startup)
            self.request_id = None
        
    def generate_error_code(self):
        """Generate unique error code for tracking."""
        return f"ERR_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
    
    def to_dict(self):
        """Convert error to dictionary for logging and API responses."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'user_message': self.user_message,
            'category': self.category.value,
            'severity': self.severity.value,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'request_id': self.request_id
        }

class ValidationError(ApplicationError):
    """Validation error for input validation failures."""
    def __init__(self, message, field=None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )
        if field:
            self.details['field'] = field

class DatabaseError(ApplicationError):
    """Database operation error."""
    def __init__(self, message, operation=None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            user_message="Service temporarily unavailable. Please try again.",
            **kwargs
        )
        if operation:
            self.details['operation'] = operation

class AuthenticationError(ApplicationError):
    """Authentication failure error."""
    def __init__(self, message, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Authentication failed. Please check your credentials.",
            **kwargs
        )

class AuthorizationError(ApplicationError):
    """Authorization failure error."""
    def __init__(self, message, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="You don't have permission to perform this action.",
            **kwargs
        )

class AIProcessingError(ApplicationError):
    """AI processing failure error."""
    def __init__(self, message, agent=None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AI_PROCESSING,
            severity=ErrorSeverity.HIGH,
            user_message="Analysis failed. Please try again or contact support.",
            **kwargs
        )
        if agent:
            self.details['agent'] = agent

class QueueError(ApplicationError):
    """Queue management error."""
    def __init__(self, message, queue_id=None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.QUEUE_MANAGEMENT,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if queue_id:
            self.details['queue_id'] = queue_id

class FileProcessingError(ApplicationError):
    """File processing error."""
    def __init__(self, message, filename=None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.FILE_PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            user_message="File processing failed. Please check file format and try again.",
            **kwargs
        )
        if filename:
            self.details['filename'] = filename

class ProductionLogger:
    """Enhanced logging system for production environment."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize logging for Flask app."""
        # Don't setup logging here - let the main app handle logging configuration
        # self.setup_logging(app)
        
        # Add request ID middleware
        app.before_request(self.add_request_id)
        
        # Add error handlers
        app.register_error_handler(ApplicationError, self.handle_application_error)
        app.register_error_handler(AuthenticationError, self.handle_application_error)  # Explicit handler
        app.register_error_handler(404, self.handle_404_error)
        app.register_error_handler(Exception, self.handle_generic_error)
    
    def setup_logging(self, app):
        """Setup structured logging configuration."""
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        
        # Create custom formatter that safely handles missing fields
        class SafeFormatter(logging.Formatter):
            def format(self, record):
                # Safely get request_id and user_id, with fallbacks
                try:
                    if not hasattr(record, 'request_id'):
                        record.request_id = getattr(g, 'request_id', 'N/A') if hasattr(g, 'request_id') else 'N/A'
                    if not hasattr(record, 'user_id'):
                        record.user_id = getattr(g, 'user_id', 'anonymous') if hasattr(g, 'user_id') else 'anonymous'
                except RuntimeError:
                    # Outside request context
                    record.request_id = 'STARTUP'
                    record.user_id = 'system'
                return super().format(record)
        
        formatter = SafeFormatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s - '
            'RequestID: %(request_id)s - User: %(user_id)s'
        )
        
        # Setup file handler for production
        if not app.debug:
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            file_handler = logging.FileHandler('logs/application.log')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            
            # Setup error file handler
            error_handler = logging.FileHandler('logs/errors.log')
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)
            
            app.logger.addHandler(file_handler)
            app.logger.addHandler(error_handler)
        
        app.logger.setLevel(log_level)
    
    def add_request_id(self):
        """Add unique request ID to each request."""
        g.request_id = str(uuid.uuid4())
        g.user_id = getattr(g, 'current_user_id', 'anonymous')
    
    def handle_application_error(self, error):
        """Handle custom application errors."""
        self.log_error(error)
        
        # Track error in analytics service
        try:
            from app.services.analytics_service import analytics_service
            analytics_service.track_error(error)
        except Exception as e:
            # Don't let analytics tracking failure affect error handling
            pass
        
        response_data = {
            'success': False,
            'error': {
                'code': error.error_code,
                'message': error.user_message,
                'category': error.category.value
            },
            'request_id': error.request_id
        }
        
        # Add details for development
        if current_app.debug:
            response_data['error']['details'] = error.details
            response_data['error']['internal_message'] = error.message
        
        status_code = self.get_status_code_for_category(error.category)
        return jsonify(response_data), status_code
    
    def handle_404_error(self, error):
        """Handle 404 Not Found errors - don't convert to 500."""
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'The requested resource was not found',
                'category': 'not_found'
            }
        }), 404
    
    def handle_generic_error(self, error):
        """Handle unexpected errors."""
        app_error = ApplicationError(
            message=f"Unhandled error: {str(error)}",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            details={'traceback': traceback.format_exc()}
        )
        
        return self.handle_application_error(app_error)
    
    def log_error(self, error):
        """Log error with proper context."""
        logger = logging.getLogger(__name__)
        
        # Safely get context information
        try:
            user_id = getattr(g, 'user_id', 'unknown')
        except RuntimeError:
            # Outside request context
            user_id = 'system'
        
        extra = {
            'request_id': error.request_id or 'N/A',
            'user_id': user_id
        }
        
        error_data = error.to_dict()
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error.message}", extra=extra)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error.message}", extra=extra)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error.message}", extra=extra)
        else:
            logger.info(f"Low severity error: {error.message}", extra=extra)
        
        # Log full error details
        logger.debug(f"Error details: {json.dumps(error_data, indent=2)}", extra=extra)
    
    def get_status_code_for_category(self, category):
        """Get HTTP status code based on error category."""
        status_codes = {
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.AUTHORIZATION: 403,
            ErrorCategory.DATABASE: 503,
            ErrorCategory.AI_PROCESSING: 503,
            ErrorCategory.FILE_PROCESSING: 422,
            ErrorCategory.QUEUE_MANAGEMENT: 503,
            ErrorCategory.EXTERNAL_SERVICE: 503,
            ErrorCategory.SYSTEM: 500
        }
        return status_codes.get(category, 500)

def log_function_call(logger=None):
    """Decorator to log function calls with parameters and results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(func.__module__)
            
            # Log function call
            func_logger.debug(
                f"Calling {func.__name__} with args={len(args)}, kwargs={list(kwargs.keys())}"
            )
            
            try:
                result = func(*args, **kwargs)
                func_logger.debug(f"Function {func.__name__} completed successfully")
                return result
            except Exception as e:
                func_logger.error(f"Function {func.__name__} failed: {str(e)}")
                raise
        
        return wrapper
    return decorator

def safe_database_operation(operation_name):
    """Decorator for safe database operations with automatic rollback."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from app import db
            
            try:
                result = func(*args, **kwargs)
                db.session.commit()
                return result
            except Exception as e:
                db.session.rollback()
                raise DatabaseError(
                    f"Database operation '{operation_name}' failed: {str(e)}",
                    operation=operation_name,
                    details={'function': func.__name__}
                )
        
        return wrapper
    return decorator

def validate_input(schema):
    """Decorator for input validation using provided schema."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request
            
            if request.is_json:
                data = request.get_json()
                errors = validate_data_against_schema(data, schema)
                if errors:
                    raise ValidationError(
                        "Input validation failed",
                        details={'validation_errors': errors}
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_data_against_schema(data, schema):
    """Validate data against provided schema."""
    # Simple validation - can be enhanced with jsonschema library
    errors = []
    
    for field, rules in schema.items():
        if rules.get('required', False) and field not in data:
            errors.append(f"Field '{field}' is required")
        
        if field in data:
            value = data[field]
            
            # Type validation
            if 'type' in rules and not isinstance(value, rules['type']):
                errors.append(f"Field '{field}' must be of type {rules['type'].__name__}")
            
            # Length validation
            if 'min_length' in rules and len(str(value)) < rules['min_length']:
                errors.append(f"Field '{field}' must be at least {rules['min_length']} characters")
            
            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                errors.append(f"Field '{field}' must be at most {rules['max_length']} characters")
    
    return errors

class HealthMonitor:
    """Production-grade health monitoring and alerting."""
    
    def __init__(self, app=None):
        self.app = app
        self.error_threshold = 10  # errors per hour
        self.error_count = 0
        self.last_reset = datetime.utcnow()
        
    def init_app(self, app):
        """Initialize health monitoring."""
        # Set up periodic health checks
        import atexit
        atexit.register(self.cleanup)
        
    def record_error(self, error):
        """Record error for monitoring."""
        # Reset counter if hour has passed
        if (datetime.utcnow() - self.last_reset).seconds >= 3600:
            self.error_count = 0
            self.last_reset = datetime.utcnow()
        
        self.error_count += 1
        
        # Check if threshold exceeded
        if self.error_count >= self.error_threshold:
            self.trigger_alert(f"Error threshold exceeded: {self.error_count} errors in last hour")
    
    def trigger_alert(self, message):
        """Trigger alert for critical issues."""
        logger = logging.getLogger(__name__)
        logger.critical(f"ALERT: {message}")
        
        # In production, this would send notifications
        # For now, just log critically
    
    def cleanup(self):
        """Cleanup on shutdown."""
        pass

class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise ExternalServiceError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self):
        """Check if we should attempt to reset the circuit."""
        return (
            self.last_failure_time and
            (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

class ExternalServiceError(ApplicationError):
    """External service failure error."""
    def __init__(self, message, service=None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            user_message="External service temporarily unavailable. Please try again later.",
            **kwargs
        )
        if service:
            self.details['service'] = service

# Global instances
production_logger = ProductionLogger()
health_monitor = HealthMonitor()

# Alias for backward compatibility
ErrorHandler = ProductionLogger

# Circuit breakers for external services
ollama_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

def handle_error(error):
    """
    Global error handler function for API endpoints.
    
    Args:
        error: Exception instance to handle
        
    Returns:
        Flask JSON response with error details
    """
    if isinstance(error, ApplicationError):
        return production_logger.handle_application_error(error)
    else:
        return production_logger.handle_generic_error(error)
