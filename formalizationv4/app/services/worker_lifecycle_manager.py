"""
Smart Resource Scaling - Worker Lifecycle Manager
Manages the lifecycle of worker processes with graceful scaling.
"""
import asyncio
import logging
import uuid
import signal
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class WorkerLifecycleManager:
    """Manages worker process lifecycle with graceful scaling."""
    
    def __init__(self):
        self.active_workers = {}
        self.worker_stats = {}
        self.startup_queue = asyncio.Queue()
        self.shutdown_queue = asyncio.Queue()
        self.max_workers = 8
        self.min_workers = 2
        self.resource_limits = {
            'memory_limit': '1.5GB',
            'cpu_limit': 2
        }
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False
        self.manager_task = None
    
    async def start_manager(self):
        """Start the worker lifecycle manager."""
        if self.running:
            logger.warning("Worker lifecycle manager is already running")
            return
        
        self.running = True
        self.manager_task = asyncio.create_task(self._management_loop())
        logger.info("Worker lifecycle manager started")
    
    async def stop_manager(self):
        """Stop the worker lifecycle manager."""
        self.running = False
        if self.manager_task:
            self.manager_task.cancel()
            try:
                await self.manager_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown all workers
        await self._shutdown_all_workers()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Worker lifecycle manager stopped")
    
    async def _management_loop(self):
        """Main management loop for worker lifecycle."""
        while self.running:
            try:
                # Process startup requests
                await self._process_startup_queue()
                
                # Process shutdown requests
                await self._process_shutdown_queue()
                
                # Health check on active workers
                await self._health_check_workers()
                
                # Clean up completed workers
                await self._cleanup_completed_workers()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in worker management loop: {str(e)}")
                await asyncio.sleep(30)
    
    async def scale_up_workers(self, target_count: int, worker_type: str = 'analysis') -> Dict[str, Any]:
        """Gracefully scale up workers."""
        try:
            current_count = len([w for w in self.active_workers.values() if w['type'] == worker_type])
            
            if target_count <= current_count:
                return {
                    'success': True,
                    'message': f"Already have {current_count} {worker_type} workers (target: {target_count})",
                    'current_count': current_count,
                    'target_count': target_count
                }
            
            workers_to_add = min(target_count - current_count, self.max_workers - current_count)
            
            if workers_to_add <= 0:
                return {
                    'success': False,
                    'message': f"Cannot scale up: already at maximum capacity ({self.max_workers})",
                    'current_count': current_count,
                    'target_count': target_count
                }
            
            # Queue worker startup requests
            startup_requests = []
            for i in range(workers_to_add):
                worker_id = f"{worker_type}_worker_{uuid.uuid4().hex[:8]}"
                startup_request = {
                    'worker_id': worker_id,
                    'worker_type': worker_type,
                    'priority': 'normal'
                }
                await self.startup_queue.put(startup_request)
                startup_requests.append(worker_id)
            
            logger.info(f"Queued {workers_to_add} {worker_type} workers for startup: {startup_requests}")
            
            return {
                'success': True,
                'message': f"Queued {workers_to_add} {worker_type} workers for startup",
                'current_count': current_count,
                'target_count': target_count,
                'workers_queued': startup_requests
            }
            
        except Exception as e:
            logger.error(f"Error scaling up workers: {str(e)}")
            return {
                'success': False,
                'message': f"Error scaling up workers: {str(e)}",
                'current_count': current_count,
                'target_count': target_count
            }
    
    async def scale_down_workers(self, target_count: int, worker_type: str = 'analysis') -> Dict[str, Any]:
        """Gracefully scale down workers."""
        try:
            current_workers = [w for w in self.active_workers.items() if w[1]['type'] == worker_type]
            current_count = len(current_workers)
            
            if target_count >= current_count:
                return {
                    'success': True,
                    'message': f"Already have {current_count} {worker_type} workers (target: {target_count})",
                    'current_count': current_count,
                    'target_count': target_count
                }
            
            workers_to_remove = max(current_count - target_count, 0)
            min_workers_to_keep = max(target_count, self.min_workers)
            
            if current_count - workers_to_remove < min_workers_to_keep:
                workers_to_remove = current_count - min_workers_to_keep
            
            if workers_to_remove <= 0:
                return {
                    'success': False,
                    'message': f"Cannot scale down: already at minimum capacity ({self.min_workers})",
                    'current_count': current_count,
                    'target_count': target_count
                }
            
            # Select workers for removal (prioritize idle workers)
            idle_workers = await self._get_idle_workers(worker_type)
            busy_workers = [w for w in current_workers if w[0] not in [iw[0] for iw in idle_workers]]
            
            # Queue shutdown requests
            shutdown_requests = []
            
            # Remove idle workers first
            for worker_id, worker_info in idle_workers[:workers_to_remove]:
                shutdown_request = {
                    'worker_id': worker_id,
                    'worker_type': worker_type,
                    'graceful': True,
                    'timeout': 60
                }
                await self.shutdown_queue.put(shutdown_request)
                shutdown_requests.append(worker_id)
                workers_to_remove -= 1
                
                if workers_to_remove <= 0:
                    break
            
            # If we still need to remove workers, queue busy ones
            if workers_to_remove > 0:
                for worker_id, worker_info in busy_workers[:workers_to_remove]:
                    shutdown_request = {
                        'worker_id': worker_id,
                        'worker_type': worker_type,
                        'graceful': True,
                        'timeout': 300  # Longer timeout for busy workers
                    }
                    await self.shutdown_queue.put(shutdown_request)
                    shutdown_requests.append(worker_id)
            
            logger.info(f"Queued {len(shutdown_requests)} {worker_type} workers for shutdown: {shutdown_requests}")
            
            return {
                'success': True,
                'message': f"Queued {len(shutdown_requests)} {worker_type} workers for shutdown",
                'current_count': current_count,
                'target_count': target_count,
                'workers_queued': shutdown_requests
            }
            
        except Exception as e:
            logger.error(f"Error scaling down workers: {str(e)}")
            return {
                'success': False,
                'message': f"Error scaling down workers: {str(e)}",
                'current_count': current_count if 'current_count' in locals() else 0,
                'target_count': target_count
            }
    
    async def _process_startup_queue(self):
        """Process worker startup requests."""
        while not self.startup_queue.empty() and len(self.active_workers) < self.max_workers:
            try:
                startup_request = await asyncio.wait_for(self.startup_queue.get(), timeout=1.0)
                
                worker_id = startup_request['worker_id']
                worker_type = startup_request['worker_type']
                
                # Pre-allocate resources
                await self._pre_allocate_worker_resources(worker_id)
                
                # Start worker with resource limits
                worker_process = await self._start_worker_with_limits(
                    worker_id=worker_id,
                    worker_type=worker_type,
                    memory_limit=self.resource_limits['memory_limit'],
                    cpu_limit=self.resource_limits['cpu_limit']
                )
                
                if worker_process:
                    self.active_workers[worker_id] = {
                        'process': worker_process,
                        'type': worker_type,
                        'started_at': datetime.utcnow(),
                        'memory_limit': self.resource_limits['memory_limit'],
                        'cpu_limit': self.resource_limits['cpu_limit'],
                        'status': 'starting',
                        'health_check_failures': 0,
                        'last_health_check': datetime.utcnow()
                    }
                    
                    # Wait for worker to be ready
                    if await self._wait_for_worker_ready(worker_id, timeout=30):
                        self.active_workers[worker_id]['status'] = 'active'
                        logger.info(f"Successfully started {worker_type} worker {worker_id}")
                    else:
                        logger.warning(f"Worker {worker_id} failed to become ready within timeout")
                        self.active_workers[worker_id]['status'] = 'failed'
                
            except asyncio.TimeoutError:
                break  # No more startup requests
            except Exception as e:
                logger.error(f"Error processing startup request: {str(e)}")
    
    async def _process_shutdown_queue(self):
        """Process worker shutdown requests."""
        while not self.shutdown_queue.empty():
            try:
                shutdown_request = await asyncio.wait_for(self.shutdown_queue.get(), timeout=1.0)
                
                worker_id = shutdown_request['worker_id']
                graceful = shutdown_request.get('graceful', True)
                timeout = shutdown_request.get('timeout', 60)
                
                await self._graceful_worker_shutdown(worker_id, graceful, timeout)
                
            except asyncio.TimeoutError:
                break  # No more shutdown requests
            except Exception as e:
                logger.error(f"Error processing shutdown request: {str(e)}")
    
    async def _start_worker_with_limits(self, worker_id: str, worker_type: str, 
                                       memory_limit: str, cpu_limit: int) -> Optional[subprocess.Popen]:
        """Start a worker process with resource limits."""
        try:
            # Prepare command based on worker type
            if worker_type == 'analysis':
                cmd = ['python', 'worker.py']
            elif worker_type == 'queue':
                cmd = ['python', '-c', 'from app.services.queue_service import QueueService; import asyncio; asyncio.run(QueueService().process_queue())']
            else:
                logger.error(f"Unknown worker type: {worker_type}")
                return None
            
            # Add environment variables for resource limits
            env = {
                'WORKER_ID': worker_id,
                'WORKER_TYPE': worker_type,
                'MEMORY_LIMIT': memory_limit,
                'CPU_LIMIT': str(cpu_limit)
            }
            
            # Start process using thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(
                self.executor,
                self._start_process_sync,
                cmd,
                env
            )
            
            return process
            
        except Exception as e:
            logger.error(f"Error starting worker {worker_id}: {str(e)}")
            return None
    
    def _start_process_sync(self, cmd: List[str], env: Dict[str, str]) -> subprocess.Popen:
        """Start process synchronously (for use in thread pool)."""
        import os
        full_env = os.environ.copy()
        full_env.update(env)
        
        return subprocess.Popen(
            cmd,
            env=full_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
    
    async def _pre_allocate_worker_resources(self, worker_id: str):
        """Pre-allocate resources for a worker."""
        try:
            # This could involve setting up memory pools, 
            # file descriptors, or other resources
            logger.debug(f"Pre-allocating resources for worker {worker_id}")
            await asyncio.sleep(0.1)  # Simulate resource allocation
            
        except Exception as e:
            logger.error(f"Error pre-allocating resources for worker {worker_id}: {str(e)}")
    
    async def _wait_for_worker_ready(self, worker_id: str, timeout: int = 30) -> bool:
        """Wait for worker to be ready."""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if worker_id not in self.active_workers:
                    return False
                
                worker_info = self.active_workers[worker_id]
                
                # Check if process is still alive
                if worker_info['process'].poll() is not None:
                    logger.error(f"Worker {worker_id} process died during startup")
                    return False
                
                # Simulate readiness check (could be replaced with actual health check)
                await asyncio.sleep(1)
                
                # For now, assume worker is ready after 3 seconds
                if time.time() - start_time > 3:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for worker {worker_id} to be ready: {str(e)}")
            return False
    
    async def _get_idle_workers(self, worker_type: str) -> List[tuple]:
        """Get list of idle workers of the specified type."""
        try:
            idle_workers = []
            
            for worker_id, worker_info in self.active_workers.items():
                if worker_info['type'] == worker_type and worker_info['status'] == 'active':
                    # Check if worker is idle (simple heuristic)
                    # In a real implementation, this would check actual worker activity
                    if self._is_worker_idle(worker_id):
                        idle_workers.append((worker_id, worker_info))
            
            return idle_workers
            
        except Exception as e:
            logger.error(f"Error getting idle workers: {str(e)}")
            return []
    
    def _is_worker_idle(self, worker_id: str) -> bool:
        """Check if a worker is idle (simple implementation)."""
        try:
            worker_info = self.active_workers.get(worker_id)
            if not worker_info:
                return False
            
            # Simple heuristic: worker is idle if it's been running for more than 5 minutes
            # and hasn't failed health checks
            running_time = (datetime.utcnow() - worker_info['started_at']).total_seconds()
            return running_time > 300 and worker_info['health_check_failures'] == 0
            
        except Exception as e:
            logger.error(f"Error checking if worker {worker_id} is idle: {str(e)}")
            return False
    
    async def _graceful_worker_shutdown(self, worker_id: str, graceful: bool = True, timeout: int = 60):
        """Gracefully shutdown a worker."""
        try:
            if worker_id not in self.active_workers:
                logger.warning(f"Worker {worker_id} not found for shutdown")
                return
            
            worker_info = self.active_workers[worker_id]
            worker_info['status'] = 'shutting_down'
            
            process = worker_info['process']
            
            if graceful:
                # Send SIGTERM for graceful shutdown
                try:
                    if hasattr(process, 'terminate'):
                        process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        await asyncio.wait_for(
                            self._wait_for_process_completion(process),
                            timeout=timeout
                        )
                        logger.info(f"Worker {worker_id} shutdown gracefully")
                    except asyncio.TimeoutError:
                        logger.warning(f"Worker {worker_id} did not shutdown gracefully, forcing termination")
                        if hasattr(process, 'kill'):
                            process.kill()
                        
                except Exception as e:
                    logger.error(f"Error during graceful shutdown of worker {worker_id}: {str(e)}")
                    # Force kill as fallback
                    if hasattr(process, 'kill'):
                        process.kill()
            else:
                # Force shutdown
                if hasattr(process, 'kill'):
                    process.kill()
                logger.info(f"Worker {worker_id} force terminated")
            
            # Clean up resources
            await self._cleanup_worker_resources(worker_id)
            
            # Remove from active workers
            del self.active_workers[worker_id]
            
        except Exception as e:
            logger.error(f"Error shutting down worker {worker_id}: {str(e)}")
    
    async def _wait_for_process_completion(self, process: subprocess.Popen):
        """Wait for process to complete."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, process.wait)
    
    async def _cleanup_worker_resources(self, worker_id: str):
        """Clean up resources for a worker."""
        try:
            logger.debug(f"Cleaning up resources for worker {worker_id}")
            # This could involve cleaning up memory pools, 
            # file descriptors, or other resources
            await asyncio.sleep(0.1)  # Simulate resource cleanup
            
        except Exception as e:
            logger.error(f"Error cleaning up resources for worker {worker_id}: {str(e)}")
    
    async def _health_check_workers(self):
        """Perform health checks on active workers."""
        try:
            current_time = datetime.utcnow()
            
            for worker_id, worker_info in list(self.active_workers.items()):
                try:
                    # Check if process is still alive
                    if worker_info['process'].poll() is not None:
                        logger.warning(f"Worker {worker_id} process died, marking for cleanup")
                        worker_info['status'] = 'failed'
                        worker_info['health_check_failures'] += 1
                        continue
                    
                    # Update last health check time
                    worker_info['last_health_check'] = current_time
                    
                    # Reset health check failures if worker is responding
                    if worker_info['status'] == 'active':
                        worker_info['health_check_failures'] = 0
                        
                except Exception as e:
                    logger.error(f"Error health checking worker {worker_id}: {str(e)}")
                    worker_info['health_check_failures'] += 1
                    
                    # Mark worker as failed after 3 consecutive failures
                    if worker_info['health_check_failures'] >= 3:
                        logger.error(f"Worker {worker_id} failed health check 3 times, marking as failed")
                        worker_info['status'] = 'failed'
                        
        except Exception as e:
            logger.error(f"Error during worker health checks: {str(e)}")
    
    async def _cleanup_completed_workers(self):
        """Clean up workers that have completed or failed."""
        try:
            workers_to_remove = []
            
            for worker_id, worker_info in self.active_workers.items():
                if worker_info['status'] in ['failed', 'completed']:
                    workers_to_remove.append(worker_id)
            
            for worker_id in workers_to_remove:
                logger.info(f"Cleaning up completed/failed worker {worker_id}")
                await self._graceful_worker_shutdown(worker_id, graceful=False, timeout=5)
                
        except Exception as e:
            logger.error(f"Error cleaning up completed workers: {str(e)}")
    
    async def _shutdown_all_workers(self):
        """Shutdown all active workers."""
        try:
            logger.info("Shutting down all active workers")
            
            # Queue shutdown for all workers
            for worker_id in list(self.active_workers.keys()):
                shutdown_request = {
                    'worker_id': worker_id,
                    'worker_type': self.active_workers[worker_id]['type'],
                    'graceful': True,
                    'timeout': 30
                }
                await self.shutdown_queue.put(shutdown_request)
            
            # Process all shutdown requests
            while not self.shutdown_queue.empty():
                await self._process_shutdown_queue()
                await asyncio.sleep(1)
            
            # Force cleanup any remaining workers
            for worker_id in list(self.active_workers.keys()):
                await self._graceful_worker_shutdown(worker_id, graceful=False, timeout=5)
            
            logger.info("All workers shutdown complete")
            
        except Exception as e:
            logger.error(f"Error shutting down all workers: {str(e)}")
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get current status of all workers."""
        try:
            status = {
                'total_workers': len(self.active_workers),
                'workers_by_type': {},
                'workers_by_status': {},
                'resource_usage': {
                    'memory_limit_total': 0,
                    'cpu_limit_total': 0
                },
                'workers': {}
            }
            
            for worker_id, worker_info in self.active_workers.items():
                worker_type = worker_info['type']
                worker_status = worker_info['status']
                
                # Count by type
                status['workers_by_type'][worker_type] = status['workers_by_type'].get(worker_type, 0) + 1
                
                # Count by status
                status['workers_by_status'][worker_status] = status['workers_by_status'].get(worker_status, 0) + 1
                
                # Add to resource usage
                status['resource_usage']['cpu_limit_total'] += worker_info.get('cpu_limit', 0)
                
                # Worker details
                status['workers'][worker_id] = {
                    'type': worker_type,
                    'status': worker_status,
                    'started_at': worker_info['started_at'].isoformat(),
                    'uptime_seconds': (datetime.utcnow() - worker_info['started_at']).total_seconds(),
                    'health_check_failures': worker_info.get('health_check_failures', 0),
                    'last_health_check': worker_info.get('last_health_check', datetime.utcnow()).isoformat()
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting worker status: {str(e)}")
            return {'error': str(e)}

# Global instance
worker_lifecycle_manager = WorkerLifecycleManager()
