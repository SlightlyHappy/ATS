#!/usr/bin/env python3
"""
Enhanced Background worker with Smart Resource Scaling for HR Consultancy ATS v1.2
Handles queue processing with intelligent resource management and dynamic scaling.
"""
import os
import sys
import asyncio
import signal
import logging
import threading
from contextlib import asynccontextmanager
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.services.queue_service import QueueService
from scripts.sales_background_tasks import SalesIntelligenceScheduler

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnhancedQueueWorker:
    """Enhanced worker with Smart Resource Scaling integration."""
    
    def __init__(self):
        self.app = create_app()
        self.queue_service = QueueService()
        self.sales_scheduler = SalesIntelligenceScheduler()
        self.running = False
        self.tasks = set()
        self.scheduler_thread = None
        
        # Smart Resource Scaling integration
        self.scaling_enabled = os.getenv('ENABLE_SMART_SCALING', 'true').lower() == 'true'
        self.worker_id = f"worker_{os.getpid()}"
        self.performance_metrics = {
            'start_time': datetime.utcnow(),
            'jobs_processed': 0,
            'jobs_failed': 0,
            'last_activity': datetime.utcnow()
        }
    
    async def start(self):
        """Start the enhanced worker with Smart Resource Scaling."""
        self.running = True
        logger.info(f"Enhanced Queue Worker {self.worker_id} starting with Smart Resource Scaling")
        
        # Initialize Smart Resource Scaling if enabled
        if self.scaling_enabled:
            await self._initialize_smart_scaling()
        
        # Start sales intelligence scheduler in a separate thread
        self.scheduler_thread = threading.Thread(
            target=self.sales_scheduler.start,
            daemon=True
        )
        self.scheduler_thread.start()
        
        with self.app.app_context():
            # Start enhanced queue processing
            tasks = [
                asyncio.create_task(self.run_enhanced_queue_processor()),
                asyncio.create_task(self._performance_monitor())
            ]
            
            if self.scaling_enabled:
                tasks.append(asyncio.create_task(self._resource_reporter()))
            
            self.tasks.update(tasks)
            
            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                logger.info("Enhanced worker tasks cancelled")
            except Exception as e:
                logger.error(f"Enhanced worker error: {str(e)}")
            finally:
                self.running = False
    
    async def _initialize_smart_scaling(self):
        """Initialize Smart Resource Scaling components."""
        try:
            # Try to load enhanced functionality into existing queue service
            # The queue_service.py has been enhanced with Smart Resource Scaling
            self.queue_service._try_load_enhanced_service()
            
            if hasattr(self.queue_service, '_enhanced_service') and self.queue_service._enhanced_service:
                logger.info("Using Enhanced Queue Service functionality via integrated queue_service")
            else:
                logger.info("Using standard queue service with integrated enhancements")
            
            # Try to register with Smart Resource Scaler
            try:
                from app.services.smart_resource_scaler import smart_resource_scaler
                if not smart_resource_scaler.running:
                    await smart_resource_scaler.start()
                
                worker_info = {
                    'worker_id': self.worker_id,
                    'pid': os.getpid(),
                    'start_time': self.performance_metrics['start_time'],
                    'capabilities': ['queue_processing', 'sales_intelligence']
                }
                
                await smart_resource_scaler.register_worker(self.worker_id, worker_info)
                logger.info(f"Worker {self.worker_id} registered with Smart Resource Scaler")
                
            except ImportError:
                logger.info("Smart Resource Scaler not available, continuing without scaling")
                self.scaling_enabled = False
                
        except Exception as e:
            logger.warning(f"Smart scaling initialization failed: {e}")
            self.scaling_enabled = False
    
    async def run_enhanced_queue_processor(self):
        """Enhanced queue processing with performance tracking."""
        logger.info("Starting enhanced queue processor")
        
        while self.running:
            try:
                # Update activity timestamp
                self.performance_metrics['last_activity'] = datetime.utcnow()
                
                # Process queue items with enhanced service
                if hasattr(self.queue_service, 'process_queue'):
                    await self.queue_service.process_queue()
                else:
                    # Fallback to synchronous processing
                    self.queue_service.process_queue()
                
                # Update performance metrics
                self.performance_metrics['jobs_processed'] += 1
                
                # Adaptive sleep based on queue load
                sleep_time = await self._calculate_adaptive_sleep()
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in enhanced queue processor: {str(e)}")
                self.performance_metrics['jobs_failed'] += 1
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _calculate_adaptive_sleep(self):
        """Calculate adaptive sleep time based on queue load."""
        try:
            # Check queue length if possible
            if hasattr(self.queue_service, 'get_enhanced_queue_status'):
                status = self.queue_service.get_enhanced_queue_status()
                pending_count = status.get('traditional_queue', {}).get('pending', 0)
                
                if pending_count > 20:
                    return 0.5  # High load - process faster
                elif pending_count > 10:
                    return 1.0  # Medium load - normal speed
                else:
                    return 2.0  # Low load - slower processing
            else:
                return 1.0  # Default sleep time
                
        except Exception:
            return 1.0  # Fallback sleep time
    
    async def _performance_monitor(self):
        """Monitor and log worker performance."""
        while self.running:
            try:
                uptime = (datetime.utcnow() - self.performance_metrics['start_time']).total_seconds()
                
                # Log performance every 5 minutes
                if uptime % 300 < 60:  # Log within first minute of each 5-minute interval
                    logger.info(f"Worker {self.worker_id} Performance: "
                              f"Uptime={uptime:.0f}s, "
                              f"Processed={self.performance_metrics['jobs_processed']}, "
                              f"Failed={self.performance_metrics['jobs_failed']}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")
                await asyncio.sleep(60)
    
    async def _resource_reporter(self):
        """Report resource usage to Smart Resource Scaler."""
        if not self.scaling_enabled:
            return
        
        while self.running:
            try:
                # Collect resource stats
                worker_stats = {
                    'worker_id': self.worker_id,
                    'pid': os.getpid(),
                    'jobs_processed': self.performance_metrics['jobs_processed'],
                    'jobs_failed': self.performance_metrics['jobs_failed'],
                    'last_activity': self.performance_metrics['last_activity'],
                    'status': 'active'
                }
                
                # Try to get memory/CPU usage
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    worker_stats.update({
                        'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
                        'cpu_usage_percent': process.cpu_percent()
                    })
                except ImportError:
                    pass  # psutil not available
                
                # Report to scaler
                try:
                    from app.services.smart_resource_scaler import smart_resource_scaler
                    await smart_resource_scaler.update_worker_stats(self.worker_id, worker_stats)
                except ImportError:
                    pass  # Scaler not available
                
                await asyncio.sleep(30)  # Report every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in resource reporter: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop the enhanced worker gracefully."""
        logger.info(f"Stopping Enhanced Queue Worker {self.worker_id}...")
        self.running = False
        
        # Unregister from Smart Resource Scaler
        if self.scaling_enabled:
            try:
                from app.services.smart_resource_scaler import smart_resource_scaler
                await smart_resource_scaler.unregister_worker(self.worker_id)
                logger.info(f"Worker {self.worker_id} unregistered from Smart Resource Scaler")
            except ImportError:
                pass  # Scaler not available
        
        # Stop sales scheduler
        if hasattr(self, 'sales_scheduler'):
            self.sales_scheduler.stop()
        
        # Cancel all running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # Log final performance metrics
        uptime = (datetime.utcnow() - self.performance_metrics['start_time']).total_seconds()
        logger.info(f"Worker {self.worker_id} final stats: "
                   f"uptime={uptime:.1f}s, "
                   f"processed={self.performance_metrics['jobs_processed']}, "
                   f"failed={self.performance_metrics['jobs_failed']}")
        
        logger.info(f"Enhanced Queue Worker {self.worker_id} stopped")

# Global worker instance
worker = None

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}")
    if worker:
        asyncio.create_task(worker.stop())

async def main():
    """Main entry point for Enhanced Queue Worker."""
    global worker
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    worker = EnhancedQueueWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        if worker:
            await worker.stop()

if __name__ == '__main__':
    # Check if running in production
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("Running Enhanced Worker in Railway environment with Smart Resource Scaling")
    else:
        logger.info("Running Enhanced Worker in development environment")
    
    # Log startup information
    logger.info("=== Enhanced Queue Worker v1.2 ===")
    logger.info("Features: Smart Resource Scaling, Performance Monitoring, Adaptive Processing")
    
    # Run the enhanced worker
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Enhanced worker shutdown complete")
    except Exception as e:
        logger.error(f"Enhanced worker failed: {str(e)}")
        sys.exit(1)
