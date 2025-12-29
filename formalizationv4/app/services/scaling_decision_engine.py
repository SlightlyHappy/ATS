"""
Smart Resource Scaling - Scaling Decision Engine
Makes intelligent scaling decisions based on system metrics and rules.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from app.services.resource_monitor import resource_monitor

logger = logging.getLogger(__name__)

class ScalingDecisionEngine:
    """Makes intelligent scaling decisions based on system metrics and rules."""
    
    def __init__(self):
        self.scaling_rules = {
            'scale_up_conditions': [
                {
                    'name': 'high_queue_length',
                    'condition': lambda m: m['queue_length'] > 20,
                    'weight': 0.4,
                    'max_workers_increase': 2
                },
                {
                    'name': 'high_cpu_sustained',
                    'condition': lambda m: resource_monitor.is_sustained_high_cpu(m, threshold=0.8, duration=300),
                    'weight': 0.3,
                    'max_workers_increase': 1
                },
                {
                    'name': 'low_memory_pressure',
                    'condition': lambda m: m['memory']['percent'] < 70,
                    'weight': 0.2,
                    'max_workers_increase': 3
                },
                {
                    'name': 'peak_traffic_hours',
                    'condition': lambda m: resource_monitor.is_peak_hours(),
                    'weight': 0.1,
                    'max_workers_increase': 1
                }
            ],
            'scale_down_conditions': [
                {
                    'name': 'low_queue_length',
                    'condition': lambda m: m['queue_length'] < 3,
                    'weight': 0.4,
                    'min_workers_maintained': 2
                },
                {
                    'name': 'low_cpu_sustained',
                    'condition': lambda m: resource_monitor.is_sustained_low_cpu(m, threshold=0.3, duration=600),
                    'weight': 0.3,
                    'min_workers_maintained': 2
                },
                {
                    'name': 'off_peak_hours',
                    'condition': lambda m: resource_monitor.is_off_peak_hours(),
                    'weight': 0.2,
                    'min_workers_maintained': 1
                },
                {
                    'name': 'memory_available',
                    'condition': lambda m: m['memory']['percent'] < 50,
                    'weight': 0.1,
                    'min_workers_maintained': 2
                }
            ]
        }
        self.scaling_history = []
        self.last_scaling_decision = None
        self.cooldown_period = 300  # 5 minutes cooldown between scaling decisions
    
    async def make_scaling_decision(self, current_metrics: Dict[str, Any], worker_count: int) -> Dict[str, Any]:
        """Make intelligent scaling decisions based on multiple factors."""
        try:
            # Check cooldown period
            if self._in_cooldown_period():
                return {
                    'action': 'maintain', 
                    'target_workers': worker_count, 
                    'confidence': 0.5,
                    'reason': 'Cooldown period active'
                }
            
            # Calculate scale-up score
            scale_up_score = 0
            max_increase = 0
            triggered_up_rules = []
            
            for rule in self.scaling_rules['scale_up_conditions']:
                try:
                    if rule['condition'](current_metrics):
                        scale_up_score += rule['weight']
                        max_increase = max(max_increase, rule['max_workers_increase'])
                        triggered_up_rules.append(rule['name'])
                except Exception as e:
                    logger.warning(f"Error evaluating scale-up rule '{rule['name']}': {str(e)}")
            
            # Calculate scale-down score
            scale_down_score = 0
            min_workers = 6  # Default minimum
            triggered_down_rules = []
            
            for rule in self.scaling_rules['scale_down_conditions']:
                try:
                    if rule['condition'](current_metrics):
                        scale_down_score += rule['weight']
                        min_workers = min(min_workers, rule['min_workers_maintained'])
                        triggered_down_rules.append(rule['name'])
                except Exception as e:
                    logger.warning(f"Error evaluating scale-down rule '{rule['name']}': {str(e)}")
            
            # Make decision with hysteresis (different thresholds for up/down)
            decision_threshold_up = 0.6
            decision_threshold_down = 0.6
            
            if scale_up_score > decision_threshold_up and worker_count < 8:  # Max 8 workers
                new_workers = min(worker_count + max_increase, 8)
                decision = {
                    'action': 'scale_up', 
                    'target_workers': new_workers, 
                    'confidence': scale_up_score,
                    'triggered_rules': triggered_up_rules,
                    'reason': f"Scale-up score: {scale_up_score:.2f}, triggered rules: {', '.join(triggered_up_rules)}"
                }
                
            elif scale_down_score > decision_threshold_down and worker_count > min_workers:
                new_workers = max(worker_count - 1, min_workers)
                decision = {
                    'action': 'scale_down', 
                    'target_workers': new_workers, 
                    'confidence': scale_down_score,
                    'triggered_rules': triggered_down_rules,
                    'reason': f"Scale-down score: {scale_down_score:.2f}, triggered rules: {', '.join(triggered_down_rules)}"
                }
                
            else:
                decision = {
                    'action': 'maintain', 
                    'target_workers': worker_count, 
                    'confidence': 0.5,
                    'triggered_rules': [],
                    'reason': f"No action needed. Up score: {scale_up_score:.2f}, Down score: {scale_down_score:.2f}"
                }
            
            # Record the decision
            await self._record_scaling_decision(decision, current_metrics, worker_count)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error making scaling decision: {str(e)}")
            return {
                'action': 'maintain', 
                'target_workers': worker_count, 
                'confidence': 0.0,
                'reason': f"Error in decision making: {str(e)}"
            }
    
    def _in_cooldown_period(self) -> bool:
        """Check if we're in a cooldown period after the last scaling decision."""
        if not self.last_scaling_decision:
            return False
        
        time_since_last = (datetime.utcnow() - self.last_scaling_decision['timestamp']).total_seconds()
        return time_since_last < self.cooldown_period
    
    async def _record_scaling_decision(self, decision: Dict[str, Any], metrics: Dict[str, Any], current_workers: int):
        """Record scaling decision for analysis and cooldown."""
        try:
            decision_record = {
                'timestamp': datetime.utcnow(),
                'decision': decision,
                'metrics_snapshot': {
                    'cpu_percent': metrics['cpu']['percent'],
                    'memory_percent': metrics['memory']['percent'],
                    'queue_length': metrics['queue_length'],
                    'processing_count': metrics['processing_count']
                },
                'current_workers': current_workers
            }
            
            self.scaling_history.append(decision_record)
            
            # Keep only last 24 hours of decisions
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.scaling_history = [
                record for record in self.scaling_history 
                if record['timestamp'] > cutoff_time
            ]
            
            # Update last decision timestamp if action was taken
            if decision['action'] != 'maintain':
                self.last_scaling_decision = decision_record
                logger.info(f"Scaling decision recorded: {decision['action']} to {decision['target_workers']} workers. Reason: {decision['reason']}")
                
        except Exception as e:
            logger.error(f"Error recording scaling decision: {str(e)}")
    
    async def evaluate_custom_condition(self, condition_name: str, metrics: Dict[str, Any]) -> bool:
        """Evaluate custom scaling conditions."""
        try:
            if condition_name == 'queue_overwhelmed':
                # Queue is overwhelmed if length > 50 and processing efficiency < 0.3
                return (metrics['queue_length'] > 50 and 
                        metrics.get('queue_efficiency', 0) < 0.3)
            
            elif condition_name == 'memory_pressure':
                # Memory pressure if >85% for last 2 minutes
                recent_metrics = resource_monitor.get_recent_metrics(2)
                if len(recent_metrics) < 4:  # Need at least 4 data points
                    return False
                high_memory_count = sum(1 for m in recent_metrics if m['memory']['percent'] > 85)
                return high_memory_count / len(recent_metrics) > 0.75
            
            elif condition_name == 'processing_bottleneck':
                # Bottleneck if processing count hasn't changed in 5 minutes despite queue
                recent_metrics = resource_monitor.get_recent_metrics(5)
                if len(recent_metrics) < 10:
                    return False
                
                processing_counts = [m['processing_count'] for m in recent_metrics]
                queue_lengths = [m['queue_length'] for m in recent_metrics]
                
                # Check if processing is stagnant while queue exists
                processing_variance = max(processing_counts) - min(processing_counts)
                avg_queue_length = sum(queue_lengths) / len(queue_lengths)
                
                return processing_variance <= 1 and avg_queue_length > 10
            
            else:
                logger.warning(f"Unknown custom condition: {condition_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating custom condition '{condition_name}': {str(e)}")
            return False
    
    def get_scaling_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get scaling analytics for the specified time period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            relevant_decisions = [
                record for record in self.scaling_history 
                if record['timestamp'] > cutoff_time
            ]
            
            if not relevant_decisions:
                return {
                    'total_decisions': 0,
                    'scale_ups': 0,
                    'scale_downs': 0,
                    'maintains': 0,
                    'average_confidence': 0,
                    'most_triggered_rules': []
                }
            
            # Analyze decisions
            scale_ups = sum(1 for r in relevant_decisions if r['decision']['action'] == 'scale_up')
            scale_downs = sum(1 for r in relevant_decisions if r['decision']['action'] == 'scale_down')
            maintains = sum(1 for r in relevant_decisions if r['decision']['action'] == 'maintain')
            
            # Calculate average confidence
            confidences = [r['decision']['confidence'] for r in relevant_decisions]
            avg_confidence = sum(confidences) / len(confidences)
            
            # Count most triggered rules
            all_triggered_rules = []
            for record in relevant_decisions:
                all_triggered_rules.extend(record['decision'].get('triggered_rules', []))
            
            rule_counts = {}
            for rule in all_triggered_rules:
                rule_counts[rule] = rule_counts.get(rule, 0) + 1
            
            most_triggered = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_decisions': len(relevant_decisions),
                'scale_ups': scale_ups,
                'scale_downs': scale_downs,
                'maintains': maintains,
                'average_confidence': avg_confidence,
                'most_triggered_rules': most_triggered,
                'scaling_frequency': len(relevant_decisions) / max(hours, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting scaling analytics: {str(e)}")
            return {'error': str(e)}
    
    async def update_scaling_rules(self, new_rules: Dict[str, Any]):
        """Update scaling rules dynamically."""
        try:
            # Validate new rules structure
            required_keys = ['scale_up_conditions', 'scale_down_conditions']
            if not all(key in new_rules for key in required_keys):
                raise ValueError(f"New rules must contain keys: {required_keys}")
            
            # Backup current rules
            old_rules = self.scaling_rules.copy()
            
            # Update rules
            self.scaling_rules = new_rules
            
            logger.info("Scaling rules updated successfully")
            
            # Record the update
            await self._record_scaling_decision(
                {
                    'action': 'rules_updated',
                    'target_workers': 0,
                    'confidence': 1.0,
                    'reason': 'Scaling rules updated by admin'
                },
                {},
                0
            )
            
        except Exception as e:
            logger.error(f"Error updating scaling rules: {str(e)}")
            # Restore old rules on error
            if 'old_rules' in locals():
                self.scaling_rules = old_rules
            raise

# Global instance
scaling_decision_engine = ScalingDecisionEngine()
