"""
Auto-Scaling Configuration Service - Phase 2.2 Implementation
Provides intelligent auto-scaling recommendations and configuration management
for horizontal and vertical scaling based on load patterns and performance metrics.
"""
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import threading

logger = logging.getLogger(__name__)

# =============================================================================
# SCALING DATA CLASSES
# =============================================================================

@dataclass
class ScalingMetrics:
    """Metrics used for scaling decisions."""
    timestamp: datetime
    avg_cpu: float
    avg_memory: float
    peak_cpu: float
    peak_memory: float
    avg_queue_length: float
    max_queue_length: int
    avg_response_time: float
    error_rate: float
    throughput: float
    active_connections: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'avg_cpu': self.avg_cpu,
            'avg_memory': self.avg_memory,
            'peak_cpu': self.peak_cpu,
            'peak_memory': self.peak_memory,
            'avg_queue_length': self.avg_queue_length,
            'max_queue_length': self.max_queue_length,
            'avg_response_time': self.avg_response_time,
            'error_rate': self.error_rate,
            'throughput': self.throughput,
            'active_connections': self.active_connections
        }

@dataclass
class ScalingConfiguration:
    """Configuration for auto-scaling behavior."""
    name: str
    enabled: bool
    min_instances: int
    max_instances: int
    target_cpu_utilization: float
    target_memory_utilization: float
    scale_up_threshold: float
    scale_down_threshold: float
    scale_up_cooldown: int  # seconds
    scale_down_cooldown: int  # seconds
    evaluation_periods: int
    queue_length_threshold: int
    response_time_threshold: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'min_instances': self.min_instances,
            'max_instances': self.max_instances,
            'target_cpu_utilization': self.target_cpu_utilization,
            'target_memory_utilization': self.target_memory_utilization,
            'scale_up_threshold': self.scale_up_threshold,
            'scale_down_threshold': self.scale_down_threshold,
            'scale_up_cooldown': self.scale_up_cooldown,
            'scale_down_cooldown': self.scale_down_cooldown,
            'evaluation_periods': self.evaluation_periods,
            'queue_length_threshold': self.queue_length_threshold,
            'response_time_threshold': self.response_time_threshold
        }

@dataclass
class ScalingAction:
    """Represents a scaling action recommendation."""
    timestamp: datetime
    action_type: str  # 'scale_up', 'scale_down', 'maintain'
    current_instances: int
    target_instances: int
    trigger_reason: str
    confidence: float
    estimated_impact: Dict[str, Any]
    configuration_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'action_type': self.action_type,
            'current_instances': self.current_instances,
            'target_instances': self.target_instances,
            'trigger_reason': self.trigger_reason,
            'confidence': self.confidence,
            'estimated_impact': self.estimated_impact,
            'configuration_used': self.configuration_used
        }

# =============================================================================
# AUTO-SCALING CONFIGURATION SERVICE
# =============================================================================

class AutoScalingConfigurationService:
    """
    Intelligent auto-scaling configuration service that provides scaling 
    recommendations based on load patterns, performance metrics, and 
    predictive analysis.
    """
    
    def __init__(self, app=None):
        self.app = app
        
        # Default scaling configurations for different environments
        self.scaling_configurations = {
            'production': ScalingConfiguration(
                name='production',
                enabled=True,
                min_instances=2,
                max_instances=8,
                target_cpu_utilization=70.0,
                target_memory_utilization=75.0,
                scale_up_threshold=80.0,
                scale_down_threshold=40.0,
                scale_up_cooldown=300,  # 5 minutes
                scale_down_cooldown=600,  # 10 minutes
                evaluation_periods=3,
                queue_length_threshold=10,
                response_time_threshold=2.0
            ),
            'staging': ScalingConfiguration(
                name='staging',
                enabled=True,
                min_instances=1,
                max_instances=4,
                target_cpu_utilization=75.0,
                target_memory_utilization=80.0,
                scale_up_threshold=85.0,
                scale_down_threshold=30.0,
                scale_up_cooldown=180,  # 3 minutes
                scale_down_cooldown=300,  # 5 minutes
                evaluation_periods=2,
                queue_length_threshold=5,
                response_time_threshold=3.0
            ),
            'development': ScalingConfiguration(
                name='development',
                enabled=False,
                min_instances=1,
                max_instances=2,
                target_cpu_utilization=80.0,
                target_memory_utilization=85.0,
                scale_up_threshold=90.0,
                scale_down_threshold=20.0,
                scale_up_cooldown=120,  # 2 minutes
                scale_down_cooldown=180,  # 3 minutes
                evaluation_periods=1,
                queue_length_threshold=3,
                response_time_threshold=5.0
            )
        }
        
        # Current state
        self.current_environment = 'production'
        self.current_instances = 1
        self.last_scaling_action = None
        self.last_scale_up_time = None
        self.last_scale_down_time = None
        
        # History tracking
        self.scaling_metrics_history = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.scaling_actions_history = deque(maxlen=100)
        
        # Performance tracking
        self.performance_baselines = {}
        self.scaling_effectiveness = deque(maxlen=50)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the auto-scaling service with Flask app."""
        self.app = app
        
        # Load configuration from app
        config = app.config
        
        # Determine environment
        self.current_environment = config.get('ENVIRONMENT', 'production').lower()
        if self.current_environment not in self.scaling_configurations:
            self.current_environment = 'production'
        
        # Override configurations from app config
        if config.get('AUTO_SCALING_CONFIG'):
            self._load_custom_configurations(config['AUTO_SCALING_CONFIG'])
        
        # Get current instance count
        self.current_instances = config.get('CURRENT_INSTANCES', 1)
        
        logger.info(f"Auto-Scaling Configuration Service initialized for {self.current_environment} environment")
    
    def _load_custom_configurations(self, custom_config: Dict[str, Any]):
        """Load custom scaling configurations from app config."""
        try:
            for env_name, config_data in custom_config.items():
                if env_name in self.scaling_configurations:
                    # Update existing configuration
                    current_config = self.scaling_configurations[env_name]
                    for key, value in config_data.items():
                        if hasattr(current_config, key):
                            setattr(current_config, key, value)
                        
                    logger.info(f"Updated scaling configuration for {env_name}")
                    
        except Exception as e:
            logger.error(f"Error loading custom scaling configurations: {str(e)}")
    
    # =============================================================================
    # SCALING METRICS ANALYSIS
    # =============================================================================
    
    def collect_scaling_metrics(self, load_manager=None) -> ScalingMetrics:
        """Collect metrics for scaling decisions."""
        try:
            current_time = datetime.utcnow()
            
            # Get metrics from load manager if available
            if load_manager and hasattr(load_manager, 'load_metrics_history'):
                recent_metrics = list(load_manager.load_metrics_history)[-10:]  # Last 5 minutes
                
                if recent_metrics:
                    # Calculate aggregated metrics
                    cpu_values = [m.cpu_usage for m in recent_metrics]
                    memory_values = [m.memory_usage for m in recent_metrics]
                    queue_values = [m.queue_length for m in recent_metrics]
                    response_times = [m.response_time_avg for m in recent_metrics if m.response_time_avg > 0]
                    error_rates = [m.error_rate for m in recent_metrics]
                    
                    avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
                    avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0
                    peak_cpu = max(cpu_values) if cpu_values else 0
                    peak_memory = max(memory_values) if memory_values else 0
                    avg_queue_length = sum(queue_values) / len(queue_values) if queue_values else 0
                    max_queue_length = max(queue_values) if queue_values else 0
                    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                    error_rate = sum(error_rates) / len(error_rates) if error_rates else 0
                    
                    # Calculate throughput (approximate)
                    throughput = self._estimate_throughput(recent_metrics)
                    
                    # Get connection count
                    active_connections = recent_metrics[-1].active_connections if recent_metrics else 0
                    
                else:
                    # No recent metrics available
                    avg_cpu = avg_memory = peak_cpu = peak_memory = 50.0
                    avg_queue_length = max_queue_length = 0
                    avg_response_time = 1.0
                    error_rate = throughput = active_connections = 0
                    
            else:
                # Fallback metrics collection
                avg_cpu, avg_memory = self._get_fallback_metrics()
                peak_cpu = avg_cpu * 1.2
                peak_memory = avg_memory * 1.1
                avg_queue_length = max_queue_length = 0
                avg_response_time = 1.0
                error_rate = throughput = active_connections = 0
            
            scaling_metrics = ScalingMetrics(
                timestamp=current_time,
                avg_cpu=round(avg_cpu, 2),
                avg_memory=round(avg_memory, 2),
                peak_cpu=round(peak_cpu, 2),
                peak_memory=round(peak_memory, 2),
                avg_queue_length=round(avg_queue_length, 2),
                max_queue_length=max_queue_length,
                avg_response_time=round(avg_response_time, 3),
                error_rate=round(error_rate, 4),
                throughput=round(throughput, 2),
                active_connections=active_connections
            )
            
            # Store in history
            self.scaling_metrics_history.append(scaling_metrics)
            
            return scaling_metrics
            
        except Exception as e:
            logger.error(f"Error collecting scaling metrics: {str(e)}")
            # Return safe default metrics
            return ScalingMetrics(
                timestamp=datetime.utcnow(),
                avg_cpu=50.0,
                avg_memory=50.0,
                peak_cpu=60.0,
                peak_memory=60.0,
                avg_queue_length=0.0,
                max_queue_length=0,
                avg_response_time=1.0,
                error_rate=0.0,
                throughput=0.0,
                active_connections=0
            )
    
    def _estimate_throughput(self, recent_metrics: List) -> float:
        """Estimate current throughput based on queue changes."""
        try:
            if len(recent_metrics) < 2:
                return 0.0
            
            # Calculate processing rate based on queue changes
            total_processed = 0
            time_windows = 0
            
            for i in range(1, len(recent_metrics)):
                current = recent_metrics[i]
                previous = recent_metrics[i-1]
                
                # Time difference in minutes
                time_diff = (current.timestamp - previous.timestamp).total_seconds() / 60
                if time_diff > 0:
                    # Estimate items processed
                    queue_change = previous.queue_length - current.queue_length
                    if queue_change > 0:  # Queue decreased, items were processed
                        processing_rate = queue_change / time_diff
                        total_processed += processing_rate
                        time_windows += 1
            
            return total_processed / time_windows if time_windows > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _get_fallback_metrics(self) -> Tuple[float, float]:
        """Get fallback CPU and memory metrics."""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            return cpu_percent, memory_percent
        except Exception:
            return 50.0, 50.0  # Safe defaults
    
    # =============================================================================
    # SCALING DECISION ENGINE
    # =============================================================================
    
    def evaluate_scaling_need(self, load_manager=None) -> ScalingAction:
        """Evaluate if scaling is needed and return recommended action."""
        try:
            current_time = datetime.utcnow()
            
            # Get current configuration
            config = self.scaling_configurations[self.current_environment]
            
            # Check if scaling is enabled
            if not config.enabled:
                return ScalingAction(
                    timestamp=current_time,
                    action_type='maintain',
                    current_instances=self.current_instances,
                    target_instances=self.current_instances,
                    trigger_reason='Auto-scaling disabled',
                    confidence=1.0,
                    estimated_impact={'status': 'no_change'},
                    configuration_used=config.name
                )
            
            # Collect current metrics
            current_metrics = self.collect_scaling_metrics(load_manager)
            
            # Check cooldown periods
            if self._is_in_cooldown(config):
                return ScalingAction(
                    timestamp=current_time,
                    action_type='maintain',
                    current_instances=self.current_instances,
                    target_instances=self.current_instances,
                    trigger_reason='In cooldown period',
                    confidence=0.8,
                    estimated_impact={'status': 'cooldown_active'},
                    configuration_used=config.name
                )
            
            # Evaluate scaling conditions
            scale_up_needed = self._evaluate_scale_up_conditions(current_metrics, config)
            scale_down_needed = self._evaluate_scale_down_conditions(current_metrics, config)
            
            if scale_up_needed['needed'] and self.current_instances < config.max_instances:
                target_instances = min(
                    self.current_instances + self._calculate_scale_increment(current_metrics, config),
                    config.max_instances
                )
                
                return ScalingAction(
                    timestamp=current_time,
                    action_type='scale_up',
                    current_instances=self.current_instances,
                    target_instances=target_instances,
                    trigger_reason=scale_up_needed['reason'],
                    confidence=scale_up_needed['confidence'],
                    estimated_impact=self._estimate_scaling_impact('scale_up', target_instances, current_metrics),
                    configuration_used=config.name
                )
                
            elif scale_down_needed['needed'] and self.current_instances > config.min_instances:
                target_instances = max(
                    self.current_instances - self._calculate_scale_decrement(current_metrics, config),
                    config.min_instances
                )
                
                return ScalingAction(
                    timestamp=current_time,
                    action_type='scale_down',
                    current_instances=self.current_instances,
                    target_instances=target_instances,
                    trigger_reason=scale_down_needed['reason'],
                    confidence=scale_down_needed['confidence'],
                    estimated_impact=self._estimate_scaling_impact('scale_down', target_instances, current_metrics),
                    configuration_used=config.name
                )
                
            else:
                return ScalingAction(
                    timestamp=current_time,
                    action_type='maintain',
                    current_instances=self.current_instances,
                    target_instances=self.current_instances,
                    trigger_reason='No scaling needed - metrics within target ranges',
                    confidence=0.7,
                    estimated_impact={'status': 'stable'},
                    configuration_used=config.name
                )
                
        except Exception as e:
            logger.error(f"Error evaluating scaling need: {str(e)}")
            return ScalingAction(
                timestamp=datetime.utcnow(),
                action_type='maintain',
                current_instances=self.current_instances,
                target_instances=self.current_instances,
                trigger_reason=f'Error in evaluation: {str(e)}',
                confidence=0.3,
                estimated_impact={'status': 'error'},
                configuration_used=self.current_environment
            )
    
    def _is_in_cooldown(self, config: ScalingConfiguration) -> bool:
        """Check if we're in a cooldown period."""
        try:
            current_time = datetime.utcnow()
            
            # Check scale-up cooldown
            if self.last_scale_up_time:
                time_since_scale_up = (current_time - self.last_scale_up_time).total_seconds()
                if time_since_scale_up < config.scale_up_cooldown:
                    return True
            
            # Check scale-down cooldown
            if self.last_scale_down_time:
                time_since_scale_down = (current_time - self.last_scale_down_time).total_seconds()
                if time_since_scale_down < config.scale_down_cooldown:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _evaluate_scale_up_conditions(self, metrics: ScalingMetrics, config: ScalingConfiguration) -> Dict[str, Any]:
        """Evaluate if scale-up is needed."""
        try:
            reasons = []
            confidence_factors = []
            
            # CPU threshold check
            if metrics.avg_cpu > config.scale_up_threshold:
                reasons.append(f"CPU usage {metrics.avg_cpu:.1f}% > {config.scale_up_threshold}%")
                confidence_factors.append(min(1.0, (metrics.avg_cpu - config.scale_up_threshold) / 20))
            
            # Memory threshold check
            if metrics.avg_memory > config.scale_up_threshold:
                reasons.append(f"Memory usage {metrics.avg_memory:.1f}% > {config.scale_up_threshold}%")
                confidence_factors.append(min(1.0, (metrics.avg_memory - config.scale_up_threshold) / 20))
            
            # Queue length check
            if metrics.max_queue_length > config.queue_length_threshold:
                reasons.append(f"Queue length {metrics.max_queue_length} > {config.queue_length_threshold}")
                confidence_factors.append(min(1.0, metrics.max_queue_length / (config.queue_length_threshold * 2)))
            
            # Response time check
            if metrics.avg_response_time > config.response_time_threshold:
                reasons.append(f"Response time {metrics.avg_response_time:.2f}s > {config.response_time_threshold}s")
                confidence_factors.append(min(1.0, metrics.avg_response_time / (config.response_time_threshold * 2)))
            
            # Historical trend analysis
            trend_factor = self._analyze_load_trend()
            if trend_factor > 0.7:
                reasons.append("Increasing load trend detected")
                confidence_factors.append(trend_factor)
            
            # Determine if scale-up is needed
            needed = len(reasons) >= config.evaluation_periods
            confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
            
            return {
                'needed': needed,
                'reason': '; '.join(reasons) if reasons else 'No scale-up triggers',
                'confidence': round(confidence, 3)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating scale-up conditions: {str(e)}")
            return {'needed': False, 'reason': f'Error: {str(e)}', 'confidence': 0.0}
    
    def _evaluate_scale_down_conditions(self, metrics: ScalingMetrics, config: ScalingConfiguration) -> Dict[str, Any]:
        """Evaluate if scale-down is needed."""
        try:
            reasons = []
            confidence_factors = []
            
            # CPU threshold check
            if metrics.peak_cpu < config.scale_down_threshold:
                reasons.append(f"Peak CPU {metrics.peak_cpu:.1f}% < {config.scale_down_threshold}%")
                confidence_factors.append(min(1.0, (config.scale_down_threshold - metrics.peak_cpu) / 20))
            
            # Memory threshold check
            if metrics.peak_memory < config.scale_down_threshold:
                reasons.append(f"Peak memory {metrics.peak_memory:.1f}% < {config.scale_down_threshold}%")
                confidence_factors.append(min(1.0, (config.scale_down_threshold - metrics.peak_memory) / 20))
            
            # Queue length check (should be consistently low)
            if metrics.avg_queue_length < config.queue_length_threshold / 2:
                reasons.append(f"Average queue length {metrics.avg_queue_length:.1f} < {config.queue_length_threshold / 2}")
                confidence_factors.append(0.8)
            
            # Response time check
            if metrics.avg_response_time < config.response_time_threshold / 2:
                reasons.append(f"Response time {metrics.avg_response_time:.2f}s < {config.response_time_threshold / 2}s")
                confidence_factors.append(0.8)
            
            # Historical trend analysis
            trend_factor = self._analyze_load_trend()
            if trend_factor < -0.5:
                reasons.append("Decreasing load trend detected")
                confidence_factors.append(abs(trend_factor))
            
            # Safety checks - don't scale down if error rate is high
            if metrics.error_rate > 0.05:  # > 5% error rate
                return {'needed': False, 'reason': f'High error rate {metrics.error_rate:.1%}', 'confidence': 0.0}
            
            # Determine if scale-down is needed
            needed = len(reasons) >= config.evaluation_periods and self.current_instances > config.min_instances
            confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
            
            return {
                'needed': needed,
                'reason': '; '.join(reasons) if reasons else 'No scale-down triggers',
                'confidence': round(confidence, 3)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating scale-down conditions: {str(e)}")
            return {'needed': False, 'reason': f'Error: {str(e)}', 'confidence': 0.0}
    
    def _analyze_load_trend(self) -> float:
        """Analyze load trend over recent history."""
        try:
            if len(self.scaling_metrics_history) < 5:
                return 0.0  # Not enough data
            
            # Get recent metrics for trend analysis
            recent_metrics = list(self.scaling_metrics_history)[-10:]
            
            # Calculate trend for CPU and memory
            cpu_values = [m.avg_cpu for m in recent_metrics]
            memory_values = [m.avg_memory for m in recent_metrics]
            
            cpu_trend = self._calculate_linear_trend(cpu_values)
            memory_trend = self._calculate_linear_trend(memory_values)
            
            # Combined trend factor
            combined_trend = (cpu_trend + memory_trend) / 2
            
            return max(-1.0, min(1.0, combined_trend))
            
        except Exception:
            return 0.0
    
    def _calculate_linear_trend(self, values: List[float]) -> float:
        """Calculate linear trend for a series of values."""
        try:
            if len(values) < 3:
                return 0.0
            
            n = len(values)
            x_sum = sum(range(n))
            y_sum = sum(values)
            xy_sum = sum(i * values[i] for i in range(n))
            x2_sum = sum(i * i for i in range(n))
            
            # Calculate slope (trend)
            denominator = n * x2_sum - x_sum * x_sum
            if denominator == 0:
                return 0.0
                
            slope = (n * xy_sum - x_sum * y_sum) / denominator
            
            # Normalize slope to a reasonable range
            return slope / 10  # Adjust normalization factor as needed
            
        except Exception:
            return 0.0
    
    def _calculate_scale_increment(self, metrics: ScalingMetrics, config: ScalingConfiguration) -> int:
        """Calculate how many instances to add when scaling up."""
        try:
            # Base increment
            increment = 1
            
            # Increase increment for severe conditions
            if metrics.avg_cpu > 90 or metrics.avg_memory > 90:
                increment = 2
            elif metrics.max_queue_length > config.queue_length_threshold * 3:
                increment = 2
            elif metrics.avg_response_time > config.response_time_threshold * 2:
                increment = 2
            
            return increment
            
        except Exception:
            return 1
    
    def _calculate_scale_decrement(self, metrics: ScalingMetrics, config: ScalingConfiguration) -> int:
        """Calculate how many instances to remove when scaling down."""
        try:
            # Conservative scale-down - typically 1 instance at a time
            decrement = 1
            
            # Only scale down multiple instances if load is very low
            if (metrics.peak_cpu < config.scale_down_threshold / 2 and 
                metrics.peak_memory < config.scale_down_threshold / 2 and
                metrics.max_queue_length == 0):
                decrement = min(2, self.current_instances - config.min_instances)
            
            return decrement
            
        except Exception:
            return 1
    
    def _estimate_scaling_impact(self, action_type: str, target_instances: int, metrics: ScalingMetrics) -> Dict[str, Any]:
        """Estimate the impact of a scaling action."""
        try:
            current_load_per_instance = {
                'cpu': metrics.avg_cpu / self.current_instances if self.current_instances > 0 else metrics.avg_cpu,
                'memory': metrics.avg_memory / self.current_instances if self.current_instances > 0 else metrics.avg_memory
            }
            
            if action_type == 'scale_up':
                # Estimate load distribution after scaling up
                new_cpu_per_instance = (metrics.avg_cpu * self.current_instances) / target_instances
                new_memory_per_instance = (metrics.avg_memory * self.current_instances) / target_instances
                
                estimated_improvement = {
                    'cpu_reduction': metrics.avg_cpu - new_cpu_per_instance,
                    'memory_reduction': metrics.avg_memory - new_memory_per_instance,
                    'queue_processing_improvement': target_instances / self.current_instances,
                    'response_time_improvement': max(0.5, 1 - (0.2 * (target_instances - self.current_instances)))
                }
                
                return {
                    'action': 'scale_up',
                    'instances_change': target_instances - self.current_instances,
                    'estimated_cpu_per_instance': round(new_cpu_per_instance, 2),
                    'estimated_memory_per_instance': round(new_memory_per_instance, 2),
                    'improvements': estimated_improvement
                }
                
            elif action_type == 'scale_down':
                # Estimate load increase after scaling down
                new_cpu_per_instance = (metrics.avg_cpu * self.current_instances) / target_instances
                new_memory_per_instance = (metrics.avg_memory * self.current_instances) / target_instances
                
                estimated_impact = {
                    'cpu_increase': new_cpu_per_instance - metrics.avg_cpu,
                    'memory_increase': new_memory_per_instance - metrics.avg_memory,
                    'queue_processing_reduction': target_instances / self.current_instances,
                    'response_time_impact': 1 + (0.1 * (self.current_instances - target_instances))
                }
                
                return {
                    'action': 'scale_down',
                    'instances_change': self.current_instances - target_instances,
                    'estimated_cpu_per_instance': round(new_cpu_per_instance, 2),
                    'estimated_memory_per_instance': round(new_memory_per_instance, 2),
                    'impacts': estimated_impact
                }
                
            else:
                return {'action': 'maintain', 'status': 'no_change'}
                
        except Exception as e:
            logger.error(f"Error estimating scaling impact: {str(e)}")
            return {'action': action_type, 'error': str(e)}
    
    # =============================================================================
    # SCALING ACTION EXECUTION
    # =============================================================================
    
    def execute_scaling_action(self, action: ScalingAction) -> Dict[str, Any]:
        """Execute a scaling action (in production, this would call cloud APIs)."""
        try:
            if action.action_type == 'maintain':
                return {
                    'success': True,
                    'action': 'maintain',
                    'message': 'No scaling action needed',
                    'current_instances': self.current_instances
                }
            
            # Log the scaling action
            logger.info(f"Executing scaling action: {action.action_type} from {action.current_instances} to {action.target_instances}")
            
            # Record the action
            self.scaling_actions_history.append(action)
            
            # Update instance count
            old_instances = self.current_instances
            self.current_instances = action.target_instances
            
            # Update timing for cooldown tracking
            current_time = datetime.utcnow()
            if action.action_type == 'scale_up':
                self.last_scale_up_time = current_time
            elif action.action_type == 'scale_down':
                self.last_scale_down_time = current_time
            
            # Store for effectiveness tracking
            self._track_scaling_effectiveness(action)
            
            # In production, here you would call cloud provider APIs:
            # - AWS Auto Scaling Groups
            # - Kubernetes HPA
            # - Railway scaling
            # - etc.
            
            return {
                'success': True,
                'action': action.action_type,
                'message': f'Scaled from {old_instances} to {action.target_instances} instances',
                'old_instances': old_instances,
                'new_instances': action.target_instances,
                'reason': action.trigger_reason,
                'confidence': action.confidence,
                'timestamp': current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing scaling action: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action': action.action_type,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _track_scaling_effectiveness(self, action: ScalingAction):
        """Track the effectiveness of scaling actions for learning."""
        try:
            effectiveness_record = {
                'timestamp': action.timestamp.isoformat(),
                'action_type': action.action_type,
                'instances_change': action.target_instances - action.current_instances,
                'trigger_reason': action.trigger_reason,
                'confidence': action.confidence,
                'pre_scaling_metrics': None,  # Will be filled when we measure post-scaling
                'post_scaling_metrics': None,
                'effectiveness_score': None
            }
            
            self.scaling_effectiveness.append(effectiveness_record)
            
        except Exception as e:
            logger.error(f"Error tracking scaling effectiveness: {str(e)}")
    
    # =============================================================================
    # CONFIGURATION MANAGEMENT
    # =============================================================================
    
    def update_scaling_configuration(self, environment: str, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update scaling configuration for an environment."""
        try:
            if environment not in self.scaling_configurations:
                return {
                    'success': False,
                    'error': f'Unknown environment: {environment}',
                    'available_environments': list(self.scaling_configurations.keys())
                }
            
            config = self.scaling_configurations[environment]
            updated_fields = []
            
            # Update configuration fields
            for field, value in config_updates.items():
                if hasattr(config, field):
                    old_value = getattr(config, field)
                    setattr(config, field, value)
                    updated_fields.append(f'{field}: {old_value} -> {value}')
                else:
                    logger.warning(f"Unknown configuration field: {field}")
            
            logger.info(f"Updated scaling configuration for {environment}: {', '.join(updated_fields)}")
            
            return {
                'success': True,
                'environment': environment,
                'updated_fields': updated_fields,
                'new_configuration': config.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error updating scaling configuration: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_scaling_configuration(self, environment: str = None) -> Dict[str, Any]:
        """Get scaling configuration for an environment."""
        try:
            if environment:
                if environment not in self.scaling_configurations:
                    return {
                        'error': f'Unknown environment: {environment}',
                        'available_environments': list(self.scaling_configurations.keys())
                    }
                return self.scaling_configurations[environment].to_dict()
            else:
                # Return all configurations
                return {
                    env: config.to_dict() 
                    for env, config in self.scaling_configurations.items()
                }
                
        except Exception as e:
            logger.error(f"Error getting scaling configuration: {str(e)}")
            return {'error': str(e)}
    
    # =============================================================================
    # MONITORING AND REPORTING
    # =============================================================================
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status and recent actions."""
        try:
            config = self.scaling_configurations[self.current_environment]
            current_time = datetime.utcnow()
            
            # Check cooldown status
            in_scale_up_cooldown = False
            in_scale_down_cooldown = False
            
            if self.last_scale_up_time:
                time_since_scale_up = (current_time - self.last_scale_up_time).total_seconds()
                in_scale_up_cooldown = time_since_scale_up < config.scale_up_cooldown
            
            if self.last_scale_down_time:
                time_since_scale_down = (current_time - self.last_scale_down_time).total_seconds()
                in_scale_down_cooldown = time_since_scale_down < config.scale_down_cooldown
            
            # Recent actions
            recent_actions = [
                action.to_dict() for action in list(self.scaling_actions_history)[-5:]
            ]
            
            return {
                'timestamp': current_time.isoformat(),
                'current_environment': self.current_environment,
                'current_instances': self.current_instances,
                'scaling_enabled': config.enabled,
                'instance_limits': {
                    'min': config.min_instances,
                    'max': config.max_instances
                },
                'cooldown_status': {
                    'scale_up_cooldown': in_scale_up_cooldown,
                    'scale_down_cooldown': in_scale_down_cooldown,
                    'last_scale_up': self.last_scale_up_time.isoformat() if self.last_scale_up_time else None,
                    'last_scale_down': self.last_scale_down_time.isoformat() if self.last_scale_down_time else None
                },
                'recent_actions': recent_actions,
                'metrics_history_count': len(self.scaling_metrics_history),
                'actions_history_count': len(self.scaling_actions_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting scaling status: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_scaling_metrics_history(self, hours: int = 1) -> Dict[str, Any]:
        """Get scaling metrics history for analysis."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter metrics by time
            filtered_metrics = [
                m.to_dict() for m in self.scaling_metrics_history
                if m.timestamp >= cutoff_time
            ]
            
            # Calculate summary statistics
            if filtered_metrics:
                cpu_values = [m['avg_cpu'] for m in filtered_metrics]
                memory_values = [m['avg_memory'] for m in filtered_metrics]
                
                summary = {
                    'avg_cpu': sum(cpu_values) / len(cpu_values),
                    'max_cpu': max(cpu_values),
                    'min_cpu': min(cpu_values),
                    'avg_memory': sum(memory_values) / len(memory_values),
                    'max_memory': max(memory_values),
                    'min_memory': min(memory_values)
                }
            else:
                summary = {}
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'hours_requested': hours,
                'metrics_count': len(filtered_metrics),
                'summary': summary,
                'metrics': filtered_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting scaling metrics history: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# =============================================================================
# GLOBAL AUTO-SCALING SERVICE INSTANCE
# =============================================================================

auto_scaling_service = AutoScalingConfigurationService()
