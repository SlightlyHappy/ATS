"""
Dynamic Load-Aware Processing System - Phase 2.1 Implementation
Integrates with existing performance monitoring and resource management to provide
intelligent load-based processing decisions and auto-scaling capabilities.
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import threading

from flask import current_app
from app import db
from sqlalchemy import text

logger = logging.getLogger(__name__)

# =============================================================================
# LOAD MANAGEMENT DATA CLASSES
# =============================================================================

@dataclass
class LoadMetrics:
    """Comprehensive load metrics for decision making."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    queue_length: int
    active_connections: int
    processing_count: int
    response_time_avg: float
    error_rate: float
    load_classification: str
    available_capacity: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'queue_length': self.queue_length,
            'active_connections': self.active_connections,
            'processing_count': self.processing_count,
            'response_time_avg': self.response_time_avg,
            'error_rate': self.error_rate,
            'load_classification': self.load_classification,
            'available_capacity': self.available_capacity
        }

@dataclass
class ProcessingStrategy:
    """Processing strategy based on current load conditions."""
    name: str
    max_concurrent: int
    priority_queues: List[str]
    batch_size: int
    timeout_multiplier: float
    agent_limit: int
    cache_priority: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'max_concurrent': self.max_concurrent,
            'priority_queues': self.priority_queues,
            'batch_size': self.batch_size,
            'timeout_multiplier': self.timeout_multiplier,
            'agent_limit': self.agent_limit,
            'cache_priority': self.cache_priority
        }

@dataclass
class LoadDecision:
    """Load-based processing decision."""
    timestamp: datetime
    load_metrics: LoadMetrics
    strategy: ProcessingStrategy
    recommendation: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'load_metrics': self.load_metrics.to_dict(),
            'strategy': self.strategy.to_dict(),
            'recommendation': self.recommendation,
            'confidence': self.confidence
        }

# =============================================================================
# DYNAMIC LOAD MANAGER
# =============================================================================

class DynamicLoadManager:
    """
    Intelligent load management system that makes real-time processing decisions
    based on system metrics and performance data.
    """
    
    def __init__(self, app=None):
        self.app = app
        
        # Load classification thresholds
        self.load_thresholds = {
            'critical': {'cpu': 95, 'memory': 90, 'queue': 50, 'response_time': 5.0},
            'high': {'cpu': 80, 'memory': 80, 'queue': 20, 'response_time': 2.0},
            'medium': {'cpu': 60, 'memory': 70, 'queue': 10, 'response_time': 1.0},
            'normal': {'cpu': 40, 'memory': 50, 'queue': 5, 'response_time': 0.5},
            'low': {'cpu': 20, 'memory': 30, 'queue': 2, 'response_time': 0.3}
        }
        
        # Processing strategies for each load level
        self.processing_strategies = {
            'critical': ProcessingStrategy(
                name='critical_load',
                max_concurrent=1,
                priority_queues=['critical'],
                batch_size=1,
                timeout_multiplier=0.5,
                agent_limit=1,
                cache_priority='high'
            ),
            'high': ProcessingStrategy(
                name='high_load',
                max_concurrent=2,
                priority_queues=['critical', 'admin'],
                batch_size=1,
                timeout_multiplier=0.7,
                agent_limit=2,
                cache_priority='high'
            ),
            'medium': ProcessingStrategy(
                name='medium_load',
                max_concurrent=4,
                priority_queues=['critical', 'admin', 'premium', 'normal'],
                batch_size=2,
                timeout_multiplier=0.9,
                agent_limit=4,
                cache_priority='medium'
            ),
            'normal': ProcessingStrategy(
                name='normal_load',
                max_concurrent=6,
                priority_queues=['critical', 'admin', 'premium', 'normal', 'background'],
                batch_size=3,
                timeout_multiplier=1.0,
                agent_limit=6,
                cache_priority='medium'
            ),
            'low': ProcessingStrategy(
                name='low_load',
                max_concurrent=8,
                priority_queues=['critical', 'admin', 'premium', 'normal', 'background', 'batch'],
                batch_size=4,
                timeout_multiplier=1.2,
                agent_limit=8,
                cache_priority='low'
            )
        }
        
        # Decision history and metrics
        self.decision_history = deque(maxlen=1000)
        self.load_metrics_history = deque(maxlen=2880)  # 24 hours at 30-second intervals
        
        # Processing state
        self.current_strategy = self.processing_strategies['normal']
        self.active_processing = 0
        self.last_decision_time = datetime.utcnow()
        self.decision_cooldown = 30  # seconds
        
        # Background processing
        self._manager_active = False
        self._manager_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="load_manager")
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the load manager with Flask app."""
        self.app = app
        
        # Load configuration from app
        config = app.config
        self.decision_cooldown = config.get('LOAD_DECISION_COOLDOWN', 30)
        
        # Update thresholds from config
        if config.get('LOAD_THRESHOLDS'):
            self.load_thresholds.update(config['LOAD_THRESHOLDS'])
        
        # Start background load management
        self.start_load_management()
        
        logger.info("Dynamic Load Manager initialized")
    
    # =============================================================================
    # LOAD MANAGEMENT CONTROL
    # =============================================================================
    
    def start_load_management(self):
        """Start background load management."""
        if self._manager_active:
            return
        
        self._manager_active = True
        self._manager_executor.submit(self._load_management_loop)
        
        logger.info("Dynamic load management started")
    
    def stop_load_management(self):
        """Stop background load management."""
        self._manager_active = False
        logger.info("Dynamic load management stopped")
    
    # =============================================================================
    # LOAD METRICS COLLECTION
    # =============================================================================
    
    def collect_current_load_metrics(self) -> LoadMetrics:
        """Collect current system load metrics."""
        try:
            current_time = datetime.utcnow()
            
            # Get performance monitor data if available
            performance_monitor = getattr(self.app, 'performance_monitor', None)
            
            if performance_monitor:
                # Use Phase 1 performance monitoring service
                current_metrics = performance_monitor.collect_current_metrics()
                
                system_data = current_metrics.get('system', {}) or {}
                app_data = current_metrics.get('application', {}) or {}
                db_data = current_metrics.get('database', {}) or {}
                
                cpu_usage = system_data.get('cpu_usage', 0) or 0
                memory_usage = system_data.get('memory_usage', 0) or 0
                # Application queue is nested under 'queue' in ApplicationMetrics.to_dict
                queue_length = (app_data.get('queue', {}) or {}).get('length', 0) or 0
                # Active DB connections are under database.connections.active
                active_connections = (db_data.get('connections', {}) or {}).get('active', 0) or 0
                # processing_count not provided by PM; keep 0 for now
                processing_count = 0
                response_time_avg = app_data.get('avg_response_time', 0) or 0
                # Performance monitor returns error_rate as percentage; normalize to 0-1 fraction
                error_rate_pct = app_data.get('error_rate', 0) or 0
                error_rate = (error_rate_pct / 100.0) if error_rate_pct > 1 else error_rate_pct
            
            else:
                # Fallback to basic metrics collection
                cpu_usage, memory_usage = self._get_basic_system_metrics()
                queue_length = self._get_queue_length()
                active_connections = 0
                processing_count = 0
                response_time_avg = 0
                error_rate = 0
            
            # Classify load level
            load_classification = self._classify_load(
                cpu_usage, memory_usage, queue_length, response_time_avg
            )
            
            # Calculate available capacity
            available_capacity = self._calculate_available_capacity(
                cpu_usage, memory_usage, queue_length
            )
            
            load_metrics = LoadMetrics(
                timestamp=current_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                queue_length=queue_length,
                active_connections=active_connections,
                processing_count=processing_count,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                load_classification=load_classification,
                available_capacity=available_capacity
            )
            
            # Store in history
            self.load_metrics_history.append(load_metrics)
            
            return load_metrics
            
        except Exception as e:
            logger.error(f"Error collecting load metrics: {str(e)}")
            # Return safe default metrics
            return LoadMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=50.0,
                memory_usage=50.0,
                queue_length=0,
                active_connections=0,
                processing_count=0,
                response_time_avg=1.0,
                error_rate=0.0,
                load_classification='normal',
                available_capacity=0.5
            )
    
    def _get_basic_system_metrics(self) -> Tuple[float, float]:
        """Get basic CPU and memory metrics as fallback."""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            return cpu_usage, memory_usage
        except Exception:
            return 50.0, 50.0  # Safe defaults
    
    def _get_queue_length(self) -> int:
        """Get current queue length."""
        try:
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM analysis_queue 
                WHERE status IN ('pending', 'processing')
            """)).scalar()
            
            return int(result or 0)
        except Exception:
            return 0
    
    def _classify_load(self, cpu: float, memory: float, queue: int, response_time: float) -> str:
        """Classify current system load level."""
        try:
            # Check each load level from most severe to least
            for level in ['critical', 'high', 'medium', 'normal', 'low']:
                thresholds = self.load_thresholds[level]
                
                # Critical: any threshold exceeded
                if level == 'critical':
                    if (cpu >= thresholds['cpu'] or 
                        memory >= thresholds['memory'] or 
                        queue >= thresholds['queue'] or 
                        response_time >= thresholds['response_time']):
                        return level
                
                # Other levels: majority of thresholds exceeded
                else:
                    exceeded_count = 0
                    total_checks = 0
                    
                    if cpu >= thresholds['cpu']:
                        exceeded_count += 1
                    total_checks += 1
                    
                    if memory >= thresholds['memory']:
                        exceeded_count += 1
                    total_checks += 1
                    
                    if queue >= thresholds['queue']:
                        exceeded_count += 1
                    total_checks += 1
                    
                    if response_time >= thresholds['response_time']:
                        exceeded_count += 1
                    total_checks += 1
                    
                    # If more than half the thresholds are exceeded, classify as this level
                    if exceeded_count >= total_checks / 2:
                        return level
            
            return 'low'  # Default to lowest load level
            
        except Exception as e:
            logger.error(f"Error classifying load: {str(e)}")
            return 'normal'
    
    def _calculate_available_capacity(self, cpu: float, memory: float, queue: int) -> float:
        """Calculate available processing capacity (0.0 to 1.0)."""
        try:
            # Calculate capacity based on resource usage
            cpu_capacity = max(0, (100 - cpu) / 100)
            memory_capacity = max(0, (100 - memory) / 100)
            
            # Queue pressure affects capacity
            queue_pressure = min(1.0, queue / 20)  # Normalize queue to 0-1
            queue_capacity = max(0, 1.0 - queue_pressure)
            
            # Weighted average of capacities
            available_capacity = (
                cpu_capacity * 0.4 + 
                memory_capacity * 0.4 + 
                queue_capacity * 0.2
            )
            
            return round(available_capacity, 3)
            
        except Exception:
            return 0.5  # Safe default
    
    # =============================================================================
    # LOAD-AWARE DECISION MAKING
    # =============================================================================
    
    def make_processing_decision(self, force: bool = False) -> LoadDecision:
        """Make intelligent processing decision based on current load."""
        try:
            current_time = datetime.utcnow()
            
            # Check cooldown unless forced
            if not force:
                time_since_last = (current_time - self.last_decision_time).total_seconds()
                if time_since_last < self.decision_cooldown:
                    # Return current strategy without change
                    load_metrics = self.collect_current_load_metrics()
                    return LoadDecision(
                        timestamp=current_time,
                        load_metrics=load_metrics,
                        strategy=self.current_strategy,
                        recommendation='maintaining_current_strategy',
                        confidence=0.8
                    )
            
            # Collect current metrics
            load_metrics = self.collect_current_load_metrics()
            
            # Get strategy for current load level
            new_strategy = self.processing_strategies[load_metrics.load_classification]
            
            # Determine recommendation
            recommendation = self._generate_recommendation(load_metrics, new_strategy)
            
            # Calculate confidence based on metric stability
            confidence = self._calculate_decision_confidence(load_metrics)
            
            # Create decision
            decision = LoadDecision(
                timestamp=current_time,
                load_metrics=load_metrics,
                strategy=new_strategy,
                recommendation=recommendation,
                confidence=confidence
            )
            
            # Update current strategy if high confidence
            if confidence > 0.7:
                self.current_strategy = new_strategy
                self.last_decision_time = current_time
            
            # Store decision in history
            self.decision_history.append(decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error making processing decision: {str(e)}")
            # Return safe default decision
            load_metrics = self.collect_current_load_metrics()
            return LoadDecision(
                timestamp=datetime.utcnow(),
                load_metrics=load_metrics,
                strategy=self.current_strategy,
                recommendation='error_using_current_strategy',
                confidence=0.3
            )
    
    def _generate_recommendation(self, load_metrics: LoadMetrics, strategy: ProcessingStrategy) -> str:
        """Generate human-readable recommendation based on metrics and strategy."""
        try:
            load_level = load_metrics.load_classification
            cpu = load_metrics.cpu_usage
            memory = load_metrics.memory_usage
            queue = load_metrics.queue_length
            
            if load_level == 'critical':
                return f"CRITICAL: Reduce load immediately. CPU: {cpu:.1f}%, Memory: {memory:.1f}%, Queue: {queue}"
            elif load_level == 'high':
                return f"HIGH LOAD: Process only priority items. CPU: {cpu:.1f}%, Memory: {memory:.1f}%"
            elif load_level == 'medium':
                return f"MEDIUM LOAD: Reduced concurrent processing. Queue: {queue} items"
            elif load_level == 'normal':
                return f"NORMAL: Standard processing capacity. System stable"
            else:  # low
                return f"LOW LOAD: Can increase processing capacity. System underutilized"
                
        except Exception:
            return "Unable to generate recommendation due to error"
    
    def _calculate_decision_confidence(self, current_metrics: LoadMetrics) -> float:
        """Calculate confidence in decision based on metric stability."""
        try:
            if len(self.load_metrics_history) < 3:
                return 0.6  # Medium confidence with limited data
            
            # Get recent metrics for stability analysis
            recent_metrics = list(self.load_metrics_history)[-5:]
            
            # Calculate metric variations
            cpu_values = [m.cpu_usage for m in recent_metrics]
            memory_values = [m.memory_usage for m in recent_metrics]
            queue_values = [m.queue_length for m in recent_metrics]
            
            # Calculate coefficient of variation (stability indicator)
            def coeff_variation(values):
                if len(values) < 2:
                    return 0
                mean_val = sum(values) / len(values)
                if mean_val == 0:
                    return 0
                variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
                std_dev = variance ** 0.5
                return std_dev / mean_val
            
            cpu_stability = 1 - min(1.0, coeff_variation(cpu_values))
            memory_stability = 1 - min(1.0, coeff_variation(memory_values))
            queue_stability = 1 - min(1.0, coeff_variation(queue_values))
            
            # Overall confidence
            confidence = (cpu_stability + memory_stability + queue_stability) / 3
            
            # Adjust confidence based on extremes
            if current_metrics.cpu_usage > 90 or current_metrics.memory_usage > 90:
                confidence = max(0.9, confidence)  # High confidence in critical situations
            
            return round(confidence, 3)
            
        except Exception:
            return 0.5  # Default confidence
    
    # =============================================================================
    # AUTO-SCALING INTEGRATION
    # =============================================================================
    
    def get_scaling_recommendation(self) -> Dict[str, Any]:
        """Get recommendations for auto-scaling based on load trends."""
        try:
            if len(self.load_metrics_history) < 10:
                return {
                    'action': 'maintain',
                    'reason': 'insufficient_data',
                    'confidence': 0.3
                }
            
            # Analyze load trends over last 10 minutes
            recent_metrics = list(self.load_metrics_history)[-20:]  # Last 10 minutes
            
            # Calculate trend indicators
            cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_metrics])
            memory_trend = self._calculate_trend([m.memory_usage for m in recent_metrics])
            queue_trend = self._calculate_trend([m.queue_length for m in recent_metrics])
            
            # Current load classification distribution
            load_counts = {}
            for m in recent_metrics:
                load_counts[m.load_classification] = load_counts.get(m.load_classification, 0) + 1
            
            # Determine scaling action
            if load_counts.get('critical', 0) > 3 or load_counts.get('high', 0) > 10:
                return {
                    'action': 'scale_up',
                    'reason': 'sustained_high_load',
                    'confidence': 0.9,
                    'metrics': {
                        'cpu_trend': cpu_trend,
                        'memory_trend': memory_trend,
                        'queue_trend': queue_trend,
                        'load_distribution': load_counts
                    }
                }
            elif load_counts.get('low', 0) > 15 and all(trend < 0.1 for trend in [cpu_trend, memory_trend, queue_trend]):
                return {
                    'action': 'scale_down',
                    'reason': 'sustained_low_load',
                    'confidence': 0.8,
                    'metrics': {
                        'cpu_trend': cpu_trend,
                        'memory_trend': memory_trend,
                        'queue_trend': queue_trend,
                        'load_distribution': load_counts
                    }
                }
            else:
                return {
                    'action': 'maintain',
                    'reason': 'stable_load',
                    'confidence': 0.7,
                    'metrics': {
                        'cpu_trend': cpu_trend,
                        'memory_trend': memory_trend,
                        'queue_trend': queue_trend,
                        'load_distribution': load_counts
                    }
                }
                
        except Exception as e:
            logger.error(f"Error generating scaling recommendation: {str(e)}")
            return {
                'action': 'maintain',
                'reason': f'error: {str(e)}',
                'confidence': 0.2
            }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend indicator for a series of values."""
        try:
            if len(values) < 3:
                return 0.0
            
            # Simple linear trend calculation
            n = len(values)
            x_sum = sum(range(n))
            y_sum = sum(values)
            xy_sum = sum(i * values[i] for i in range(n))
            x2_sum = sum(i * i for i in range(n))
            
            # Calculate slope
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            
            return round(slope, 4)
            
        except Exception:
            return 0.0
    
    # =============================================================================
    # BACKGROUND PROCESSING
    # =============================================================================
    
    def _load_management_loop(self):
        """Background loop for continuous load management."""
        while self._manager_active:
            try:
                if not self.app:
                    logger.warning("Load manager has no app bound; skipping cycle")
                    time.sleep(30)
                    continue
                # Ensure Flask application context for any DB/config access
                with self.app.app_context():
                    # Make processing decision every 30 seconds
                    decision = self.make_processing_decision()
                    
                    # Log significant decisions
                    if decision.load_metrics.load_classification in ['critical', 'high']:
                        logger.warning(f"Load Management: {decision.recommendation}")
                    elif decision.confidence > 0.8:
                        logger.info(f"Load Management: {decision.recommendation}")
                    
                    # Apply processing adjustments if needed
                    self._apply_processing_adjustments(decision)
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in load management loop: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def _apply_processing_adjustments(self, decision: LoadDecision):
        """Apply processing adjustments based on decision."""
        try:
            strategy = decision.strategy
            load_level = decision.load_metrics.load_classification
            
            # Update configuration for other services
            if hasattr(self.app, 'config'):
                # Update concurrent processing limits
                self.app.config['MAX_CONCURRENT_AGENTS'] = strategy.agent_limit
                self.app.config['QUEUE_BATCH_SIZE'] = strategy.batch_size
                self.app.config['LOAD_AWARE_PROCESSING'] = True
                self.app.config['CURRENT_LOAD_LEVEL'] = load_level
                
                # Adjust timeouts based on load
                base_timeout = self.app.config.get('AI_TIMEOUT_SECONDS', 60)
                self.app.config['AI_TIMEOUT_SECONDS'] = int(base_timeout * strategy.timeout_multiplier)
            
            # Signal other services about load changes
            self._notify_services_of_load_change(decision)
            
        except Exception as e:
            logger.error(f"Error applying processing adjustments: {str(e)}")
    
    def _notify_services_of_load_change(self, decision: LoadDecision):
        """Notify other services about load level changes."""
        try:
            # Notify enhanced cache service about cache priority changes
            enhanced_cache = getattr(self.app, 'enhanced_cache', None)
            if enhanced_cache and hasattr(enhanced_cache, 'set_cache_priority'):
                enhanced_cache.set_cache_priority(decision.strategy.cache_priority)
            
            # Could notify queue manager, worker processes, etc.
            logger.debug(f"Notified services of load change to {decision.load_metrics.load_classification}")
            
        except Exception as e:
            logger.error(f"Error notifying services of load change: {str(e)}")
    
    # =============================================================================
    # API METHODS
    # =============================================================================
    
    def get_current_load_status(self) -> Dict[str, Any]:
        """Get current load status and processing strategy."""
        try:
            current_metrics = self.collect_current_load_metrics()
            recent_decision = self.decision_history[-1] if self.decision_history else None
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'current_metrics': current_metrics.to_dict(),
                'current_strategy': self.current_strategy.to_dict(),
                'recent_decision': recent_decision.to_dict() if recent_decision else None,
                'scaling_recommendation': self.get_scaling_recommendation(),
                'decision_history_count': len(self.decision_history),
                'metrics_history_count': len(self.load_metrics_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting load status: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_load_history(self, hours: int = 1) -> Dict[str, Any]:
        """Get load metrics history for analysis."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter metrics by time
            filtered_metrics = [
                m.to_dict() for m in self.load_metrics_history
                if m.timestamp >= cutoff_time
            ]
            
            # Filter decisions by time
            filtered_decisions = [
                d.to_dict() for d in self.decision_history
                if d.timestamp >= cutoff_time
            ]
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'hours_requested': hours,
                'metrics_count': len(filtered_metrics),
                'decisions_count': len(filtered_decisions),
                'load_metrics': filtered_metrics,
                'decisions': filtered_decisions
            }
            
        except Exception as e:
            logger.error(f"Error getting load history: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def force_strategy_change(self, strategy_name: str) -> Dict[str, Any]:
        """Force a specific processing strategy (admin override)."""
        try:
            if strategy_name not in self.processing_strategies:
                return {
                    'success': False,
                    'error': f'Unknown strategy: {strategy_name}',
                    'available_strategies': list(self.processing_strategies.keys())
                }
            
            # Force strategy change
            old_strategy = self.current_strategy.name
            self.current_strategy = self.processing_strategies[strategy_name]
            self.last_decision_time = datetime.utcnow()
            
            # Create decision record
            current_metrics = self.collect_current_load_metrics()
            decision = LoadDecision(
                timestamp=datetime.utcnow(),
                load_metrics=current_metrics,
                strategy=self.current_strategy,
                recommendation=f'Admin override: forced change from {old_strategy} to {strategy_name}',
                confidence=1.0
            )
            
            self.decision_history.append(decision)
            
            # Apply the changes
            self._apply_processing_adjustments(decision)
            
            logger.warning(f"Admin forced strategy change from {old_strategy} to {strategy_name}")
            
            return {
                'success': True,
                'old_strategy': old_strategy,
                'new_strategy': strategy_name,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error forcing strategy change: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# =============================================================================
# GLOBAL LOAD MANAGER INSTANCE
# =============================================================================

dynamic_load_manager = DynamicLoadManager()
