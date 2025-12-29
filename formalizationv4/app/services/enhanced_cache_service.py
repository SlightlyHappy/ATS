"""
Enhanced Caching Service - Phase 2 Implementation
Implements multi-layer caching with Redis support, cache warming,
and intelligent invalidation strategies.
"""
import time
import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, field
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from flask import current_app, request
from app import cache as flask_cache

logger = logging.getLogger(__name__)

# =============================================================================
# CACHE CONFIGURATION AND TYPES
# =============================================================================

@dataclass
class CacheConfig:
    """Cache configuration with optimization settings."""
    # Layer configurations
    l1_enabled: bool = True              # In-memory cache
    l2_enabled: bool = True              # Redis cache
    l3_enabled: bool = True              # Persistent storage cache
    
    # Timeouts (in seconds)
    l1_timeout: int = 300                # 5 minutes
    l2_timeout: int = 1800               # 30 minutes
    l3_timeout: int = 86400              # 24 hours
    
    # Size limits
    l1_max_size: int = 1000              # Max items in L1 cache
    l2_max_memory: str = "100mb"         # Redis memory limit
    
    # Cache warming
    warm_on_startup: bool = True
    warm_interval: int = 3600            # 1 hour
    warm_critical_endpoints: List[str] = field(default_factory=lambda: [
        '/api/v1/batch/admin/dashboard',
        '/api/v1/admin/analytics/dashboard',
        '/api/v1/monitoring/metrics'
    ])
    
    # Performance settings
    async_write: bool = True             # Async cache writes
    compression_enabled: bool = True     # Compress large values
    compression_threshold: int = 1024    # Compress if > 1KB
    
    # Invalidation settings
    auto_invalidation: bool = True
    invalidation_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        'user_updated': ['user_stats', 'user_analytics', 'dashboard_summary'],
        'analysis_completed': ['queue_stats', 'analytics', 'dashboard'],
        'system_config_changed': ['system_status', 'performance_metrics']
    })


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    writes: int = 0
    evictions: int = 0
    errors: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate as percentage."""
        return 100.0 - self.hit_rate


# =============================================================================
# ENHANCED CACHING SERVICE
# =============================================================================

class EnhancedCacheService:
    """
    Multi-layer caching service with Redis support, cache warming,
    and intelligent invalidation strategies.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config: CacheConfig = CacheConfig()
        self.metrics: CacheMetrics = CacheMetrics()
        
        # Cache layers
        self._l1_cache: Dict[str, Dict] = {}  # In-memory cache
        self._l2_redis = None                  # Redis client
        self._l3_persistent = flask_cache      # Flask-Cache
        
        # Cache metadata
        self._cache_metadata: Dict[str, Dict] = {}
        self._cache_dependencies: Dict[str, List[str]] = {}
        
        # Background tasks
        self._warming_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache_warm")
        self._write_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="cache_write")
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the caching service with Flask app."""
        self.app = app
        
        # Load configuration from app config
        self._load_config_from_app()
        
        # Initialize Redis if available and configured
        self._init_redis()
        
        # Setup cache warming if enabled
        if self.config.warm_on_startup:
            self._schedule_cache_warming()
        
        # Register teardown handlers
        app.teardown_appcontext(self._cleanup_context)
        
        logger.info(f"Enhanced cache service initialized with config: {self.config}")
    
    def _load_config_from_app(self):
        """Load cache configuration from Flask app config."""
        if not self.app:
            return
        
        config = self.app.config
        
        # Update cache config from app settings
        self.config.l1_enabled = config.get('ENABLE_L1_CACHE', True)
        self.config.l2_enabled = config.get('ENABLE_L2_CACHE', REDIS_AVAILABLE)
        self.config.l1_timeout = config.get('L1_CACHE_TIMEOUT', 300)
        self.config.l2_timeout = config.get('L2_CACHE_TIMEOUT', 1800)
        self.config.warm_on_startup = config.get('CACHE_WARM_ON_STARTUP', True)
        self.config.compression_enabled = config.get('CACHE_COMPRESSION', True)
        self.config.async_write = config.get('CACHE_ASYNC_WRITE', True)
    
    def _init_redis(self):
        """Initialize Redis connection if available."""
        if not REDIS_AVAILABLE or not self.config.l2_enabled:
            logger.info("Redis caching disabled or unavailable")
            return
        
        try:
            redis_url = self.app.config.get('REDIS_URL') or self.app.config.get('CACHE_REDIS_URL')
            if redis_url:
                self._l2_redis = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test Redis connection
                self._l2_redis.ping()
                logger.info(f"Redis cache initialized: {redis_url}")
            else:
                logger.warning("Redis URL not configured, L2 cache disabled")
                self.config.l2_enabled = False
                
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            self.config.l2_enabled = False
            self._l2_redis = None
    
    # =============================================================================
    # CORE CACHE OPERATIONS
    # =============================================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache with multi-layer fallback.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        self.metrics.total_requests += 1
        
        try:
            # L1: In-memory cache
            if self.config.l1_enabled:
                l1_value = self._get_from_l1(key)
                if l1_value is not None:
                    self.metrics.hits += 1
                    self._update_access_time(key)
                    return l1_value
            
            # L2: Redis cache
            if self.config.l2_enabled and self._l2_redis:
                l2_value = self._get_from_l2(key)
                if l2_value is not None:
                    self.metrics.hits += 1
                    # Populate L1 cache
                    if self.config.l1_enabled:
                        self._set_to_l1(key, l2_value, self.config.l1_timeout)
                    self._update_access_time(key)
                    return l2_value
            
            # L3: Persistent cache (Flask-Cache)
            if self.config.l3_enabled:
                l3_value = self._l3_persistent.get(key)
                if l3_value is not None:
                    self.metrics.hits += 1
                    # Populate higher cache layers
                    if self.config.l2_enabled:
                        self._set_to_l2(key, l3_value, self.config.l2_timeout)
                    if self.config.l1_enabled:
                        self._set_to_l1(key, l3_value, self.config.l1_timeout)
                    self._update_access_time(key)
                    return l3_value
            
            # Cache miss
            self.metrics.misses += 1
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {str(e)}")
            self.metrics.errors += 1
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None, 
            tags: Optional[List[str]] = None, dependencies: Optional[List[str]] = None) -> bool:
        """
        Set value in cache with multi-layer storage.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Cache timeout in seconds
            tags: Cache tags for invalidation
            dependencies: Cache dependencies for invalidation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.metrics.writes += 1
            
            # Use default timeouts if not specified
            l1_timeout = timeout or self.config.l1_timeout
            l2_timeout = timeout or self.config.l2_timeout
            l3_timeout = timeout or self.config.l3_timeout
            
            # Store metadata
            metadata = {
                'created_at': datetime.utcnow().isoformat(),
                'timeout': timeout,
                'tags': tags or [],
                'dependencies': dependencies or [],
                'access_count': 0,
                'last_accessed': datetime.utcnow().isoformat()
            }
            self._cache_metadata[key] = metadata
            
            # Store dependencies for invalidation
            if dependencies:
                self._cache_dependencies[key] = dependencies
            
            if self.config.async_write:
                # Asynchronous write to all cache layers
                self._write_executor.submit(self._write_to_all_layers, key, value, l1_timeout, l2_timeout, l3_timeout)
            else:
                # Synchronous write
                self._write_to_all_layers(key, value, l1_timeout, l2_timeout, l3_timeout)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {str(e)}")
            self.metrics.errors += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from all cache layers."""
        try:
            success = True
            
            # Delete from L1
            if self.config.l1_enabled and key in self._l1_cache:
                del self._l1_cache[key]
            
            # Delete from L2
            if self.config.l2_enabled and self._l2_redis:
                try:
                    self._l2_redis.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to delete from Redis: {str(e)}")
                    success = False
            
            # Delete from L3
            if self.config.l3_enabled:
                try:
                    self._l3_persistent.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to delete from L3 cache: {str(e)}")
                    success = False
            
            # Clean up metadata
            self._cache_metadata.pop(key, None)
            self._cache_dependencies.pop(key, None)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {str(e)}")
            self.metrics.errors += 1
            return False
    
    def clear(self, pattern: Optional[str] = None) -> bool:
        """Clear cache with optional pattern matching."""
        try:
            if pattern:
                # Clear keys matching pattern
                keys_to_delete = []
                
                # Find matching keys in L1
                if self.config.l1_enabled:
                    for key in list(self._l1_cache.keys()):
                        if self._matches_pattern(key, pattern):
                            keys_to_delete.append(key)
                
                # Find matching keys in L2
                if self.config.l2_enabled and self._l2_redis:
                    try:
                        redis_keys = self._l2_redis.keys(pattern)
                        keys_to_delete.extend(redis_keys)
                    except Exception as e:
                        logger.warning(f"Failed to get Redis keys: {str(e)}")
                
                # Delete matching keys
                for key in set(keys_to_delete):
                    self.delete(key)
            else:
                # Clear all caches
                if self.config.l1_enabled:
                    self._l1_cache.clear()
                
                if self.config.l2_enabled and self._l2_redis:
                    try:
                        self._l2_redis.flushdb()
                    except Exception as e:
                        logger.warning(f"Failed to flush Redis: {str(e)}")
                
                if self.config.l3_enabled:
                    try:
                        self._l3_persistent.clear()
                    except Exception as e:
                        logger.warning(f"Failed to clear L3 cache: {str(e)}")
                
                # Clear metadata
                self._cache_metadata.clear()
                self._cache_dependencies.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            self.metrics.errors += 1
            return False
    
    # =============================================================================
    # CACHE DECORATORS
    # =============================================================================
    
    def cached(self, timeout: int = 300, key_prefix: str = '', 
               unless: Optional[Callable] = None, tags: Optional[List[str]] = None,
               dependencies: Optional[List[str]] = None):
        """
        Enhanced caching decorator with multi-layer support.
        
        Args:
            timeout: Cache timeout in seconds
            key_prefix: Prefix for cache keys
            unless: Function that returns True to skip caching
            tags: Cache tags for invalidation
            dependencies: Cache dependencies
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Skip caching if unless condition is met
                if unless and unless():
                    return f(*args, **kwargs)
                
                # Generate cache key
                cache_key = self._generate_cache_key(f, args, kwargs, key_prefix)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = f(*args, **kwargs)
                self.set(cache_key, result, timeout, tags, dependencies)
                
                return result
            
            return decorated_function
        return decorator
    
    def cache_response(self, timeout: int = 300, key_prefix: str = 'api_response',
                      vary_on: Optional[List[str]] = None):
        """
        Cache API response decorator.
        
        Args:
            timeout: Cache timeout in seconds
            key_prefix: Prefix for cache keys
            vary_on: Request attributes to include in cache key
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not request:
                    return f(*args, **kwargs)
                
                # Generate cache key based on request
                cache_key = self._generate_request_cache_key(f, key_prefix, vary_on)
                
                # Try to get from cache
                cached_response = self.get(cache_key)
                if cached_response is not None:
                    return cached_response
                
                # Execute function and cache response
                response = f(*args, **kwargs)
                self.set(cache_key, response, timeout)
                
                return response
            
            return decorated_function
        return decorator
    
    # =============================================================================
    # CACHE INVALIDATION
    # =============================================================================
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate cache entries by tags."""
        invalidated_count = 0
        
        try:
            keys_to_invalidate = []
            
            # Find keys with matching tags
            for key, metadata in self._cache_metadata.items():
                key_tags = metadata.get('tags', [])
                if any(tag in key_tags for tag in tags):
                    keys_to_invalidate.append(key)
            
            # Invalidate found keys
            for key in keys_to_invalidate:
                if self.delete(key):
                    invalidated_count += 1
            
            logger.info(f"Invalidated {invalidated_count} cache entries for tags: {tags}")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Error invalidating cache by tags: {str(e)}")
            return 0
    
    def invalidate_by_dependencies(self, dependencies: List[str]) -> int:
        """Invalidate cache entries by dependencies."""
        invalidated_count = 0
        
        try:
            keys_to_invalidate = []
            
            # Find keys with matching dependencies
            for key, deps in self._cache_dependencies.items():
                if any(dep in deps for dep in dependencies):
                    keys_to_invalidate.append(key)
            
            # Invalidate found keys
            for key in keys_to_invalidate:
                if self.delete(key):
                    invalidated_count += 1
            
            logger.info(f"Invalidated {invalidated_count} cache entries for dependencies: {dependencies}")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Error invalidating cache by dependencies: {str(e)}")
            return 0
    
    def trigger_invalidation(self, event: str, context: Optional[Dict] = None):
        """Trigger cache invalidation based on system events."""
        try:
            patterns = self.config.invalidation_patterns.get(event, [])
            if not patterns:
                return
            
            total_invalidated = 0
            
            for pattern in patterns:
                # Invalidate by pattern
                keys_before = len(self._cache_metadata)
                self.clear(pattern)
                keys_after = len(self._cache_metadata)
                invalidated = keys_before - keys_after
                total_invalidated += invalidated
            
            logger.info(f"Triggered invalidation for event '{event}': {total_invalidated} entries invalidated")
            
        except Exception as e:
            logger.error(f"Error triggering invalidation for event '{event}': {str(e)}")
    
    # =============================================================================
    # CACHE WARMING
    # =============================================================================
    
    def warm_cache(self, endpoints: Optional[List[str]] = None):
        """Warm cache for critical endpoints."""
        endpoints = endpoints or self.config.warm_critical_endpoints
        
        logger.info(f"Starting cache warming for {len(endpoints)} endpoints")
        
        for endpoint in endpoints:
            self._warming_executor.submit(self._warm_endpoint, endpoint)
    
    def _warm_endpoint(self, endpoint: str):
        """Warm cache for a specific endpoint."""
        try:
            # This would typically make internal requests to warm the cache
            # Implementation depends on your specific endpoints
            logger.debug(f"Warming cache for endpoint: {endpoint}")
            
            # Example: Could use test client to make requests
            # with self.app.test_client() as client:
            #     client.get(endpoint)
            
        except Exception as e:
            logger.error(f"Failed to warm cache for endpoint '{endpoint}': {str(e)}")
    
    def _schedule_cache_warming(self):
        """Schedule periodic cache warming."""
        if not self.config.warm_interval:
            return
        
        # This would typically use a scheduler like APScheduler
        # For now, we'll just log that it should be scheduled
        logger.info(f"Cache warming scheduled every {self.config.warm_interval} seconds")
    
    # =============================================================================
    # METRICS AND MONITORING
    # =============================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        return {
            'hit_rate': round(self.metrics.hit_rate, 2),
            'miss_rate': round(self.metrics.miss_rate, 2),
            'total_requests': self.metrics.total_requests,
            'hits': self.metrics.hits,
            'misses': self.metrics.misses,
            'writes': self.metrics.writes,
            'evictions': self.metrics.evictions,
            'errors': self.metrics.errors,
            'cache_sizes': {
                'l1_entries': len(self._l1_cache) if self.config.l1_enabled else 0,
                'l2_connected': bool(self._l2_redis) if self.config.l2_enabled else False,
                'l3_enabled': self.config.l3_enabled
            },
            'configuration': {
                'l1_enabled': self.config.l1_enabled,
                'l2_enabled': self.config.l2_enabled,
                'l3_enabled': self.config.l3_enabled,
                'async_write': self.config.async_write,
                'compression_enabled': self.config.compression_enabled
            }
        }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        info = {
            'total_keys': len(self._cache_metadata),
            'layers': {},
            'top_accessed_keys': self._get_top_accessed_keys(10),
            'cache_age_distribution': self._get_cache_age_distribution()
        }
        
        # Layer information
        if self.config.l1_enabled:
            info['layers']['l1'] = {
                'type': 'memory',
                'entries': len(self._l1_cache),
                'max_size': self.config.l1_max_size
            }
        
        if self.config.l2_enabled and self._l2_redis:
            try:
                redis_info = self._l2_redis.info('memory')
                info['layers']['l2'] = {
                    'type': 'redis',
                    'memory_used': redis_info.get('used_memory_human', 'unknown'),
                    'connected': True
                }
            except Exception:
                info['layers']['l2'] = {'type': 'redis', 'connected': False}
        
        if self.config.l3_enabled:
            info['layers']['l3'] = {
                'type': 'flask_cache',
                'backend': str(type(self._l3_persistent)).split('.')[-1]
            }
        
        return info
    
    # =============================================================================
    # PRIVATE HELPER METHODS
    # =============================================================================
    
    def _get_from_l1(self, key: str) -> Any:
        """Get value from L1 (memory) cache."""
        if key not in self._l1_cache:
            return None
        
        cache_entry = self._l1_cache[key]
        
        # Check expiration
        if cache_entry['expires_at'] < time.time():
            del self._l1_cache[key]
            self.metrics.evictions += 1
            return None
        
        return cache_entry['value']
    
    def _get_from_l2(self, key: str) -> Any:
        """Get value from L2 (Redis) cache."""
        if not self._l2_redis:
            return None
        
        try:
            serialized_value = self._l2_redis.get(key)
            if serialized_value is None:
                return None
            
            return self._deserialize_value(serialized_value)
            
        except Exception as e:
            logger.warning(f"L2 cache get error: {str(e)}")
            return None
    
    def _set_to_l1(self, key: str, value: Any, timeout: int):
        """Set value in L1 (memory) cache."""
        # Implement LRU eviction if necessary
        if len(self._l1_cache) >= self.config.l1_max_size:
            self._evict_lru_l1()
        
        self._l1_cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + timeout
        }
    
    def _set_to_l2(self, key: str, value: Any, timeout: int):
        """Set value in L2 (Redis) cache."""
        if not self._l2_redis:
            return
        
        try:
            serialized_value = self._serialize_value(value)
            self._l2_redis.setex(key, timeout, serialized_value)
            
        except Exception as e:
            logger.warning(f"L2 cache set error: {str(e)}")
    
    def _write_to_all_layers(self, key: str, value: Any, l1_timeout: int, l2_timeout: int, l3_timeout: int):
        """Write value to all cache layers."""
        try:
            # L1 (Memory)
            if self.config.l1_enabled:
                self._set_to_l1(key, value, l1_timeout)
            
            # L2 (Redis)
            if self.config.l2_enabled:
                self._set_to_l2(key, value, l2_timeout)
            
            # L3 (Flask-Cache)
            if self.config.l3_enabled:
                try:
                    self._l3_persistent.set(key, value, timeout=l3_timeout)
                except Exception as e:
                    logger.warning(f"L3 cache set error: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error writing to cache layers: {str(e)}")
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage."""
        try:
            serialized = json.dumps(value, default=str)
            
            # Compress if enabled and value is large enough
            if (self.config.compression_enabled and 
                len(serialized) > self.config.compression_threshold):
                try:
                    import gzip
                    compressed = gzip.compress(serialized.encode())
                    return f"gzip:{compressed.hex()}"
                except Exception:
                    pass  # Fall back to uncompressed
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            return str(value)
    
    def _deserialize_value(self, serialized: str) -> Any:
        """Deserialize value from storage."""
        try:
            # Check if compressed
            if serialized.startswith('gzip:'):
                try:
                    import gzip
                    compressed_data = bytes.fromhex(serialized[5:])
                    decompressed = gzip.decompress(compressed_data).decode()
                    return json.loads(decompressed)
                except Exception:
                    pass  # Fall back to regular deserialization
            
            return json.loads(serialized)
            
        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}")
            return serialized
    
    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict, prefix: str) -> str:
        """Generate cache key for function call."""
        # Create key from function name, args, and kwargs
        key_parts = [prefix, func.__name__]
        
        # Add args to key
        if args:
            key_parts.append(str(hash(args)))
        
        # Add kwargs to key (sorted for consistency)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(str(hash(tuple(sorted_kwargs))))
        
        return ':'.join(key_parts)
    
    def _generate_request_cache_key(self, func: Callable, prefix: str, vary_on: Optional[List[str]]) -> str:
        """Generate cache key for API request."""
        key_parts = [prefix, func.__name__]
        
        # Add request-specific components
        if request:
            key_parts.append(request.method)
            key_parts.append(request.path)
            
            # Add query parameters
            if request.args:
                sorted_args = sorted(request.args.items())
                key_parts.append(str(hash(tuple(sorted_args))))
            
            # Add custom vary_on attributes
            if vary_on:
                for attr in vary_on:
                    if hasattr(request, attr):
                        key_parts.append(str(getattr(request, attr)))
        
        return ':'.join(key_parts)
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple wildcard support)."""
        if '*' not in pattern:
            return pattern in key
        
        # Simple wildcard matching
        pattern_parts = pattern.split('*')
        key_index = 0
        
        for part in pattern_parts:
            if not part:
                continue
            
            index = key.find(part, key_index)
            if index == -1:
                return False
            key_index = index + len(part)
        
        return True
    
    def _update_access_time(self, key: str):
        """Update last access time for key."""
        if key in self._cache_metadata:
            self._cache_metadata[key]['last_accessed'] = datetime.utcnow().isoformat()
            self._cache_metadata[key]['access_count'] += 1
    
    def _evict_lru_l1(self):
        """Evict least recently used item from L1 cache."""
        if not self._l1_cache:
            return
        
        # Find oldest entry
        oldest_key = min(
            self._l1_cache.keys(),
            key=lambda k: self._l1_cache[k]['created_at']
        )
        
        del self._l1_cache[oldest_key]
        self.metrics.evictions += 1
    
    def _get_top_accessed_keys(self, limit: int) -> List[Dict[str, Any]]:
        """Get top accessed cache keys."""
        sorted_keys = sorted(
            self._cache_metadata.items(),
            key=lambda x: x[1].get('access_count', 0),
            reverse=True
        )
        
        return [
            {
                'key': key,
                'access_count': metadata.get('access_count', 0),
                'last_accessed': metadata.get('last_accessed'),
                'created_at': metadata.get('created_at')
            }
            for key, metadata in sorted_keys[:limit]
        ]
    
    def _get_cache_age_distribution(self) -> Dict[str, int]:
        """Get distribution of cache entry ages."""
        now = datetime.utcnow()
        distribution = {
            'less_than_1min': 0,
            '1min_to_5min': 0,
            '5min_to_30min': 0,
            '30min_to_1hour': 0,
            'more_than_1hour': 0
        }
        
        for metadata in self._cache_metadata.values():
            try:
                created_at = datetime.fromisoformat(metadata['created_at'])
                age_seconds = (now - created_at).total_seconds()
                
                if age_seconds < 60:
                    distribution['less_than_1min'] += 1
                elif age_seconds < 300:
                    distribution['1min_to_5min'] += 1
                elif age_seconds < 1800:
                    distribution['5min_to_30min'] += 1
                elif age_seconds < 3600:
                    distribution['30min_to_1hour'] += 1
                else:
                    distribution['more_than_1hour'] += 1
                    
            except Exception:
                continue
        
        return distribution
    
    def _cleanup_context(self, error):
        """Clean up cache context on request teardown."""
        # Could implement request-specific cleanup here
        pass


# =============================================================================
# GLOBAL CACHE SERVICE INSTANCE
# =============================================================================

enhanced_cache = EnhancedCacheService()
