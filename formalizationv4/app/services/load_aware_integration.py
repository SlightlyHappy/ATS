"""
Load-Aware Processing Integration Service - Phase 2.3 Implementation
Integrates dynamic load management and auto-scaling services with existing
performance monitoring to provide unified load-aware processing capabilities.
"""
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import threading

from flask import Blueprint, jsonify, request, current_app, has_app_context

from app.services.dynamic_load_manager import dynamic_load_manager
from app.services.auto_scaling_service import auto_scaling_service

logger = logging.getLogger(__name__)

# =============================================================================
# INTEGRATION SERVICE
# =============================================================================

class LoadAwareProcessingIntegration:
    """
    Integration service that coordinates dynamic load management,
    auto-scaling, and performance monitoring for intelligent processing decisions.
    """
    
    def __init__(self, app=None):
        self.app = app
        
        # Service references
        self.load_manager = dynamic_load_manager
        self.scaling_service = auto_scaling_service
        self.performance_monitor = None
        self.enhanced_cache = None
        
        # Integration state
        self.integration_active = False
        self.last_coordination_time = None
        self.coordination_interval = 60  # seconds
        
        # Integration metrics
        self.coordination_history = []
        self.system_health_status = 'unknown'
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the integration service with Flask app."""
        self.app = app
        
        # Get references to other services
        self.performance_monitor = getattr(app, 'performance_monitor', None)
        self.enhanced_cache = getattr(app, 'enhanced_cache', None)
        
        # Initialize sub-services
        self.load_manager.init_app(app)
        self.scaling_service.init_app(app)
        
        # Start coordination
        self.start_coordination()
        
        logger.info("Load-Aware Processing Integration Service initialized")
    
    # =============================================================================
    # COORDINATION CONTROL
    # =============================================================================
    
    def start_coordination(self):
        """Start coordinated load-aware processing."""
        if self.integration_active:
            return
        
        self.integration_active = True
        
        # Start background coordination
        coordination_thread = threading.Thread(
            target=self._coordination_loop,
            name="load_coordination",
            daemon=True
        )
        coordination_thread.start()
        
        logger.info("Load-aware processing coordination started")
    
    def stop_coordination(self):
        """Stop coordinated load-aware processing."""
        self.integration_active = False
        
        # Stop sub-services
        if hasattr(self.load_manager, 'stop_load_management'):
            self.load_manager.stop_load_management()
        
        logger.info("Load-aware processing coordination stopped")
    
    # =============================================================================
    # COORDINATED PROCESSING DECISIONS
    # =============================================================================
    
    def make_coordinated_processing_decision(self) -> Dict[str, Any]:
        """Make coordinated processing decision using all available services.
        Ensures a Flask app context is active for any framework-bound operations.
        """
        if self.app and not has_app_context():
            try:
                with self.app.app_context():
                    return self._make_coordinated_processing_decision_core()
            except Exception as e:
                logger.error(f"Error making coordinated decision (with app context): {str(e)}")
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': str(e),
                    'system_health': {'overall_status': 'error'},
                    'coordinated_recommendations': {'primary': 'maintain_current_state_due_to_error'}
                }
        # Already in a context or no app required
        return self._make_coordinated_processing_decision_core()

    def _make_coordinated_processing_decision_core(self) -> Dict[str, Any]:
        """Core logic for coordinated processing decision (expects app context if needed)."""
        try:
            current_time = datetime.utcnow()
            # Collect data from all services
            load_decision = self.load_manager.make_processing_decision()
            scaling_action = self.scaling_service.evaluate_scaling_need(self.load_manager)
            # Get performance monitoring data if available
            performance_data = None
            if self.performance_monitor:
                try:
                    if hasattr(self.performance_monitor, 'get_current_status'):
                        performance_data = self.performance_monitor.get_current_status()
                    elif hasattr(self.performance_monitor, 'get_performance_summary'):
                        performance_data = self.performance_monitor.get_performance_summary()
                    else:
                        performance_data = self.performance_monitor.collect_current_metrics()
                except Exception as e:
                    logger.warning(f"Could not get performance data: {str(e)}")
            # Assess overall system health
            system_health = self._assess_system_health(load_decision, scaling_action, performance_data)
            # Generate coordinated recommendations
            recommendations = self._generate_coordinated_recommendations(
                load_decision, scaling_action, system_health
            )
            # Create coordinated decision
            coordinated_decision = {
                'timestamp': current_time.isoformat(),
                'system_health': system_health,
                'load_management': {
                    'load_level': load_decision.load_metrics.load_classification,
                    'strategy': load_decision.strategy.name,
                    'recommendation': load_decision.recommendation,
                    'confidence': load_decision.confidence
                },
                'auto_scaling': {
                    'action': scaling_action.action_type,
                    'current_instances': scaling_action.current_instances,
                    'target_instances': scaling_action.target_instances,
                    'trigger_reason': scaling_action.trigger_reason,
                    'confidence': scaling_action.confidence
                },
                'performance_monitoring': performance_data,
                'coordinated_recommendations': recommendations,
                'next_evaluation': (current_time + timedelta(seconds=self.coordination_interval)).isoformat()
            }
            # Store coordination history (bounded)
            self.coordination_history.append(coordinated_decision)
            if len(self.coordination_history) > 100:
                self.coordination_history.pop(0)
            # Update system health status
            self.system_health_status = system_health['overall_status']
            self.last_coordination_time = current_time
            return coordinated_decision
        except Exception as e:
            logger.error(f"Error making coordinated processing decision: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'system_health': {'overall_status': 'error'},
                'coordinated_recommendations': {'primary': 'maintain_current_state_due_to_error'}
            }

    def _assess_system_health(self, load_decision, scaling_action, performance_data) -> Dict[str, Any]:
        """Assess overall system health based on all available data."""
        try:
            health_indicators = []
            health_scores = []
            
            # Load management health
            load_level = load_decision.load_metrics.load_classification
            if load_level == 'critical':
                health_indicators.append('Critical load detected')
                health_scores.append(0.1)
            elif load_level == 'high':
                health_indicators.append('High load detected')
                health_scores.append(0.3)
            elif load_level == 'medium':
                health_indicators.append('Medium load')
                health_scores.append(0.6)
            elif load_level == 'normal':
                health_indicators.append('Normal load')
                health_scores.append(0.8)
            else:  # low
                health_indicators.append('Low load')
                health_scores.append(0.9)
            
            # Resource utilization health
            cpu_usage = load_decision.load_metrics.cpu_usage
            memory_usage = load_decision.load_metrics.memory_usage
            
            if cpu_usage > 90 or memory_usage > 90:
                health_indicators.append('Critical resource utilization')
                health_scores.append(0.2)
            elif cpu_usage > 80 or memory_usage > 80:
                health_indicators.append('High resource utilization')
                health_scores.append(0.4)
            elif cpu_usage > 60 or memory_usage > 70:
                health_indicators.append('Moderate resource utilization')
                health_scores.append(0.7)
            else:
                health_indicators.append('Healthy resource utilization')
                health_scores.append(0.9)
            
            # Queue health
            queue_length = load_decision.load_metrics.queue_length
            if queue_length > 50:
                health_indicators.append('Critical queue backlog')
                health_scores.append(0.2)
            elif queue_length > 20:
                health_indicators.append('High queue backlog')
                health_scores.append(0.4)
            elif queue_length > 10:
                health_indicators.append('Moderate queue backlog')
                health_scores.append(0.7)
            else:
                health_indicators.append('Healthy queue state')
                health_scores.append(0.9)
            
            # Response time health
            response_time = load_decision.load_metrics.response_time_avg
            if response_time > 5.0:
                health_indicators.append('Critical response times')
                health_scores.append(0.2)
            elif response_time > 2.0:
                health_indicators.append('High response times')
                health_scores.append(0.4)
            elif response_time > 1.0:
                health_indicators.append('Moderate response times')
                health_scores.append(0.7)
            else:
                health_indicators.append('Healthy response times')
                health_scores.append(0.9)
            
            # Error rate health
            error_rate = load_decision.load_metrics.error_rate
            if error_rate > 0.1:  # >10%
                health_indicators.append('Critical error rate')
                health_scores.append(0.1)
            elif error_rate > 0.05:  # >5%
                health_indicators.append('High error rate')
                health_scores.append(0.3)
            elif error_rate > 0.01:  # >1%
                health_indicators.append('Moderate error rate')
                health_scores.append(0.7)
            else:
                health_indicators.append('Healthy error rate')
                health_scores.append(0.9)
            
            # Performance monitoring health
            if performance_data:
                try:
                    if performance_data.get('alerts_count', 0) > 0:
                        health_indicators.append('Performance alerts active')
                        health_scores.append(0.4)
                    else:
                        health_indicators.append('No performance alerts')
                        health_scores.append(0.8)
                except Exception:
                    pass
            
            # Calculate overall health score
            overall_score = sum(health_scores) / len(health_scores) if health_scores else 0.5
            
            # Determine overall status
            if overall_score >= 0.8:
                overall_status = 'healthy'
            elif overall_score >= 0.6:
                overall_status = 'moderate'
            elif overall_score >= 0.4:
                overall_status = 'degraded'
            elif overall_score >= 0.2:
                overall_status = 'critical'
            else:
                overall_status = 'emergency'
            
            return {
                'overall_status': overall_status,
                'overall_score': round(overall_score, 3),
                'health_indicators': health_indicators,
                'detailed_scores': {
                    'load_level': load_level,
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'queue_length': queue_length,
                    'response_time': response_time,
                    'error_rate': error_rate
                }
            }
            
        except Exception as e:
            logger.error(f"Error assessing system health: {str(e)}")
            return {
                'overall_status': 'error',
                'overall_score': 0.0,
                'error': str(e)
            }
    
    def _generate_coordinated_recommendations(self, load_decision, scaling_action, system_health) -> Dict[str, Any]:
        """Generate coordinated recommendations based on all available data."""
        try:
            recommendations = {
                'primary': None,
                'secondary': [],
                'immediate_actions': [],
                'monitoring_focus': [],
                'configuration_adjustments': []
            }
            
            overall_status = system_health.get('overall_status', 'unknown')
            load_level = load_decision.load_metrics.load_classification
            
            # Primary recommendation based on overall system health
            if overall_status == 'emergency':
                recommendations['primary'] = 'emergency_load_shedding'
                recommendations['immediate_actions'] = [
                    'Activate emergency load shedding',
                    'Scale up immediately if possible',
                    'Enable high-priority only processing',
                    'Increase cache TTL to reduce load'
                ]
            elif overall_status == 'critical':
                recommendations['primary'] = 'aggressive_load_reduction'
                recommendations['immediate_actions'] = [
                    'Reduce concurrent processing',
                    'Prioritize critical operations only',
                    'Consider scaling up',
                    'Monitor system closely'
                ]
            elif overall_status == 'degraded':
                recommendations['primary'] = 'moderate_load_adjustment'
                recommendations['immediate_actions'] = [
                    'Adjust processing strategy',
                    'Monitor resource usage',
                    'Prepare for scaling if needed'
                ]
            elif overall_status == 'moderate':
                recommendations['primary'] = 'optimization_opportunity'
                recommendations['secondary'] = [
                    'Fine-tune processing parameters',
                    'Optimize cache usage',
                    'Monitor for trends'
                ]
            else:  # healthy
                recommendations['primary'] = 'maintain_current_state'
                recommendations['secondary'] = [
                    'Continue monitoring',
                    'Consider cost optimizations',
                    'Review performance metrics'
                ]
            
            # Scaling recommendations
            if scaling_action.action_type == 'scale_up':
                recommendations['immediate_actions'].append(f'Scale up to {scaling_action.target_instances} instances')
            elif scaling_action.action_type == 'scale_down':
                recommendations['secondary'].append(f'Consider scaling down to {scaling_action.target_instances} instances')
            
            # Load management recommendations
            if load_level in ['critical', 'high']:
                recommendations['configuration_adjustments'].extend([
                    'Reduce batch sizes',
                    'Increase timeout multipliers',
                    'Enable high-priority queue processing only'
                ])
            elif load_level == 'low':
                recommendations['configuration_adjustments'].extend([
                    'Increase batch sizes',
                    'Enable all queue processing',
                    'Consider background tasks'
                ])
            
            # Monitoring focus
            if load_decision.load_metrics.cpu_usage > 80:
                recommendations['monitoring_focus'].append('CPU usage trends')
            if load_decision.load_metrics.memory_usage > 80:
                recommendations['monitoring_focus'].append('Memory usage and leaks')
            if load_decision.load_metrics.queue_length > 10:
                recommendations['monitoring_focus'].append('Queue processing efficiency')
            if load_decision.load_metrics.response_time_avg > 2.0:
                recommendations['monitoring_focus'].append('Response time optimization')
            if load_decision.load_metrics.error_rate > 0.01:
                recommendations['monitoring_focus'].append('Error rate investigation')
            
            # Cache optimization recommendations
            if load_level in ['critical', 'high']:
                recommendations['configuration_adjustments'].append('Increase cache priority to high')
            elif load_level == 'low':
                recommendations['configuration_adjustments'].append('Optimize cache for long-term storage')
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating coordinated recommendations: {str(e)}")
            return {
                'primary': 'error_state_maintain_current',
                'error': str(e)
            }
    
    # =============================================================================
    # BACKGROUND COORDINATION LOOP
    # =============================================================================
    
    def _coordination_loop(self):
        """Background loop for coordinated processing decisions."""
        while self.integration_active:
            try:
                if not self.app:
                    logger.warning("Load-aware integration has no app bound; skipping coordination cycle")
                    time.sleep(self.coordination_interval)
                    continue
                # Ensure Flask application context for any DB/config/service access
                with self.app.app_context():
                    # Make coordinated decision
                    decision = self.make_coordinated_processing_decision()
                    # Execute coordinated actions
                    self._execute_coordinated_actions(decision)
                    # Log significant decisions
                    overall_status = decision.get('system_health', {}).get('overall_status', 'unknown')
                    if overall_status in ['critical', 'emergency']:
                        logger.error(
                            f"System Health: {overall_status} - {decision.get('coordinated_recommendations', {}).get('primary', 'unknown')}"

                        )
                    elif overall_status == 'degraded':
                        logger.warning(
                            f"System Health: {overall_status} - {decision.get('coordinated_recommendations', {}).get('primary', 'unknown')}"

                        )
                    else:
                        logger.info(f"System Health: {overall_status}")
                time.sleep(self.coordination_interval)
            except Exception as e:
                logger.error(f"Error in coordination loop: {str(e)}")
                time.sleep(self.coordination_interval * 2)  # Wait longer on error
    
    def _execute_coordinated_actions(self, decision: Dict[str, Any]):
        """Execute coordinated actions based on decision."""
        try:
            recommendations = decision.get('coordinated_recommendations', {})
            primary_action = recommendations.get('primary')
            immediate_actions = recommendations.get('immediate_actions', [])
            
            # Execute scaling actions if needed
            scaling_info = decision.get('auto_scaling', {})
            if scaling_info.get('action') in ['scale_up', 'scale_down']:
                scaling_action_data = decision.get('auto_scaling')
                if scaling_action_data and scaling_action_data.get('confidence', 0) > 0.7:
                    # In production, this would execute actual scaling
                    logger.info(f"Would execute scaling: {scaling_action_data['action']} to {scaling_action_data['target_instances']} instances")
            
            # Apply configuration adjustments
            config_adjustments = recommendations.get('configuration_adjustments', [])
            if config_adjustments:
                self._apply_configuration_adjustments(config_adjustments)
            
            # Update cache configuration if needed
            load_info = decision.get('load_management', {})
            if load_info and self.enhanced_cache:
                load_level = load_info.get('load_level', 'normal')
                self._update_cache_configuration(load_level)
            
        except Exception as e:
            logger.error(f"Error executing coordinated actions: {str(e)}")
    
    def _apply_configuration_adjustments(self, adjustments: List[str]):
        """Apply configuration adjustments to the application."""
        try:
            if not self.app:
                return
            
            config = self.app.config
            
            for adjustment in adjustments:
                if 'reduce batch sizes' in adjustment.lower():
                    current_batch = config.get('QUEUE_BATCH_SIZE', 3)
                    config['QUEUE_BATCH_SIZE'] = max(1, current_batch - 1)
                    
                elif 'increase batch sizes' in adjustment.lower():
                    current_batch = config.get('QUEUE_BATCH_SIZE', 3)
                    config['QUEUE_BATCH_SIZE'] = min(10, current_batch + 1)
                    
                elif 'increase timeout multipliers' in adjustment.lower():
                    current_timeout = config.get('AI_TIMEOUT_SECONDS', 60)
                    config['AI_TIMEOUT_SECONDS'] = min(300, int(current_timeout * 1.2))
                    
                elif 'high-priority queue processing only' in adjustment.lower():
                    config['PRIORITY_QUEUES_ONLY'] = True
                    
                elif 'enable all queue processing' in adjustment.lower():
                    config['PRIORITY_QUEUES_ONLY'] = False
                    
                elif 'increase cache priority to high' in adjustment.lower() and self.enhanced_cache:
                    if hasattr(self.enhanced_cache, 'set_cache_priority'):
                        self.enhanced_cache.set_cache_priority('high')
            
            logger.debug(f"Applied {len(adjustments)} configuration adjustments")
            
        except Exception as e:
            logger.error(f"Error applying configuration adjustments: {str(e)}")
    
    def _update_cache_configuration(self, load_level: str):
        """Update cache configuration based on load level."""
        try:
            if not self.enhanced_cache:
                return
            
            if hasattr(self.enhanced_cache, 'set_cache_priority'):
                if load_level in ['critical', 'high']:
                    self.enhanced_cache.set_cache_priority('high')
                elif load_level == 'medium':
                    self.enhanced_cache.set_cache_priority('medium')
                else:
                    self.enhanced_cache.set_cache_priority('low')
            
        except Exception as e:
            logger.error(f"Error updating cache configuration: {str(e)}")
    
    # =============================================================================
    # API METHODS
    # =============================================================================
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status and health."""
        try:
            current_time = datetime.utcnow()
            
            # Get latest coordinated decision
            latest_decision = self.coordination_history[-1] if self.coordination_history else None
            
            # Get service statuses
            load_status = self.load_manager.get_current_load_status()
            scaling_status = self.scaling_service.get_scaling_status()
            
            return {
                'timestamp': current_time.isoformat(),
                'integration_active': self.integration_active,
                'system_health_status': self.system_health_status,
                'last_coordination_time': self.last_coordination_time.isoformat() if self.last_coordination_time else None,
                'coordination_interval': self.coordination_interval,
                'coordination_history_count': len(self.coordination_history),
                'latest_coordinated_decision': latest_decision,
                'load_management_status': load_status,
                'auto_scaling_status': scaling_status,
                'performance_monitoring_active': self.performance_monitor is not None,
                'enhanced_cache_active': self.enhanced_cache is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting integration status: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def force_coordination_decision(self) -> Dict[str, Any]:
        """Force an immediate coordinated processing decision."""
        try:
            logger.info("Forcing immediate coordinated processing decision")
            decision = self.make_coordinated_processing_decision()
            self._execute_coordinated_actions(decision)
            
            return {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'forced_decision': decision
            }
            
        except Exception as e:
            logger.error(f"Error forcing coordination decision: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report. Ensures an app context for safe access."""
        if self.app and not has_app_context():
            try:
                with self.app.app_context():
                    return self._get_system_health_report_core()
            except Exception as e:
                logger.error(f"Error generating system health report (with app context): {str(e)}")
                return {
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
        return self._get_system_health_report_core()

    def _get_system_health_report_core(self) -> Dict[str, Any]:
        """Core logic for system health report (expects app context if needed)."""
        try:
            current_time = datetime.utcnow()
            # Get current health assessment
            load_decision = self.load_manager.make_processing_decision()
            scaling_action = self.scaling_service.evaluate_scaling_need(self.load_manager)
            performance_data = None
            if self.performance_monitor:
                try:
                    if hasattr(self.performance_monitor, 'get_current_status'):
                        performance_data = self.performance_monitor.get_current_status()
                    elif hasattr(self.performance_monitor, 'get_performance_summary'):
                        performance_data = self.performance_monitor.get_performance_summary()
                    else:
                        performance_data = self.performance_monitor.collect_current_metrics()
                except Exception:
                    pass
            system_health = self._assess_system_health(load_decision, scaling_action, performance_data)
            # Generate health trends
            health_trends = self._analyze_health_trends()
            # Get recommendations
            recommendations = self._generate_coordinated_recommendations(
                load_decision, scaling_action, system_health
            )
            return {
                'timestamp': current_time.isoformat(),
                'system_health': system_health,
                'health_trends': health_trends,
                'current_load_metrics': load_decision.load_metrics.to_dict(),
                'current_scaling_status': {
                    'current_instances': scaling_action.current_instances,
                    'recommended_action': scaling_action.action_type,
                    'target_instances': scaling_action.target_instances
                },
                'performance_status': performance_data,
                'recommendations': recommendations,
                'coordination_effectiveness': self._calculate_coordination_effectiveness()
            }
        except Exception as e:
            logger.error(f"Error generating system health report: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _analyze_health_trends(self) -> Dict[str, Any]:
        """Analyze health trends over recent coordination history."""
        try:
            if len(self.coordination_history) < 5:
                return {'status': 'insufficient_data'}
            
            # Get recent health scores
            recent_decisions = self.coordination_history[-10:]
            health_scores = []
            
            for decision in recent_decisions:
                health = decision.get('system_health', {})
                score = health.get('overall_score', 0.5)
                health_scores.append(score)
            
            if not health_scores:
                return {'status': 'no_health_data'}
            
            # Calculate trend
            avg_score = sum(health_scores) / len(health_scores)
            recent_avg = sum(health_scores[-3:]) / 3 if len(health_scores) >= 3 else avg_score
            older_avg = sum(health_scores[:3]) / 3 if len(health_scores) >= 6 else avg_score
            
            trend = recent_avg - older_avg
            
            if trend > 0.1:
                trend_status = 'improving'
            elif trend < -0.1:
                trend_status = 'degrading'
            else:
                trend_status = 'stable'
            
            return {
                'status': 'analyzed',
                'overall_trend': trend_status,
                'trend_value': round(trend, 3),
                'average_health_score': round(avg_score, 3),
                'recent_average': round(recent_avg, 3),
                'data_points': len(health_scores)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing health trends: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _calculate_coordination_effectiveness(self) -> Dict[str, Any]:
        """Calculate the effectiveness of coordination decisions."""
        try:
            if len(self.coordination_history) < 3:
                return {'status': 'insufficient_data'}
            
            # Analyze decision outcomes
            total_decisions = len(self.coordination_history)
            health_improvements = 0
            health_degradations = 0
            
            for i in range(1, len(self.coordination_history)):
                current_health = self.coordination_history[i].get('system_health', {}).get('overall_score', 0.5)
                previous_health = self.coordination_history[i-1].get('system_health', {}).get('overall_score', 0.5)
                
                if current_health > previous_health + 0.05:
                    health_improvements += 1
                elif current_health < previous_health - 0.05:
                    health_degradations += 1
            
            effectiveness_score = (health_improvements - health_degradations) / (total_decisions - 1) if total_decisions > 1 else 0
            
            return {
                'status': 'calculated',
                'effectiveness_score': round(effectiveness_score, 3),
                'total_decisions': total_decisions,
                'health_improvements': health_improvements,
                'health_degradations': health_degradations,
                'stability_ratio': round((total_decisions - 1 - health_improvements - health_degradations) / (total_decisions - 1), 3) if total_decisions > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating coordination effectiveness: {str(e)}")
            return {'status': 'error', 'error': str(e)}


# =============================================================================
# GLOBAL INTEGRATION SERVICE INSTANCE
# =============================================================================

load_aware_integration = LoadAwareProcessingIntegration()
