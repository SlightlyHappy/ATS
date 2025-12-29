#!/usr/bin/env python3
"""
Service Health Management with Circuit Breaker Pattern
Replaces hardcoded "unavailable" messages with dynamic health checking
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import threading
import json

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class CircuitState(Enum):
    """Circuit breaker state enumeration"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, bypass service
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class ServiceHealth:
    """Service health information"""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    success_count: int = 0
    last_error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 60
    half_open_max_calls: int = 3

class CircuitBreaker:
    """Circuit breaker implementation for service health management"""
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        self._lock = threading.Lock()
        
        logger.info(f"Circuit breaker initialized for {service_name}")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            return self._state
    
    def can_execute(self) -> bool:
        """Check if service call can be executed"""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"Circuit breaker for {self.service_name} moved to HALF_OPEN")
                    return True
                return False
            elif self._state == CircuitState.HALF_OPEN:
                return self._half_open_calls < self.config.half_open_max_calls
            
            return False
    
    def record_success(self):
        """Record successful service call"""
        with self._lock:
            self._failure_count = 0
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._success_count = 0
                    logger.info(f"Circuit breaker for {self.service_name} reset to CLOSED")
    
    def record_failure(self, error: str):
        """Record failed service call"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker for {self.service_name} opened due to failure: {error}")
            elif self._state == CircuitState.CLOSED and self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker for {self.service_name} opened after {self._failure_count} failures")
            
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self._last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self._last_failure_time
        return time_since_failure >= self.config.timeout_seconds

class ServiceHealthManager:
    """
    Manages health of all services with circuit breaker pattern
    Replaces hardcoded "unavailable" messages with dynamic health checking
    """
    
    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_checkers: Dict[str, Callable] = {}
        self.check_intervals: Dict[str, int] = {}
        self.last_checks: Dict[str, float] = {}
        
        # Background health checking
        self._running = False
        self._health_check_thread = None
        
        logger.info("Service Health Manager initialized")
    
    def register_service(
        self, 
        service_name: str, 
        health_checker: Callable[[], Dict[str, Any]], 
        check_interval: int = 30,
        circuit_config: CircuitBreakerConfig = None
    ):
        """Register a service for health monitoring"""
        
        self.services[service_name] = ServiceHealth(
            service_name=service_name,
            status=ServiceStatus.UNKNOWN,
            last_check=datetime.utcnow()
        )
        
        self.circuit_breakers[service_name] = CircuitBreaker(service_name, circuit_config)
        self.health_checkers[service_name] = health_checker
        self.check_intervals[service_name] = check_interval
        self.last_checks[service_name] = 0
        
        logger.info(f"Registered service '{service_name}' for health monitoring")
    
    def start_monitoring(self):
        """Start background health monitoring"""
        if self._running:
            return
        
        self._running = True
        self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_check_thread.start()
        
        logger.info("Service health monitoring started")
    
    def stop_monitoring(self):
        """Stop background health monitoring"""
        self._running = False
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)
        
        logger.info("Service health monitoring stopped")
    
    def _health_check_loop(self):
        """Background health check loop"""
        while self._running:
            try:
                current_time = time.time()
                
                for service_name in self.services.keys():
                    check_interval = self.check_intervals[service_name]
                    last_check = self.last_checks[service_name]
                    
                    if current_time - last_check >= check_interval:
                        self._check_service_health(service_name)
                        self.last_checks[service_name] = current_time
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                time.sleep(10)
    
    def _check_service_health(self, service_name: str):
        """Check health of a specific service"""
        try:
            health_checker = self.health_checkers.get(service_name)
            if not health_checker:
                return
            
            start_time = time.time()
            
            # Run health check
            health_result = health_checker()
            
            response_time = (time.time() - start_time) * 1000
            
            # Update service health
            service_health = self.services[service_name]
            service_health.last_check = datetime.utcnow()
            service_health.response_time_ms = response_time
            
            if health_result.get('healthy', False):
                service_health.status = ServiceStatus.HEALTHY
                service_health.success_count += 1
                service_health.last_error = None
                
                # Record success in circuit breaker
                circuit_breaker = self.circuit_breakers[service_name]
                circuit_breaker.record_success()
                
            else:
                error_msg = health_result.get('error', 'Unknown error')
                service_health.status = ServiceStatus.UNHEALTHY
                service_health.error_count += 1
                service_health.last_error = error_msg
                
                # Record failure in circuit breaker
                circuit_breaker = self.circuit_breakers[service_name]
                circuit_breaker.record_failure(error_msg)
            
            # Update metadata
            service_health.metadata.update(health_result.get('metadata', {}))
            
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            
            # Record as failure
            service_health = self.services[service_name]
            service_health.status = ServiceStatus.UNHEALTHY
            service_health.error_count += 1
            service_health.last_error = str(e)
            service_health.last_check = datetime.utcnow()
            
            circuit_breaker = self.circuit_breakers[service_name]
            circuit_breaker.record_failure(str(e))
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if service is available through circuit breaker"""
        circuit_breaker = self.circuit_breakers.get(service_name)
        if not circuit_breaker:
            return True  # Unknown services are considered available
        
        return circuit_breaker.can_execute()
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get health information for a service"""
        return self.services.get(service_name)
    
    def get_all_services_health(self) -> Dict[str, ServiceHealth]:
        """Get health information for all services"""
        return self.services.copy()
    
    def get_service_status_message(self, service_name: str) -> str:
        """Get dynamic status message for a service (replaces hardcoded messages)"""
        if not self.is_service_available(service_name):
            service_health = self.get_service_health(service_name)
            circuit_breaker = self.circuit_breakers.get(service_name)
            
            if circuit_breaker and circuit_breaker.state == CircuitState.OPEN:
                return f"{service_name} is temporarily unavailable (circuit breaker open)"
            elif service_health and service_health.last_error:
                return f"{service_name} is experiencing issues: {service_health.last_error}"
            else:
                return f"{service_name} is currently unavailable"
        
        service_health = self.get_service_health(service_name)
        if service_health:
            if service_health.status == ServiceStatus.HEALTHY:
                return f"{service_name} is operating normally"
            elif service_health.status == ServiceStatus.DEGRADED:
                return f"{service_name} is experiencing degraded performance"
            elif service_health.status == ServiceStatus.UNHEALTHY:
                return f"{service_name} is unhealthy but circuit breaker allows limited requests"
            else:
                return f"{service_name} status is unknown"
        
        return f"{service_name} is available"
    
    def execute_with_circuit_breaker(self, service_name: str, operation: Callable, fallback: Callable = None):
        """Execute operation with circuit breaker protection"""
        if not self.is_service_available(service_name):
            if fallback:
                logger.info(f"Using fallback for {service_name} (circuit breaker open)")
                return fallback()
            else:
                raise ServiceUnavailableError(f"{service_name} is currently unavailable")
        
        try:
            result = operation()
            
            # Record success
            circuit_breaker = self.circuit_breakers.get(service_name)
            if circuit_breaker:
                circuit_breaker.record_success()
            
            return result
            
        except Exception as e:
            # Record failure
            circuit_breaker = self.circuit_breakers.get(service_name)
            if circuit_breaker:
                circuit_breaker.record_failure(str(e))
            
            if fallback and not self.is_service_available(service_name):
                logger.warning(f"Service {service_name} failed, using fallback: {e}")
                return fallback()
            else:
                raise
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        healthy_services = []
        unhealthy_services = []
        degraded_services = []
        
        for service_name, health in self.services.items():
            circuit_breaker = self.circuit_breakers.get(service_name)
            service_info = {
                'name': service_name,
                'status': health.status.value,
                'circuit_state': circuit_breaker.state.value if circuit_breaker else 'unknown',
                'last_check': health.last_check.isoformat(),
                'response_time_ms': health.response_time_ms,
                'error_count': health.error_count,
                'success_count': health.success_count
            }
            
            if health.status == ServiceStatus.HEALTHY:
                healthy_services.append(service_info)
            elif health.status == ServiceStatus.DEGRADED:
                degraded_services.append(service_info)
            else:
                unhealthy_services.append(service_info)
        
        overall_status = ServiceStatus.HEALTHY
        if unhealthy_services:
            overall_status = ServiceStatus.UNHEALTHY
        elif degraded_services:
            overall_status = ServiceStatus.DEGRADED
        
        return {
            'overall_status': overall_status.value,
            'total_services': len(self.services),
            'healthy_services': len(healthy_services),
            'degraded_services': len(degraded_services),
            'unhealthy_services': len(unhealthy_services),
            'services': {
                'healthy': healthy_services,
                'degraded': degraded_services,
                'unhealthy': unhealthy_services
            },
            'timestamp': datetime.utcnow().isoformat()
        }

class ServiceUnavailableError(Exception):
    """Exception raised when a service is unavailable"""
    pass

# Global service health manager instance
service_health_manager = ServiceHealthManager()

def get_service_health_manager() -> ServiceHealthManager:
    """Get the global service health manager"""
    return service_health_manager

def init_service_health_monitoring(railway_db=None, cache_manager=None, ai_processor=None):
    """Initialize service health monitoring for core services"""
    
    # Railway Database health checker
    def check_railway_db():
        try:
            if not railway_db:
                return {'healthy': False, 'error': 'Railway database not initialized'}
            
            # Simple query to check connectivity
            result = railway_db.execute_read("SELECT 1 as test", [])
            if result and len(result) > 0:
                return {'healthy': True, 'metadata': {'connection_pool': 'active'}}
            else:
                return {'healthy': False, 'error': 'Query returned no results'}
                
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    # Cache health checker
    def check_cache():
        try:
            if not cache_manager:
                return {'healthy': True, 'metadata': {'cache_type': 'none', 'note': 'No cache configured'}}
            
            # Test cache operations
            test_key = 'health_check_test'
            cache_manager.set(test_key, 'test_value', ttl=5)
            result = cache_manager.get(test_key)
            
            if result == 'test_value':
                return {'healthy': True, 'metadata': {'cache_type': 'active'}}
            else:
                return {'healthy': False, 'error': 'Cache read/write test failed'}
                
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    # AI Processor health checker
    def check_ai_processor():
        try:
            if not ai_processor:
                return {'healthy': False, 'error': 'AI processor not initialized'}
            
            # Check if unified AI processor is available
            available_providers = ai_processor.get_available_providers()
            healthy_providers = [p for p, info in available_providers.items() if info.get('healthy', False)]
            
            if healthy_providers:
                return {
                    'healthy': True, 
                    'metadata': {
                        'available_providers': list(available_providers.keys()),
                        'healthy_providers': healthy_providers
                    }
                }
            else:
                return {
                    'healthy': False, 
                    'error': 'No healthy AI providers available',
                    'metadata': {'available_providers': list(available_providers.keys())}
                }
                
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    # Register services
    service_health_manager.register_service('railway_database', check_railway_db, 30)
    service_health_manager.register_service('cache_manager', check_cache, 60)
    service_health_manager.register_service('ai_processor', check_ai_processor, 60)
    
    # Start monitoring
    service_health_manager.start_monitoring()
    
    logger.info("Service health monitoring initialized for core services")
