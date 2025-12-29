"""
Advanced Auto-Scaler Service - Phase 3.2 Implementation
Enterprise horizontal scaling with intelligent load balancing,
predictive scaling, and cloud provider integration.
"""
import logging
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import threading
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# =============================================================================
# CLOUD PROVIDER INTERFACES
# =============================================================================

class CloudProviderInterface(ABC):
    """Abstract interface for cloud provider scaling operations."""
    
    @abstractmethod
    async def scale_up(self, target_instances: int, instance_type: str) -> Dict[str, Any]:
        """Scale up to target instances."""
        pass
    
    @abstractmethod
    async def scale_down(self, target_instances: int) -> Dict[str, Any]:
        """Scale down to target instances."""
        pass
    
    @abstractmethod
    async def get_current_instances(self) -> int:
        """Get current instance count."""
        pass
    
    @abstractmethod
    async def get_instance_metrics(self) -> Dict[str, Any]:
        """Get instance-level metrics."""
        pass


class RailwayScalingProvider(CloudProviderInterface):
    """Railway.app scaling provider implementation."""
    
    def __init__(self, api_token: str, service_id: str):
        self.api_token = api_token
        self.service_id = service_id
        self.base_url = "https://backboard.railway.app/graphql"
    
    async def scale_up(self, target_instances: int, instance_type: str = "standard") -> Dict[str, Any]:
        """Scale up Railway service."""
        try:
            # Railway API call would go here
            # For now, simulate the response
            logger.info(f"Railway scale-up: targeting {target_instances} instances")
            
            # Simulate API delay
            await asyncio.sleep(1)
            
            return {
                'success': True,
                'provider': 'railway',
                'action': 'scale_up',
                'target_instances': target_instances,
                'estimated_time': '2-5 minutes',
                'message': f'Scaling to {target_instances} instances initiated'
            }
            
        except Exception as e:
            logger.error(f"Railway scale-up error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def scale_down(self, target_instances: int) -> Dict[str, Any]:
        """Scale down Railway service."""
        try:
            logger.info(f"Railway scale-down: targeting {target_instances} instances")
            
            # Simulate API delay
            await asyncio.sleep(1)
            
            return {
                'success': True,
                'provider': 'railway',
                'action': 'scale_down',
                'target_instances': target_instances,
                'estimated_time': '1-3 minutes',
                'message': f'Scaling to {target_instances} instances initiated'
            }
            
        except Exception as e:
            logger.error(f"Railway scale-down error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_current_instances(self) -> int:
        """Get current Railway instance count."""
        try:
            # Railway API call would go here
            # For now, return a simulated value
            return 1  # Default Railway instance count
            
        except Exception:
            return 1
    
    async def get_instance_metrics(self) -> Dict[str, Any]:
        """Get Railway instance metrics."""
        try:
            # Railway API call would go here
            return {
                'instances': [
                    {
                        'id': 'railway-instance-1',
                        'cpu_usage': 45.2,
                        'memory_usage': 67.8,
                        'status': 'running',
                        'uptime': 3600
                    }
                ],
                'total_cpu': 45.2,
                'total_memory': 67.8,
                'healthy_instances': 1
            }
            
        except Exception:
            return {'instances': [], 'total_cpu': 0, 'total_memory': 0, 'healthy_instances': 0}


class KubernetesScalingProvider(CloudProviderInterface):
    """Kubernetes scaling provider implementation."""
    
    def __init__(self, namespace: str, deployment_name: str):
        self.namespace = namespace
        self.deployment_name = deployment_name
    
    async def scale_up(self, target_instances: int, instance_type: str = "standard") -> Dict[str, Any]:
        """Scale up Kubernetes deployment."""
        try:
            # Kubernetes API call would go here
            logger.info(f"Kubernetes scale-up: targeting {target_instances} replicas")
            
            return {
                'success': True,
                'provider': 'kubernetes',
                'action': 'scale_up',
                'target_instances': target_instances,
                'estimated_time': '30-120 seconds',
                'message': f'Scaling deployment {self.deployment_name} to {target_instances} replicas'
            }
            
        except Exception as e:
            logger.error(f"Kubernetes scale-up error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def scale_down(self, target_instances: int) -> Dict[str, Any]:
        """Scale down Kubernetes deployment."""
        try:
            logger.info(f"Kubernetes scale-down: targeting {target_instances} replicas")
            
            return {
                'success': True,
                'provider': 'kubernetes',
                'action': 'scale_down',
                'target_instances': target_instances,
                'estimated_time': '15-60 seconds',
                'message': f'Scaling deployment {self.deployment_name} to {target_instances} replicas'
            }
            
        except Exception as e:
            logger.error(f"Kubernetes scale-down error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_current_instances(self) -> int:
        """Get current Kubernetes replica count."""
        try:
            # Kubernetes API call would go here
            return 2  # Simulated value
            
        except Exception:
            return 1
    
    async def get_instance_metrics(self) -> Dict[str, Any]:
        """Get Kubernetes pod metrics."""
        try:
            return {
                'instances': [
                    {'id': 'pod-1', 'cpu_usage': 42.1, 'memory_usage': 58.3, 'status': 'running'},
                    {'id': 'pod-2', 'cpu_usage': 38.7, 'memory_usage': 61.2, 'status': 'running'}
                ],
                'total_cpu': 40.4,
                'total_memory': 59.75,
                'healthy_instances': 2
            }
            
        except Exception:
            return {'instances': [], 'total_cpu': 0, 'total_memory': 0, 'healthy_instances': 0}


# =============================================================================
# ADVANCED SCALING DATA CLASSES
# =============================================================================

@dataclass
class PredictiveMetrics:
    """Metrics for predictive scaling analysis."""
    timestamp: datetime
    predicted_load: float
    confidence: float
    prediction_horizon: int  # minutes
    factors: List[str]
    baseline_load: float
    trend_factor: float
    seasonal_factor: float
    anomaly_score: float


@dataclass
class LoadBalancingConfig:
    """Configuration for intelligent load balancing."""
    algorithm: str = 'least_connections'  # 'round_robin', 'least_connections', 'weighted', 'ip_hash'
    health_check_interval: int = 30
    health_check_timeout: int = 5
    failure_threshold: int = 3
    recovery_threshold: int = 2
    sticky_sessions: bool = False
    session_affinity_timeout: int = 3600
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: float = 0.5  # 50% error rate
    circuit_breaker_timeout: int = 60


@dataclass
class ScalingPlan:
    """Comprehensive scaling plan with timeline."""
    plan_id: str
    created_at: datetime
    target_instances: int
    current_instances: int
    scaling_steps: List[Dict[str, Any]]
    estimated_duration: int  # minutes
    cost_impact: Dict[str, float]
    risk_assessment: str
    rollback_plan: Optional[Dict[str, Any]]
    approval_required: bool = False


@dataclass
class FailoverConfig:
    """Configuration for failover mechanisms."""
    enable_automatic_failover: bool = True
    failover_threshold: float = 0.8  # 80% failure rate
    failover_timeout: int = 300  # 5 minutes
    backup_regions: List[str] = field(default_factory=list)
    cross_region_replication: bool = False
    health_check_grace_period: int = 60


# =============================================================================
# ADVANCED AUTO-SCALER SERVICE
# =============================================================================

class AdvancedAutoScalerService:
    """
    Enterprise auto-scaler with predictive scaling, intelligent load balancing,
    and multi-cloud provider support.
    """
    
    def __init__(self, app=None):
        self.app = app
        
        # Cloud providers
        self.cloud_providers: Dict[str, CloudProviderInterface] = {}
        self.active_provider = None
        
        # Load balancing
        self.load_balancing_config = LoadBalancingConfig()
        self.instance_health: Dict[str, Dict] = {}
        self.load_balancer_active = False
        
        # Predictive scaling
        self.predictive_metrics_history = deque(maxlen=2880)  # 48 hours at 1-minute intervals
        self.prediction_models: Dict[str, Any] = {}
        self.enable_predictive_scaling = True
        
        # Scaling plans and execution
        self.active_scaling_plans: Dict[str, ScalingPlan] = {}
        self.scaling_history = deque(maxlen=1000)
        self.scaling_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="scaling")
        
        # Circuit breaker for scaling operations
        self.circuit_breaker_state = 'closed'  # 'closed', 'open', 'half_open'
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None
        
        # Failover configuration
        self.failover_config = FailoverConfig()
        self.failover_active = False
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize advanced auto-scaler with Flask app."""
        self.app = app
        
        # Load configuration
        self._load_config_from_app()
        
        # Initialize cloud providers
        self._initialize_cloud_providers()
        
        # Setup load balancing
        self._setup_load_balancing()
        
        # Initialize prediction models
        self._initialize_prediction_models()
        
        # Start background monitoring
        self.start_monitoring()
        
        logger.info("Advanced auto-scaler service initialized")
    
    def _load_config_from_app(self):
        """Load configuration from Flask app config."""
        if not self.app:
            return
        
        config = self.app.config
        
        # Load cloud provider configs
        self.cloud_provider_config = {
            'railway': {
                'enabled': config.get('RAILWAY_SCALING_ENABLED', True),
                'api_token': config.get('RAILWAY_API_TOKEN'),
                'service_id': config.get('RAILWAY_SERVICE_ID')
            },
            'kubernetes': {
                'enabled': config.get('KUBERNETES_SCALING_ENABLED', False),
                'namespace': config.get('KUBERNETES_NAMESPACE', 'default'),
                'deployment': config.get('KUBERNETES_DEPLOYMENT', 'hr-ats')
            }
        }
        
        # Load predictive scaling config
        self.enable_predictive_scaling = config.get('ENABLE_PREDICTIVE_SCALING', True)
        
        # Load load balancing config
        self.load_balancing_config.algorithm = config.get('LOAD_BALANCING_ALGORITHM', 'least_connections')
        self.load_balancing_config.health_check_interval = config.get('HEALTH_CHECK_INTERVAL', 30)
        self.load_balancing_config.enable_circuit_breaker = config.get('ENABLE_CIRCUIT_BREAKER', True)
    
    def _initialize_cloud_providers(self):
        """Initialize cloud provider interfaces."""
        try:
            # Initialize Railway provider
            if (self.cloud_provider_config['railway']['enabled'] and 
                self.cloud_provider_config['railway']['api_token']):
                
                railway_provider = RailwayScalingProvider(
                    self.cloud_provider_config['railway']['api_token'],
                    self.cloud_provider_config['railway']['service_id']
                )
                self.cloud_providers['railway'] = railway_provider
                
                # Set as active provider if none set
                if not self.active_provider:
                    self.active_provider = 'railway'
                
                logger.info("Railway scaling provider initialized")
            
            # Initialize Kubernetes provider
            if self.cloud_provider_config['kubernetes']['enabled']:
                kubernetes_provider = KubernetesScalingProvider(
                    self.cloud_provider_config['kubernetes']['namespace'],
                    self.cloud_provider_config['kubernetes']['deployment']
                )
                self.cloud_providers['kubernetes'] = kubernetes_provider
                
                # Set as active provider if Railway not available
                if not self.active_provider:
                    self.active_provider = 'kubernetes'
                
                logger.info("Kubernetes scaling provider initialized")
            
            if not self.cloud_providers:
                logger.warning("No cloud providers configured for scaling")
                
        except Exception as e:
            logger.error(f"Error initializing cloud providers: {str(e)}")
    
    def _setup_load_balancing(self):
        """Setup intelligent load balancing."""
        try:
            self.load_balancer_active = True
            logger.info(f"Load balancing configured: {self.load_balancing_config.algorithm}")
            
        except Exception as e:
            logger.error(f"Error setting up load balancing: {str(e)}")
    
    def _initialize_prediction_models(self):
        """Initialize predictive scaling models."""
        try:
            # Simple trend-based prediction model
            self.prediction_models = {
                'linear_trend': {
                    'enabled': True,
                    'window_size': 60,  # 1 hour
                    'weight': 0.4
                },
                'seasonal': {
                    'enabled': True,
                    'patterns': ['daily', 'weekly'],
                    'weight': 0.3
                },
                'anomaly_detection': {
                    'enabled': True,
                    'threshold': 2.0,  # 2 standard deviations
                    'weight': 0.3
                }
            }
            
            logger.info("Predictive scaling models initialized")
            
        except Exception as e:
            logger.error(f"Error initializing prediction models: {str(e)}")
    
    # =============================================================================
    # PREDICTIVE SCALING
    # =============================================================================
    
    def generate_load_prediction(self, horizon_minutes: int = 30) -> PredictiveMetrics:
        """Generate load prediction for specified horizon."""
        try:
            current_time = datetime.utcnow()
            
            if len(self.predictive_metrics_history) < 10:
                # Not enough data for prediction
                return PredictiveMetrics(
                    timestamp=current_time,
                    predicted_load=50.0,  # Baseline assumption
                    confidence=0.3,
                    prediction_horizon=horizon_minutes,
                    factors=['insufficient_data'],
                    baseline_load=50.0,
                    trend_factor=0.0,
                    seasonal_factor=0.0,
                    anomaly_score=0.0
                )
            
            recent_metrics = list(self.predictive_metrics_history)[-60:]  # Last hour
            
            # Calculate baseline load
            baseline_load = sum(m.predicted_load for m in recent_metrics) / len(recent_metrics)
            
            # Calculate trend factor
            trend_factor = self._calculate_trend_factor(recent_metrics, horizon_minutes)
            
            # Calculate seasonal factor
            seasonal_factor = self._calculate_seasonal_factor(current_time, horizon_minutes)
            
            # Calculate anomaly score
            anomaly_score = self._calculate_anomaly_score(recent_metrics)
            
            # Combine factors for prediction
            predicted_load = baseline_load * (1 + trend_factor + seasonal_factor)
            
            # Adjust for anomalies
            if anomaly_score > 1.5:
                predicted_load *= 1.2  # Increase prediction if anomaly detected
            
            # Calculate confidence based on data quality and consistency
            confidence = self._calculate_prediction_confidence(recent_metrics, anomaly_score)
            
            # Determine contributing factors
            factors = []
            if abs(trend_factor) > 0.1:
                factors.append('trend_analysis')
            if abs(seasonal_factor) > 0.05:
                factors.append('seasonal_patterns')
            if anomaly_score > 1.0:
                factors.append('anomaly_detection')
            if not factors:
                factors.append('baseline_stable')
            
            return PredictiveMetrics(
                timestamp=current_time,
                predicted_load=round(predicted_load, 2),
                confidence=round(confidence, 3),
                prediction_horizon=horizon_minutes,
                factors=factors,
                baseline_load=round(baseline_load, 2),
                trend_factor=round(trend_factor, 3),
                seasonal_factor=round(seasonal_factor, 3),
                anomaly_score=round(anomaly_score, 3)
            )
            
        except Exception as e:
            logger.error(f"Error generating load prediction: {str(e)}")
            return PredictiveMetrics(
                timestamp=datetime.utcnow(),
                predicted_load=50.0,
                confidence=0.2,
                prediction_horizon=horizon_minutes,
                factors=['error'],
                baseline_load=50.0,
                trend_factor=0.0,
                seasonal_factor=0.0,
                anomaly_score=0.0
            )
    
    def _calculate_trend_factor(self, metrics: List[PredictiveMetrics], horizon_minutes: int) -> float:
        """Calculate trend factor for prediction."""
        try:
            if len(metrics) < 5:
                return 0.0
            
            # Simple linear regression for trend
            loads = [m.predicted_load for m in metrics]
            n = len(loads)
            
            # Calculate trend slope
            x_mean = n / 2
            y_mean = sum(loads) / n
            
            numerator = sum((i - x_mean) * (loads[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return 0.0
            
            slope = numerator / denominator
            
            # Project trend over horizon
            trend_factor = (slope * horizon_minutes) / y_mean if y_mean > 0 else 0.0
            
            # Limit trend factor to reasonable bounds
            return max(-0.5, min(0.5, trend_factor))
            
        except Exception:
            return 0.0
    
    def _calculate_seasonal_factor(self, current_time: datetime, horizon_minutes: int) -> float:
        """Calculate seasonal factor based on time patterns."""
        try:
            target_time = current_time + timedelta(minutes=horizon_minutes)
            
            # Daily patterns
            hour = target_time.hour
            daily_factor = 0.0
            
            if 9 <= hour <= 17:  # Business hours
                daily_factor = 0.1
            elif 18 <= hour <= 22:  # Evening hours
                daily_factor = 0.05
            else:  # Night hours
                daily_factor = -0.1
            
            # Weekly patterns
            weekday = target_time.weekday()
            weekly_factor = 0.0
            
            if weekday < 5:  # Monday to Friday
                weekly_factor = 0.05
            else:  # Weekend
                weekly_factor = -0.05
            
            return daily_factor + weekly_factor
            
        except Exception:
            return 0.0
    
    def _calculate_anomaly_score(self, metrics: List[PredictiveMetrics]) -> float:
        """Calculate anomaly score for recent metrics."""
        try:
            if len(metrics) < 10:
                return 0.0
            
            loads = [m.predicted_load for m in metrics]
            
            # Calculate statistics
            mean_load = sum(loads) / len(loads)
            variance = sum((x - mean_load) ** 2 for x in loads) / len(loads)
            std_dev = variance ** 0.5
            
            if std_dev == 0:
                return 0.0
            
            # Check recent values for anomalies
            recent_loads = loads[-5:]  # Last 5 data points
            anomaly_scores = [abs(load - mean_load) / std_dev for load in recent_loads]
            
            return max(anomaly_scores)
            
        except Exception:
            return 0.0
    
    def _calculate_prediction_confidence(self, metrics: List[PredictiveMetrics], anomaly_score: float) -> float:
        """Calculate confidence in prediction based on data quality."""
        try:
            base_confidence = 0.7
            
            # Reduce confidence for high anomaly scores
            anomaly_penalty = min(0.3, anomaly_score * 0.1)
            
            # Reduce confidence for insufficient data
            data_quality = min(1.0, len(metrics) / 30)  # Prefer 30+ data points
            
            # Reduce confidence for high variance
            loads = [m.predicted_load for m in metrics]
            coefficient_of_variation = (
                (sum((x - sum(loads) / len(loads)) ** 2 for x in loads) / len(loads)) ** 0.5
            ) / (sum(loads) / len(loads)) if loads else 0
            
            variance_penalty = min(0.2, coefficient_of_variation * 0.1)
            
            confidence = base_confidence * data_quality - anomaly_penalty - variance_penalty
            
            return max(0.1, min(1.0, confidence))
            
        except Exception:
            return 0.5
    
    # =============================================================================
    # INTELLIGENT LOAD BALANCING
    # =============================================================================
    
    def update_instance_health(self, instance_id: str, health_data: Dict[str, Any]):
        """Update health information for an instance."""
        try:
            current_time = datetime.utcnow()
            
            if instance_id not in self.instance_health:
                self.instance_health[instance_id] = {
                    'first_seen': current_time,
                    'consecutive_failures': 0,
                    'last_success': current_time,
                    'status': 'unknown'
                }
            
            instance_info = self.instance_health[instance_id]
            instance_info['last_check'] = current_time
            instance_info['health_data'] = health_data
            
            # Determine health status
            is_healthy = health_data.get('status') == 'healthy'
            
            if is_healthy:
                instance_info['consecutive_failures'] = 0
                instance_info['last_success'] = current_time
                instance_info['status'] = 'healthy'
            else:
                instance_info['consecutive_failures'] += 1
                if instance_info['consecutive_failures'] >= self.load_balancing_config.failure_threshold:
                    instance_info['status'] = 'unhealthy'
                else:
                    instance_info['status'] = 'degraded'
            
            # Circuit breaker logic
            if instance_info['status'] == 'unhealthy':
                self._update_circuit_breaker(instance_id, False)
            elif instance_info['consecutive_failures'] == 0:
                self._update_circuit_breaker(instance_id, True)
            
        except Exception as e:
            logger.error(f"Error updating instance health for {instance_id}: {str(e)}")
    
    def _update_circuit_breaker(self, instance_id: str, success: bool):
        """Update circuit breaker state based on instance health."""
        try:
            if not self.load_balancing_config.enable_circuit_breaker:
                return
            
            current_time = datetime.utcnow()
            
            if not success:
                self.circuit_breaker_failures += 1
                self.circuit_breaker_last_failure = current_time
                
                # Check if we should open the circuit
                failure_rate = self.circuit_breaker_failures / max(1, len(self.instance_health))
                if failure_rate >= self.load_balancing_config.circuit_breaker_threshold:
                    self.circuit_breaker_state = 'open'
                    logger.warning(f"Circuit breaker opened due to high failure rate: {failure_rate:.2%}")
            
            else:
                # Check if we can close the circuit
                if self.circuit_breaker_state == 'open':
                    time_since_failure = (current_time - self.circuit_breaker_last_failure).total_seconds()
                    if time_since_failure >= self.load_balancing_config.circuit_breaker_timeout:
                        self.circuit_breaker_state = 'half_open'
                        logger.info("Circuit breaker moved to half-open state")
                
                elif self.circuit_breaker_state == 'half_open':
                    self.circuit_breaker_state = 'closed'
                    self.circuit_breaker_failures = 0
                    logger.info("Circuit breaker closed - system recovered")
            
        except Exception as e:
            logger.error(f"Error updating circuit breaker: {str(e)}")
    
    def get_optimal_instance(self, request_context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Get optimal instance for load balancing."""
        try:
            if self.circuit_breaker_state == 'open':
                logger.warning("Circuit breaker open - rejecting request")
                return None
            
            healthy_instances = {
                instance_id: info for instance_id, info in self.instance_health.items()
                if info['status'] in ['healthy', 'degraded']
            }
            
            if not healthy_instances:
                logger.warning("No healthy instances available")
                return None
            
            # Apply load balancing algorithm
            if self.load_balancing_config.algorithm == 'round_robin':
                return self._round_robin_selection(healthy_instances)
            
            elif self.load_balancing_config.algorithm == 'least_connections':
                return self._least_connections_selection(healthy_instances)
            
            elif self.load_balancing_config.algorithm == 'weighted':
                return self._weighted_selection(healthy_instances)
            
            elif self.load_balancing_config.algorithm == 'ip_hash':
                return self._ip_hash_selection(healthy_instances, request_context)
            
            else:
                # Default to round robin
                return self._round_robin_selection(healthy_instances)
            
        except Exception as e:
            logger.error(f"Error selecting optimal instance: {str(e)}")
            return None
    
    def _round_robin_selection(self, instances: Dict[str, Dict]) -> str:
        """Round robin instance selection."""
        instance_ids = list(instances.keys())
        if not hasattr(self, '_round_robin_index'):
            self._round_robin_index = 0
        
        selected = instance_ids[self._round_robin_index % len(instance_ids)]
        self._round_robin_index += 1
        
        return selected
    
    def _least_connections_selection(self, instances: Dict[str, Dict]) -> str:
        """Least connections instance selection."""
        # Simplified: choose instance with lowest CPU usage as proxy for connections
        return min(instances.keys(), key=lambda iid: 
                  instances[iid].get('health_data', {}).get('cpu_usage', 100))
    
    def _weighted_selection(self, instances: Dict[str, Dict]) -> str:
        """Weighted instance selection based on performance."""
        # Calculate weights based on inverse of CPU usage
        weights = {}
        for instance_id, info in instances.items():
            cpu_usage = info.get('health_data', {}).get('cpu_usage', 50)
            # Higher weight for lower CPU usage
            weights[instance_id] = 100 - cpu_usage
        
        # Select based on weights
        total_weight = sum(weights.values())
        import random
        random_value = random.uniform(0, total_weight)
        
        cumulative_weight = 0
        for instance_id, weight in weights.items():
            cumulative_weight += weight
            if random_value <= cumulative_weight:
                return instance_id
        
        return list(instances.keys())[0]  # Fallback
    
    def _ip_hash_selection(self, instances: Dict[str, Dict], request_context: Optional[Dict[str, Any]]) -> str:
        """IP hash-based instance selection for session affinity."""
        if not request_context or 'client_ip' not in request_context:
            return self._round_robin_selection(instances)
        
        client_ip = request_context['client_ip']
        # Simple hash of IP to instance
        import hashlib
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        instance_index = hash_value % len(instances)
        
        return list(instances.keys())[instance_index]
    
    # =============================================================================
    # SCALING PLAN EXECUTION
    # =============================================================================
    
    async def create_scaling_plan(self, target_instances: int, 
                                 reason: str = "Manual scaling") -> ScalingPlan:
        """Create a comprehensive scaling plan."""
        try:
            current_time = datetime.utcnow()
            plan_id = f"plan_{int(current_time.timestamp())}"
            
            # Get current instances
            current_instances = await self._get_current_instance_count()
            
            # Calculate scaling steps
            scaling_steps = self._calculate_scaling_steps(current_instances, target_instances)
            
            # Estimate duration and cost
            estimated_duration = self._estimate_scaling_duration(scaling_steps)
            cost_impact = self._calculate_cost_impact(current_instances, target_instances)
            
            # Risk assessment
            risk_assessment = self._assess_scaling_risk(current_instances, target_instances)
            
            # Create rollback plan
            rollback_plan = {
                'target_instances': current_instances,
                'estimated_duration': max(5, estimated_duration // 2),
                'trigger_conditions': ['high_error_rate', 'performance_degradation']
            }
            
            # Determine if approval is required
            approval_required = (
                abs(target_instances - current_instances) > 2 or
                target_instances > 8 or
                risk_assessment == 'high'
            )
            
            plan = ScalingPlan(
                plan_id=plan_id,
                created_at=current_time,
                target_instances=target_instances,
                current_instances=current_instances,
                scaling_steps=scaling_steps,
                estimated_duration=estimated_duration,
                cost_impact=cost_impact,
                risk_assessment=risk_assessment,
                rollback_plan=rollback_plan,
                approval_required=approval_required
            )
            
            self.active_scaling_plans[plan_id] = plan
            
            logger.info(f"Created scaling plan {plan_id}: {current_instances} → {target_instances} instances")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating scaling plan: {str(e)}")
            raise
    
    async def execute_scaling_plan(self, plan_id: str) -> Dict[str, Any]:
        """Execute a scaling plan."""
        try:
            if plan_id not in self.active_scaling_plans:
                return {'success': False, 'error': 'Plan not found'}
            
            plan = self.active_scaling_plans[plan_id]
            
            if plan.approval_required:
                return {'success': False, 'error': 'Plan requires approval before execution'}
            
            logger.info(f"Executing scaling plan {plan_id}")
            
            execution_results = []
            
            for step in plan.scaling_steps:
                step_result = await self._execute_scaling_step(step)
                execution_results.append(step_result)
                
                if not step_result['success']:
                    logger.error(f"Scaling step failed: {step_result}")
                    # Consider rollback
                    break
                
                # Wait between steps if specified
                if step.get('delay_seconds', 0) > 0:
                    await asyncio.sleep(step['delay_seconds'])
            
            # Update plan status
            overall_success = all(result['success'] for result in execution_results)
            
            # Record execution in history
            execution_record = {
                'plan_id': plan_id,
                'executed_at': datetime.utcnow(),
                'success': overall_success,
                'steps_executed': len(execution_results),
                'results': execution_results
            }
            
            self.scaling_history.append(execution_record)
            
            # Clean up plan if successful
            if overall_success:
                del self.active_scaling_plans[plan_id]
            
            return {
                'success': overall_success,
                'plan_id': plan_id,
                'steps_executed': len(execution_results),
                'execution_results': execution_results
            }
            
        except Exception as e:
            logger.error(f"Error executing scaling plan {plan_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_scaling_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single scaling step."""
        try:
            action = step['action']
            target_instances = step['target_instances']
            
            provider = self.cloud_providers.get(self.active_provider)
            if not provider:
                return {'success': False, 'error': 'No active cloud provider'}
            
            if action == 'scale_up':
                result = await provider.scale_up(target_instances)
            elif action == 'scale_down':
                result = await provider.scale_down(target_instances)
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}
            
            return {
                'success': result['success'],
                'action': action,
                'target_instances': target_instances,
                'provider_response': result
            }
            
        except Exception as e:
            logger.error(f"Error executing scaling step: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_scaling_steps(self, current: int, target: int) -> List[Dict[str, Any]]:
        """Calculate optimal scaling steps."""
        steps = []
        
        if target > current:
            # Scale up gradually
            step_size = min(2, target - current)  # Max 2 instances at a time
            instances = current
            
            while instances < target:
                next_instances = min(instances + step_size, target)
                steps.append({
                    'action': 'scale_up',
                    'target_instances': next_instances,
                    'step_size': next_instances - instances,
                    'delay_seconds': 120 if next_instances < target else 0  # 2 min between steps
                })
                instances = next_instances
        
        elif target < current:
            # Scale down gradually
            step_size = min(1, current - target)  # Max 1 instance at a time for safety
            instances = current
            
            while instances > target:
                next_instances = max(instances - step_size, target)
                steps.append({
                    'action': 'scale_down',
                    'target_instances': next_instances,
                    'step_size': instances - next_instances,
                    'delay_seconds': 180 if next_instances > target else 0  # 3 min between steps
                })
                instances = next_instances
        
        return steps
    
    def _estimate_scaling_duration(self, steps: List[Dict[str, Any]]) -> int:
        """Estimate total scaling duration in minutes."""
        base_time_per_step = 3  # 3 minutes per step
        total_delay = sum(step.get('delay_seconds', 0) for step in steps) // 60
        
        return len(steps) * base_time_per_step + total_delay
    
    def _calculate_cost_impact(self, current: int, target: int) -> Dict[str, float]:
        """Calculate cost impact of scaling."""
        # Simplified cost calculation
        cost_per_instance_hour = 0.50  # $0.50 per instance per hour
        hours_projection = 24  # Project cost for 24 hours
        
        current_cost = current * cost_per_instance_hour * hours_projection
        target_cost = target * cost_per_instance_hour * hours_projection
        
        return {
            'current_daily_cost': round(current_cost, 2),
            'target_daily_cost': round(target_cost, 2),
            'cost_difference': round(target_cost - current_cost, 2),
            'percentage_change': round(((target_cost - current_cost) / current_cost * 100), 1) if current_cost > 0 else 0
        }
    
    def _assess_scaling_risk(self, current: int, target: int) -> str:
        """Assess risk level of scaling operation."""
        scale_factor = target / current if current > 0 else 1
        
        if scale_factor > 3 or scale_factor < 0.3:
            return 'high'
        elif scale_factor > 2 or scale_factor < 0.5:
            return 'medium'
        else:
            return 'low'
    
    async def _get_current_instance_count(self) -> int:
        """Get current instance count from active provider."""
        try:
            provider = self.cloud_providers.get(self.active_provider)
            if provider:
                return await provider.get_current_instances()
            return 1  # Default fallback
            
        except Exception:
            return 1
    
    # =============================================================================
    # MONITORING AND BACKGROUND TASKS
    # =============================================================================
    
    def start_monitoring(self):
        """Start background monitoring tasks."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Update predictive metrics
                    current_prediction = self.generate_load_prediction()
                    self.predictive_metrics_history.append(current_prediction)
                    
                    # Check for predictive scaling opportunities
                    if self.enable_predictive_scaling:
                        self._check_predictive_scaling(current_prediction)
                    
                    # Health check instances
                    asyncio.run(self._perform_health_checks())
                    
                    # Sleep for 1 minute
                    time.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {str(e)}")
                    time.sleep(60)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Advanced auto-scaler monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring tasks."""
        self.monitoring_active = False
        logger.info("Advanced auto-scaler monitoring stopped")
    
    def _check_predictive_scaling(self, prediction: PredictiveMetrics):
        """Check if predictive scaling action is needed."""
        try:
            if prediction.confidence < 0.7:
                return  # Not confident enough
            
            current_instances = 1  # Simplified - would get from provider
            
            # Determine if scaling is needed
            if prediction.predicted_load > 80 and current_instances < 8:
                logger.info(f"Predictive scaling: High load predicted ({prediction.predicted_load}%)")
                # Could trigger automatic scaling here
                
            elif prediction.predicted_load < 30 and current_instances > 1:
                logger.info(f"Predictive scaling: Low load predicted ({prediction.predicted_load}%)")
                # Could trigger automatic scale-down here
                
        except Exception as e:
            logger.error(f"Error in predictive scaling check: {str(e)}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all instances."""
        try:
            if not self.active_provider:
                return
            
            provider = self.cloud_providers[self.active_provider]
            instance_metrics = await provider.get_instance_metrics()
            
            for instance in instance_metrics.get('instances', []):
                self.update_instance_health(instance['id'], {
                    'status': 'healthy' if instance['status'] == 'running' else 'unhealthy',
                    'cpu_usage': instance.get('cpu_usage', 0),
                    'memory_usage': instance.get('memory_usage', 0),
                    'uptime': instance.get('uptime', 0)
                })
                
        except Exception as e:
            logger.error(f"Error performing health checks: {str(e)}")
    
    # =============================================================================
    # PUBLIC API METHODS
    # =============================================================================
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of advanced auto-scaler."""
        try:
            latest_prediction = (self.predictive_metrics_history[-1] 
                               if self.predictive_metrics_history else None)
            
            healthy_instances = sum(1 for info in self.instance_health.values() 
                                  if info['status'] == 'healthy')
            
            return {
                'active_provider': self.active_provider,
                'available_providers': list(self.cloud_providers.keys()),
                'predictive_scaling': {
                    'enabled': self.enable_predictive_scaling,
                    'latest_prediction': latest_prediction.__dict__ if latest_prediction else None,
                    'prediction_history_size': len(self.predictive_metrics_history)
                },
                'load_balancing': {
                    'algorithm': self.load_balancing_config.algorithm,
                    'circuit_breaker_state': self.circuit_breaker_state,
                    'healthy_instances': healthy_instances,
                    'total_instances': len(self.instance_health)
                },
                'scaling_plans': {
                    'active_plans': len(self.active_scaling_plans),
                    'execution_history': len(self.scaling_history)
                },
                'monitoring': {
                    'active': self.monitoring_active,
                    'health_checks_enabled': self.load_balancer_active
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {str(e)}")
            return {'error': str(e)}
    
    def get_scaling_recommendations(self) -> Dict[str, Any]:
        """Get scaling recommendations based on current state."""
        try:
            if not self.predictive_metrics_history:
                return {'recommendations': [], 'reason': 'Insufficient data'}
            
            latest_prediction = self.predictive_metrics_history[-1]
            recommendations = []
            
            # Current load analysis
            if latest_prediction.predicted_load > 85:
                recommendations.append({
                    'action': 'scale_up',
                    'urgency': 'high',
                    'reason': f'High predicted load: {latest_prediction.predicted_load}%',
                    'confidence': latest_prediction.confidence,
                    'suggested_instances': '+1 to +2'
                })
            
            elif latest_prediction.predicted_load < 25:
                recommendations.append({
                    'action': 'scale_down',
                    'urgency': 'low',
                    'reason': f'Low predicted load: {latest_prediction.predicted_load}%',
                    'confidence': latest_prediction.confidence,
                    'suggested_instances': '-1'
                })
            
            # Circuit breaker considerations
            if self.circuit_breaker_state == 'open':
                recommendations.append({
                    'action': 'investigate',
                    'urgency': 'high',
                    'reason': 'Circuit breaker is open - system health issues detected',
                    'confidence': 1.0,
                    'suggested_instances': 'Fix underlying issues before scaling'
                })
            
            return {
                'recommendations': recommendations,
                'latest_prediction': latest_prediction.__dict__,
                'confidence_threshold': 0.7,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting scaling recommendations: {str(e)}")
            return {'error': str(e)}


# =============================================================================
# GLOBAL ADVANCED AUTO-SCALER SERVICE INSTANCE
# =============================================================================

advanced_auto_scaler = AdvancedAutoScalerService()
