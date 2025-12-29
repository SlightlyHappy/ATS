"""
WSGI entry point with eventlet monkey patching handled properly.
This fixes the eventlet import issues and application context problems.
"""
import os
import sys

# Set environment variable to indicate we're using eventlet
os.environ['WORKER_CLASS'] = 'eventlet'

# Monkey patch early, before any other imports
try:
    import eventlet
    eventlet.monkey_patch()
    print("Eventlet monkey patching applied successfully")
except ImportError:
    print("Eventlet not available, using standard threading")

# Add the application directory to Python path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Now import the application
from app import create_app
from app.services.monitoring_scheduler import init_monitoring_scheduler, start_monitoring

# Create the application
app = create_app()

# Initialize monitoring in a safe way
try:
    with app.app_context():
        scheduler = init_monitoring_scheduler(app)
        
        # Start monitoring in production
        if not app.debug:
            start_monitoring()
            app.logger.info("Monitoring scheduler started for production")
        else:
            app.logger.info("Monitoring scheduler initialized but not started (debug mode)")
            
except Exception as e:
    app.logger.error(f"Failed to initialize monitoring scheduler: {e}")

# WSGI application
application = app

if __name__ == "__main__":
    print("Starting Flask application with eventlet support...")
    # Run with eventlet if available
    try:
        import eventlet.wsgi
        eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8000)), app)
    except ImportError:
        app.run(host='0.0.0.0', port=8000, debug=False)
