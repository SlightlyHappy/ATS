"""
Production-ready lazy model loader to avoid circular imports
"""

import logging

logger = logging.getLogger(__name__)

class LazyModelLoader:
    """Production-optimized lazy loader for database models"""
    
    def __init__(self):
        self._models_loaded = False
        self._models = {}
        self._load_errors = []
    
    def load_models(self, app):
        """Load all models within app context with production safety"""
        if self._models_loaded:
            return self._models
            
        logger.info('Loading models lazily...')
        
        # Production-safe context checking
        try:
            from flask import has_app_context
            
            if not has_app_context():
                logger.error('No app context available for model loading')
                return {}
        except ImportError:
            # Flask not available, continue anyway
            logger.warning('Flask context checking not available')
        
        # Reset errors for new attempt
        self._load_errors = []
        
        try:
            # Import models individually with error isolation
            models_to_load = [
                ('User', 'app.models.user', ['User', 'CreditTransaction']),
                ('Resume', 'app.models.resume', ['Resume']),
                ('Analysis', 'app.models.analysis', ['Analysis']),
                ('Queue', 'app.models.queue', ['AnalysisQueue', 'BatchUpload']),
                ('Admin', 'app.models.admin', ['AdminUser', 'AdminAction', 'SystemConfiguration', 'AdminNotification']),
                ('Sales', 'app.models.sales', ['Lead', 'LeadScoreHistory', 'LeadActivity', 'SalesMetrics', 'ROICalculation']),
                ('Analytics', 'app.models.analytics', ['PerformanceMetric', 'UsageInsight', 'ErrorTracking', 'SystemAlert', 'AnalyticsSnapshot']),
                ('API', 'app.models.api_management', ['ApiKey', 'RateLimitRule', 'Webhook', 'AccessLog'])
            ]
            
            loaded_models = {}
            
            for module_name, module_path, model_names in models_to_load:
                try:
                    module = __import__(module_path, fromlist=model_names)
                    for model_name in model_names:
                        if hasattr(module, model_name):
                            model_class = getattr(module, model_name)
                            loaded_models[model_name] = model_class
                            logger.debug(f'✓ Loaded {model_name}')
                        else:
                            logger.warning(f'⚠ Model {model_name} not found in {module_path}')
                            self._load_errors.append(f'{model_name} not found')
                            
                except ImportError as e:
                    error_msg = f'Failed to import {module_path}: {e}'
                    logger.error(error_msg)
                    self._load_errors.append(error_msg)
                except Exception as e:
                    error_msg = f'Error loading {module_name} models: {e}'
                    logger.error(error_msg)
                    self._load_errors.append(error_msg)
            
            self._models = loaded_models
            self._models_loaded = True
            
            if self._load_errors:
                logger.warning(f'✓ Loaded {len(self._models)} models with {len(self._load_errors)} errors')
                logger.warning(f'Errors: {"; ".join(self._load_errors)}')
            else:
                logger.info(f'✓ Successfully loaded {len(self._models)} models')
            
            return self._models
            
        except Exception as e:
            error_msg = f'Critical error in model loading: {e}'
            logger.error(error_msg)
            import traceback
            logger.error(f'Traceback: {traceback.format_exc()}')
            self._load_errors.append(error_msg)
            return {}
    
    def get_model(self, model_name, app=None):
        """Get a specific model by name with production safety"""
        if not self._models_loaded and app:
            self.load_models(app)
        return self._models.get(model_name)
    
    def get_all_models(self, app=None):
        """Get all loaded models with production safety"""
        if not self._models_loaded and app:
            self.load_models(app)
        return self._models.copy()  # Return copy to prevent external modification
    
    def get_load_errors(self):
        """Get any errors that occurred during model loading"""
        return self._load_errors.copy()
    
    def is_loaded(self):
        """Check if models have been loaded"""
        return self._models_loaded
    
    def get_loaded_count(self):
        """Get count of successfully loaded models"""
        return len(self._models)

# Global instance
model_loader = LazyModelLoader()
