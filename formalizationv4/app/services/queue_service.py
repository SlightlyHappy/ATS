import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_
from flask import current_app
from app import db
from app.models.queue import AnalysisQueue, QueueStatus, BatchUpload
from app.models.user import User
from app.models.resume import Resume
from app.models.analysis import Analysis
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class QueueService:
    """Enhanced service to manage resume analysis queue with Smart Resource Scaling."""
    
    def __init__(self):
        self.analysis_service = AnalysisService()
        
        # Smart Resource Scaling integration
        self.scaling_enabled = os.getenv('ENABLE_SMART_SCALING', 'true').lower() == 'true'
        self.max_concurrent_jobs = int(os.getenv('MAX_CONCURRENT_JOBS', '6'))  # Increased for v1.2
        self.processing_jobs = set()
        
        # Performance tracking
        self.performance_metrics = {
            'total_processed': 0,
            'total_failed': 0,
            'average_processing_time': 0,
            'last_reset': datetime.utcnow()
        }
        
        # Enhanced queue service reference
        self._enhanced_service = None
        self._try_load_enhanced_service()
    
    def _try_load_enhanced_service(self):
        """Try to load enhanced functionality if available."""
        try:
            # Enhanced functionality is now integrated directly into this service
            # Check if intelligent queue components are available
            try:
                from app.services.intelligent_queue_manager import intelligent_queue_manager
                self._enhanced_service = True  # Mark as having enhanced capabilities
                logger.info("Intelligent Queue Manager available for Smart Resource Scaling")
            except ImportError:
                logger.info("Intelligent Queue Manager not available, using standard queue service")
        except Exception as e:
            logger.warning(f"Failed to load enhanced functionality: {e}")

    async def _process_standard_queue_with_enhancements(self):
        """Standard queue processing with enhancements."""
        # This contains the main enhanced processing logic
        while True:
            try:
                # Adaptive concurrent job limit based on system load
                effective_max_jobs = await self._get_effective_max_jobs()
                
                # Limit concurrent processing
                if len(self.processing_jobs) >= effective_max_jobs:
                    await asyncio.sleep(2)
                    continue
                
                # Get next item to process with enhanced priority
                next_item = AnalysisQueue.query.filter_by(
                    status=QueueStatus.PENDING.value
                ).order_by(
                    AnalysisQueue.priority.desc(),
                    AnalysisQueue.created_at
                ).first()
                
                if not next_item:
                    await asyncio.sleep(5)
                    continue
                
                # Start processing with performance tracking
                task = asyncio.create_task(self._process_queue_item_with_tracking(next_item))
                self.processing_jobs.add(task)
                
                # Clean up completed tasks
                self.processing_jobs = {t for t in self.processing_jobs if not t.done()}
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in enhanced standard queue processing: {str(e)}")
                await asyncio.sleep(30)
from app import db
from app.models.queue import AnalysisQueue, QueueStatus, BatchUpload
from app.models.user import User
from app.models.resume import Resume
from app.models.analysis import Analysis
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class QueueService:
    """Enhanced service to manage resume analysis queue with Smart Resource Scaling."""
    
    def __init__(self):
        self.analysis_service = AnalysisService()
        
        # Smart Resource Scaling integration
        self.scaling_enabled = os.getenv('ENABLE_SMART_SCALING', 'true').lower() == 'true'
        self.max_concurrent_jobs = int(os.getenv('MAX_CONCURRENT_JOBS', '6'))  # Increased for v1.2
        self.processing_jobs = set()
        
        # Performance tracking
        self.performance_metrics = {
            'total_processed': 0,
            'total_failed': 0,
            'average_processing_time': 0,
            'last_reset': datetime.utcnow()
        }
        
        # Enhanced queue service reference
        self._enhanced_service = None
        self._try_load_enhanced_service()
    
    def _try_load_enhanced_service(self):
        """Try to load enhanced functionality if available."""
        try:
            # Enhanced functionality is now integrated directly into this service
            # Check if intelligent queue components are available
            try:
                from app.services.intelligent_queue_manager import intelligent_queue_manager
                self._enhanced_service = True  # Mark as having enhanced capabilities
                logger.info("Intelligent Queue Manager available for Smart Resource Scaling")
            except ImportError:
                logger.info("Intelligent Queue Manager not available, using standard queue service")
        except Exception as e:
            logger.warning(f"Failed to load enhanced functionality: {e}")
    
    def add_to_queue(self, user_id: str, resume_id: str, batch_upload_id: str = None, urgency: str = 'normal') -> AnalysisQueue:
        """Add a resume to the analysis queue with enhanced prioritization."""
        
        # Enhanced functionality is now integrated directly into this service
        # Standard queue service implementation with enhanced features
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            resume = Resume.query.get(resume_id)
            if not resume:
                raise ValueError("Resume not found")
            
            # Check if already in queue
            existing = AnalysisQueue.query.filter_by(
                resume_id=resume_id,
                status=QueueStatus.PENDING.value
            ).first()
            
            if existing:
                return existing
            
            # Enhanced priority calculation
            priority = self._calculate_enhanced_priority(user, urgency)
            
            # Create queue entry
            queue_entry = AnalysisQueue(
                user_id=user_id,
                resume_id=resume_id,
                priority=priority,
                status=QueueStatus.PENDING.value
            )
            
            db.session.add(queue_entry)
            db.session.commit()
            
            # Update queue positions
            self.update_queue_positions()
            
            logger.info(f"Added resume {resume_id} to queue for user {user_id} with priority {priority}")
            return queue_entry
            
        except Exception as e:
            logger.error(f"Error adding to queue: {str(e)}")
            db.session.rollback()
            raise
    
    def _calculate_enhanced_priority(self, user: User, urgency: str) -> int:
        """Calculate enhanced priority based on user tier and urgency."""
        try:
            # Base priority from user tier
            if user.is_admin:
                base_priority = 100
            elif hasattr(user, 'subscription_tier'):
                if user.subscription_tier == 'premium':
                    base_priority = 80
                elif user.subscription_tier == 'trial':
                    base_priority = 30
                else:
                    base_priority = 50
            else:
                base_priority = 50
            
            # Urgency multiplier
            urgency_multipliers = {
                'critical': 2.0,
                'high': 1.5,
                'normal': 1.0,
                'low': 0.7
            }
            
            urgency_multiplier = urgency_multipliers.get(urgency, 1.0)
            
            # Apply load-based adjustment
            current_queue_length = AnalysisQueue.query.filter_by(
                status=QueueStatus.PENDING.value
            ).count()
            
            # If queue is long, slightly boost all priorities
            if current_queue_length > 20:
                load_multiplier = 1.1
            elif current_queue_length > 50:
                load_multiplier = 1.2
            else:
                load_multiplier = 1.0
            
            final_priority = int(base_priority * urgency_multiplier * load_multiplier)
            return min(final_priority, 200)  # Cap at 200
            
        except Exception as e:
            logger.error(f"Error calculating enhanced priority: {str(e)}")
            return 50  # Default priority
    
    async def _process_with_intelligent_features(self):
        """Process queue using integrated intelligent features."""
        try:
            # Try to use intelligent queue manager if available
            try:
                from app.services.intelligent_queue_manager import intelligent_queue_manager
                if intelligent_queue_manager.running:
                    # Use intelligent processing
                    await self._sync_with_intelligent_queue()
                    return
            except ImportError:
                pass  # Intelligent queue manager not available
            
            # Fall back to enhanced standard processing
            await self._process_enhanced_standard_queue()
            
        except Exception as e:
            logger.error(f"Error in intelligent queue processing: {str(e)}")
            # Fall back to basic processing
            raise
    
    async def _sync_with_intelligent_queue(self):
        """Sync with intelligent queue manager processing."""
        try:
            from app.services.intelligent_queue_manager import intelligent_queue_manager
            queue_status = intelligent_queue_manager.get_queue_status()
            # Sync database records with intelligent queue state
            # Implementation would sync database queue items with intelligent processing
            await asyncio.sleep(2)  # Placeholder for actual sync logic
        except Exception as e:
            logger.error(f"Error syncing with intelligent queue: {str(e)}")
            raise
    
    async def _process_enhanced_standard_queue(self):
        """Enhanced standard queue processing."""
        # This is the existing enhanced logic from the standard processing
        # but extracted for better organization
        await self._process_standard_queue_with_enhancements()
    
    def add_batch_to_queue(self, user_id: str, resume_ids: List[str], batch_name: str = None) -> BatchUpload:
        """Add multiple resumes to queue as a batch."""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Check credits for non-admin users
            if not user.is_admin and not user.has_sufficient_credits(len(resume_ids)):
                raise ValueError("Insufficient credits for batch analysis")
            
            # Create batch upload record
            batch = BatchUpload(
                user_id=user_id,
                batch_name=batch_name or f"Batch Upload {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                total_resumes=len(resume_ids),
                status='processing'
            )
            
            db.session.add(batch)
            db.session.flush()  # Get the batch ID
            
            # Add each resume to queue
            queue_entries = []
            for resume_id in resume_ids:
                resume = Resume.query.get(resume_id)
                if resume:
                    # Update resume with batch reference
                    resume.batch_upload_id = batch.id
                    
                    # Add to queue
                    queue_entry = self.add_to_queue(user_id, resume_id)
                    queue_entries.append(queue_entry)
            
            db.session.commit()
            
            logger.info(f"Added batch of {len(resume_ids)} resumes to queue for user {user_id}")
            return batch
            
        except Exception as e:
            logger.error(f"Error adding batch to queue: {str(e)}")
            db.session.rollback()
            raise
    
    def get_queue_status(self, user_id: str = None) -> dict:
        """Get current queue status."""
        try:
            query = AnalysisQueue.query
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            pending_count = query.filter_by(status=QueueStatus.PENDING.value).count()
            processing_count = query.filter_by(status=QueueStatus.PROCESSING.value).count()
            completed_count = query.filter_by(status=QueueStatus.COMPLETED.value).count()
            failed_count = query.filter_by(status=QueueStatus.FAILED.value).count()
            
            # Get user's position in queue if user_id provided
            user_position = None
            if user_id:
                user_pending = query.filter_by(
                    user_id=user_id,
                    status=QueueStatus.PENDING.value
                ).order_by(AnalysisQueue.queue_position).first()
                
                if user_pending:
                    user_position = user_pending.queue_position
            
            return {
                'pending': pending_count,
                'processing': processing_count,
                'completed': completed_count,
                'failed': failed_count,
                'user_position': user_position,
                'estimated_wait_time': self.estimate_wait_time(user_position) if user_position else None
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {}
    
    def update_queue_positions(self):
        """Update queue positions based on priority and creation time."""
        try:
            pending_items = AnalysisQueue.query.filter_by(
                status=QueueStatus.PENDING.value
            ).order_by(
                AnalysisQueue.priority.desc(),
                AnalysisQueue.created_at
            ).all()
            
            for index, item in enumerate(pending_items, 1):
                old_position = item.queue_position
                item.queue_position = index
                item.estimated_completion_time = self.estimate_completion_time(index)
                
                # Notify if position changed
                if old_position != item.queue_position:
                    self._notify_websocket_update(item)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating queue positions: {str(e)}")
            db.session.rollback()
    
    def estimate_completion_time(self, position: int) -> datetime:
        """Estimate completion time based on queue position."""
        # Assume 2 minutes per analysis on average
        minutes_per_analysis = 2
        estimated_minutes = position * minutes_per_analysis
        return datetime.utcnow() + timedelta(minutes=estimated_minutes)
    
    def estimate_wait_time(self, position: int) -> dict:
        """Estimate wait time in human-readable format."""
        if not position:
            return None
        
        completion_time = self.estimate_completion_time(position)
        time_diff = completion_time - datetime.utcnow()
        
        minutes = int(time_diff.total_seconds() / 60)
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if hours > 0:
            return {'hours': hours, 'minutes': remaining_minutes, 'total_minutes': minutes}
        else:
            return {'hours': 0, 'minutes': minutes, 'total_minutes': minutes}
    
    async def process_queue(self):
        """Enhanced queue processing with Smart Resource Scaling integration."""
        
        # Use integrated enhanced features if available
        if self._enhanced_service and self.scaling_enabled:
            try:
                # Enhanced functionality is integrated into this service
                # Use intelligent processing features
                await self._process_with_intelligent_features()
                return
            except Exception as e:
                logger.warning(f"Enhanced features failed, falling back to standard: {e}")
        
        # Standard queue processing with performance tracking
        while True:
            try:
                # Adaptive concurrent job limit based on system load
                effective_max_jobs = await self._get_effective_max_jobs()
                
                # Limit concurrent processing
                if len(self.processing_jobs) >= effective_max_jobs:
                    await asyncio.sleep(2)  # Reduced sleep for better responsiveness
                    continue
                
                # Get next item to process with enhanced priority
                next_item = AnalysisQueue.query.filter_by(
                    status=QueueStatus.PENDING.value
                ).order_by(
                    AnalysisQueue.priority.desc(),
                    AnalysisQueue.created_at
                ).first()
                
                if not next_item:
                    await asyncio.sleep(5)  # Reduced sleep when no items
                    continue
                
                # Start processing with performance tracking
                task = asyncio.create_task(self._process_queue_item_with_tracking(next_item))
                self.processing_jobs.add(task)
                
                # Clean up completed tasks
                self.processing_jobs = {t for t in self.processing_jobs if not t.done()}
                
                await asyncio.sleep(0.5)  # Faster processing startup
                
            except Exception as e:
                logger.error(f"Error in enhanced queue processing loop: {str(e)}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _get_effective_max_jobs(self):
        """Get effective max concurrent jobs based on system load."""
        try:
            # Try to get system metrics for adaptive scaling
            try:
                import psutil
                cpu_usage = psutil.cpu_percent(interval=0.1)
                memory_usage = psutil.virtual_memory().percent
                
                # Reduce concurrency under high load
                if cpu_usage > 85 or memory_usage > 85:
                    return max(1, self.max_concurrent_jobs // 2)
                elif cpu_usage > 70 or memory_usage > 70:
                    return max(2, int(self.max_concurrent_jobs * 0.75))
                else:
                    return self.max_concurrent_jobs
                    
            except ImportError:
                # psutil not available, use configured max
                return self.max_concurrent_jobs
                
        except Exception:
            return self.max_concurrent_jobs
    
    async def _process_queue_item_with_tracking(self, queue_item: AnalysisQueue):
        """Process queue item with performance tracking."""
        start_time = datetime.utcnow()
        
        try:
            await self.process_queue_item(queue_item)
            
            # Update performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_performance_metrics(processing_time, success=True)
            
        except Exception as e:
            logger.error(f"Error processing queue item {queue_item.id}: {str(e)}")
            self._update_performance_metrics(0, success=False)
            raise
    
    def _update_performance_metrics(self, processing_time: float, success: bool):
        """Update performance statistics."""
        try:
            if success:
                self.performance_metrics['total_processed'] += 1
                
                # Update average processing time
                total_processed = self.performance_metrics['total_processed']
                current_avg = self.performance_metrics['average_processing_time']
                new_avg = ((current_avg * (total_processed - 1)) + processing_time) / total_processed
                self.performance_metrics['average_processing_time'] = new_avg
            else:
                self.performance_metrics['total_failed'] += 1
            
            # Reset stats daily
            if (datetime.utcnow() - self.performance_metrics['last_reset']).days >= 1:
                self.performance_metrics = {
                    'total_processed': 0,
                    'total_failed': 0,
                    'average_processing_time': 0,
                    'last_reset': datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced queue status with performance metrics."""
        try:
            # Enhanced functionality is integrated into this service
            # Return comprehensive status
            total_queued = AnalysisQueue.query.count()
            pending_count = AnalysisQueue.query.filter_by(status=QueueStatus.PENDING.value).count()
            processing_count = AnalysisQueue.query.filter_by(status=QueueStatus.PROCESSING.value).count()
            completed_count = AnalysisQueue.query.filter_by(status=QueueStatus.COMPLETED.value).count()
            failed_count = AnalysisQueue.query.filter_by(status=QueueStatus.FAILED.value).count()
            
            uptime = (datetime.utcnow() - self.performance_metrics['last_reset']).total_seconds()
            processing_rate = self.performance_metrics['total_processed'] / max(uptime / 3600, 1)  # per hour
            failure_rate = self.performance_metrics['total_failed'] / max(self.performance_metrics['total_processed'] + self.performance_metrics['total_failed'], 1)
            
            return {
                'queue_status': {
                    'total': total_queued,
                    'pending': pending_count,
                    'processing': processing_count,
                    'completed': completed_count,
                    'failed': failed_count
                },
                'performance_metrics': {
                    'total_processed': self.performance_metrics['total_processed'],
                    'total_failed': self.performance_metrics['total_failed'],
                    'processing_rate_per_hour': round(processing_rate, 2),
                    'failure_rate_percent': round(failure_rate * 100, 2),
                    'average_processing_time': round(self.performance_metrics['average_processing_time'], 2),
                    'current_processing_count': len(self.processing_jobs),
                    'max_concurrent_jobs': self.max_concurrent_jobs,
                    'uptime_hours': round(uptime / 3600, 2)
                },
                'scaling_status': {
                    'enabled': self.scaling_enabled,
                    'enhanced_service_available': self._enhanced_service is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced status: {str(e)}")
            return {'error': str(e)}
    
    async def process_queue_item(self, queue_item: AnalysisQueue):
        """Process a single queue item."""
        try:
            logger.info(f"Starting analysis for queue item {queue_item.id}")
            
            # Mark as processing
            queue_item.start_processing()
            self._notify_websocket_update(queue_item)
            
            # Get user and resume
            user = User.query.get(queue_item.user_id)
            resume = Resume.query.get(queue_item.resume_id)
            
            if not user or not resume:
                queue_item.mark_failed("User or resume not found")
                return
            
            # Check and deduct credits for non-admin users
            if not user.is_admin:
                if not user.deduct_credits(1, f"Analysis for {resume.filename}"):
                    queue_item.mark_failed("Insufficient credits")
                    return
                db.session.commit()
            
            # Run the analysis
            analysis_result = await self.analysis_service.analyze_resume_async(
                resume_id=str(queue_item.resume_id),
                user_id=str(queue_item.user_id)
            )
            
            if analysis_result and 'id' in analysis_result:
                # Mark as completed
                queue_item.mark_completed(analysis_result['id'])
                self._notify_websocket_update(queue_item)
                
                # Get the analysis object and notify completion
                analysis = Analysis.query.get(analysis_result['id'])
                if analysis:
                    self._notify_analysis_completed(analysis)
                
                # Update batch progress if applicable
                if resume.batch_upload_id:
                    batch = BatchUpload.query.get(resume.batch_upload_id)
                    if batch:
                        batch.update_progress()
                        self._notify_batch_update(batch)
                
                logger.info(f"Completed analysis for queue item {queue_item.id}")
            else:
                queue_item.mark_failed("Analysis failed to produce results")
                self._notify_websocket_update(queue_item)
                
        except Exception as e:
            error_msg = f"Error processing queue item: {str(e)}"
            logger.error(error_msg)
            queue_item.mark_failed(error_msg)
            self._notify_websocket_update(queue_item)
            
            # Refund credits if analysis failed and user is not admin
            if not user.is_admin:
                user.add_credits(1, f"Refund for failed analysis: {resume.filename}")
                db.session.commit()
        
        finally:
            # Update queue positions
            self.update_queue_positions()
    
    def get_user_queue_items(self, user_id: str, status: str = None) -> List[AnalysisQueue]:
        """Get queue items for a specific user."""
        try:
            query = AnalysisQueue.query.filter_by(user_id=user_id)
            
            if status:
                query = query.filter_by(status=status)
            
            return query.order_by(AnalysisQueue.created_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Error getting user queue items: {str(e)}")
            return []
    
    def cancel_queue_item(self, queue_item_id: str, user_id: str) -> bool:
        """Cancel a pending queue item."""
        try:
            queue_item = AnalysisQueue.query.filter_by(
                id=queue_item_id,
                user_id=user_id,
                status=QueueStatus.PENDING.value
            ).first()
            
            if not queue_item:
                return False
            
            queue_item.status = QueueStatus.CANCELLED.value
            db.session.commit()
            
            # Update queue positions
            self.update_queue_positions()
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling queue item: {str(e)}")
            db.session.rollback()
            return False
    
    def get_batch_status(self, batch_id: str, user_id: str) -> Optional[BatchUpload]:
        """Get status of a batch upload."""
        try:
            return BatchUpload.query.filter_by(
                id=batch_id,
                user_id=user_id
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting batch status: {str(e)}")
            return None
    
    def _notify_websocket_update(self, queue_item: AnalysisQueue):
        """Send WebSocket notification for queue updates."""
        try:
            if hasattr(current_app, 'websocket_service'):
                current_app.websocket_service.notify_queue_update(queue_item)
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {str(e)}")
    
    def _notify_analysis_completed(self, analysis: Analysis):
        """Send WebSocket notification for completed analysis."""
        try:
            if hasattr(current_app, 'websocket_service'):
                current_app.websocket_service.notify_analysis_completed(analysis)
        except Exception as e:
            logger.error(f"Error sending analysis completion notification: {str(e)}")
    
    def _notify_batch_update(self, batch: BatchUpload):
        """Send WebSocket notification for batch updates."""
        try:
            if hasattr(current_app, 'websocket_service'):
                current_app.websocket_service.notify_batch_update(batch)
        except Exception as e:
            logger.error(f"Error sending batch update notification: {str(e)}")
