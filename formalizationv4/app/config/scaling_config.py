"""
Smart Resource Scaling Configuration
Centralizes configuration for the smart resource scaling system.
"""
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ResourceScalingConfig:
    """Configuration for smart resource scaling system."""
    
    # Resource Monitoring
    monitoring_interval: int = 15  # seconds
    resource_alert_threshold_memory: float = 85.0  # percentage
    resource_alert_threshold_cpu: float = 80.0     # percentage
    queue_alert_threshold: int = 20                 # number of items
    
    # Worker Scaling
    min_workers: int = 2
    max_workers: int = 8
    target_queue_length: int = 10
    scale_up_threshold: int = 15
    scale_down_threshold: int = 5
    
    # Decision Making
    scaling_cooldown_seconds: int = 300  # 5 minutes
    sustained_load_duration: int = 180   # 3 minutes
    worker_idle_threshold: int = 600     # 10 minutes
    
    # Queue Management
    max_concurrent_jobs_per_worker: int = 3
    queue_priority_levels: int = 6
    priority_adjustment_interval: int = 60  # seconds
    batch_processing_threshold: int = 10
    
    # Performance Optimization
    memory_allocation_per_worker: int = 4096  # MB
    cpu_allocation_per_worker: float = 4.0    # cores
    disk_space_threshold: float = 90.0        # percentage
    
    # Production Environment
    production_mode: bool = False
    debug_logging: bool = True
    metrics_retention_days: int = 7
    
    @classmethod
    def from_environment(cls) -> 'ResourceScalingConfig':
        """Create configuration from environment variables."""
        return cls(
            # Resource Monitoring
            monitoring_interval=int(os.getenv('RESOURCE_MONITORING_INTERVAL', '15')),
            resource_alert_threshold_memory=float(os.getenv('MEMORY_ALERT_THRESHOLD', '85.0')),
            resource_alert_threshold_cpu=float(os.getenv('CPU_ALERT_THRESHOLD', '80.0')),
            queue_alert_threshold=int(os.getenv('QUEUE_ALERT_THRESHOLD', '20')),
            
            # Worker Scaling
            min_workers=int(os.getenv('MIN_WORKERS', '2')),
            max_workers=int(os.getenv('MAX_WORKERS', '8')),
            target_queue_length=int(os.getenv('TARGET_QUEUE_LENGTH', '10')),
            scale_up_threshold=int(os.getenv('SCALE_UP_THRESHOLD', '15')),
            scale_down_threshold=int(os.getenv('SCALE_DOWN_THRESHOLD', '5')),
            
            # Decision Making
            scaling_cooldown_seconds=int(os.getenv('SCALING_COOLDOWN', '300')),
            sustained_load_duration=int(os.getenv('SUSTAINED_LOAD_DURATION', '180')),
            worker_idle_threshold=int(os.getenv('WORKER_IDLE_THRESHOLD', '600')),
            
            # Queue Management
            max_concurrent_jobs_per_worker=int(os.getenv('MAX_CONCURRENT_JOBS_PER_WORKER', '3')),
            queue_priority_levels=int(os.getenv('QUEUE_PRIORITY_LEVELS', '6')),
            priority_adjustment_interval=int(os.getenv('PRIORITY_ADJUSTMENT_INTERVAL', '60')),
            batch_processing_threshold=int(os.getenv('BATCH_PROCESSING_THRESHOLD', '10')),
            
            # Performance Optimization
            memory_allocation_per_worker=int(os.getenv('MEMORY_PER_WORKER', '4096')),
            cpu_allocation_per_worker=float(os.getenv('CPU_PER_WORKER', '4.0')),
            disk_space_threshold=float(os.getenv('DISK_SPACE_THRESHOLD', '90.0')),
            
            # Production Environment
            production_mode=os.getenv('PRODUCTION_MODE', 'false').lower() == 'true',
            debug_logging=os.getenv('DEBUG_LOGGING', 'true').lower() == 'true',
            metrics_retention_days=int(os.getenv('METRICS_RETENTION_DAYS', '7'))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'resource_monitoring': {
                'interval': self.monitoring_interval,
                'memory_threshold': self.resource_alert_threshold_memory,
                'cpu_threshold': self.resource_alert_threshold_cpu,
                'queue_threshold': self.queue_alert_threshold
            },
            'worker_scaling': {
                'min_workers': self.min_workers,
                'max_workers': self.max_workers,
                'target_queue_length': self.target_queue_length,
                'scale_up_threshold': self.scale_up_threshold,
                'scale_down_threshold': self.scale_down_threshold
            },
            'decision_making': {
                'cooldown_seconds': self.scaling_cooldown_seconds,
                'sustained_load_duration': self.sustained_load_duration,
                'idle_threshold': self.worker_idle_threshold
            },
            'queue_management': {
                'max_concurrent_per_worker': self.max_concurrent_jobs_per_worker,
                'priority_levels': self.queue_priority_levels,
                'priority_adjustment_interval': self.priority_adjustment_interval,
                'batch_threshold': self.batch_processing_threshold
            },
            'performance': {
                'memory_per_worker': self.memory_allocation_per_worker,
                'cpu_per_worker': self.cpu_allocation_per_worker,
                'disk_threshold': self.disk_space_threshold
            },
            'environment': {
                'production_mode': self.production_mode,
                'debug_logging': self.debug_logging,
                'metrics_retention_days': self.metrics_retention_days
            }
        }
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        try:
            # Check worker scaling bounds
            if self.min_workers <= 0 or self.max_workers <= 0:
                raise ValueError("Worker counts must be positive")
            
            if self.min_workers >= self.max_workers:
                raise ValueError("min_workers must be less than max_workers")
            
            # Check thresholds
            if not (0 <= self.resource_alert_threshold_memory <= 100):
                raise ValueError("Memory threshold must be between 0 and 100")
            
            if not (0 <= self.resource_alert_threshold_cpu <= 100):
                raise ValueError("CPU threshold must be between 0 and 100")
            
            if self.scale_up_threshold <= self.scale_down_threshold:
                raise ValueError("scale_up_threshold must be greater than scale_down_threshold")
            
            # Check timing parameters
            if self.scaling_cooldown_seconds < 60:
                raise ValueError("Scaling cooldown must be at least 60 seconds")
            
            if self.sustained_load_duration < 60:
                raise ValueError("Sustained load duration must be at least 60 seconds")
            
            return True
            
        except ValueError as e:
            print(f"Configuration validation error: {e}")
            return False

# Global configuration instance
scaling_config = ResourceScalingConfig.from_environment()

# Validate configuration on import
if not scaling_config.validate():
    print("Warning: Invalid scaling configuration detected")

def get_scaling_config() -> ResourceScalingConfig:
    """Get the global scaling configuration."""
    return scaling_config

def update_scaling_config(**kwargs) -> bool:
    """Update scaling configuration parameters."""
    global scaling_config
    
    try:
        # Create new config with updated parameters
        current_dict = scaling_config.__dict__.copy()
        current_dict.update(kwargs)
        
        new_config = ResourceScalingConfig(**current_dict)
        
        # Validate new configuration
        if new_config.validate():
            scaling_config = new_config
            return True
        else:
            print("Failed to update configuration: validation failed")
            return False
            
    except Exception as e:
        print(f"Failed to update configuration: {e}")
        return False

def get_production_config() -> ResourceScalingConfig:
    """Get optimized configuration for production environment."""
    return ResourceScalingConfig(
        # Production-optimized resource monitoring
        monitoring_interval=10,
        resource_alert_threshold_memory=90.0,
        resource_alert_threshold_cpu=85.0,
        queue_alert_threshold=30,
        
        # Production worker scaling
        min_workers=4,
        max_workers=16,
        target_queue_length=15,
        scale_up_threshold=25,
        scale_down_threshold=8,
        
        # Production decision making
        scaling_cooldown_seconds=180,  # 3 minutes
        sustained_load_duration=120,   # 2 minutes
        worker_idle_threshold=900,     # 15 minutes
        
        # Production queue management
        max_concurrent_jobs_per_worker=4,
        queue_priority_levels=8,
        priority_adjustment_interval=30,
        batch_processing_threshold=20,
        
        # Production performance
        memory_allocation_per_worker=8192,  # 8GB
        cpu_allocation_per_worker=8.0,      # 8 cores
        disk_space_threshold=95.0,
        
        # Production environment
        production_mode=True,
        debug_logging=False,
        metrics_retention_days=30
    )

def get_development_config() -> ResourceScalingConfig:
    """Get configuration optimized for development environment."""
    return ResourceScalingConfig(
        # Development resource monitoring
        monitoring_interval=30,
        resource_alert_threshold_memory=70.0,
        resource_alert_threshold_cpu=60.0,
        queue_alert_threshold=10,
        
        # Development worker scaling
        min_workers=1,
        max_workers=4,
        target_queue_length=5,
        scale_up_threshold=8,
        scale_down_threshold=3,
        
        # Development decision making
        scaling_cooldown_seconds=600,  # 10 minutes
        sustained_load_duration=300,   # 5 minutes
        worker_idle_threshold=300,     # 5 minutes
        
        # Development queue management
        max_concurrent_jobs_per_worker=2,
        queue_priority_levels=4,
        priority_adjustment_interval=120,
        batch_processing_threshold=5,
        
        # Development performance
        memory_allocation_per_worker=2048,  # 2GB
        cpu_allocation_per_worker=2.0,      # 2 cores
        disk_space_threshold=80.0,
        
        # Development environment
        production_mode=False,
        debug_logging=True,
        metrics_retention_days=3
    )

def apply_environment_config():
    """Apply configuration based on environment."""
    global scaling_config
    
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    if environment == 'production':
        scaling_config = get_production_config()
        print("Applied production scaling configuration")
    elif environment == 'development':
        scaling_config = get_development_config()
        print("Applied development scaling configuration")
    else:
        # Use environment variables or defaults
        scaling_config = ResourceScalingConfig.from_environment()
        print("Applied custom scaling configuration from environment")
    
    # Validate the applied configuration
    if not scaling_config.validate():
        print("Warning: Applied configuration failed validation")

# Apply environment-specific configuration on import
apply_environment_config()
