"""
Centralized logging configuration for HR ATS System
"""

import logging
import os
from datetime import datetime

def setup_logging():
    """Setup centralized logging configuration"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for persistent logging
    log_filename = f"logs/hr_ats_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Specific loggers for different components
    loggers = [
        'app_factory',
        'core.initializers',
        'core.health_manager',
        'routes',
        'models',
        'utils'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
    
    logging.info("✅ Logging configuration initialized")
