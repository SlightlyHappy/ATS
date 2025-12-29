"""
Redis Cluster Manager - Phase 3.1 Implementation
Enterprise-scale Redis clustering with intelligent cache warming, 
advanced invalidation policies, and high availability features.
"""
import logging
import json
import hashlib
import threading
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from collections import defaultdict, deque

try:
    import redis
    import redis.sentinel
    from redis.exceptions import ConnectionError, TimeoutError, RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from flask import current_app

logger = logging.getLogger(__name__)

# =============================================================================
# REDIS CLUSTER CONFIGURATION AND TYPES
# =============================================================================

@dataclass
class RedisClusterConfig:
    """Configuration for Redis cluster management."""
    # Cluster settings
    enabled: bool = True
    cluster_mode: str = 'standalone'  # 'standalone', 'sentinel', 'cluster'
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    sentinel_service_name: str = 'mymaster'
    
    # Connection settings
    connection_pool_size: int = 50
    max_connections_per_node: int = 20
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    # Cache warming settings
    enable_cache_warming: bool = True
    warm_on_startup: bool = True
    warm_interval: int = 3600  # 1 hour
    predictive_warming: bool = True
    warming_concurrency: int = 10
    
    # Performance settings
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    enable_pipelining: bool = True
    pipeline_buffer_size: int = 100
    
    # Cache policies
    default_ttl: int = 3600  # 1 hour
    max_ttl: int = 86400  # 24 hours
    enable_intelligent_ttl: bool = True
    ttl_adjustment_factor: float = 1.0
    
    # Monitoring and alerting
    enable_monitoring: bool = True
    alert_on_failure: bool = True
    max_failure_threshold: int = 3
    failure_recovery_time: int = 300  # 5 minutes


@dataclass
class CacheWarmingStrategy:
    """Strategy for cache warming operations."""
    name: str
    priority: int  # 1-10, higher is more important
    endpoints: List[str]
    parameters: Dict[str, Any]
    frequency: int  # seconds
    conditions: List[str]  # conditions when to warm
    max_concurrent: int = 5
    timeout: int = 30
    retry_count: int = 2


@dataclass
class ClusterHealthMetrics:
    """Health metrics for Redis cluster."""
    timestamp: datetime
    total_nodes: int
    healthy_nodes: int
    failed_nodes: int
    total_memory_usage: int  # bytes
    total_keys: int
    hit_rate: float
    miss_rate: float
    operations_per_second: float
    average_response_time: float
    connection_count: int
    errors_per_minute: float


@dataclass
class InvalidationPolicy:
    """Cache invalidation policy configuration."""
    name: str
    pattern: str  # Key pattern or tag
    trigger_events: List[str]
    cascade_patterns: List[str]  # Patterns to invalidate when this triggers
    delay: int = 0  # Delay before invalidation
    batch_size: int = 100
    max_cascade_depth: int = 3


# =============================================================================
# REDIS CLUSTER MANAGER
# =============================================================================

class RedisClusterManager:
    """
    Enterprise Redis cluster manager with advanced caching features,
    intelligent warming strategies, and high availability support.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config = RedisClusterConfig()
        
        # Cluster connections
        self.redis_clients: Dict[str, redis.Redis] = {}
        self.sentinel_clients: List[redis.sentinel.Sentinel] = []
        self.cluster_client: Optional[redis.Redis] = None
        
        # Cache warming
        self.warming_strategies: List[CacheWarmingStrategy] = []
        self.warming_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="cache_warm")
        self.warming_active = False
        self.last_warming_time = None
        
        # Invalidation policies
        self.invalidation_policies: List[InvalidationPolicy] = []
        self.invalidation_queue = deque(maxlen=10000)
        self.invalidation_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="invalidation")
        
        # Monitoring and health
        self.health_metrics_history = deque(maxlen=1440)  # 24 hours
        self.health_monitor_active = False
        self.health_monitor_thread = None
        
        # Performance tracking
        self.operation_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.last_health_check = None
        
        # Pipeline management
        self.pipeline_queues: Dict[str, List] = defaultdict(list)
        self.pipeline_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Redis cluster manager with Flask app."""
        self.app = app
        
        # Load configuration from app config
        self._load_config_from_app()
        
        # Initialize cluster connections
        self._initialize_cluster()
        
        # Setup cache warming strategies
        self._setup_warming_strategies()
        
        # Setup invalidation policies
        self._setup_invalidation_policies()
        
        # Start health monitoring
        if self.config.enable_monitoring:
            self.start_health_monitoring()
        
        # Start cache warming if enabled
        if self.config.enable_cache_warming and self.config.warm_on_startup:
            self.start_cache_warming()
        
        logger.info(f"Redis cluster manager initialized: {self.config.cluster_mode} mode")
    
    def _load_config_from_app(self):
        """Load Redis cluster configuration from Flask app config."""
        if not self.app:
            return
        
        config = self.app.config
        
        # Update cluster config from app settings
        self.config.enabled = config.get('REDIS_CLUSTER_ENABLED', True)
        self.config.cluster_mode = config.get('REDIS_CLUSTER_MODE', 'standalone')
        self.config.nodes = config.get('REDIS_CLUSTER_NODES', [])
        self.config.enable_cache_warming = config.get('REDIS_CACHE_WARMING', True)
        self.config.warming_concurrency = config.get('REDIS_WARMING_CONCURRENCY', 10)
        self.config.enable_compression = config.get('REDIS_COMPRESSION', True)
        self.config.default_ttl = config.get('REDIS_DEFAULT_TTL', 3600)
        
        # Load node configurations
        if not self.config.nodes:
            redis_url = config.get('REDIS_URL') or config.get('CACHE_REDIS_URL')
            if redis_url:
                self.config.nodes = [{'url': redis_url, 'role': 'master'}]
    
    def _initialize_cluster(self):
        """Initialize Redis cluster connections."""
        if not REDIS_AVAILABLE or not self.config.enabled:
            logger.warning("Redis cluster disabled or unavailable")
            return
        
        try:
            if self.config.cluster_mode == 'standalone':
                self._initialize_standalone()
            elif self.config.cluster_mode == 'sentinel':
                self._initialize_sentinel()
            elif self.config.cluster_mode == 'cluster':
                self._initialize_redis_cluster()
            else:
                logger.error(f"Unknown cluster mode: {self.config.cluster_mode}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Redis cluster: {str(e)}")
    
    def _initialize_standalone(self):
        """Initialize standalone Redis connection."""
        if not self.config.nodes:
            logger.warning("No Redis nodes configured for standalone mode")
            return
        
        node_config = self.config.nodes[0]
        try:
            redis_client = redis.from_url(
                node_config['url'],
                decode_responses=True,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval,
                max_connections=self.config.max_connections_per_node
            )
            
            # Test connection
            redis_client.ping()
            self.redis_clients['master'] = redis_client
            self.cluster_client = redis_client
            
            logger.info("Standalone Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to standalone Redis: {str(e)}")
    
    def _initialize_sentinel(self):
        """Initialize Redis Sentinel connections."""
        try:
            sentinel_hosts = [(node['host'], node['port']) for node in self.config.nodes 
                            if node.get('role') == 'sentinel']
            
            if not sentinel_hosts:
                logger.warning("No sentinel hosts configured")
                return
            
            sentinel = redis.sentinel.Sentinel(
                sentinel_hosts,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout
            )
            
            # Get master and slave connections
            master = sentinel.master_for(
                self.config.sentinel_service_name,
                decode_responses=True,
                retry_on_timeout=self.config.retry_on_timeout
            )
            
            slave = sentinel.slave_for(
                self.config.sentinel_service_name,
                decode_responses=True,
                retry_on_timeout=self.config.retry_on_timeout
            )
            
            # Test connections
            master.ping()
            slave.ping()
            
            self.redis_clients['master'] = master
            self.redis_clients['slave'] = slave
            self.cluster_client = master
            self.sentinel_clients.append(sentinel)
            
            logger.info(f"Redis Sentinel connections established for service: {self.config.sentinel_service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis Sentinel: {str(e)}")
    
    def _initialize_redis_cluster(self):
        """Initialize Redis Cluster connection."""
        try:
            startup_nodes = [{'host': node['host'], 'port': node['port']} 
                           for node in self.config.nodes]
            
            if not startup_nodes:
                logger.warning("No cluster nodes configured")
                return
            
            # Redis cluster client would be initialized here
            # For now, we'll use the first node as a fallback
            logger.info("Redis Cluster mode configured (fallback to standalone)")
            self._initialize_standalone()
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis Cluster: {str(e)}")
    
    # =============================================================================
    # CORE CACHE OPERATIONS WITH CLUSTERING
    # =============================================================================
    
    def get(self, key: str, use_slave: bool = True) -> Any:
        """Get value from Redis cluster with read optimization."""
        try:
            start_time = time.time()
            
            # Choose client based on read preference
            client = self._get_read_client() if use_slave else self._get_write_client()
            if not client:
                return None
            
            # Get value with decompression if needed
            value = client.get(key)
            if value is None:
                return None
            
            # Decompress if needed
            if self.config.enable_compression and isinstance(value, bytes):
                value = self._decompress_value(value)
            
            # Deserialize
            result = self._deserialize_value(value)
            
            # Track performance
            self._track_operation_time(time.time() - start_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Redis cluster get error for key '{key}': {str(e)}")
            self._track_error('get')
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            nx: bool = False, xx: bool = False) -> bool:
        """Set value in Redis cluster with intelligent TTL."""
        try:
            start_time = time.time()
            
            client = self._get_write_client()
            if not client:
                return False
            
            # Serialize value
            serialized_value = self._serialize_value(value)
            
            # Compress if needed
            if (self.config.enable_compression and 
                len(serialized_value) > self.config.compression_threshold):
                serialized_value = self._compress_value(serialized_value)
            
            # Determine TTL
            effective_ttl = self._calculate_intelligent_ttl(key, ttl)
            
            # Set value with appropriate flags
            if nx:
                result = client.set(key, serialized_value, ex=effective_ttl, nx=True)
            elif xx:
                result = client.set(key, serialized_value, ex=effective_ttl, xx=True)
            else:
                result = client.setex(key, effective_ttl, serialized_value)
            
            # Track performance
            self._track_operation_time(time.time() - start_time)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis cluster set error for key '{key}': {str(e)}")
            self._track_error('set')
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis cluster."""
        try:
            client = self._get_write_client()
            if not client:
                return False
            
            result = client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis cluster delete error for key '{key}': {str(e)}")
            self._track_error('delete')
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis cluster."""
        try:
            client = self._get_read_client()
            if not client:
                return False
            
            return bool(client.exists(key))
            
        except Exception as e:
            logger.error(f"Redis cluster exists error for key '{key}': {str(e)}")
            self._track_error('exists')
            return False
    
    def mget(self, keys: List[str]) -> List[Any]:
        """Get multiple values from Redis cluster."""
        try:
            client = self._get_read_client()
            if not client:
                return [None] * len(keys)
            
            values = client.mget(keys)
            results = []
            
            for value in values:
                if value is None:
                    results.append(None)
                else:
                    # Decompress and deserialize
                    if self.config.enable_compression and isinstance(value, bytes):
                        value = self._decompress_value(value)
                    results.append(self._deserialize_value(value))
            
            return results
            
        except Exception as e:
            logger.error(f"Redis cluster mget error: {str(e)}")
            self._track_error('mget')
            return [None] * len(keys)
    
    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in Redis cluster."""
        try:
            client = self._get_write_client()
            if not client:
                return False
            
            # Prepare serialized mapping
            serialized_mapping = {}
            for key, value in mapping.items():
                serialized_value = self._serialize_value(value)
                if (self.config.enable_compression and 
                    len(serialized_value) > self.config.compression_threshold):
                    serialized_value = self._compress_value(serialized_value)
                serialized_mapping[key] = serialized_value
            
            # Use pipeline for atomic operation
            pipe = client.pipeline()
            pipe.mset(serialized_mapping)
            
            # Set TTL for all keys if specified
            if ttl:
                for key in mapping.keys():
                    effective_ttl = self._calculate_intelligent_ttl(key, ttl)
                    pipe.expire(key, effective_ttl)
            
            pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Redis cluster mset error: {str(e)}")
            self._track_error('mset')
            return False
    
    # =============================================================================
    # CACHE WARMING STRATEGIES
    # =============================================================================
    
    def _setup_warming_strategies(self):
        """Setup default cache warming strategies."""
        if not self.config.enable_cache_warming:
            return
        
        # Critical API endpoints strategy
        critical_strategy = CacheWarmingStrategy(
            name='critical_endpoints',
            priority=10,
            endpoints=[
                '/api/v1/batch/admin/dashboard',
                '/api/v1/admin/analytics/dashboard',
                '/api/v1/monitoring/performance/current',
                '/api/v1/optimization/status'
            ],
            parameters={'timeout': 30},
            frequency=1800,  # 30 minutes
            conditions=['startup', 'low_hit_rate', 'schedule'],
            max_concurrent=3,
            timeout=30,
            retry_count=2
        )
        
        # User data strategy
        user_data_strategy = CacheWarmingStrategy(
            name='user_data',
            priority=8,
            endpoints=[
                '/api/v1/admin/users/stats',
                '/api/v1/admin/analytics/recent',
                '/api/v1/monitoring/cache/metrics'
            ],
            parameters={'include_inactive': False},
            frequency=3600,  # 1 hour
            conditions=['schedule', 'user_activity_spike'],
            max_concurrent=2,
            timeout=45,
            retry_count=1
        )
        
        # Analytics strategy
        analytics_strategy = CacheWarmingStrategy(
            name='analytics_data',
            priority=6,
            endpoints=[
                '/api/v1/admin/analytics/summary',
                '/api/v1/monitoring/performance/summary',
                '/api/v1/optimization/recommendations'
            ],
            parameters={'period': '24h'},
            frequency=7200,  # 2 hours
            conditions=['schedule', 'analytics_request_spike'],
            max_concurrent=2,
            timeout=60,
            retry_count=1
        )
        
        self.warming_strategies = [critical_strategy, user_data_strategy, analytics_strategy]
        logger.info(f"Configured {len(self.warming_strategies)} cache warming strategies")
    
    def start_cache_warming(self):
        """Start cache warming background process."""
        if self.warming_active:
            logger.warning("Cache warming already active")
            return
        
        self.warming_active = True
        
        # Initial warm-up
        if self.config.warm_on_startup:
            self._execute_warming_strategy('startup')
        
        # Schedule periodic warming
        self._schedule_periodic_warming()
        
        logger.info("Cache warming started")
    
    def stop_cache_warming(self):
        """Stop cache warming background process."""
        self.warming_active = False
        logger.info("Cache warming stopped")
    
    def _execute_warming_strategy(self, trigger: str):
        """Execute cache warming strategies for a specific trigger."""
        if not self.warming_active:
            return
        
        applicable_strategies = [s for s in self.warming_strategies if trigger in s.conditions]
        applicable_strategies.sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"Executing {len(applicable_strategies)} warming strategies for trigger: {trigger}")
        
        for strategy in applicable_strategies:
            self.warming_executor.submit(self._warm_strategy, strategy, trigger)
    
    def _warm_strategy(self, strategy: CacheWarmingStrategy, trigger: str):
        """Warm cache for a specific strategy."""
        try:
            logger.debug(f"Warming strategy '{strategy.name}' triggered by '{trigger}'")
            
            # Use thread pool for concurrent endpoint warming
            with ThreadPoolExecutor(max_workers=strategy.max_concurrent) as executor:
                futures = []
                
                for endpoint in strategy.endpoints:
                    future = executor.submit(
                        self._warm_endpoint, 
                        endpoint, 
                        strategy.parameters, 
                        strategy.timeout
                    )
                    futures.append(future)
                
                # Wait for completion with timeout
                completed = 0
                for future in as_completed(futures, timeout=strategy.timeout * 2):
                    try:
                        result = future.result()
                        if result:
                            completed += 1
                    except Exception as e:
                        logger.warning(f"Endpoint warming failed: {str(e)}")
                
                logger.info(f"Strategy '{strategy.name}' completed: {completed}/{len(strategy.endpoints)} endpoints warmed")
                
        except Exception as e:
            logger.error(f"Error warming strategy '{strategy.name}': {str(e)}")
    
    def _warm_endpoint(self, endpoint: str, parameters: Dict[str, Any], timeout: int) -> bool:
        """Warm cache for a specific endpoint."""
        try:
            # This would typically make internal requests to warm the cache
            # For now, we'll simulate by pre-computing and caching common keys
            
            # Generate cache keys for this endpoint
            cache_keys = self._generate_cache_keys_for_endpoint(endpoint, parameters)
            
            # Pre-warm these keys if they don't exist
            for key in cache_keys:
                if not self.exists(key):
                    # Generate and cache the data
                    cached_data = self._generate_cache_data_for_key(key, endpoint)
                    if cached_data:
                        ttl = self._calculate_intelligent_ttl(key)
                        self.set(key, cached_data, ttl)
            
            logger.debug(f"Warmed {len(cache_keys)} keys for endpoint: {endpoint}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to warm endpoint '{endpoint}': {str(e)}")
            return False
    
    def _generate_cache_keys_for_endpoint(self, endpoint: str, parameters: Dict[str, Any]) -> List[str]:
        """Generate likely cache keys for an endpoint."""
        # This is a simplified implementation
        # In practice, this would analyze the endpoint and generate appropriate keys
        base_key = endpoint.replace('/', '_').replace('-', '_')
        
        keys = [
            f"{base_key}_default",
            f"{base_key}_summary",
            f"{base_key}_recent"
        ]
        
        # Add parameter-specific keys
        for param, value in parameters.items():
            keys.append(f"{base_key}_{param}_{value}")
        
        return keys
    
    def _generate_cache_data_for_key(self, key: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """Generate cache data for a key (placeholder implementation)."""
        # This would contain actual logic to generate cache data
        # For now, return a placeholder
        return {
            'cached_at': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'key': key,
            'data': f"Warmed data for {key}"
        }
    
    def _schedule_periodic_warming(self):
        """Schedule periodic cache warming."""
        def warming_scheduler():
            while self.warming_active:
                try:
                    current_time = datetime.utcnow()
                    
                    for strategy in self.warming_strategies:
                        # Check if it's time to warm this strategy
                        if (not self.last_warming_time or 
                            (current_time - self.last_warming_time).total_seconds() >= strategy.frequency):
                            
                            self._execute_warming_strategy('schedule')
                            self.last_warming_time = current_time
                            break
                    
                    # Sleep for 1 minute before next check
                    time.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Error in warming scheduler: {str(e)}")
                    time.sleep(60)
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=warming_scheduler, daemon=True)
        scheduler_thread.start()
    
    # =============================================================================
    # ADVANCED INVALIDATION POLICIES
    # =============================================================================
    
    def _setup_invalidation_policies(self):
        """Setup advanced cache invalidation policies."""
        # User data invalidation policy
        user_policy = InvalidationPolicy(
            name='user_data_invalidation',
            pattern='user_*',
            trigger_events=['user_updated', 'user_deleted', 'user_analysis_completed'],
            cascade_patterns=['dashboard_*', 'analytics_user_*', 'stats_*'],
            delay=0,
            batch_size=50,
            max_cascade_depth=2
        )
        
        # Analytics invalidation policy
        analytics_policy = InvalidationPolicy(
            name='analytics_invalidation',
            pattern='analytics_*',
            trigger_events=['analysis_completed', 'new_analysis_submitted'],
            cascade_patterns=['dashboard_analytics_*', 'summary_*'],
            delay=5,  # 5 second delay to allow for completion
            batch_size=100,
            max_cascade_depth=1
        )
        
        # System configuration invalidation policy
        system_policy = InvalidationPolicy(
            name='system_config_invalidation',
            pattern='config_*',
            trigger_events=['config_updated', 'system_restart'],
            cascade_patterns=['*'],  # Invalidate everything on config change
            delay=0,
            batch_size=200,
            max_cascade_depth=1
        )
        
        self.invalidation_policies = [user_policy, analytics_policy, system_policy]
        logger.info(f"Configured {len(self.invalidation_policies)} invalidation policies")
    
    def trigger_invalidation(self, event: str, context: Optional[Dict[str, Any]] = None):
        """Trigger cache invalidation based on event."""
        try:
            applicable_policies = [p for p in self.invalidation_policies if event in p.trigger_events]
            
            if not applicable_policies:
                logger.debug(f"No invalidation policies for event: {event}")
                return
            
            logger.info(f"Triggering invalidation for event '{event}' with {len(applicable_policies)} policies")
            
            for policy in applicable_policies:
                self.invalidation_executor.submit(self._execute_invalidation_policy, policy, event, context)
                
        except Exception as e:
            logger.error(f"Error triggering invalidation for event '{event}': {str(e)}")
    
    def _execute_invalidation_policy(self, policy: InvalidationPolicy, event: str, context: Optional[Dict[str, Any]]):
        """Execute a specific invalidation policy."""
        try:
            # Apply delay if specified
            if policy.delay > 0:
                time.sleep(policy.delay)
            
            # Find keys matching the pattern
            matching_keys = self._find_keys_by_pattern(policy.pattern)
            
            # Invalidate in batches
            for i in range(0, len(matching_keys), policy.batch_size):
                batch = matching_keys[i:i + policy.batch_size]
                self._invalidate_key_batch(batch)
            
            logger.info(f"Invalidated {len(matching_keys)} keys for policy '{policy.name}'")
            
            # Execute cascade invalidation
            if policy.cascade_patterns and policy.max_cascade_depth > 0:
                self._execute_cascade_invalidation(policy.cascade_patterns, policy.max_cascade_depth - 1)
                
        except Exception as e:
            logger.error(f"Error executing invalidation policy '{policy.name}': {str(e)}")
    
    def _find_keys_by_pattern(self, pattern: str) -> List[str]:
        """Find Redis keys matching a pattern."""
        try:
            client = self._get_read_client()
            if not client:
                return []
            
            # Use SCAN for memory-efficient key discovery
            keys = []
            for key in client.scan_iter(match=pattern, count=1000):
                keys.append(key)
            
            return keys
            
        except Exception as e:
            logger.error(f"Error finding keys by pattern '{pattern}': {str(e)}")
            return []
    
    def _invalidate_key_batch(self, keys: List[str]):
        """Invalidate a batch of keys."""
        try:
            client = self._get_write_client()
            if not client or not keys:
                return
            
            # Use pipeline for efficient batch deletion
            pipe = client.pipeline()
            for key in keys:
                pipe.delete(key)
            pipe.execute()
            
        except Exception as e:
            logger.error(f"Error invalidating key batch: {str(e)}")
    
    def _execute_cascade_invalidation(self, cascade_patterns: List[str], max_depth: int):
        """Execute cascade invalidation for dependent patterns."""
        if max_depth <= 0:
            return
        
        try:
            for pattern in cascade_patterns:
                matching_keys = self._find_keys_by_pattern(pattern)
                if matching_keys:
                    self._invalidate_key_batch(matching_keys)
                    logger.debug(f"Cascade invalidated {len(matching_keys)} keys for pattern '{pattern}'")
                    
        except Exception as e:
            logger.error(f"Error in cascade invalidation: {str(e)}")
    
    # =============================================================================
    # HEALTH MONITORING AND METRICS
    # =============================================================================
    
    def start_health_monitoring(self):
        """Start health monitoring background process."""
        if self.health_monitor_active:
            logger.warning("Health monitoring already active")
            return
        
        self.health_monitor_active = True
        
        def health_monitor():
            while self.health_monitor_active:
                try:
                    metrics = self.collect_health_metrics()
                    self.health_metrics_history.append(metrics)
                    
                    # Check for alerts
                    self._check_health_alerts(metrics)
                    
                    # Sleep for monitoring interval
                    time.sleep(self.config.health_check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in health monitoring: {str(e)}")
                    time.sleep(self.config.health_check_interval)
        
        self.health_monitor_thread = threading.Thread(target=health_monitor, daemon=True)
        self.health_monitor_thread.start()
        
        logger.info("Redis cluster health monitoring started")
    
    def stop_health_monitoring(self):
        """Stop health monitoring background process."""
        self.health_monitor_active = False
        logger.info("Redis cluster health monitoring stopped")
    
    def collect_health_metrics(self) -> ClusterHealthMetrics:
        """Collect current health metrics from Redis cluster."""
        try:
            current_time = datetime.utcnow()
            
            # Initialize metrics
            total_nodes = len(self.redis_clients)
            healthy_nodes = 0
            failed_nodes = 0
            total_memory_usage = 0
            total_keys = 0
            hit_rate = 0.0
            miss_rate = 0.0
            operations_per_second = 0.0
            average_response_time = 0.0
            connection_count = 0
            errors_per_minute = 0.0
            
            # Collect metrics from each client
            for client_name, client in self.redis_clients.items():
                try:
                    # Test connection
                    client.ping()
                    healthy_nodes += 1
                    
                    # Get info
                    info = client.info()
                    
                    # Memory usage
                    total_memory_usage += info.get('used_memory', 0)
                    
                    # Key count
                    db_info = client.info('keyspace')
                    for db_name, db_stats in db_info.items():
                        if db_name.startswith('db'):
                            total_keys += db_stats.get('keys', 0)
                    
                    # Hit/miss rates
                    stats = client.info('stats')
                    hits = stats.get('keyspace_hits', 0)
                    misses = stats.get('keyspace_misses', 0)
                    total_requests = hits + misses
                    
                    if total_requests > 0:
                        hit_rate = (hits / total_requests) * 100
                        miss_rate = (misses / total_requests) * 100
                    
                    # Connection count
                    connection_count += info.get('connected_clients', 0)
                    
                except Exception as e:
                    logger.warning(f"Failed to collect metrics from {client_name}: {str(e)}")
                    failed_nodes += 1
            
            # Calculate average response time
            if self.operation_times:
                average_response_time = sum(self.operation_times) / len(self.operation_times)
            
            # Calculate errors per minute
            total_errors = sum(self.error_counts.values())
            errors_per_minute = total_errors / 1.0  # Simplified calculation
            
            return ClusterHealthMetrics(
                timestamp=current_time,
                total_nodes=total_nodes,
                healthy_nodes=healthy_nodes,
                failed_nodes=failed_nodes,
                total_memory_usage=total_memory_usage,
                total_keys=total_keys,
                hit_rate=round(hit_rate, 2),
                miss_rate=round(miss_rate, 2),
                operations_per_second=round(operations_per_second, 2),
                average_response_time=round(average_response_time * 1000, 2),  # Convert to ms
                connection_count=connection_count,
                errors_per_minute=round(errors_per_minute, 2)
            )
            
        except Exception as e:
            logger.error(f"Error collecting health metrics: {str(e)}")
            return ClusterHealthMetrics(
                timestamp=datetime.utcnow(),
                total_nodes=0,
                healthy_nodes=0,
                failed_nodes=0,
                total_memory_usage=0,
                total_keys=0,
                hit_rate=0.0,
                miss_rate=0.0,
                operations_per_second=0.0,
                average_response_time=0.0,
                connection_count=0,
                errors_per_minute=0.0
            )
    
    def _check_health_alerts(self, metrics: ClusterHealthMetrics):
        """Check health metrics for alert conditions."""
        try:
            alerts = []
            
            # Check node health
            if metrics.failed_nodes > 0:
                alerts.append(f"Failed nodes detected: {metrics.failed_nodes}/{metrics.total_nodes}")
            
            # Check hit rate
            if metrics.hit_rate < 60.0:
                alerts.append(f"Low hit rate: {metrics.hit_rate}%")
            
            # Check response time
            if metrics.average_response_time > 100.0:  # > 100ms
                alerts.append(f"High response time: {metrics.average_response_time}ms")
            
            # Check error rate
            if metrics.errors_per_minute > 10.0:
                alerts.append(f"High error rate: {metrics.errors_per_minute} errors/min")
            
            # Log alerts
            if alerts:
                logger.warning(f"Redis cluster health alerts: {'; '.join(alerts)}")
                
        except Exception as e:
            logger.error(f"Error checking health alerts: {str(e)}")
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def _get_read_client(self) -> Optional[redis.Redis]:
        """Get Redis client for read operations."""
        if 'slave' in self.redis_clients:
            return self.redis_clients['slave']
        return self.cluster_client
    
    def _get_write_client(self) -> Optional[redis.Redis]:
        """Get Redis client for write operations."""
        if 'master' in self.redis_clients:
            return self.redis_clients['master']
        return self.cluster_client
    
    def _calculate_intelligent_ttl(self, key: str, requested_ttl: Optional[int] = None) -> int:
        """Calculate intelligent TTL based on key patterns and usage."""
        if not self.config.enable_intelligent_ttl:
            return requested_ttl or self.config.default_ttl
        
        # Base TTL
        base_ttl = requested_ttl or self.config.default_ttl
        
        # Adjust based on key patterns
        if 'dashboard' in key or 'critical' in key:
            # Critical data - shorter TTL for freshness
            base_ttl = int(base_ttl * 0.5)
        elif 'analytics' in key or 'stats' in key:
            # Analytics data - longer TTL (less frequently changing)
            base_ttl = int(base_ttl * 1.5)
        elif 'user' in key:
            # User data - moderate TTL
            base_ttl = int(base_ttl * 1.0)
        
        # Apply global adjustment factor
        base_ttl = int(base_ttl * self.config.ttl_adjustment_factor)
        
        # Ensure within bounds
        return max(60, min(base_ttl, self.config.max_ttl))
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        try:
            return json.dumps(value, default=str)
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            return json.dumps(str(value))
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from Redis storage."""
        try:
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Deserialization error: {str(e)}")
            return value
    
    def _compress_value(self, value: str) -> bytes:
        """Compress value for storage (placeholder implementation)."""
        # In production, this would use gzip or another compression algorithm
        return value.encode('utf-8')
    
    def _decompress_value(self, value: bytes) -> str:
        """Decompress value from storage (placeholder implementation)."""
        # In production, this would decompress using the appropriate algorithm
        return value.decode('utf-8')
    
    def _track_operation_time(self, duration: float):
        """Track operation timing for performance monitoring."""
        self.operation_times.append(duration)
    
    def _track_error(self, operation: str):
        """Track errors for monitoring."""
        self.error_counts[operation] += 1
    
    # =============================================================================
    # PUBLIC API METHODS
    # =============================================================================
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get comprehensive cluster status."""
        try:
            latest_metrics = self.health_metrics_history[-1] if self.health_metrics_history else None
            
            return {
                'cluster_mode': self.config.cluster_mode,
                'total_nodes': len(self.redis_clients),
                'healthy_nodes': latest_metrics.healthy_nodes if latest_metrics else 0,
                'warming_active': self.warming_active,
                'monitoring_active': self.health_monitor_active,
                'warming_strategies': len(self.warming_strategies),
                'invalidation_policies': len(self.invalidation_policies),
                'latest_metrics': latest_metrics.__dict__ if latest_metrics else None,
                'configuration': {
                    'cache_warming': self.config.enable_cache_warming,
                    'compression': self.config.enable_compression,
                    'intelligent_ttl': self.config.enable_intelligent_ttl,
                    'monitoring': self.config.enable_monitoring
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cluster status: {str(e)}")
            return {'error': str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the cluster."""
        try:
            if not self.health_metrics_history:
                return {'error': 'No metrics available'}
            
            recent_metrics = list(self.health_metrics_history)[-10:]
            
            avg_hit_rate = sum(m.hit_rate for m in recent_metrics) / len(recent_metrics)
            avg_response_time = sum(m.average_response_time for m in recent_metrics) / len(recent_metrics)
            avg_ops_per_sec = sum(m.operations_per_second for m in recent_metrics) / len(recent_metrics)
            
            return {
                'average_hit_rate': round(avg_hit_rate, 2),
                'average_response_time': round(avg_response_time, 2),
                'average_operations_per_second': round(avg_ops_per_sec, 2),
                'total_errors': sum(self.error_counts.values()),
                'error_breakdown': dict(self.error_counts),
                'metrics_count': len(self.health_metrics_history),
                'last_updated': recent_metrics[-1].timestamp.isoformat() if recent_metrics else None
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {'error': str(e)}
    
    def force_cache_warming(self, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """Force cache warming for specific or all strategies."""
        try:
            if strategy_name:
                strategy = next((s for s in self.warming_strategies if s.name == strategy_name), None)
                if not strategy:
                    return {'error': f'Strategy not found: {strategy_name}'}
                
                self.warming_executor.submit(self._warm_strategy, strategy, 'manual')
                return {'message': f'Triggered warming for strategy: {strategy_name}'}
            else:
                self._execute_warming_strategy('manual')
                return {'message': f'Triggered warming for all {len(self.warming_strategies)} strategies'}
                
        except Exception as e:
            logger.error(f"Error forcing cache warming: {str(e)}")
            return {'error': str(e)}


# =============================================================================
# GLOBAL REDIS CLUSTER MANAGER INSTANCE
# =============================================================================

redis_cluster_manager = RedisClusterManager()
