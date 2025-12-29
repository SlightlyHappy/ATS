"""
Startup Configuration for HR ATS Application
Centralized configuration management for startup processes
"""

import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class ServiceConfig:
    """Configuration for individual services"""
    name: str
    required: bool = True
    timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 5
    health_check_interval: int = 10
    dependencies: List[str] = field(default_factory=list)
    environment_vars: List[str] = field(default_factory=list)

@dataclass
class StartupConfig:
    """Centralized startup configuration"""
    
    # Environment
    is_production: bool = field(default_factory=lambda: os.getenv('RAILWAY_ENVIRONMENT') == 'production')
    is_railway: bool = field(default_factory=lambda: bool(os.getenv('RAILWAY_ENVIRONMENT')))
    debug_mode: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    
    # Timeouts and retries
    global_startup_timeout: int = 300  # 5 minutes total startup timeout
    service_startup_timeout: int = 60   # Per service timeout
    health_check_timeout: int = 30      # Health check timeout
    
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Service definitions
    services: Dict[str, ServiceConfig] = field(default_factory=lambda: {
        'database': ServiceConfig(
            name='database',
            required=True,
            timeout=60,
            retry_count=3,
            environment_vars=['DATABASE_URL', 'DATABASE_PUBLIC_URL']
        ),
        'ollama': ServiceConfig(
            name='ollama',
            required=False,  # Can continue without Ollama
            timeout=120,
            retry_count=2,
            dependencies=[]
        ),
        'ai_processor': ServiceConfig(
            name='ai_processor',
            required=False,
            timeout=30,
            retry_count=2,
            dependencies=['database']
        ),
        'health_monitor': ServiceConfig(
            name='health_monitor',
            required=False,
            timeout=15,
            retry_count=1,
            dependencies=['database']
        )
    })
    
    def __post_init__(self):
        """Post initialization setup"""
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format=self.log_format,
            handlers=[logging.StreamHandler()]
        )
        
        # Adjust configuration for Railway environment
        if self.is_railway:
            self._configure_for_railway()
    
    def _configure_for_railway(self):
        """Adjust configuration for Railway deployment"""
        # Railway-specific optimizations
        self.services['database'].timeout = 90  # Railway DB can be slower to connect
        self.services['ollama'].timeout = 180   # Model loading takes time
        
        # Railway has 32GB RAM, so we can be more aggressive with Ollama
        if os.getenv('RAILWAY_MEMORY_OPTIMIZED') == 'true':
            self.services['ollama'].required = True  # Make Ollama required on Railway Pro
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service"""
        return self.services.get(service_name)
    
    def get_required_services(self) -> List[str]:
        """Get list of required services"""
        return [name for name, config in self.services.items() if config.required]
    
    def get_optional_services(self) -> List[str]:
        """Get list of optional services"""
        return [name for name, config in self.services.items() if not config.required]
    
    def validate_environment(self) -> List[str]:
        """Validate environment variables for all services"""
        missing_vars = []
        
        for service_name, config in self.services.items():
            if config.required:
                for var in config.environment_vars:
                    if not os.getenv(var):
                        missing_vars.append(f"{service_name}: {var}")
        
        return missing_vars
