#!/usr/bin/env python3
"""
Frontend Performance Helpers for HR ATS System
Provides caching, optimization, and performance monitoring utilities
"""

import json
import logging
import time
import hashlib
import gzip
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from functools import wraps
import threading
from collections import defaultdict, OrderedDict
import psutil
import os

from flask import request, jsonify, g, current_app
from railway_database import RailwayPostgreSQL

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = self.created_at

@dataclass
class PerformanceMetric:
    """Performance metric tracking"""
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    request_size_bytes: int
    response_size_bytes: int
    cache_hit: bool
    timestamp: datetime
    user_id: Optional[str] = None
    error_message: Optional[str] = None

class MemoryCache:
    """Thread-safe in-memory cache with LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_size_bytes': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self._lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            entry = self.cache[key]
            
            # Check expiration
            if datetime.utcnow() > entry.expires_at:
                del self.cache[key]
                self.stats['misses'] += 1
                return None
            
            # Update access tracking
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            
            self.stats['hits'] += 1
            return entry.data
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None, tags: List[str] = None) -> bool:
        """Set item in cache"""
        try:
            with self._lock:
                # Calculate data size
                data_size = len(json.dumps(data, default=str).encode('utf-8'))
                
                # Set TTL
                if ttl is None:
                    ttl = self.default_ttl
                
                # Create cache entry
                now = datetime.utcnow()
                entry = CacheEntry(
                    key=key,
                    data=data,
                    created_at=now,
                    expires_at=now + timedelta(seconds=ttl),
                    size_bytes=data_size,
                    tags=tags or []
                )
                
                # Remove old entry if exists
                if key in self.cache:
                    old_entry = self.cache[key]
                    self.stats['total_size_bytes'] -= old_entry.size_bytes
                    del self.cache[key]
                
                # Add new entry
                self.cache[key] = entry
                self.stats['total_size_bytes'] += data_size
                
                # Evict if necessary
                self._evict_if_needed()
                
                return True
                
        except Exception as e:
            logger.error(f"Error setting cache entry {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                self.stats['total_size_bytes'] -= entry.size_bytes
                del self.cache[key]
                return True
            return False
    
    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear cache entries by tags"""
        cleared_count = 0
        with self._lock:
            keys_to_remove = []
            for key, entry in self.cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                entry = self.cache[key]
                self.stats['total_size_bytes'] -= entry.size_bytes
                del self.cache[key]
                cleared_count += 1
        
        return cleared_count
    
    def clear(self) -> int:
        """Clear all cache entries"""
        with self._lock:
            count = len(self.cache)
            self.cache.clear()
            self.stats['total_size_bytes'] = 0
            return count
    
    def _evict_if_needed(self):
        """Evict least recently used items if cache is full"""
        while len(self.cache) > self.max_size:
            # Remove least recently used item
            key, entry = self.cache.popitem(last=False)
            self.stats['total_size_bytes'] -= entry.size_bytes
            self.stats['evictions'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'evictions': self.stats['evictions'],
                'total_entries': len(self.cache),
                'max_entries': self.max_size,
                'total_size_bytes': self.stats['total_size_bytes'],
                'average_entry_size': self.stats['total_size_bytes'] // len(self.cache) if self.cache else 0
            }

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: List[PerformanceMetric] = []
        self._lock = threading.Lock()
        
        # Aggregated statistics
        self.endpoint_stats = defaultdict(lambda: {
            'total_requests': 0,
            'total_response_time': 0,
            'min_response_time': float('inf'),
            'max_response_time': 0,
            'error_count': 0,
            'cache_hits': 0
        })
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        with self._lock:
            self.metrics.append(metric)
            
            # Update endpoint statistics
            endpoint_key = f"{metric.method} {metric.endpoint}"
            stats = self.endpoint_stats[endpoint_key]
            
            stats['total_requests'] += 1
            stats['total_response_time'] += metric.response_time_ms
            stats['min_response_time'] = min(stats['min_response_time'], metric.response_time_ms)
            stats['max_response_time'] = max(stats['max_response_time'], metric.response_time_ms)
            
            if metric.status_code >= 400:
                stats['error_count'] += 1
            
            if metric.cache_hit:
                stats['cache_hits'] += 1
            
            # Evict old metrics if necessary
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
    
    def get_endpoint_stats(self, endpoint: str = None) -> Dict[str, Any]:
        """Get endpoint performance statistics"""
        with self._lock:
            if endpoint:
                stats = dict(self.endpoint_stats.get(endpoint, {}))
                if stats and stats['total_requests'] > 0:
                    stats['average_response_time'] = stats['total_response_time'] / stats['total_requests']
                    stats['cache_hit_rate'] = (stats['cache_hits'] / stats['total_requests']) * 100
                return stats
            else:
                # Return all endpoint stats
                result = {}
                for endpoint_key, stats in self.endpoint_stats.items():
                    endpoint_stats = dict(stats)
                    if endpoint_stats['total_requests'] > 0:
                        endpoint_stats['average_response_time'] = endpoint_stats['total_response_time'] / endpoint_stats['total_requests']
                        endpoint_stats['cache_hit_rate'] = (endpoint_stats['cache_hits'] / endpoint_stats['total_requests']) * 100
                    result[endpoint_key] = endpoint_stats
                return result
    
    def get_recent_metrics(self, minutes: int = 60) -> List[PerformanceMetric]:
        """Get recent performance metrics"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        with self._lock:
            return [m for m in self.metrics if m.timestamp >= cutoff_time]
    
    def get_slow_requests(self, threshold_ms: float = 1000, limit: int = 50) -> List[PerformanceMetric]:
        """Get slow requests above threshold"""
        with self._lock:
            slow_requests = [m for m in self.metrics if m.response_time_ms >= threshold_ms]
            return sorted(slow_requests, key=lambda x: x.response_time_ms, reverse=True)[:limit]

class PerformanceHelper:
    """Main performance helper class"""
    
    def __init__(self, db_manager=None):
        self.cache = MemoryCache(max_size=2000, default_ttl=300)
        self.monitor = PerformanceMonitor()
        if db_manager and hasattr(db_manager, 'railway_pg'):
            self.db = db_manager.railway_pg
        else:
            self.db = RailwayPostgreSQL()
        
        # Response compression settings
        self.compression_threshold = 1024  # Compress responses larger than 1KB
        
        # Database query cache
        self.query_cache = MemoryCache(max_size=500, default_ttl=180)
        
    def cache_response(self, key: str, ttl: int = 300, tags: List[str] = None):
        """Decorator for caching API responses"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key if not provided
                if callable(key):
                    cache_key = key(*args, **kwargs)
                else:
                    cache_key = key
                
                # Try to get from cache
                cached_response = self.cache.get(cache_key)
                if cached_response:
                    # Record cache hit
                    g.cache_hit = True
                    return jsonify(cached_response)
                
                # Execute function
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                # Cache the response if it's successful
                if hasattr(result, 'status_code') and result.status_code == 200:
                    response_data = result.get_json() if hasattr(result, 'get_json') else result
                    self.cache.set(cache_key, response_data, ttl, tags)
                
                # Record cache miss
                g.cache_hit = False
                g.execution_time = execution_time
                
                return result
            return wrapper
        return decorator
    
    def cached_database_query(self, query: str, params: List[Any], ttl: int = 180) -> List[Dict[str, Any]]:
        """Execute database query with caching"""
        # Generate cache key from query and parameters
        cache_key = hashlib.md5(f"{query}:{json.dumps(params, default=str)}".encode()).hexdigest()
        
        # Try cache first
        cached_result = self.query_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Execute query
        start_time = time.time()
        result = self.db.execute_read(query, params)
        execution_time = (time.time() - start_time) * 1000
        
        # Cache result
        self.query_cache.set(cache_key, result, ttl)
        
        logger.debug(f"Database query executed in {execution_time:.2f}ms (cached)")
        return result
    
    def compress_response(self, data: Any) -> str:
        """Compress response data"""
        try:
            json_data = json.dumps(data, default=str)
            if len(json_data) > self.compression_threshold:
                compressed = gzip.compress(json_data.encode('utf-8'))
                return base64.b64encode(compressed).decode('utf-8')
            return json_data
        except Exception as e:
            logger.error(f"Error compressing response: {e}")
            return json.dumps(data, default=str)
    
    def decompress_response(self, compressed_data: str) -> Any:
        """Decompress response data"""
        try:
            # Try to decompress
            compressed_bytes = base64.b64decode(compressed_data.encode('utf-8'))
            decompressed = gzip.decompress(compressed_bytes).decode('utf-8')
            return json.loads(decompressed)
        except:
            # If decompression fails, assume it's uncompressed JSON
            return json.loads(compressed_data)
    
    def paginate_efficiently(self, query_builder: Callable, page: int, per_page: int, 
                           count_query_builder: Callable = None) -> Dict[str, Any]:
        """Efficient pagination with counting optimization"""
        # Clamp pagination parameters
        page = max(1, page)
        per_page = min(max(1, per_page), 100)
        
        offset = (page - 1) * per_page
        
        # Get paginated results
        results = query_builder(limit=per_page, offset=offset)
        
        # Get total count (optimize for common cases)
        if count_query_builder:
            total_count = count_query_builder()
        else:
            # Fallback to estimating count for large datasets
            if page == 1 and len(results) < per_page:
                total_count = len(results)
            else:
                # This should be optimized based on your specific use case
                total_count = query_builder(count_only=True)
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            'results': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
                'next_page': page + 1 if page < total_pages else None,
                'prev_page': page - 1 if page > 1 else None
            }
        }
    
    def batch_load(self, ids: List[str], loader_func: Callable, cache_key_prefix: str, ttl: int = 300) -> Dict[str, Any]:
        """Batch load entities with caching"""
        results = {}
        uncached_ids = []
        
        # Check cache for each ID
        for entity_id in ids:
            cache_key = f"{cache_key_prefix}:{entity_id}"
            cached_entity = self.cache.get(cache_key)
            if cached_entity:
                results[entity_id] = cached_entity
            else:
                uncached_ids.append(entity_id)
        
        # Load uncached entities in batch
        if uncached_ids:
            loaded_entities = loader_func(uncached_ids)
            
            # Cache and add to results
            for entity in loaded_entities:
                entity_id = str(entity.get('id', ''))
                if entity_id:
                    cache_key = f"{cache_key_prefix}:{entity_id}"
                    self.cache.set(cache_key, entity, ttl)
                    results[entity_id] = entity
        
        return results
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3)
                },
                'process': {
                    'memory_rss_mb': process_memory.rss / (1024**2),
                    'memory_vms_mb': process_memory.vms / (1024**2),
                    'cpu_percent': process.cpu_percent(),
                    'threads': process.num_threads()
                },
                'cache': {
                    'response_cache': self.cache.get_stats(),
                    'query_cache': self.query_cache.get_stats()
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}
    
    def optimize_database_query(self, query: str, params: List[Any] = None) -> str:
        """Optimize database query (basic implementation)"""
        # Basic query optimization rules
        optimized_query = query
        
        # Add LIMIT if missing for potentially large result sets
        if 'SELECT' in query.upper() and 'LIMIT' not in query.upper():
            if 'ORDER BY' in query.upper():
                optimized_query = query + ' LIMIT 1000'
            else:
                optimized_query = query + ' ORDER BY id LIMIT 1000'
        
        # Suggest using indexes for WHERE clauses
        if 'WHERE' in query.upper() and params:
            logger.debug(f"Query using WHERE clause - ensure indexes exist for: {params}")
        
        return optimized_query
    
    def clear_cache_by_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern"""
        # This is a simplified implementation
        # In production, you might use Redis with pattern matching
        cleared_count = 0
        
        if pattern == 'user:*':
            cleared_count = self.cache.clear_by_tags(['user'])
        elif pattern == 'resume:*':
            cleared_count = self.cache.clear_by_tags(['resume'])
        elif pattern == '*':
            cleared_count = self.cache.clear()
        
        return cleared_count

# Global performance helper instance
performance_helper = PerformanceHelper()

# Performance monitoring middleware
def monitor_performance():
    """Flask before/after request handlers for performance monitoring"""
    
    def before_request():
        g.start_time = time.time()
        g.cache_hit = False
        g.execution_time = 0
    
    def after_request(response):
        try:
            # Calculate response time
            response_time = (time.time() - g.start_time) * 1000
            
            # Get request size
            request_size = len(request.get_data()) if request.get_data() else 0
            
            # Get response size
            response_size = len(response.get_data()) if hasattr(response, 'get_data') else 0
            
            # Create performance metric
            metric = PerformanceMetric(
                endpoint=request.endpoint or request.path,
                method=request.method,
                response_time_ms=response_time,
                status_code=response.status_code,
                request_size_bytes=request_size,
                response_size_bytes=response_size,
                cache_hit=getattr(g, 'cache_hit', False),
                timestamp=datetime.utcnow(),
                user_id=getattr(g, 'user_id', None),
                error_message=None if response.status_code < 400 else 'HTTP Error'
            )
            
            # Record metric
            performance_helper.monitor.record_metric(metric)
            
            # Add performance headers
            response.headers['X-Response-Time'] = f"{response_time:.2f}ms"
            response.headers['X-Cache-Hit'] = str(g.cache_hit)
            
            # Add compression header if response is large
            if response_size > performance_helper.compression_threshold:
                response.headers['X-Compression-Recommended'] = 'true'
            
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
        
        return response
    
    return before_request, after_request

# Decorator for caching database queries
def cached_query(ttl: int = 300, tags: List[str] = None):
    """Decorator for caching database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"query:{func.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Try cache first
            cached_result = performance_helper.cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            performance_helper.cache.set(cache_key, result, ttl, tags)
            
            return result
        return wrapper
    return decorator

# Utility functions
def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()

def warmup_cache(cache_functions: List[Callable]):
    """Warm up cache with commonly accessed data"""
    for func in cache_functions:
        try:
            func()
            logger.info(f"Cache warmed up for {func.__name__}")
        except Exception as e:
            logger.error(f"Error warming up cache for {func.__name__}: {e}")

def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary for monitoring dashboard"""
    system_metrics = performance_helper.get_system_metrics()
    endpoint_stats = performance_helper.monitor.get_endpoint_stats()
    recent_metrics = performance_helper.monitor.get_recent_metrics(minutes=60)
    
    # Calculate summary statistics
    if recent_metrics:
        avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
        error_count = sum(1 for m in recent_metrics if m.status_code >= 400)
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        cache_hit_rate = (cache_hits / len(recent_metrics)) * 100
    else:
        avg_response_time = 0
        error_count = 0
        cache_hit_rate = 0
    
    return {
        'summary': {
            'avg_response_time_ms': round(avg_response_time, 2),
            'error_count_last_hour': error_count,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'total_requests_last_hour': len(recent_metrics)
        },
        'system_metrics': system_metrics,
        'top_endpoints': dict(list(endpoint_stats.items())[:10]),
        'timestamp': datetime.utcnow().isoformat()
    }
