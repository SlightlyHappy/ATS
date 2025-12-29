"""
Background Task Optimizer - Phase 3.2 Implementation
Enterprise background task processing with intelligent scheduling,
priority management, and resource optimization.
"""
import logging
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Set
from dataclasses import dataclass, field
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from enum import Enum
import threading
import queue
import heapq
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# =============================================================================
# TASK PROCESSING ENUMS AND DATA CLASSES
# =============================================================================

class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class WorkerType(Enum):
    """Background worker types."""
    CPU_INTENSIVE = "cpu_intensive"
    IO_INTENSIVE = "io_intensive"
    MEMORY_INTENSIVE = "memory_intensive"
    GENERAL = "general"


@dataclass
class TaskDefinition:
    """Definition for a background task."""
    task_id: str
    task_type: str
    priority: TaskPriority
    worker_type: WorkerType
    payload: Dict[str, Any]
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    max_retries: int = 3
    timeout_seconds: int = 300
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # seconds
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecution:
    """Execution record for a task."""
    task_id: str
    execution_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: TaskStatus
    worker_id: str
    attempt_number: int
    result: Optional[Any] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerMetrics:
    """Metrics for background workers."""
    worker_id: str
    worker_type: WorkerType
    tasks_completed: int
    tasks_failed: int
    total_processing_time: float
    average_task_duration: float
    cpu_usage: float
    memory_usage: float
    last_activity: datetime
    status: str  # 'active', 'idle', 'busy', 'error'


@dataclass
class TaskSchedulingConfig:
    """Configuration for task scheduling."""
    max_concurrent_tasks: int = 10
    max_workers_per_type: Dict[WorkerType, int] = field(default_factory=lambda: {
        WorkerType.CPU_INTENSIVE: 4,
        WorkerType.IO_INTENSIVE: 8,
        WorkerType.MEMORY_INTENSIVE: 2,
        WorkerType.GENERAL: 6
    })
    priority_weights: Dict[TaskPriority, float] = field(default_factory=lambda: {
        TaskPriority.CRITICAL: 1.0,
        TaskPriority.HIGH: 0.8,
        TaskPriority.NORMAL: 0.6,
        TaskPriority.LOW: 0.4,
        TaskPriority.BACKGROUND: 0.2
    })
    enable_dynamic_scaling: bool = True
    enable_load_balancing: bool = True
    enable_priority_escalation: bool = True
    escalation_timeout: int = 3600  # seconds
    batch_processing_enabled: bool = True
    batch_size_limits: Dict[str, int] = field(default_factory=lambda: {
        'default': 5,
        'analysis': 3,
        'notification': 10,
        'cleanup': 20
    })


# =============================================================================
# TASK PROCESSORS AND HANDLERS
# =============================================================================

class TaskProcessor(ABC):
    """Abstract base class for task processors."""
    
    @abstractmethod
    async def process(self, task: TaskDefinition) -> Dict[str, Any]:
        """Process a task and return results."""
        pass
    
    @abstractmethod
    def get_estimated_duration(self, task: TaskDefinition) -> int:
        """Get estimated duration for a task in seconds."""
        pass
    
    @abstractmethod
    def get_resource_requirements(self, task: TaskDefinition) -> Dict[str, Any]:
        """Get resource requirements for a task."""
        pass


class AnalysisTaskProcessor(TaskProcessor):
    """Processor for analysis tasks."""
    
    async def process(self, task: TaskDefinition) -> Dict[str, Any]:
        """Process analysis tasks."""
        try:
            logger.info(f"Processing analysis task: {task.task_id}")
            
            # Simulate analysis processing
            payload = task.payload
            analysis_type = payload.get('analysis_type', 'general')
            
            # Different processing times based on analysis type
            if analysis_type == 'resume_analysis':
                processing_time = 30  # 30 seconds
                result = await self._process_resume_analysis(payload)
            elif analysis_type == 'batch_analysis':
                processing_time = 60  # 1 minute
                result = await self._process_batch_analysis(payload)
            elif analysis_type == 'deep_analysis':
                processing_time = 120  # 2 minutes
                result = await self._process_deep_analysis(payload)
            else:
                processing_time = 15  # 15 seconds
                result = await self._process_general_analysis(payload)
            
            # Simulate processing time
            await asyncio.sleep(min(processing_time, 5))  # Cap at 5 seconds for demo
            
            return {
                'success': True,
                'result': result,
                'processing_time': processing_time,
                'analysis_type': analysis_type
            }
            
        except Exception as e:
            logger.error(f"Error processing analysis task {task.task_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _process_resume_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process resume analysis."""
        return {
            'analysis_completed': True,
            'score': 85.5,
            'skills_extracted': ['Python', 'Flask', 'SQL'],
            'experience_years': 5
        }
    
    async def _process_batch_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process batch analysis."""
        batch_size = payload.get('batch_size', 5)
        return {
            'batch_processed': True,
            'items_analyzed': batch_size,
            'average_score': 78.3,
            'completion_rate': 0.95
        }
    
    async def _process_deep_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process deep analysis."""
        return {
            'deep_analysis_completed': True,
            'insights': ['High technical skills', 'Leadership potential'],
            'recommendations': ['Consider for senior role'],
            'confidence': 0.92
        }
    
    async def _process_general_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process general analysis."""
        return {
            'analysis_completed': True,
            'status': 'processed',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_estimated_duration(self, task: TaskDefinition) -> int:
        """Get estimated duration for analysis tasks."""
        analysis_type = task.payload.get('analysis_type', 'general')
        duration_map = {
            'resume_analysis': 30,
            'batch_analysis': 60,
            'deep_analysis': 120,
            'general': 15
        }
        return duration_map.get(analysis_type, 15)
    
    def get_resource_requirements(self, task: TaskDefinition) -> Dict[str, Any]:
        """Get resource requirements for analysis tasks."""
        analysis_type = task.payload.get('analysis_type', 'general')
        
        if analysis_type == 'deep_analysis':
            return {'cpu': 'high', 'memory': 'high', 'worker_type': WorkerType.CPU_INTENSIVE}
        elif analysis_type == 'batch_analysis':
            return {'cpu': 'medium', 'memory': 'medium', 'worker_type': WorkerType.CPU_INTENSIVE}
        else:
            return {'cpu': 'low', 'memory': 'low', 'worker_type': WorkerType.GENERAL}


class NotificationTaskProcessor(TaskProcessor):
    """Processor for notification tasks."""
    
    async def process(self, task: TaskDefinition) -> Dict[str, Any]:
        """Process notification tasks."""
        try:
            logger.info(f"Processing notification task: {task.task_id}")
            
            payload = task.payload
            notification_type = payload.get('notification_type', 'email')
            
            # Simulate notification sending
            if notification_type == 'email':
                result = await self._send_email_notification(payload)
            elif notification_type == 'sms':
                result = await self._send_sms_notification(payload)
            elif notification_type == 'push':
                result = await self._send_push_notification(payload)
            else:
                result = await self._send_generic_notification(payload)
            
            return {
                'success': True,
                'result': result,
                'notification_type': notification_type
            }
            
        except Exception as e:
            logger.error(f"Error processing notification task {task.task_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _send_email_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification."""
        await asyncio.sleep(2)  # Simulate email sending
        return {
            'notification_sent': True,
            'type': 'email',
            'recipient': payload.get('recipient', 'unknown'),
            'sent_at': datetime.utcnow().isoformat()
        }
    
    async def _send_sms_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS notification."""
        await asyncio.sleep(1)  # Simulate SMS sending
        return {
            'notification_sent': True,
            'type': 'sms',
            'recipient': payload.get('recipient', 'unknown'),
            'sent_at': datetime.utcnow().isoformat()
        }
    
    async def _send_push_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send push notification."""
        await asyncio.sleep(0.5)  # Simulate push notification
        return {
            'notification_sent': True,
            'type': 'push',
            'recipient': payload.get('recipient', 'unknown'),
            'sent_at': datetime.utcnow().isoformat()
        }
    
    async def _send_generic_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send generic notification."""
        await asyncio.sleep(1)
        return {
            'notification_sent': True,
            'type': 'generic',
            'recipient': payload.get('recipient', 'unknown'),
            'sent_at': datetime.utcnow().isoformat()
        }
    
    def get_estimated_duration(self, task: TaskDefinition) -> int:
        """Get estimated duration for notification tasks."""
        notification_type = task.payload.get('notification_type', 'email')
        duration_map = {
            'email': 5,
            'sms': 3,
            'push': 2,
            'generic': 3
        }
        return duration_map.get(notification_type, 3)
    
    def get_resource_requirements(self, task: TaskDefinition) -> Dict[str, Any]:
        """Get resource requirements for notification tasks."""
        return {'cpu': 'low', 'memory': 'low', 'worker_type': WorkerType.IO_INTENSIVE}


class CleanupTaskProcessor(TaskProcessor):
    """Processor for cleanup tasks."""
    
    async def process(self, task: TaskDefinition) -> Dict[str, Any]:
        """Process cleanup tasks."""
        try:
            logger.info(f"Processing cleanup task: {task.task_id}")
            
            payload = task.payload
            cleanup_type = payload.get('cleanup_type', 'general')
            
            if cleanup_type == 'cache_cleanup':
                result = await self._perform_cache_cleanup(payload)
            elif cleanup_type == 'log_cleanup':
                result = await self._perform_log_cleanup(payload)
            elif cleanup_type == 'temp_file_cleanup':
                result = await self._perform_temp_file_cleanup(payload)
            else:
                result = await self._perform_general_cleanup(payload)
            
            return {
                'success': True,
                'result': result,
                'cleanup_type': cleanup_type
            }
            
        except Exception as e:
            logger.error(f"Error processing cleanup task {task.task_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _perform_cache_cleanup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cache cleanup."""
        await asyncio.sleep(3)  # Simulate cleanup
        return {
            'cleanup_completed': True,
            'type': 'cache',
            'items_cleaned': 150,
            'space_freed': '45MB'
        }
    
    async def _perform_log_cleanup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform log cleanup."""
        await asyncio.sleep(5)  # Simulate log cleanup
        return {
            'cleanup_completed': True,
            'type': 'logs',
            'files_cleaned': 25,
            'space_freed': '120MB'
        }
    
    async def _perform_temp_file_cleanup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform temporary file cleanup."""
        await asyncio.sleep(2)  # Simulate file cleanup
        return {
            'cleanup_completed': True,
            'type': 'temp_files',
            'files_cleaned': 75,
            'space_freed': '25MB'
        }
    
    async def _perform_general_cleanup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform general cleanup."""
        await asyncio.sleep(3)
        return {
            'cleanup_completed': True,
            'type': 'general',
            'items_processed': 50
        }
    
    def get_estimated_duration(self, task: TaskDefinition) -> int:
        """Get estimated duration for cleanup tasks."""
        cleanup_type = task.payload.get('cleanup_type', 'general')
        duration_map = {
            'cache_cleanup': 10,
            'log_cleanup': 20,
            'temp_file_cleanup': 8,
            'general': 10
        }
        return duration_map.get(cleanup_type, 10)
    
    def get_resource_requirements(self, task: TaskDefinition) -> Dict[str, Any]:
        """Get resource requirements for cleanup tasks."""
        cleanup_type = task.payload.get('cleanup_type', 'general')
        
        if cleanup_type == 'log_cleanup':
            return {'cpu': 'medium', 'memory': 'low', 'worker_type': WorkerType.IO_INTENSIVE}
        else:
            return {'cpu': 'low', 'memory': 'low', 'worker_type': WorkerType.IO_INTENSIVE}


# =============================================================================
# INTELLIGENT TASK SCHEDULER
# =============================================================================

class IntelligentTaskScheduler:
    """Intelligent task scheduler with priority management and load balancing."""
    
    def __init__(self, config: TaskSchedulingConfig):
        self.config = config
        
        # Task queues by priority
        self.priority_queues: Dict[TaskPriority, queue.PriorityQueue] = {
            priority: queue.PriorityQueue() for priority in TaskPriority
        }
        
        # Task tracking
        self.pending_tasks: Dict[str, TaskDefinition] = {}
        self.running_tasks: Dict[str, TaskExecution] = {}
        self.completed_tasks: deque = deque(maxlen=10000)
        
        # Dependency tracking
        self.task_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.waiting_for_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Scheduling metrics
        self.scheduling_metrics = {
            'tasks_scheduled': 0,
            'tasks_completed': 0,
            'average_wait_time': 0.0,
            'priority_distribution': defaultdict(int)
        }
        
        # Batch processing
        self.batch_queues: Dict[str, List[TaskDefinition]] = defaultdict(list)
        self.batch_timers: Dict[str, datetime] = {}
    
    def schedule_task(self, task: TaskDefinition) -> bool:
        """Schedule a task for execution."""
        try:
            # Check dependencies
            if task.dependencies:
                unmet_dependencies = self._check_dependencies(task)
                if unmet_dependencies:
                    self.waiting_for_dependencies[task.task_id] = unmet_dependencies
                    self.pending_tasks[task.task_id] = task
                    logger.info(f"Task {task.task_id} waiting for dependencies: {unmet_dependencies}")
                    return True
            
            # Check if task should be batched
            if self._should_batch_task(task):
                self._add_to_batch(task)
                return True
            
            # Add to appropriate priority queue
            self._add_to_priority_queue(task)
            
            self.pending_tasks[task.task_id] = task
            self.scheduling_metrics['tasks_scheduled'] += 1
            self.scheduling_metrics['priority_distribution'][task.priority] += 1
            
            logger.info(f"Task {task.task_id} scheduled with priority {task.priority.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling task {task.task_id}: {str(e)}")
            return False
    
    def get_next_task(self, worker_type: WorkerType) -> Optional[TaskDefinition]:
        """Get the next task for execution based on priority and worker type."""
        try:
            # Process batches first if ready
            batch_task = self._get_ready_batch_task(worker_type)
            if batch_task:
                return batch_task
            
            # Get highest priority task compatible with worker type
            for priority in TaskPriority:
                if not self.priority_queues[priority].empty():
                    try:
                        # Look for compatible task without removing it
                        temp_tasks = []
                        found_task = None
                        
                        while not self.priority_queues[priority].empty():
                            _, timestamp, task_id = self.priority_queues[priority].get_nowait()
                            
                            if task_id in self.pending_tasks:
                                task = self.pending_tasks[task_id]
                                
                                # Check worker type compatibility
                                if self._is_worker_compatible(task, worker_type):
                                    found_task = task
                                    break
                                else:
                                    # Put back in queue
                                    temp_tasks.append((task.priority.value, timestamp, task_id))
                        
                        # Put back non-compatible tasks
                        for priority_val, ts, tid in temp_tasks:
                            self.priority_queues[priority].put((priority_val, ts, tid))
                        
                        if found_task:
                            # Remove from pending tasks
                            del self.pending_tasks[found_task.task_id]
                            return found_task
                            
                    except queue.Empty:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting next task for worker type {worker_type}: {str(e)}")
            return None
    
    def _check_dependencies(self, task: TaskDefinition) -> Set[str]:
        """Check which dependencies are not yet completed."""
        unmet_dependencies = set()
        
        for dep_task_id in task.dependencies:
            # Check if dependency is completed
            if not self._is_task_completed(dep_task_id):
                unmet_dependencies.add(dep_task_id)
        
        return unmet_dependencies
    
    def _is_task_completed(self, task_id: str) -> bool:
        """Check if a task is completed."""
        # Check in completed tasks
        for execution in self.completed_tasks:
            if execution.task_id == task_id and execution.status == TaskStatus.COMPLETED:
                return True
        return False
    
    def _should_batch_task(self, task: TaskDefinition) -> bool:
        """Determine if a task should be batched."""
        if not self.config.batch_processing_enabled:
            return False
        
        # Check if task type supports batching
        batchable_types = ['notification', 'cleanup', 'data_processing']
        return task.task_type in batchable_types
    
    def _add_to_batch(self, task: TaskDefinition):
        """Add task to batch queue."""
        batch_key = f"{task.task_type}_{task.priority.name}"
        self.batch_queues[batch_key].append(task)
        
        # Set timer for batch if not exists
        if batch_key not in self.batch_timers:
            self.batch_timers[batch_key] = datetime.utcnow()
        
        logger.debug(f"Task {task.task_id} added to batch {batch_key}")
    
    def _get_ready_batch_task(self, worker_type: WorkerType) -> Optional[TaskDefinition]:
        """Get a ready batch task for processing."""
        current_time = datetime.utcnow()
        
        for batch_key, tasks in self.batch_queues.items():
            if not tasks:
                continue
            
            # Check if batch is ready
            batch_start_time = self.batch_timers.get(batch_key)
            if not batch_start_time:
                continue
            
            task_type = batch_key.split('_')[0]
            batch_size_limit = self.config.batch_size_limits.get(task_type, 5)
            
            time_elapsed = (current_time - batch_start_time).total_seconds()
            
            # Process batch if size limit reached or timeout exceeded
            if len(tasks) >= batch_size_limit or time_elapsed >= 60:  # 1 minute timeout
                # Create batch task
                batch_task = self._create_batch_task(batch_key, tasks)
                
                # Clear batch
                self.batch_queues[batch_key] = []
                if batch_key in self.batch_timers:
                    del self.batch_timers[batch_key]
                
                return batch_task
        
        return None
    
    def _create_batch_task(self, batch_key: str, tasks: List[TaskDefinition]) -> TaskDefinition:
        """Create a batch task from individual tasks."""
        task_type, priority_name = batch_key.split('_', 1)
        priority = TaskPriority[priority_name]
        
        # Combine payloads
        batch_payload = {
            'batch_type': task_type,
            'batch_size': len(tasks),
            'individual_tasks': [
                {
                    'task_id': task.task_id,
                    'payload': task.payload
                } for task in tasks
            ]
        }
        
        # Create batch task
        batch_task = TaskDefinition(
            task_id=f"batch_{int(datetime.utcnow().timestamp())}",
            task_type=f"batch_{task_type}",
            priority=priority,
            worker_type=self._determine_batch_worker_type(tasks),
            payload=batch_payload,
            created_at=datetime.utcnow(),
            estimated_duration=sum(task.estimated_duration or 10 for task in tasks)
        )
        
        logger.info(f"Created batch task {batch_task.task_id} with {len(tasks)} individual tasks")
        return batch_task
    
    def _determine_batch_worker_type(self, tasks: List[TaskDefinition]) -> WorkerType:
        """Determine worker type for batch task."""
        # Use the most common worker type in the batch
        worker_types = [task.worker_type for task in tasks]
        return max(set(worker_types), key=worker_types.count)
    
    def _add_to_priority_queue(self, task: TaskDefinition):
        """Add task to priority queue."""
        # Use negative timestamp for proper priority ordering (earlier = higher priority for same priority level)
        timestamp = -time.time()
        
        # Apply priority escalation if enabled
        if self.config.enable_priority_escalation:
            timestamp = self._apply_priority_escalation(task, timestamp)
        
        self.priority_queues[task.priority].put((task.priority.value, timestamp, task.task_id))
    
    def _apply_priority_escalation(self, task: TaskDefinition, timestamp: float) -> float:
        """Apply priority escalation based on wait time."""
        current_time = datetime.utcnow()
        wait_time = (current_time - task.created_at).total_seconds()
        
        # Escalate priority if waiting too long
        if wait_time > self.config.escalation_timeout:
            # Reduce timestamp to increase priority
            escalation_factor = wait_time / self.config.escalation_timeout
            timestamp -= escalation_factor * 1000
            
            logger.info(f"Applied priority escalation to task {task.task_id} (wait time: {wait_time}s)")
        
        return timestamp
    
    def _is_worker_compatible(self, task: TaskDefinition, worker_type: WorkerType) -> bool:
        """Check if worker type is compatible with task requirements."""
        # Get task's preferred worker type
        task_requirements = task.resource_requirements
        preferred_worker_type = task_requirements.get('worker_type', task.worker_type)
        
        # General workers can handle any task
        if worker_type == WorkerType.GENERAL:
            return True
        
        # Specific workers can only handle their type or general tasks
        return preferred_worker_type == worker_type or preferred_worker_type == WorkerType.GENERAL
    
    def mark_task_completed(self, task_id: str, execution: TaskExecution):
        """Mark a task as completed and check for dependent tasks."""
        try:
            # Add to completed tasks
            self.completed_tasks.append(execution)
            self.scheduling_metrics['tasks_completed'] += 1
            
            # Check for tasks waiting on this dependency
            dependent_tasks = []
            for waiting_task_id, dependencies in list(self.waiting_for_dependencies.items()):
                if task_id in dependencies:
                    dependencies.remove(task_id)
                    
                    # If no more dependencies, schedule the task
                    if not dependencies:
                        del self.waiting_for_dependencies[waiting_task_id]
                        if waiting_task_id in self.pending_tasks:
                            dependent_task = self.pending_tasks[waiting_task_id]
                            dependent_tasks.append(dependent_task)
            
            # Schedule dependent tasks
            for dependent_task in dependent_tasks:
                logger.info(f"Scheduling dependent task {dependent_task.task_id}")
                self._add_to_priority_queue(dependent_task)
            
        except Exception as e:
            logger.error(f"Error marking task {task_id} as completed: {str(e)}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        try:
            queue_status = {}
            
            for priority in TaskPriority:
                queue_status[priority.name] = {
                    'pending_count': self.priority_queues[priority].qsize(),
                    'priority_value': priority.value
                }
            
            return {
                'priority_queues': queue_status,
                'pending_tasks': len(self.pending_tasks),
                'running_tasks': len(self.running_tasks),
                'waiting_for_dependencies': len(self.waiting_for_dependencies),
                'batch_queues': {k: len(v) for k, v in self.batch_queues.items()},
                'metrics': self.scheduling_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {'error': str(e)}


# =============================================================================
# BACKGROUND TASK OPTIMIZER
# =============================================================================

class BackgroundTaskOptimizer:
    """
    Enterprise background task optimizer with intelligent scheduling,
    dynamic worker management, and performance optimization.
    """
    
    def __init__(self, app=None):
        self.app = app
        
        # Configuration
        self.config = TaskSchedulingConfig()
        
        # Task processors
        self.task_processors: Dict[str, TaskProcessor] = {
            'analysis': AnalysisTaskProcessor(),
            'notification': NotificationTaskProcessor(),
            'cleanup': CleanupTaskProcessor(),
            'batch_analysis': AnalysisTaskProcessor(),
            'batch_notification': NotificationTaskProcessor(),
            'batch_cleanup': CleanupTaskProcessor()
        }
        
        # Scheduler and workers
        self.scheduler = IntelligentTaskScheduler(self.config)
        self.worker_pools: Dict[WorkerType, ThreadPoolExecutor] = {}
        self.worker_metrics: Dict[str, WorkerMetrics] = {}
        
        # Task execution tracking
        self.task_executions: Dict[str, TaskExecution] = {}
        self.execution_history = deque(maxlen=10000)
        
        # Performance monitoring
        self.performance_metrics = {
            'total_tasks_processed': 0,
            'average_processing_time': 0.0,
            'success_rate': 1.0,
            'worker_utilization': 0.0,
            'queue_wait_time': 0.0
        }
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Dynamic scaling
        self.enable_dynamic_scaling = True
        self.scaling_decisions = deque(maxlen=100)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize background task optimizer with Flask app."""
        self.app = app
        
        # Load configuration
        self._load_config_from_app()
        
        # Initialize worker pools
        self._initialize_worker_pools()
        
        # Start background monitoring
        self.start_monitoring()
        
        logger.info("Background task optimizer initialized")
    
    def _load_config_from_app(self):
        """Load configuration from Flask app config."""
        if not self.app:
            return
        
        config = self.app.config
        
        # Update scheduling config
        self.config.max_concurrent_tasks = config.get('MAX_BACKGROUND_TASKS', 10)
        self.config.enable_dynamic_scaling = config.get('ENABLE_DYNAMIC_TASK_SCALING', True)
        self.config.enable_load_balancing = config.get('ENABLE_TASK_LOAD_BALANCING', True)
        self.config.batch_processing_enabled = config.get('ENABLE_BATCH_PROCESSING', True)
        
        # Update worker limits
        worker_limits = config.get('BACKGROUND_WORKER_LIMITS', {})
        if worker_limits:
            for worker_type_name, limit in worker_limits.items():
                try:
                    worker_type = WorkerType(worker_type_name)
                    self.config.max_workers_per_type[worker_type] = limit
                except ValueError:
                    logger.warning(f"Unknown worker type in config: {worker_type_name}")
    
    def _initialize_worker_pools(self):
        """Initialize worker pools for different task types."""
        try:
            for worker_type, max_workers in self.config.max_workers_per_type.items():
                self.worker_pools[worker_type] = ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix=f"bg_worker_{worker_type.value}"
                )
                
                logger.info(f"Initialized {worker_type.value} worker pool with {max_workers} workers")
            
        except Exception as e:
            logger.error(f"Error initializing worker pools: {str(e)}")
    
    # =============================================================================
    # TASK SUBMISSION AND MANAGEMENT
    # =============================================================================
    
    def submit_task(self, task_type: str, payload: Dict[str, Any], 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   worker_type: WorkerType = WorkerType.GENERAL,
                   dependencies: Optional[List[str]] = None,
                   scheduled_at: Optional[datetime] = None,
                   max_retries: int = 3,
                   timeout_seconds: int = 300) -> str:
        """Submit a task for background processing."""
        try:
            # Generate task ID
            task_id = f"{task_type}_{int(datetime.utcnow().timestamp())}_{id(payload)}"
            
            # Get task processor to estimate requirements
            processor = self.task_processors.get(task_type)
            if not processor:
                raise ValueError(f"No processor available for task type: {task_type}")
            
            # Create task definition
            task = TaskDefinition(
                task_id=task_id,
                task_type=task_type,
                priority=priority,
                worker_type=worker_type,
                payload=payload,
                created_at=datetime.utcnow(),
                scheduled_at=scheduled_at,
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
                dependencies=dependencies or [],
                estimated_duration=processor.get_estimated_duration(task)
            )
            
            # Get resource requirements
            task.resource_requirements = processor.get_resource_requirements(task)
            
            # Schedule the task
            if self.scheduler.schedule_task(task):
                logger.info(f"Task {task_id} submitted successfully")
                
                # Start task processing if not already running
                if not self.monitoring_active:
                    self.start_monitoring()
                
                return task_id
            else:
                raise Exception("Failed to schedule task")
            
        except Exception as e:
            logger.error(f"Error submitting task: {str(e)}")
            raise
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        try:
            # Check if task is pending
            if task_id in self.scheduler.pending_tasks:
                del self.scheduler.pending_tasks[task_id]
                logger.info(f"Cancelled pending task {task_id}")
                return True
            
            # Check if task is running
            if task_id in self.task_executions:
                execution = self.task_executions[task_id]
                execution.status = TaskStatus.CANCELLED
                execution.completed_at = datetime.utcnow()
                
                # Move to history
                self.execution_history.append(execution)
                del self.task_executions[task_id]
                
                logger.info(f"Cancelled running task {task_id}")
                return True
            
            logger.warning(f"Task {task_id} not found for cancellation")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task."""
        try:
            # Check running tasks
            if task_id in self.task_executions:
                execution = self.task_executions[task_id]
                return {
                    'task_id': task_id,
                    'status': execution.status.value,
                    'started_at': execution.started_at.isoformat(),
                    'worker_id': execution.worker_id,
                    'attempt_number': execution.attempt_number
                }
            
            # Check pending tasks
            if task_id in self.scheduler.pending_tasks:
                task = self.scheduler.pending_tasks[task_id]
                return {
                    'task_id': task_id,
                    'status': 'pending',
                    'created_at': task.created_at.isoformat(),
                    'priority': task.priority.name,
                    'estimated_duration': task.estimated_duration
                }
            
            # Check completed tasks
            for execution in self.execution_history:
                if execution.task_id == task_id:
                    return {
                        'task_id': task_id,
                        'status': execution.status.value,
                        'started_at': execution.started_at.isoformat(),
                        'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                        'result': execution.result,
                        'error': execution.error
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return {'error': str(e)}
    
    # =============================================================================
    # TASK PROCESSING
    # =============================================================================
    
    async def _process_task_async(self, task: TaskDefinition, worker_id: str) -> TaskExecution:
        """Process a task asynchronously."""
        execution_id = f"exec_{int(datetime.utcnow().timestamp())}"
        start_time = datetime.utcnow()
        
        # Create execution record
        execution = TaskExecution(
            task_id=task.task_id,
            execution_id=execution_id,
            started_at=start_time,
            completed_at=None,
            status=TaskStatus.RUNNING,
            worker_id=worker_id,
            attempt_number=1
        )
        
        # Track execution
        self.task_executions[task.task_id] = execution
        
        try:
            logger.info(f"Starting task {task.task_id} on worker {worker_id}")
            
            # Get task processor
            processor = self.task_processors.get(task.task_type)
            if not processor:
                raise Exception(f"No processor for task type: {task.task_type}")
            
            # Process the task with timeout
            try:
                result = await asyncio.wait_for(
                    processor.process(task),
                    timeout=task.timeout_seconds
                )
                
                # Update execution record
                execution.status = TaskStatus.COMPLETED
                execution.result = result
                execution.completed_at = datetime.utcnow()
                
                # Calculate metrics
                processing_time = (execution.completed_at - execution.started_at).total_seconds()
                execution.metrics = {
                    'processing_time': processing_time,
                    'success': result.get('success', True)
                }
                
                logger.info(f"Task {task.task_id} completed successfully in {processing_time:.2f}s")
                
            except asyncio.TimeoutError:
                raise Exception(f"Task timed out after {task.timeout_seconds} seconds")
            
        except Exception as e:
            # Update execution record with error
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            
            logger.error(f"Task {task.task_id} failed: {str(e)}")
        
        finally:
            # Move to history and clean up
            self.execution_history.append(execution)
            if task.task_id in self.task_executions:
                del self.task_executions[task.task_id]
            
            # Notify scheduler of completion
            self.scheduler.mark_task_completed(task.task_id, execution)
        
        return execution
    
    def _process_task_sync(self, task: TaskDefinition, worker_id: str) -> TaskExecution:
        """Process a task synchronously (wrapper for async processing)."""
        try:
            # Create new event loop for this worker thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._process_task_async(task, worker_id))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in synchronous task processing: {str(e)}")
            
            # Create failed execution record
            execution = TaskExecution(
                task_id=task.task_id,
                execution_id=f"exec_failed_{int(datetime.utcnow().timestamp())}",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status=TaskStatus.FAILED,
                worker_id=worker_id,
                attempt_number=1,
                error=str(e)
            )
            
            self.execution_history.append(execution)
            return execution
    
    # =============================================================================
    # BACKGROUND MONITORING AND PROCESSING
    # =============================================================================
    
    def start_monitoring(self):
        """Start background monitoring and task processing."""
        if self.monitoring_active:
            logger.warning("Background task monitoring already active")
            return
        
        self.monitoring_active = True
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Process tasks for each worker type
                    for worker_type, worker_pool in self.worker_pools.items():
                        self._process_worker_queue(worker_type, worker_pool)
                    
                    # Update performance metrics
                    self._update_performance_metrics()
                    
                    # Dynamic scaling check
                    if self.enable_dynamic_scaling:
                        self._check_dynamic_scaling()
                    
                    # Sleep for 1 second before next iteration
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in background monitoring loop: {str(e)}")
                    time.sleep(5)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Background task monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring and task processing."""
        self.monitoring_active = False
        
        # Shutdown worker pools
        for worker_type, worker_pool in self.worker_pools.items():
            worker_pool.shutdown(wait=True)
            logger.info(f"Shutdown {worker_type.value} worker pool")
        
        logger.info("Background task monitoring stopped")
    
    def _process_worker_queue(self, worker_type: WorkerType, worker_pool: ThreadPoolExecutor):
        """Process queue for a specific worker type."""
        try:
            # Check available capacity
            active_threads = worker_pool._threads
            max_workers = worker_pool._max_workers
            available_capacity = max_workers - len(active_threads)
            
            if available_capacity <= 0:
                return
            
            # Get next task
            task = self.scheduler.get_next_task(worker_type)
            if not task:
                return
            
            # Submit task for processing
            worker_id = f"{worker_type.value}_{threading.get_ident()}"
            
            future = worker_pool.submit(self._process_task_sync, task, worker_id)
            
            # Optional: Track futures for completion monitoring
            # Could add callback with future.add_done_callback()
            
        except Exception as e:
            logger.error(f"Error processing worker queue for {worker_type.value}: {str(e)}")
    
    def _update_performance_metrics(self):
        """Update performance metrics."""
        try:
            # Calculate metrics from recent executions
            recent_executions = list(self.execution_history)[-100:]  # Last 100 executions
            
            if recent_executions:
                # Success rate
                successful_tasks = sum(1 for ex in recent_executions if ex.status == TaskStatus.COMPLETED)
                self.performance_metrics['success_rate'] = successful_tasks / len(recent_executions)
                
                # Average processing time
                processing_times = [
                    (ex.completed_at - ex.started_at).total_seconds()
                    for ex in recent_executions
                    if ex.completed_at and ex.started_at
                ]
                
                if processing_times:
                    self.performance_metrics['average_processing_time'] = sum(processing_times) / len(processing_times)
                
                # Total tasks processed
                self.performance_metrics['total_tasks_processed'] = len(self.execution_history)
            
            # Worker utilization
            total_workers = sum(pool._max_workers for pool in self.worker_pools.values())
            active_workers = sum(len(pool._threads) for pool in self.worker_pools.values())
            
            if total_workers > 0:
                self.performance_metrics['worker_utilization'] = active_workers / total_workers
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
    
    def _check_dynamic_scaling(self):
        """Check if dynamic scaling is needed."""
        try:
            queue_status = self.scheduler.get_queue_status()
            
            for worker_type, worker_pool in self.worker_pools.items():
                current_max = worker_pool._max_workers
                
                # Calculate queue load for this worker type
                total_pending = sum(
                    queue_status['priority_queues'][priority]['pending_count']
                    for priority in queue_status['priority_queues']
                )
                
                # Simple scaling logic
                if total_pending > current_max * 2:  # High load
                    new_max = min(current_max + 1, 20)  # Scale up by 1, max 20
                    self._resize_worker_pool(worker_type, new_max)
                    
                elif total_pending == 0 and current_max > 1:  # No load
                    new_max = max(current_max - 1, 1)  # Scale down by 1, min 1
                    self._resize_worker_pool(worker_type, new_max)
                    
        except Exception as e:
            logger.error(f"Error checking dynamic scaling: {str(e)}")
    
    def _resize_worker_pool(self, worker_type: WorkerType, new_max_workers: int):
        """Resize worker pool (simplified implementation)."""
        try:
            current_max = self.worker_pools[worker_type]._max_workers
            
            if new_max_workers != current_max:
                # Record scaling decision
                scaling_decision = {
                    'timestamp': datetime.utcnow(),
                    'worker_type': worker_type.value,
                    'old_max': current_max,
                    'new_max': new_max_workers,
                    'reason': 'dynamic_scaling'
                }
                
                self.scaling_decisions.append(scaling_decision)
                
                # In a real implementation, you would resize the pool
                # For now, just log the decision
                logger.info(f"Dynamic scaling: {worker_type.value} pool {current_max} → {new_max_workers}")
                
        except Exception as e:
            logger.error(f"Error resizing worker pool {worker_type.value}: {str(e)}")
    
    # =============================================================================
    # PUBLIC API METHODS
    # =============================================================================
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of background task optimizer."""
        try:
            queue_status = self.scheduler.get_queue_status()
            
            worker_status = {}
            for worker_type, worker_pool in self.worker_pools.items():
                worker_status[worker_type.value] = {
                    'max_workers': worker_pool._max_workers,
                    'active_threads': len(worker_pool._threads),
                    'queue_size': getattr(worker_pool._work_queue, 'qsize', lambda: 0)()
                }
            
            return {
                'queue_status': queue_status,
                'worker_status': worker_status,
                'performance_metrics': self.performance_metrics,
                'task_processors': list(self.task_processors.keys()),
                'configuration': {
                    'max_concurrent_tasks': self.config.max_concurrent_tasks,
                    'dynamic_scaling': self.enable_dynamic_scaling,
                    'batch_processing': self.config.batch_processing_enabled
                },
                'recent_scaling_decisions': list(self.scaling_decisions)[-10:],
                'execution_history_size': len(self.execution_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {str(e)}")
            return {'error': str(e)}
    
    def get_task_metrics(self) -> Dict[str, Any]:
        """Get task processing metrics."""
        try:
            recent_executions = list(self.execution_history)[-1000:]  # Last 1000 executions
            
            if not recent_executions:
                return {'message': 'No task execution history available'}
            
            # Group by task type
            task_type_metrics = defaultdict(lambda: {
                'count': 0,
                'success_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0
            })
            
            for execution in recent_executions:
                task_type = execution.task_id.split('_')[0]  # Extract task type from ID
                metrics = task_type_metrics[task_type]
                
                metrics['count'] += 1
                if execution.status == TaskStatus.COMPLETED:
                    metrics['success_count'] += 1
                
                if execution.started_at and execution.completed_at:
                    processing_time = (execution.completed_at - execution.started_at).total_seconds()
                    metrics['total_time'] += processing_time
            
            # Calculate averages
            for task_type, metrics in task_type_metrics.items():
                if metrics['count'] > 0:
                    metrics['success_rate'] = metrics['success_count'] / metrics['count']
                    metrics['avg_time'] = metrics['total_time'] / metrics['count']
            
            return {
                'task_type_metrics': dict(task_type_metrics),
                'overall_metrics': self.performance_metrics,
                'total_executions': len(recent_executions)
            }
            
        except Exception as e:
            logger.error(f"Error getting task metrics: {str(e)}")
            return {'error': str(e)}


# =============================================================================
# GLOBAL BACKGROUND TASK OPTIMIZER INSTANCE
# =============================================================================

background_task_optimizer = BackgroundTaskOptimizer()
