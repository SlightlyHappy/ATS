"""
Intelligent Queue Management - Priority-Based Queue System
Implements sophisticated multi-tier queue with dynamic priority adjustment.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from queue import PriorityQueue
from dataclasses import dataclass, field
import uuid

from app import db
from app.models.queue import AnalysisQueue, QueueStatus
from app.models.user import User
from app.services.resource_monitor import resource_monitor

logger = logging.getLogger(__name__)

@dataclass
class QueueItem:
    """Enhanced queue item with dynamic priority calculation."""
    id: str
    user_id: str
    resume_id: str
    base_priority: float
    urgency: str
    created_at: datetime
    user_tier: str
    estimated_memory: int = 0
    estimated_cpu_time: int = 0
    dynamic_priority: float = field(init=False)
    base_timeout: int = 300  # 5 minutes default
    
    def __post_init__(self):
        self.dynamic_priority = self.base_priority

class IntelligentQueueManager:
    """Sophisticated multi-tier queue with dynamic priority adjustment and load-aware processing."""
    
    def __init__(self):
        self.queues = {
            'critical': [],     # Emergency/System critical (Priority 1)
            'admin': [],        # Admin users (Priority 2)
            'premium': [],      # Premium users (Priority 3)
            'normal': [],       # Regular users (Priority 4)
            'background': [],   # Background refinement (Priority 5)
            'batch': []         # Batch processing (Priority 6)
        }
        
        self.queue_weights = {
            'critical': 1.0,    # Always process first
            'admin': 0.8,       # High priority
            'premium': 0.6,     # Medium-high priority
            'normal': 0.4,      # Standard priority
            'background': 0.2,  # Low priority
            'batch': 0.1        # Lowest priority
        }
        
        self.processing_slots = {
            'critical': {'min': 1, 'max': 2},
            'admin': {'min': 1, 'max': 3},
            'premium': {'min': 1, 'max': 2},
            'normal': {'min': 2, 'max': 4},
            'background': {'min': 0, 'max': 2},
            'batch': {'min': 0, 'max': 1}
        }
        
        self.priority_adjuster = DynamicPriorityAdjuster()
        self.load_processor = LoadAwareProcessor(self)
        self.running = False
        self.processor_task = None
        self.current_processing = set()
        self.processing_history = []
    
    async def start_processing(self):
        """Start intelligent queue processing."""
        if self.running:
            logger.warning("Intelligent queue manager is already running")
            return
        
        self.running = True
        self.processor_task = asyncio.create_task(self._intelligent_queue_processing())
        logger.info("Intelligent queue processing started")
    
    async def stop_processing(self):
        """Stop queue processing."""
        self.running = False
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        # Wait for current processing to complete
        while self.current_processing:
            await asyncio.sleep(1)
        
        logger.info("Intelligent queue processing stopped")
    
    async def _intelligent_queue_processing(self):
        """Process queues with intelligent prioritization."""
        while self.running:
            try:
                # Get current system load
                system_metrics = await resource_monitor.collect_system_metrics()
                
                # Calculate available processing capacity
                available_capacity = await self._calculate_available_capacity(system_metrics)
                
                # Determine queue processing strategy
                processing_strategy = await self._determine_processing_strategy(
                    system_metrics, available_capacity
                )
                
                # Execute processing strategy
                await self._execute_processing_strategy(processing_strategy)
                
                # Update dynamic priorities
                await self._update_dynamic_priorities()
                
                # Adaptive sleep based on queue state
                sleep_time = self._calculate_adaptive_sleep()
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in intelligent queue processing: {str(e)}")
                await asyncio.sleep(30)
    
    async def add_to_queue(self, user_id: str, resume_id: str, urgency: str = 'normal', 
                          estimated_resources: Dict[str, int] = None) -> str:
        """Add item to appropriate queue based on user tier and urgency."""
        try:
            # Get user information
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Determine user tier
            user_tier = self._get_user_tier(user)
            
            # Create queue item
            queue_item = QueueItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                resume_id=resume_id,
                base_priority=self._calculate_base_priority(user_tier, urgency),
                urgency=urgency,
                created_at=datetime.utcnow(),
                user_tier=user_tier,
                estimated_memory=estimated_resources.get('memory', 512) if estimated_resources else 512,
                estimated_cpu_time=estimated_resources.get('cpu_time', 60) if estimated_resources else 60
            )
            
            # Calculate initial dynamic priority
            priority_info = await self.priority_adjuster.calculate_dynamic_priority(queue_item)
            queue_item.dynamic_priority = priority_info['priority']
            
            # Determine target queue
            target_queue = self._determine_target_queue(user_tier, urgency)
            
            # Add to queue
            self.queues[target_queue].append(queue_item)
            
            # Sort queue by dynamic priority
            self.queues[target_queue].sort(key=lambda x: x.dynamic_priority, reverse=True)
            
            logger.info(f"Added item {queue_item.id} to {target_queue} queue with priority {queue_item.dynamic_priority:.2f}")
            
            return queue_item.id
            
        except Exception as e:
            logger.error(f"Error adding item to queue: {str(e)}")
            raise
    
    def _get_user_tier(self, user: User) -> str:
        """Determine user tier."""
        if user.is_admin:
            return 'admin'
        elif hasattr(user, 'subscription_tier') and user.subscription_tier == 'premium':
            return 'premium'
        elif hasattr(user, 'subscription_tier') and user.subscription_tier == 'trial':
            return 'trial'
        else:
            return 'regular'
    
    def _calculate_base_priority(self, user_tier: str, urgency: str) -> float:
        """Calculate base priority based on user tier and urgency."""
        tier_priorities = {
            'admin': 100,
            'premium': 80,
            'regular': 50,
            'trial': 30
        }
        
        urgency_multipliers = {
            'critical': 2.0,
            'high': 1.5,
            'normal': 1.0,
            'low': 0.5
        }
        
        base = tier_priorities.get(user_tier, 50)
        multiplier = urgency_multipliers.get(urgency, 1.0)
        
        return base * multiplier
    
    def _determine_target_queue(self, user_tier: str, urgency: str) -> str:
        """Determine which queue to use based on user tier and urgency."""
        if urgency == 'critical':
            return 'critical'
        elif user_tier == 'admin':
            return 'admin'
        elif user_tier == 'premium':
            return 'premium'
        elif urgency == 'low':
            return 'background'
        else:
            return 'normal'
    
    async def _calculate_available_capacity(self, system_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate available processing capacity based on system metrics."""
        try:
            cpu_usage = system_metrics['cpu']['percent']
            memory_usage = system_metrics['memory']['percent']
            current_processing = len(self.current_processing)
            
            # Calculate capacity based on resource usage
            cpu_capacity = max(0, (100 - cpu_usage) / 100)
            memory_capacity = max(0, (100 - memory_usage) / 100)
            
            # Determine maximum concurrent processes
            max_concurrent = 8  # Base maximum
            
            if cpu_usage > 90 or memory_usage > 90:
                max_concurrent = 1
            elif cpu_usage > 80 or memory_usage > 80:
                max_concurrent = 2
            elif cpu_usage > 70 or memory_usage > 70:
                max_concurrent = 4
            elif cpu_usage > 60 or memory_usage > 60:
                max_concurrent = 6
            
            available_slots = max(0, max_concurrent - current_processing)
            
            return {
                'cpu_capacity': cpu_capacity,
                'memory_capacity': memory_capacity,
                'max_concurrent': max_concurrent,
                'available_slots': available_slots,
                'current_processing': current_processing
            }
            
        except Exception as e:
            logger.error(f"Error calculating available capacity: {str(e)}")
            return {
                'cpu_capacity': 0.5,
                'memory_capacity': 0.5,
                'max_concurrent': 2,
                'available_slots': 1,
                'current_processing': 0
            }
    
    async def _determine_processing_strategy(self, system_metrics: Dict[str, Any], 
                                           available_capacity: Dict[str, Any]) -> Dict[str, Any]:
        """Determine processing strategy based on system load and capacity."""
        try:
            cpu_usage = system_metrics['cpu']['percent']
            memory_usage = system_metrics['memory']['percent']
            available_slots = available_capacity['available_slots']
            
            # Determine load level
            if cpu_usage > 95 or memory_usage > 90:
                load_level = 'critical_load'
            elif cpu_usage > 80 or memory_usage > 80:
                load_level = 'high_load'
            elif cpu_usage > 60 or memory_usage > 70:
                load_level = 'medium_load'
            elif cpu_usage > 40 or memory_usage > 50:
                load_level = 'normal_load'
            else:
                load_level = 'low_load'
            
            return await self.load_processor.determine_load_strategy(
                load_level, available_slots, system_metrics
            )
            
        except Exception as e:
            logger.error(f"Error determining processing strategy: {str(e)}")
            return {
                'load_level': 'normal_load',
                'max_concurrent': 2,
                'allowed_queues': ['critical', 'admin', 'normal'],
                'batch_size': 1,
                'timeout_reduction': 1.0
            }
    
    async def _execute_processing_strategy(self, strategy: Dict[str, Any]):
        """Execute processing strategy."""
        try:
            # Get items from allowed queues
            processing_items = []
            
            for queue_name in strategy['allowed_queues']:
                if queue_name not in self.queues:
                    continue
                
                queue = self.queues[queue_name]
                
                if not queue:
                    continue
                
                # Calculate items to take from this queue
                queue_weight = self.queue_weights[queue_name]
                items_from_queue = max(1, int(strategy['batch_size'] * queue_weight))
                
                # Take items with highest priority
                items = queue[:items_from_queue]
                processing_items.extend(items)
            
            # Sort by dynamic priority
            processing_items.sort(key=lambda x: x.dynamic_priority, reverse=True)
            
            # Limit to max concurrent
            processing_items = processing_items[:strategy['max_concurrent']]
            
            # Process items with appropriate timeouts
            timeout_multiplier = strategy['timeout_reduction']
            
            tasks = []
            for item in processing_items:
                if len(self.current_processing) >= strategy['max_concurrent']:
                    break
                
                adjusted_timeout = item.base_timeout * timeout_multiplier
                task = asyncio.create_task(
                    self._process_item_with_timeout(item, adjusted_timeout)
                )
                tasks.append(task)
                self.current_processing.add(item.id)
                
                # Remove from queue
                for queue_name, queue in self.queues.items():
                    if item in queue:
                        queue.remove(item)
                        break
            
            # Don't wait for tasks to complete (they run in background)
            if tasks:
                logger.info(f"Started processing {len(tasks)} items with strategy: {strategy['load_level']}")
                
        except Exception as e:
            logger.error(f"Error executing processing strategy: {str(e)}")
    
    async def _process_item_with_timeout(self, item: QueueItem, timeout: float):
        """Process a queue item with timeout."""
        try:
            logger.info(f"Processing queue item {item.id} with timeout {timeout}s")
            
            # Simulate processing (replace with actual processing logic)
            from app.services.queue_service import QueueService
            queue_service = QueueService()
            
            # Get the actual queue entry from database
            queue_entry = AnalysisQueue.query.filter_by(
                resume_id=item.resume_id,
                status=QueueStatus.PENDING.value
            ).first()
            
            if queue_entry:
                await asyncio.wait_for(
                    queue_service.process_queue_item(queue_entry),
                    timeout=timeout
                )
            
            logger.info(f"Successfully processed queue item {item.id}")
            
        except asyncio.TimeoutError:
            logger.warning(f"Queue item {item.id} processing timed out after {timeout}s")
        except Exception as e:
            logger.error(f"Error processing queue item {item.id}: {str(e)}")
        finally:
            # Remove from current processing
            self.current_processing.discard(item.id)
            
            # Record in processing history
            self.processing_history.append({
                'item_id': item.id,
                'processed_at': datetime.utcnow(),
                'success': True  # Would be set based on actual result
            })
            
            # Keep only recent history
            if len(self.processing_history) > 1000:
                self.processing_history = self.processing_history[-1000:]
    
    async def _update_dynamic_priorities(self):
        """Update dynamic priorities for all queue items."""
        try:
            for queue_name, queue in self.queues.items():
                for item in queue:
                    priority_info = await self.priority_adjuster.calculate_dynamic_priority(item)
                    item.dynamic_priority = priority_info['priority']
                
                # Re-sort queue by updated priorities
                queue.sort(key=lambda x: x.dynamic_priority, reverse=True)
                
        except Exception as e:
            logger.error(f"Error updating dynamic priorities: {str(e)}")
    
    def _calculate_adaptive_sleep(self) -> float:
        """Calculate adaptive sleep time based on queue state."""
        try:
            total_items = sum(len(queue) for queue in self.queues.values())
            current_processing = len(self.current_processing)
            
            if total_items == 0:
                return 10.0  # No items, sleep longer
            elif current_processing >= 8:
                return 5.0   # At capacity, moderate sleep
            elif total_items > 50:
                return 1.0   # High load, check frequently
            elif total_items > 20:
                return 2.0   # Medium load
            else:
                return 3.0   # Low load
                
        except Exception:
            return 5.0  # Default fallback
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get comprehensive queue status."""
        try:
            status = {
                'total_items': 0,
                'queues': {},
                'processing': {
                    'current_count': len(self.current_processing),
                    'current_items': list(self.current_processing)
                },
                'performance': {
                    'items_processed_last_hour': 0,
                    'average_processing_time': 0
                }
            }
            
            # Queue details
            for queue_name, queue in self.queues.items():
                queue_info = {
                    'count': len(queue),
                    'priority_range': {
                        'min': min(item.dynamic_priority for item in queue) if queue else 0,
                        'max': max(item.dynamic_priority for item in queue) if queue else 0
                    },
                    'oldest_item_age': 0,
                    'items': []
                }
                
                if queue:
                    oldest_item = min(queue, key=lambda x: x.created_at)
                    queue_info['oldest_item_age'] = (datetime.utcnow() - oldest_item.created_at).total_seconds()
                    
                    # Include top 5 items for monitoring
                    queue_info['items'] = [
                        {
                            'id': item.id,
                            'priority': item.dynamic_priority,
                            'age_seconds': (datetime.utcnow() - item.created_at).total_seconds(),
                            'user_tier': item.user_tier,
                            'urgency': item.urgency
                        }
                        for item in queue[:5]
                    ]
                
                status['queues'][queue_name] = queue_info
                status['total_items'] += queue_info['count']
            
            # Performance metrics
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_processed = [
                h for h in self.processing_history 
                if h['processed_at'] > one_hour_ago
            ]
            status['performance']['items_processed_last_hour'] = len(recent_processed)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {'error': str(e)}


class DynamicPriorityAdjuster:
    """Handles dynamic priority adjustment based on multiple factors."""
    
    def __init__(self):
        self.priority_factors = {
            'user_tier': {
                'admin': 1.5,
                'premium': 1.2,
                'regular': 1.0,
                'trial': 0.8
            },
            'request_urgency': {
                'critical': 2.0,
                'high': 1.5,
                'normal': 1.0,
                'low': 0.5
            },
            'wait_time_bonus': {
                'max_bonus': 0.5,           # Maximum bonus for waiting
                'bonus_threshold': 300,     # Start bonus after 5 minutes
                'bonus_rate': 0.001         # Bonus per second waiting
            },
            'resource_cost': {
                'low_memory': 1.2,         # Boost for low-memory tasks
                'high_memory': 0.8,        # Reduce for high-memory tasks
                'quick_analysis': 1.1,     # Boost for quick tasks
                'complex_analysis': 0.9    # Reduce for complex tasks
            }
        }
    
    async def calculate_dynamic_priority(self, queue_item: QueueItem) -> Dict[str, Any]:
        """Calculate dynamic priority based on multiple factors."""
        try:
            base_priority = queue_item.base_priority
            
            # User tier factor
            user_tier_factor = self.priority_factors['user_tier'].get(
                queue_item.user_tier, 1.0
            )
            
            # Request urgency factor
            urgency_factor = self.priority_factors['request_urgency'].get(
                queue_item.urgency, 1.0
            )
            
            # Wait time bonus
            wait_time = (datetime.utcnow() - queue_item.created_at).total_seconds()
            wait_bonus = min(
                self.priority_factors['wait_time_bonus']['max_bonus'],
                max(0, (wait_time - self.priority_factors['wait_time_bonus']['bonus_threshold']) * 
                    self.priority_factors['wait_time_bonus']['bonus_rate'])
            )
            
            # Resource cost factor
            resource_factor = await self._calculate_resource_factor(queue_item)
            
            # System load factor
            load_factor = await self._calculate_load_factor(queue_item)
            
            # Calculate final priority
            dynamic_priority = (
                base_priority * 
                user_tier_factor * 
                urgency_factor * 
                resource_factor * 
                load_factor + 
                wait_bonus
            )
            
            return {
                'priority': dynamic_priority,
                'factors': {
                    'base': base_priority,
                    'user_tier': user_tier_factor,
                    'urgency': urgency_factor,
                    'wait_bonus': wait_bonus,
                    'resource': resource_factor,
                    'load': load_factor
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating dynamic priority: {str(e)}")
            return {
                'priority': queue_item.base_priority,
                'factors': {
                    'base': queue_item.base_priority,
                    'error': str(e)
                }
            }
    
    async def _calculate_resource_factor(self, queue_item: QueueItem) -> float:
        """Calculate resource cost factor."""
        try:
            # Favor low-resource tasks when system is under pressure
            if queue_item.estimated_memory < 256:
                return self.priority_factors['resource_cost']['low_memory']
            elif queue_item.estimated_memory > 1024:
                return self.priority_factors['resource_cost']['high_memory']
            elif queue_item.estimated_cpu_time < 30:
                return self.priority_factors['resource_cost']['quick_analysis']
            elif queue_item.estimated_cpu_time > 120:
                return self.priority_factors['resource_cost']['complex_analysis']
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"Error calculating resource factor: {str(e)}")
            return 1.0
    
    async def _calculate_load_factor(self, queue_item: QueueItem) -> float:
        """Calculate system load factor."""
        try:
            # Get current system metrics
            recent_metrics = resource_monitor.get_average_metrics(5)
            
            cpu_usage = recent_metrics['cpu_percent']
            memory_usage = recent_metrics['memory_percent']
            
            # Under high load, prioritize quick tasks
            if cpu_usage > 80 or memory_usage > 80:
                if queue_item.estimated_cpu_time < 30:
                    return 1.3  # Boost quick tasks
                elif queue_item.estimated_cpu_time > 120:
                    return 0.7  # Reduce complex tasks
            
            # Under normal load, no adjustment
            return 1.0
            
        except Exception as e:
            logger.error(f"Error calculating load factor: {str(e)}")
            return 1.0


class LoadAwareProcessor:
    """Handles load-aware processing strategies."""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.load_strategies = {
            'critical_load': {        # >95% CPU or >90% Memory
                'max_concurrent': 1,
                'allowed_queues': ['critical'],
                'batch_size': 1,
                'timeout_reduction': 0.5
            },
            'high_load': {           # >80% CPU or >80% Memory
                'max_concurrent': 2,
                'allowed_queues': ['critical', 'admin'],
                'batch_size': 1,
                'timeout_reduction': 0.7
            },
            'medium_load': {         # >60% CPU or >70% Memory
                'max_concurrent': 4,
                'allowed_queues': ['critical', 'admin', 'premium', 'normal'],
                'batch_size': 2,
                'timeout_reduction': 0.9
            },
            'normal_load': {         # <60% CPU and <70% Memory
                'max_concurrent': 6,
                'allowed_queues': ['critical', 'admin', 'premium', 'normal', 'background'],
                'batch_size': 3,
                'timeout_reduction': 1.0
            },
            'low_load': {           # <40% CPU and <50% Memory
                'max_concurrent': 8,
                'allowed_queues': ['critical', 'admin', 'premium', 'normal', 'background', 'batch'],
                'batch_size': 4,
                'timeout_reduction': 1.2
            }
        }
    
    async def determine_load_strategy(self, load_level: str, available_slots: int, 
                                    system_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Determine processing strategy based on load level."""
        try:
            strategy = self.load_strategies.get(load_level, self.load_strategies['normal_load']).copy()
            
            # Adjust max_concurrent based on available slots
            strategy['max_concurrent'] = min(strategy['max_concurrent'], available_slots)
            
            # Add load level for reference
            strategy['load_level'] = load_level
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error determining load strategy: {str(e)}")
            return self.load_strategies['normal_load'].copy()

# Global instance
intelligent_queue_manager = IntelligentQueueManager()
