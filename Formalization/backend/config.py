# Production Configuration for High-Volume Resume Processing

import os
from typing import Dict, Any

class ProductionConfig:
    """Configuration optimized for processing 100-200 resumes efficiently."""
    
    # Memory Management - can be overridden by environment variables
    MAX_MEMORY_CACHE_SIZE = int(os.getenv('MAX_MEMORY_CACHE_SIZE', 50))
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1))  # Process one resume at a time for stability
    MAX_CONCURRENT_PROCESSING = int(os.getenv('MAX_CONCURRENT_PROCESSING', 1))  # Disable concurrency for Ollama
    
    # File Management
    COMPRESS_PROCESSED_FILES = os.getenv('COMPRESS_PROCESSED_FILES', 'True').lower() == 'true'
    MAX_FILE_AGE_HOURS = 24  # Auto-cleanup files older than 24 hours
    ENABLE_DISK_CACHE = True
    
    # AI Processing Optimization
    AI_TIMEOUT = 1200  # Increased from 200 to 300 seconds for limited hardware
    AI_CONNECTION_POOL_SIZE = 4
    AI_RETRY_ATTEMPTS = 2
    ENABLE_AI_RESPONSE_CACHING = os.getenv('ENABLE_AI_RESPONSE_CACHING', 'True').lower() == 'true'
    
    # Model Selection for High Volume
    HIGH_VOLUME_MODEL = 'qwen2.5:3b'  # Faster model for bulk processing
    ACCURACY_MODEL = 'qwen2.5:7b'     # Higher accuracy for critical resumes
    
    # Batch Processing
    ENABLE_BATCH_MODE = True
    BATCH_ANALYSIS_THRESHOLD = int(os.getenv('BATCH_ANALYSIS_THRESHOLD', 5))
    
    # Memory Monitoring
    MEMORY_WARNING_THRESHOLD = float(os.getenv('MEMORY_WARNING_THRESHOLD', 0.8))
    ENABLE_MEMORY_MONITORING = os.getenv('ENABLE_MEMORY_MONITORING', 'True').lower() == 'true'
    
    # Database-like storage (file-based for local deployment)
    ENABLE_PERSISTENT_STORAGE = os.getenv('ENABLE_PERSISTENT_STORAGE', 'True').lower() == 'true'
    STORAGE_FORMAT = 'json'  # 'json' or 'pickle'
    BATCH_ANALYSIS_THRESHOLD = 5  # Switch to batch mode when >= 5 resumes
    
    # Memory Monitoring
    MEMORY_WARNING_THRESHOLD = 0.8  # 80% memory usage warning
    ENABLE_MEMORY_MONITORING = True
    
    # Database-like storage (file-based for local deployment)
    ENABLE_PERSISTENT_STORAGE = True
    STORAGE_FORMAT = 'json'  # 'json' or 'pickle'
    
    @classmethod
    def get_model_for_volume(cls, resume_count: int) -> str:
        """Select optimal model based on processing volume."""
        if resume_count >= 20:
            return cls.HIGH_VOLUME_MODEL
        return cls.ACCURACY_MODEL
    
    @classmethod
    def get_concurrent_limit(cls, resume_count: int) -> int:
        """Get optimal concurrency limit based on volume."""
        # Disabled concurrency for Ollama stability
        return 1

# Environment-based configuration
config = ProductionConfig()
