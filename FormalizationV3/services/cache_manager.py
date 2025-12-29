"""
Centralized caching system for HR ATS
Extracted from monolithic app.py
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)

class CacheManager:
    """Centralized cache management system"""
    
    def __init__(self, default_ttl: int = 300, max_cache_size: int = 1000):
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self._cache = {}
        self._response_cache = {}
        self._admin_cache = {}
        self._lock = threading.RLock()
        
        logger.info(f"Cache manager initialized with TTL={default_ttl}s, max_size={max_cache_size}")
    
    def get(self, cache_key: str, ttl_seconds: Optional[int] = None) -> Optional[Any]:
        """Get cached value with TTL check"""
        ttl = ttl_seconds or self.default_ttl
        
        with self._lock:
            if (cache_key in self._cache and 
                (datetime.now() - self._cache[cache_key]['cached_at']).seconds < ttl):
                logger.debug(f"Cache hit for key: {cache_key}")
                return self._cache[cache_key]['data']
            
            logger.debug(f"Cache miss for key: {cache_key}")
            return None
    
    def set(self, cache_key: str, data: Any) -> None:
        """Set cache value with timestamp"""
        with self._lock:
            self._cache[cache_key] = {
                'data': data,
                'cached_at': datetime.now()
            }
            
            # Cleanup if cache is too large
            if len(self._cache) > self.max_cache_size:
                self._cleanup_old_entries()
            
            logger.debug(f"Cache set for key: {cache_key}")
    
    def get_response_cache(self, cache_key: str, ttl_seconds: Optional[int] = None) -> Optional[Any]:
        """Get cached response with TTL check"""
        ttl = ttl_seconds or self.default_ttl
        
        with self._lock:
            if (cache_key in self._response_cache and 
                (datetime.now() - self._response_cache[cache_key]['cached_at']).seconds < ttl):
                return self._response_cache[cache_key]['data']
            return None
    
    def set_response_cache(self, cache_key: str, data: Any) -> None:
        """Set response cache with timestamp"""
        with self._lock:
            self._response_cache[cache_key] = {
                'data': data,
                'cached_at': datetime.now()
            }
            
            # Cleanup old cache entries (keep last 100 entries)
            if len(self._response_cache) > 100:
                self._cleanup_response_cache()
    
    def get_admin_cache(self, cache_key: str, ttl_seconds: Optional[int] = None) -> Optional[Any]:
        """Get admin cached result"""
        ttl = ttl_seconds or self.default_ttl
        
        with self._lock:
            if (cache_key in self._admin_cache and 
                (datetime.now() - self._admin_cache[cache_key]['cached_at']).seconds < ttl):
                return self._admin_cache[cache_key]['data']
            return None
    
    def set_admin_cache(self, cache_key: str, data: Any) -> None:
        """Set admin cache with timestamp"""
        with self._lock:
            self._admin_cache[cache_key] = {
                'data': data,
                'cached_at': datetime.now()
            }
    
    def invalidate(self, pattern: Optional[str] = None) -> None:
        """Invalidate cache entries"""
        with self._lock:
            if pattern:
                # Invalidate specific cache patterns
                keys_to_remove = [key for key in self._cache.keys() if pattern in key]
                for key in keys_to_remove:
                    self._cache.pop(key, None)
                    logger.debug(f"Invalidated cache key: {key}")
                
                # Also check response cache
                response_keys_to_remove = [key for key in self._response_cache.keys() if pattern in key]
                for key in response_keys_to_remove:
                    self._response_cache.pop(key, None)
                    
                # Also check admin cache
                admin_keys_to_remove = [key for key in self._admin_cache.keys() if pattern in key]
                for key in admin_keys_to_remove:
                    self._admin_cache.pop(key, None)
            else:
                # Clear all caches
                self._cache.clear()
                self._response_cache.clear()
                self._admin_cache.clear()
                logger.info("All caches cleared")
    
    def cleanup_expired(self) -> None:
        """Cleanup expired cache entries"""
        with self._lock:
            current_time = datetime.now()
            expired_keys = []
            
            # Check main cache
            for key, cache_data in self._cache.items():
                if (current_time - cache_data['cached_at']).seconds > 3600:  # 1 hour max
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._cache.pop(key, None)
            
            # Check response cache
            response_expired_keys = []
            for key, cache_data in self._response_cache.items():
                if (current_time - cache_data['cached_at']).seconds > 1800:  # 30 min max
                    response_expired_keys.append(key)
            
            for key in response_expired_keys:
                self._response_cache.pop(key, None)
            
            # Check admin cache
            admin_expired_keys = []
            for key, cache_data in self._admin_cache.items():
                if (current_time - cache_data['cached_at']).seconds > 3600:  # 1 hour max
                    admin_expired_keys.append(key)
            
            for key in admin_expired_keys:
                self._admin_cache.pop(key, None)
            
            total_expired = len(expired_keys) + len(response_expired_keys) + len(admin_expired_keys)
            if total_expired > 0:
                logger.info(f"Cleaned up {total_expired} expired cache entries")
    
    def _cleanup_old_entries(self) -> None:
        """Remove oldest entries to maintain cache size limit"""
        if len(self._cache) <= self.max_cache_size:
            return
        
        # Sort by timestamp and remove oldest 20% of entries
        sorted_keys = sorted(self._cache.keys(), 
                           key=lambda k: self._cache[k]['cached_at'])
        
        entries_to_remove = int(len(self._cache) * 0.2)
        for key in sorted_keys[:entries_to_remove]:
            self._cache.pop(key, None)
        
        logger.info(f"Removed {entries_to_remove} old cache entries to maintain size limit")
    
    def _cleanup_response_cache(self) -> None:
        """Remove oldest response cache entries"""
        # Remove oldest 20 entries
        sorted_keys = sorted(self._response_cache.keys(), 
                           key=lambda k: self._response_cache[k]['cached_at'])
        
        for key in sorted_keys[:20]:
            self._response_cache.pop(key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'main_cache_size': len(self._cache),
                'response_cache_size': len(self._response_cache),
                'admin_cache_size': len(self._admin_cache),
                'max_cache_size': self.max_cache_size,
                'default_ttl': self.default_ttl,
                'timestamp': datetime.now().isoformat()
            }

# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def initialize_cache_manager(default_ttl: int = 300, max_cache_size: int = 1000) -> CacheManager:
    """Initialize global cache manager with custom settings"""
    global _cache_manager
    _cache_manager = CacheManager(default_ttl, max_cache_size)
    return _cache_manager
