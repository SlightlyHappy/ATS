"""
Analytics middleware for automatic user action tracking.
Implements Priority 1.3: Enhanced Monitoring features.
"""
import time
from flask import request, g
from functools import wraps

def track_user_action(event_type: str, event_category: str = None, 
                     event_action: str = None, resource_type: str = None):
    """Decorator to automatically track user actions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_code = None
            error_message = None
            
            try:
                # Execute the original function
                result = func(*args, **kwargs)
                
                return result
                
            except Exception as e:
                success = False
                error_code = getattr(e, 'error_code', 'UNKNOWN_ERROR')
                error_message = str(e)
                raise
                
            finally:
                # Track the action regardless of success/failure
                try:
                    duration = time.time() - start_time
                    
                    # Import here to avoid circular imports
                    from app.services.analytics_service import analytics_service
                    from app.services.auth_manager import get_current_user
                    
                    # Get user info
                    current_user = get_current_user()
                    user_id = str(current_user.id) if current_user else None
                    
                    # Determine action details
                    action_category = event_category or 'api'
                    action_name = event_action or func.__name__
                    
                    # Track the action
                    analytics_service.track_user_action(
                        event_type=event_type,
                        event_category=action_category,
                        event_action=action_name,
                        user_id=user_id,
                        resource_type=resource_type,
                        duration_seconds=duration,
                        success=success,
                        error_code=error_code,
                        error_message=error_message
                    )
                    
                except Exception as tracking_error:
                    # Don't let tracking failures affect the main function
                    pass
        
        return wrapper
    return decorator

class AnalyticsMiddleware:
    """Middleware for automatic analytics tracking."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize analytics middleware."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Called before each request."""
        # Store request start time
        g.request_start_time = time.time()
        
        # Generate session ID if not exists
        if not hasattr(g, 'session_id'):
            import uuid
            g.session_id = str(uuid.uuid4())
    
    def after_request(self, response):
        """Called after each request."""
        try:
            # Calculate response time
            if hasattr(g, 'request_start_time'):
                response_time = time.time() - g.request_start_time
                
                # Record performance metric for API response time
                from app.services.analytics_service import analytics_service
                
                analytics_service.record_performance_metric(
                    'api', 'response_time', 'application',
                    response_time, 'seconds', 2.0, 5.0,
                    tags={
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'status_code': response.status_code
                    }
                )
                
                # Track page views and API calls
                if request.method in ['GET', 'POST', 'PUT', 'DELETE']:
                    from app.services.auth_manager import get_current_user
                    
                    current_user = get_current_user()
                    user_id = str(current_user.id) if current_user else None
                    
                    event_type = 'page_view' if request.method == 'GET' and not request.path.startswith('/api/') else 'api_call'
                    
                    analytics_service.track_user_action(
                        event_type=event_type,
                        event_category='navigation' if event_type == 'page_view' else 'api',
                        event_action=f"{request.method} {request.endpoint or request.path}",
                        user_id=user_id,
                        duration_seconds=response_time,
                        success=response.status_code < 400,
                        error_code=str(response.status_code) if response.status_code >= 400 else None,
                        metadata={
                            'endpoint': request.endpoint,
                            'method': request.method,
                            'status_code': response.status_code,
                            'path': request.path
                        }
                    )
        
        except Exception as e:
            # Don't let analytics tracking affect the response
            pass
        
        return response

# Global analytics middleware instance
analytics_middleware = AnalyticsMiddleware()
