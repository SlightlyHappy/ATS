"""
Smart Resource Scaling - Main Coordinator
Coordinates resource monitoring, scaling decisions, and worker management.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from app.services.resource_monitor import resource_monitor
from app.services.scaling_decision_engine import scaling_decision_engine
from app.services.worker_lifecycle_manager import worker_lifecycle_manager
from app.services.intelligent_queue_manager import intelligent_queue_manager

logger = logging.getLogger(__name__)

class SmartResourceScaler:
    """Main coordinator for smart resource scaling system."""
    
    def __init__(self):
        self.running = False
        self.coordinator_task = None
        self.scaling_interval = 60  # Check scaling every 60 seconds
        self.last_scaling_check = None
        self.scaling_history = []
        self.config = {
            'min_workers': 2,
            'max_workers': 8,
            'scaling_cooldown': 300,  # 5 minutes
            'aggressive_scaling': False,
            'auto_scaling_enabled': True
        }
    
    async def start(self):
        """Start the smart resource scaling system."""
        if self.running:
            logger.warning("Smart resource scaler is already running")
            return
        
        logger.info("Starting Smart Resource Scaling System")
        
        try:
            # Start all components
            await resource_monitor.start_monitoring()
            await worker_lifecycle_manager.start_manager()
            await intelligent_queue_manager.start_processing()
            
            # Start coordination loop
            self.running = True
            self.coordinator_task = asyncio.create_task(self._coordination_loop())
            
            logger.info("Smart Resource Scaling System started successfully")
            
        except Exception as e:
            logger.error(f"Error starting Smart Resource Scaling System: {str(e)}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the smart resource scaling system."""
        logger.info("Stopping Smart Resource Scaling System")
        
        self.running = False
        
        # Stop coordination loop
        if self.coordinator_task:
            self.coordinator_task.cancel()
            try:
                await self.coordinator_task
            except asyncio.CancelledError:
                pass
        
        # Stop all components
        try:
            await intelligent_queue_manager.stop_processing()
            await worker_lifecycle_manager.stop_manager()
            await resource_monitor.stop_monitoring()
        except Exception as e:
            logger.error(f"Error stopping components: {str(e)}")
        
        logger.info("Smart Resource Scaling System stopped")
    
    async def _coordination_loop(self):
        """Main coordination loop for resource scaling."""
        logger.info("Smart resource scaling coordination loop started")
        
        while self.running:
            try:
                # Check if it's time for a scaling decision
                if self._should_check_scaling():
                    await self._perform_scaling_check()
                
                # Update system status
                await self._update_system_status()
                
                # Perform health checks
                await self._perform_health_checks()
                
                # Sleep until next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in coordination loop: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def _should_check_scaling(self) -> bool:
        """Check if it's time to make a scaling decision."""
        if not self.config['auto_scaling_enabled']:
            return False
        
        if self.last_scaling_check is None:
            return True
        
        time_since_last = (datetime.utcnow() - self.last_scaling_check).total_seconds()
        return time_since_last >= self.scaling_interval
    
    async def _perform_scaling_check(self):
        """Perform a scaling check and make decisions."""
        try:
            logger.debug("Performing scaling check")
            
            # Get current metrics
            current_metrics = await resource_monitor.collect_system_metrics()
            
            # Get current worker count
            worker_status = worker_lifecycle_manager.get_worker_status()
            current_workers = worker_status['workers_by_status'].get('active', 0)
            
            # Make scaling decision
            scaling_decision = await scaling_decision_engine.make_scaling_decision(
                current_metrics, current_workers
            )
            
            # Execute scaling decision
            await self._execute_scaling_decision(scaling_decision, current_workers)
            
            # Record the check
            self.last_scaling_check = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error performing scaling check: {str(e)}")
    
    async def _execute_scaling_decision(self, decision: Dict[str, Any], current_workers: int):
        """Execute a scaling decision."""
        try:
            action = decision['action']
            target_workers = decision['target_workers']
            confidence = decision['confidence']
            reason = decision.get('reason', 'No reason provided')
            
            if action == 'maintain':
                logger.debug(f"Scaling decision: maintain {current_workers} workers. Reason: {reason}")
                return
            
            # Record scaling decision
            scaling_record = {
                'timestamp': datetime.utcnow(),
                'action': action,
                'current_workers': current_workers,
                'target_workers': target_workers,
                'confidence': confidence,
                'reason': reason,
                'success': False
            }
            
            if action == 'scale_up':
                logger.info(f"Scaling UP from {current_workers} to {target_workers} workers (confidence: {confidence:.2f})")
                logger.info(f"Scale-up reason: {reason}")
                
                result = await worker_lifecycle_manager.scale_up_workers(target_workers, 'analysis')
                scaling_record['success'] = result['success']
                scaling_record['details'] = result
                
                if result['success']:
                    logger.info(f"Scale-up successful: {result['message']}")
                else:
                    logger.warning(f"Scale-up failed: {result['message']}")
            
            elif action == 'scale_down':
                logger.info(f"Scaling DOWN from {current_workers} to {target_workers} workers (confidence: {confidence:.2f})")
                logger.info(f"Scale-down reason: {reason}")
                
                result = await worker_lifecycle_manager.scale_down_workers(target_workers, 'analysis')
                scaling_record['success'] = result['success']
                scaling_record['details'] = result
                
                if result['success']:
                    logger.info(f"Scale-down successful: {result['message']}")
                else:
                    logger.warning(f"Scale-down failed: {result['message']}")
            
            # Store scaling history
            self.scaling_history.append(scaling_record)
            
            # Keep only recent history
            if len(self.scaling_history) > 100:
                self.scaling_history = self.scaling_history[-100:]
            
        except Exception as e:
            logger.error(f"Error executing scaling decision: {str(e)}")
    
    async def _update_system_status(self):
        """Update overall system status."""
        try:
            # This could update a shared status object or database
            # For now, we'll just log key metrics periodically
            
            current_time = datetime.utcnow()
            
            # Log status every 5 minutes
            if (not hasattr(self, '_last_status_log') or 
                (current_time - self._last_status_log).total_seconds() > 300):
                
                await self._log_system_status()
                self._last_status_log = current_time
                
        except Exception as e:
            logger.error(f"Error updating system status: {str(e)}")
    
    async def _log_system_status(self):
        """Log comprehensive system status."""
        try:
            # Get metrics from all components
            resource_metrics = resource_monitor.get_average_metrics(5)
            worker_status = worker_lifecycle_manager.get_worker_status()
            queue_status = intelligent_queue_manager.get_queue_status()
            
            logger.info("=== SYSTEM STATUS ===")
            logger.info(f"CPU Usage: {resource_metrics['cpu_percent']:.1f}%")
            logger.info(f"Memory Usage: {resource_metrics['memory_percent']:.1f}%")
            logger.info(f"Queue Length: {resource_metrics['queue_length']:.0f}")
            logger.info(f"Active Workers: {worker_status['total_workers']}")
            logger.info(f"Total Queue Items: {queue_status['total_items']}")
            logger.info(f"Currently Processing: {queue_status['processing']['current_count']}")
            logger.info("=====================")
            
        except Exception as e:
            logger.error(f"Error logging system status: {str(e)}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all components."""
        try:
            # Check if all components are running
            if not resource_monitor.running:
                logger.warning("Resource monitor is not running, attempting restart")
                await resource_monitor.start_monitoring()
            
            if not worker_lifecycle_manager.running:
                logger.warning("Worker lifecycle manager is not running, attempting restart")
                await worker_lifecycle_manager.start_manager()
            
            if not intelligent_queue_manager.running:
                logger.warning("Intelligent queue manager is not running, attempting restart")
                await intelligent_queue_manager.start_processing()
            
        except Exception as e:
            logger.error(f"Error performing health checks: {str(e)}")
    
    async def manual_scale_up(self, target_workers: int, reason: str = "Manual scaling") -> Dict[str, Any]:
        """Manually scale up workers."""
        try:
            logger.info(f"Manual scale-up requested to {target_workers} workers: {reason}")
            
            result = await worker_lifecycle_manager.scale_up_workers(target_workers, 'analysis')
            
            # Record manual scaling
            scaling_record = {
                'timestamp': datetime.utcnow(),
                'action': 'manual_scale_up',
                'current_workers': worker_lifecycle_manager.get_worker_status()['total_workers'],
                'target_workers': target_workers,
                'confidence': 1.0,
                'reason': f"Manual: {reason}",
                'success': result['success'],
                'details': result
            }
            self.scaling_history.append(scaling_record)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in manual scale-up: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    async def manual_scale_down(self, target_workers: int, reason: str = "Manual scaling") -> Dict[str, Any]:
        """Manually scale down workers."""
        try:
            logger.info(f"Manual scale-down requested to {target_workers} workers: {reason}")
            
            result = await worker_lifecycle_manager.scale_down_workers(target_workers, 'analysis')
            
            # Record manual scaling
            scaling_record = {
                'timestamp': datetime.utcnow(),
                'action': 'manual_scale_down',
                'current_workers': worker_lifecycle_manager.get_worker_status()['total_workers'],
                'target_workers': target_workers,
                'confidence': 1.0,
                'reason': f"Manual: {reason}",
                'success': result['success'],
                'details': result
            }
            self.scaling_history.append(scaling_record)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in manual scale-down: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update scaling configuration."""
        try:
            old_config = self.config.copy()
            
            # Validate and update configuration
            valid_keys = {'min_workers', 'max_workers', 'scaling_cooldown', 'aggressive_scaling', 'auto_scaling_enabled'}
            for key, value in new_config.items():
                if key in valid_keys:
                    self.config[key] = value
                else:
                    logger.warning(f"Invalid config key: {key}")
            
            # Update dependent components
            if 'min_workers' in new_config:
                worker_lifecycle_manager.min_workers = self.config['min_workers']
            if 'max_workers' in new_config:
                worker_lifecycle_manager.max_workers = self.config['max_workers']
            if 'scaling_cooldown' in new_config:
                scaling_decision_engine.cooldown_period = self.config['scaling_cooldown']
            
            logger.info(f"Configuration updated: {new_config}")
            
            return {
                'success': True,
                'old_config': old_config,
                'new_config': self.config
            }
            
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the entire system."""
        try:
            return {
                'system_info': {
                    'running': self.running,
                    'started_at': getattr(self, 'start_time', None),
                    'last_scaling_check': self.last_scaling_check.isoformat() if self.last_scaling_check else None,
                    'config': self.config
                },
                'resource_metrics': resource_monitor.get_average_metrics(5),
                'worker_status': worker_lifecycle_manager.get_worker_status(),
                'queue_status': intelligent_queue_manager.get_queue_status(),
                'scaling_analytics': scaling_decision_engine.get_scaling_analytics(24),
                'recent_scaling_history': [
                    {
                        **record,
                        'timestamp': record['timestamp'].isoformat()
                    }
                    for record in self.scaling_history[-10:]  # Last 10 scaling actions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {str(e)}")
            return {'error': str(e)}
    
    async def emergency_scale_down(self, reason: str = "Emergency shutdown") -> Dict[str, Any]:
        """Emergency scale down to minimum workers."""
        try:
            logger.warning(f"Emergency scale-down triggered: {reason}")
            
            result = await worker_lifecycle_manager.scale_down_workers(self.config['min_workers'], 'analysis')
            
            # Record emergency scaling
            scaling_record = {
                'timestamp': datetime.utcnow(),
                'action': 'emergency_scale_down',
                'current_workers': worker_lifecycle_manager.get_worker_status()['total_workers'],
                'target_workers': self.config['min_workers'],
                'confidence': 1.0,
                'reason': f"Emergency: {reason}",
                'success': result['success'],
                'details': result
            }
            self.scaling_history.append(scaling_record)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in emergency scale-down: {str(e)}")
            return {'success': False, 'message': str(e)}

# Global instance
smart_resource_scaler = SmartResourceScaler()
