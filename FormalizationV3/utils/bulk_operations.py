#!/usr/bin/env python3
"""
Bulk Operations Manager for HR ATS System
Provides efficient bulk processing for resumes, users, and data operations
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue, Empty
import traceback
import psutil
import os

from railway_database import RailwayPostgreSQL
from utils.realtime_manager import emit_processing_update, emit_queue_update
from storage_manager import StorageManager

logger = logging.getLogger(__name__)

# Optional imports that may fail due to configuration
try:
    from ai_processor import AIProcessor
    AI_PROCESSOR_AVAILABLE = True
except Exception as e:
    logger.warning(f"AI processor import failed: {e}")
    AIProcessor = None
    AI_PROCESSOR_AVAILABLE = False

try:
    from email_automation import EmailManager
    EMAIL_MANAGER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Email manager import failed: {e}")
    EmailManager = None
    EMAIL_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class BulkOperation:
    """Bulk operation definition"""
    operation_id: str
    operation_type: str
    user_id: str
    items: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed, cancelled
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    error_details: List[Dict[str, Any]] = None
    results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.error_details is None:
            self.error_details = []
        if self.results is None:
            self.results = []
        self.total_items = len(self.items)

@dataclass
class BulkProgress:
    """Progress tracking for bulk operations"""
    operation_id: str
    stage: str
    progress_percentage: int
    current_item: int
    total_items: int
    estimated_completion: Optional[datetime]
    processing_rate: float  # items per second
    errors_count: int
    last_update: datetime

class BulkOperationsManager:
    """Manager for bulk operations with queue processing and progress tracking"""
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 100, db_manager=None, realtime_manager=None):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.operations: Dict[str, BulkOperation] = {}
        self.operation_queue = Queue(maxsize=max_queue_size)
        self.is_running = False
        self.worker_threads: List[threading.Thread] = []
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Database and services
        self.db = db_manager.railway_pg if db_manager and hasattr(db_manager, 'railway_pg') else RailwayPostgreSQL()
        self.storage_manager = StorageManager()
        
        # Optional AI processor
        if AI_PROCESSOR_AVAILABLE:
            try:
                self.ai_processor = AIProcessor()
            except Exception as e:
                logger.warning(f"Failed to initialize AI processor: {e}")
                self.ai_processor = None
        else:
            self.ai_processor = None
        
        # Optional email manager
        if EMAIL_MANAGER_AVAILABLE:
            try:
                self.email_manager = EmailManager()
            except Exception as e:
                logger.warning(f"Failed to initialize email manager: {e}")
                self.email_manager = None
        else:
            self.email_manager = None
        
        # Operation handlers
        self.operation_handlers = {
            'bulk_resume_upload': self._handle_bulk_resume_upload,
            'bulk_resume_analysis': self._handle_bulk_resume_analysis,
            'bulk_user_creation': self._handle_bulk_user_creation,
            'bulk_email_send': self._handle_bulk_email_send,
            'bulk_data_export': self._handle_bulk_data_export,
            'bulk_data_import': self._handle_bulk_data_import,
            'bulk_resume_delete': self._handle_bulk_resume_delete,
            'bulk_user_update': self._handle_bulk_user_update,
            'bulk_skills_update': self._handle_bulk_skills_update,
            'bulk_status_update': self._handle_bulk_status_update
        }
        
        # Performance monitoring
        self.performance_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_processing_time': 0,
            'peak_memory_usage': 0,
            'cpu_usage_history': []
        }
        
        self.start_workers()
    
    def start_workers(self):
        """Start worker threads for processing operations"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_thread,
                name=f"BulkWorker-{i}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=self._monitoring_thread,
            name="BulkMonitor",
            daemon=True
        )
        monitor_thread.start()
        
        logger.info(f"Started {self.max_workers} bulk operation workers")
    
    def stop_workers(self):
        """Stop all worker threads"""
        self.is_running = False
        
        # Signal workers to stop
        for _ in range(self.max_workers):
            self.operation_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.worker_threads:
            if worker.is_alive():
                worker.join(timeout=30)
        
        self.executor.shutdown(wait=True)
        logger.info("Stopped bulk operation workers")
    
    def submit_operation(self, operation_type: str, user_id: str, items: List[Dict[str, Any]], 
                        parameters: Dict[str, Any] = None) -> str:
        """Submit a new bulk operation"""
        if operation_type not in self.operation_handlers:
            raise ValueError(f"Unknown operation type: {operation_type}")
        
        if len(items) == 0:
            raise ValueError("No items provided for bulk operation")
        
        if self.operation_queue.qsize() >= self.max_queue_size:
            raise RuntimeError("Bulk operation queue is full")
        
        # Create operation
        operation = BulkOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=operation_type,
            user_id=user_id,
            items=items,
            parameters=parameters or {}
        )
        
        # Store and queue operation
        self.operations[operation.operation_id] = operation
        self.operation_queue.put(operation.operation_id)
        
        logger.info(f"Submitted bulk operation {operation.operation_id} for user {user_id}")
        return operation.operation_id
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of bulk operation"""
        if operation_id not in self.operations:
            return None
        
        operation = self.operations[operation_id]
        return {
            'operation_id': operation_id,
            'operation_type': operation.operation_type,
            'status': operation.status,
            'progress': {
                'total_items': operation.total_items,
                'processed_items': operation.processed_items,
                'successful_items': operation.successful_items,
                'failed_items': operation.failed_items,
                'progress_percentage': round((operation.processed_items / operation.total_items) * 100, 2) if operation.total_items > 0 else 0
            },
            'timing': {
                'created_at': operation.created_at.isoformat() if operation.created_at else None,
                'started_at': operation.started_at.isoformat() if operation.started_at else None,
                'completed_at': operation.completed_at.isoformat() if operation.completed_at else None,
                'duration': (operation.completed_at - operation.started_at).total_seconds() if operation.completed_at and operation.started_at else None
            },
            'errors': operation.error_details,
            'results_count': len(operation.results)
        }
    
    def get_operation_results(self, operation_id: str, offset: int = 0, limit: int = 100) -> Optional[Dict[str, Any]]:
        """Get results of completed bulk operation"""
        if operation_id not in self.operations:
            return None
        
        operation = self.operations[operation_id]
        total_results = len(operation.results)
        results = operation.results[offset:offset+limit]
        
        return {
            'operation_id': operation_id,
            'status': operation.status,
            'total_results': total_results,
            'results': results,
            'pagination': {
                'offset': offset,
                'limit': limit,
                'has_more': offset + limit < total_results
            }
        }
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a pending or running operation"""
        if operation_id not in self.operations:
            return False
        
        operation = self.operations[operation_id]
        if operation.status in ['completed', 'failed', 'cancelled']:
            return False
        
        operation.status = 'cancelled'
        operation.completed_at = datetime.utcnow()
        
        logger.info(f"Cancelled bulk operation {operation_id}")
        return True
    
    def _worker_thread(self):
        """Worker thread for processing operations"""
        while self.is_running:
            try:
                # Get operation from queue
                operation_id = self.operation_queue.get(timeout=1)
                
                if operation_id is None:  # Shutdown signal
                    break
                
                if operation_id not in self.operations:
                    continue
                
                operation = self.operations[operation_id]
                
                # Skip if already processed
                if operation.status != 'pending':
                    continue
                
                # Process operation
                self._process_operation(operation)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
                logger.error(traceback.format_exc())
    
    def _process_operation(self, operation: BulkOperation):
        """Process a single bulk operation"""
        try:
            operation.status = 'running'
            operation.started_at = datetime.utcnow()
            
            logger.info(f"Starting bulk operation {operation.operation_id} ({operation.operation_type})")
            
            # Get handler
            handler = self.operation_handlers.get(operation.operation_type)
            if not handler:
                raise ValueError(f"No handler for operation type: {operation.operation_type}")
            
            # Execute operation
            handler(operation)
            
            # Mark as completed
            operation.status = 'completed'
            operation.completed_at = datetime.utcnow()
            
            # Update stats
            self.performance_stats['total_operations'] += 1
            self.performance_stats['successful_operations'] += 1
            
            logger.info(f"Completed bulk operation {operation.operation_id}")
            
        except Exception as e:
            logger.error(f"Failed bulk operation {operation.operation_id}: {e}")
            logger.error(traceback.format_exc())
            
            operation.status = 'failed'
            operation.completed_at = datetime.utcnow()
            operation.error_details.append({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Update stats
            self.performance_stats['total_operations'] += 1
            self.performance_stats['failed_operations'] += 1
        
        finally:
            # Emit completion event
            try:
                emit_processing_update(
                    operation.user_id,
                    operation.operation_id,
                    'completed' if operation.status == 'completed' else 'failed',
                    100,
                    {
                        'operation_type': operation.operation_type,
                        'total_items': operation.total_items,
                        'successful_items': operation.successful_items,
                        'failed_items': operation.failed_items
                    }
                )
            except Exception as e:
                logger.error(f"Error emitting completion event: {e}")
    
    def _handle_bulk_resume_upload(self, operation: BulkOperation):
        """Handle bulk resume upload operation"""
        for i, item in enumerate(operation.items):
            try:
                if operation.status == 'cancelled':
                    break
                
                # Extract item data
                file_data = item.get('file_data')
                filename = item.get('filename')
                user_id = operation.user_id
                
                if not file_data or not filename:
                    raise ValueError("Missing file_data or filename")
                
                # Upload file
                file_url = self.storage_manager.upload_file(
                    file_data, 
                    filename, 
                    user_id
                )
                
                # Create resume record
                resume_data = {
                    'user_id': user_id,
                    'filename': filename,
                    'file_url': file_url,
                    'upload_date': datetime.utcnow(),
                    'status': 'uploaded'
                }
                
                resume_id = self.db.execute_write(
                    """INSERT INTO resumes (user_id, filename, file_url, upload_date, status) 
                       VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (user_id, filename, file_url, resume_data['upload_date'], 'uploaded')
                )[0]['id']
                
                operation.results.append({
                    'index': i,
                    'filename': filename,
                    'resume_id': resume_id,
                    'file_url': file_url,
                    'status': 'success'
                })
                
                operation.successful_items += 1
                
            except Exception as e:
                logger.error(f"Error processing resume upload {i}: {e}")
                operation.error_details.append({
                    'index': i,
                    'filename': item.get('filename', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                operation.failed_items += 1
            
            operation.processed_items += 1
            
            # Emit progress update
            if operation.processed_items % 5 == 0 or operation.processed_items == operation.total_items:
                progress = round((operation.processed_items / operation.total_items) * 100, 2)
                emit_processing_update(
                    operation.user_id,
                    operation.operation_id,
                    'uploading',
                    progress,
                    {
                        'processed': operation.processed_items,
                        'total': operation.total_items,
                        'successful': operation.successful_items,
                        'failed': operation.failed_items
                    }
                )
    
    def _handle_bulk_resume_analysis(self, operation: BulkOperation):
        """Handle bulk resume analysis operation"""
        for i, item in enumerate(operation.items):
            try:
                if operation.status == 'cancelled':
                    break
                
                resume_id = item.get('resume_id')
                if not resume_id:
                    raise ValueError("Missing resume_id")
                
                # Get resume data
                resume = self.db.execute_read(
                    "SELECT * FROM resumes WHERE id = %s",
                    (resume_id,)
                )
                
                if not resume:
                    raise ValueError(f"Resume {resume_id} not found")
                
                resume = resume[0]
                
                # Perform AI analysis if available
                if self.ai_processor:
                    analysis_result = self.ai_processor.analyze_resume(
                        resume['file_url'],
                        resume['filename']
                    )
                else:
                    # Fallback analysis without AI
                    analysis_result = {
                        'skills': [],
                        'experience_years': 0,
                        'education': 'Not analyzed',
                        'analysis_summary': 'AI processor not available',
                        'overall_score': 0
                    }
                
                # Update resume with analysis
                self.db.execute_write(
                    """UPDATE resumes SET 
                       skills = %s, 
                       experience_years = %s, 
                       education = %s, 
                       analysis_data = %s, 
                       analysis_date = %s,
                       status = %s
                       WHERE id = %s""",
                    (
                        json.dumps(analysis_result.get('skills', [])),
                        analysis_result.get('experience_years', 0),
                        json.dumps(analysis_result.get('education', [])),
                        json.dumps(analysis_result),
                        datetime.utcnow(),
                        'analyzed',
                        resume_id
                    )
                )
                
                operation.results.append({
                    'index': i,
                    'resume_id': resume_id,
                    'analysis': analysis_result,
                    'status': 'success'
                })
                
                operation.successful_items += 1
                
            except Exception as e:
                logger.error(f"Error analyzing resume {i}: {e}")
                operation.error_details.append({
                    'index': i,
                    'resume_id': item.get('resume_id', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                operation.failed_items += 1
            
            operation.processed_items += 1
            
            # Emit progress update
            if operation.processed_items % 3 == 0 or operation.processed_items == operation.total_items:
                progress = round((operation.processed_items / operation.total_items) * 100, 2)
                emit_processing_update(
                    operation.user_id,
                    operation.operation_id,
                    'analyzing',
                    progress,
                    {
                        'processed': operation.processed_items,
                        'total': operation.total_items,
                        'successful': operation.successful_items,
                        'failed': operation.failed_items
                    }
                )
    
    def _handle_bulk_user_creation(self, operation: BulkOperation):
        """Handle bulk user creation operation"""
        for i, item in enumerate(operation.items):
            try:
                if operation.status == 'cancelled':
                    break
                
                # Extract user data
                email = item.get('email')
                password = item.get('password')
                first_name = item.get('first_name', '')
                last_name = item.get('last_name', '')
                role = item.get('role', 'user')
                
                if not email or not password:
                    raise ValueError("Missing email or password")
                
                # Check if user exists
                existing_user = self.db.execute_read(
                    "SELECT id FROM users WHERE email = %s",
                    (email,)
                )
                
                if existing_user:
                    raise ValueError(f"User with email {email} already exists")
                
                # Create user
                user_id = self.db.execute_write(
                    """INSERT INTO users (email, password, first_name, last_name, role, created_at) 
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                    (email, password, first_name, last_name, role, datetime.utcnow())
                )[0]['id']
                
                operation.results.append({
                    'index': i,
                    'user_id': user_id,
                    'email': email,
                    'status': 'success'
                })
                
                operation.successful_items += 1
                
            except Exception as e:
                logger.error(f"Error creating user {i}: {e}")
                operation.error_details.append({
                    'index': i,
                    'email': item.get('email', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                operation.failed_items += 1
            
            operation.processed_items += 1
            
            # Emit progress update
            if operation.processed_items % 10 == 0 or operation.processed_items == operation.total_items:
                progress = round((operation.processed_items / operation.total_items) * 100, 2)
                emit_processing_update(
                    operation.user_id,
                    operation.operation_id,
                    'creating_users',
                    progress,
                    {
                        'processed': operation.processed_items,
                        'total': operation.total_items,
                        'successful': operation.successful_items,
                        'failed': operation.failed_items
                    }
                )
    
    def _handle_bulk_email_send(self, operation: BulkOperation):
        """Handle bulk email sending operation"""
        template = operation.parameters.get('template')
        subject = operation.parameters.get('subject')
        
        for i, item in enumerate(operation.items):
            try:
                if operation.status == 'cancelled':
                    break
                
                recipient_email = item.get('email')
                template_vars = item.get('template_vars', {})
                
                if not recipient_email:
                    raise ValueError("Missing recipient email")
                
                # Send email if email manager is available
                if self.email_manager:
                    self.email_manager.send_template_email(
                        recipient_email,
                        subject,
                        template,
                        template_vars
                    )
                    status = 'sent'
                else:
                    # Simulate email sending
                    logger.warning(f"Email manager not available, simulating email to {recipient_email}")
                    status = 'simulated'
                
                operation.results.append({
                    'index': i,
                    'email': recipient_email,
                    'status': status
                })
                
                operation.successful_items += 1
                
            except Exception as e:
                logger.error(f"Error sending email {i}: {e}")
                operation.error_details.append({
                    'index': i,
                    'email': item.get('email', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                operation.failed_items += 1
            
            operation.processed_items += 1
            
            # Emit progress update
            if operation.processed_items % 10 == 0 or operation.processed_items == operation.total_items:
                progress = round((operation.processed_items / operation.total_items) * 100, 2)
                emit_processing_update(
                    operation.user_id,
                    operation.operation_id,
                    'sending_emails',
                    progress,
                    {
                        'processed': operation.processed_items,
                        'total': operation.total_items,
                        'successful': operation.successful_items,
                        'failed': operation.failed_items
                    }
                )
    
    def _handle_bulk_data_export(self, operation: BulkOperation):
        """Handle bulk data export operation"""
        export_type = operation.parameters.get('export_type', 'csv')
        table_name = operation.parameters.get('table_name')
        filters = operation.parameters.get('filters', {})
        
        try:
            # Build query based on filters
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    where_clauses.append(f"{key} = %s")
                    params.append(value)
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Execute export query
            data = self.db.execute_read(query, params)
            
            # Generate export file
            if export_type == 'csv':
                export_data = self._generate_csv_export(data)
            elif export_type == 'json':
                export_data = self._generate_json_export(data)
            else:
                raise ValueError(f"Unsupported export type: {export_type}")
            
            # Store export file
            filename = f"export_{table_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{export_type}"
            file_url = self.storage_manager.upload_file(
                export_data.encode('utf-8'),
                filename,
                operation.user_id
            )
            
            operation.results.append({
                'export_type': export_type,
                'filename': filename,
                'file_url': file_url,
                'record_count': len(data)
            })
            
            operation.successful_items = len(data)
            operation.processed_items = len(data)
            
        except Exception as e:
            logger.error(f"Error in bulk export: {e}")
            operation.error_details.append({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            operation.failed_items = 1
    
    def _handle_bulk_data_import(self, operation: BulkOperation):
        """Handle bulk data import operation"""
        import_type = operation.parameters.get('import_type', 'csv')
        table_name = operation.parameters.get('table_name')
        file_url = operation.parameters.get('file_url')
        
        try:
            # Download import file
            import_data = self.storage_manager.download_file(file_url)
            
            # Parse import data
            if import_type == 'csv':
                records = self._parse_csv_import(import_data.decode('utf-8'))
            elif import_type == 'json':
                records = self._parse_json_import(import_data.decode('utf-8'))
            else:
                raise ValueError(f"Unsupported import type: {import_type}")
            
            operation.total_items = len(records)
            
            # Process each record
            for i, record in enumerate(records):
                try:
                    if operation.status == 'cancelled':
                        break
                    
                    # Build insert query
                    columns = list(record.keys())
                    placeholders = ["%s"] * len(columns)
                    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    values = list(record.values())
                    
                    # Execute insert
                    self.db.execute_write(query, values)
                    
                    operation.successful_items += 1
                    operation.results.append({
                        'record_id': i + 1,
                        'status': 'imported',
                        'data': record
                    })
                    
                except Exception as e:
                    logger.error(f"Error importing record {i}: {e}")
                    operation.failed_items += 1
                    operation.error_details.append({
                        'record_id': i + 1,
                        'error': str(e),
                        'data': record,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                operation.processed_items += 1
                
                # Update progress
                progress = (operation.processed_items / operation.total_items) * 100
                self.queue_manager.update_operation_progress(
                    operation.operation_id,
                    progress,
                    {
                        'processed': operation.processed_items,
                        'total': operation.total_items,
                        'successful': operation.successful_items,
                        'failed': operation.failed_items
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in bulk import: {e}")
            operation.error_details.append({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            operation.failed_items = operation.total_items - operation.successful_items
    
    def _handle_bulk_resume_delete(self, operation: BulkOperation):
        """Handle bulk resume deletion operation"""
        for i, item in enumerate(operation.items):
            try:
                if operation.status == 'cancelled':
                    break
                
                resume_id = item.get('resume_id')
                if not resume_id:
                    raise ValueError("Missing resume_id")
                
                # Get resume data for file cleanup
                resume = self.db.execute_read(
                    "SELECT file_url FROM resumes WHERE id = %s",
                    (resume_id,)
                )
                
                if resume:
                    # Delete file from storage
                    if resume[0]['file_url']:
                        self.storage_manager.delete_file(resume[0]['file_url'])
                    
                    # Delete from database
                    self.db.execute_write(
                        "DELETE FROM resumes WHERE id = %s",
                        (resume_id,)
                    )
                    
                    operation.successful_items += 1
                else:
                    operation.failed_items += 1
                
                operation.results.append({
                    'index': i,
                    'resume_id': resume_id,
                    'status': 'deleted' if resume else 'not_found'
                })
                
            except Exception as e:
                logger.error(f"Error deleting resume {i}: {e}")
                operation.error_details.append({
                    'index': i,
                    'resume_id': item.get('resume_id', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                operation.failed_items += 1
            
            operation.processed_items += 1
    
    def _handle_bulk_user_update(self, operation: BulkOperation):
        """Handle bulk user updates"""
        update_fields = operation.parameters.get('update_fields', {})
        
        for i, item in enumerate(operation.items):
            try:
                if operation.status == 'cancelled':
                    break
                
                user_id = item.get('user_id')
                if not user_id:
                    raise ValueError("Missing user_id")
                
                # Build update query
                set_clauses = []
                params = []
                
                for field, value in update_fields.items():
                    # Allow per-item overrides
                    if field in item:
                        value = item[field]
                    
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
                
                if not set_clauses:
                    raise ValueError("No fields to update")
                
                params.append(user_id)
                
                # Execute update
                result = self.db.execute_write(
                    f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s",
                    params
                )
                
                operation.results.append({
                    'index': i,
                    'user_id': user_id,
                    'updated_fields': list(update_fields.keys()),
                    'status': 'success'
                })
                
                operation.successful_items += 1
                
            except Exception as e:
                logger.error(f"Error updating user {i}: {e}")
                operation.error_details.append({
                    'index': i,
                    'user_id': item.get('user_id', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                operation.failed_items += 1
            
            operation.processed_items += 1
    
    def _handle_bulk_skills_update(self, operation: BulkOperation):
        """Handle bulk skills updates for resumes"""
        # Implementation for bulk skills updates
        pass
    
    def _handle_bulk_status_update(self, operation: BulkOperation):
        """Handle bulk status updates"""
        # Implementation for bulk status updates
        pass
    
    def _generate_csv_export(self, data: List[Dict[str, Any]]) -> str:
        """Generate CSV export from data"""
        import csv
        import io
        
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    def _generate_json_export(self, data: List[Dict[str, Any]]) -> str:
        """Generate JSON export from data"""
        return json.dumps(data, indent=2, default=str)
    
    def _parse_csv_import(self, csv_data: str) -> List[Dict[str, Any]]:
        """Parse CSV import data"""
        import csv
        import io
        
        records = []
        reader = csv.DictReader(io.StringIO(csv_data))
        
        for row in reader:
            # Clean and convert values
            record = {}
            for key, value in row.items():
                if key and value is not None:
                    # Try to convert numeric values
                    if value.isdigit():
                        record[key] = int(value)
                    elif value.replace('.', '').isdigit():
                        record[key] = float(value)
                    else:
                        record[key] = value.strip()
            records.append(record)
        
        return records
    
    def _parse_json_import(self, json_data: str) -> List[Dict[str, Any]]:
        """Parse JSON import data"""
        data = json.loads(json_data)
        
        # Handle both single record and array of records
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError("JSON data must be an object or array of objects")
    
    def _monitoring_thread(self):
        """Monitor system resources and performance"""
        while self.is_running:
            try:
                # Monitor CPU and memory
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                
                self.performance_stats['cpu_usage_history'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'cpu_percent': cpu_usage,
                    'memory_percent': memory_usage
                })
                
                # Keep only last 100 entries
                if len(self.performance_stats['cpu_usage_history']) > 100:
                    self.performance_stats['cpu_usage_history'] = self.performance_stats['cpu_usage_history'][-100:]
                
                # Update peak memory usage
                if memory_usage > self.performance_stats['peak_memory_usage']:
                    self.performance_stats['peak_memory_usage'] = memory_usage
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring thread: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        active_operations = sum(1 for op in self.operations.values() if op.status == 'running')
        pending_operations = self.operation_queue.qsize()
        
        return {
            **self.performance_stats,
            'active_operations': active_operations,
            'pending_operations': pending_operations,
            'total_stored_operations': len(self.operations),
            'worker_threads': len(self.worker_threads),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def cleanup_old_operations(self, days_old: int = 7):
        """Clean up operations older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        operations_to_remove = []
        for operation_id, operation in self.operations.items():
            if operation.completed_at and operation.completed_at < cutoff_date:
                operations_to_remove.append(operation_id)
        
        for operation_id in operations_to_remove:
            del self.operations[operation_id]
        
        logger.info(f"Cleaned up {len(operations_to_remove)} old operations")
        return len(operations_to_remove)

# Global bulk operations manager
try:
    bulk_manager = BulkOperationsManager()
except Exception as e:
    logger.warning(f"Failed to create global bulk manager: {e}")
    bulk_manager = None

# Convenience functions
def submit_bulk_resume_upload(user_id: str, resume_files: List[Dict[str, Any]]) -> str:
    """Submit bulk resume upload operation"""
    if not bulk_manager:
        raise ValueError("Bulk operations manager not available")
    return bulk_manager.submit_operation('bulk_resume_upload', user_id, resume_files)

def submit_bulk_resume_analysis(user_id: str, resume_ids: List[str]) -> str:
    """Submit bulk resume analysis operation"""
    if not bulk_manager:
        raise ValueError("Bulk operations manager not available")
    items = [{'resume_id': resume_id} for resume_id in resume_ids]
    return bulk_manager.submit_operation('bulk_resume_analysis', user_id, items)

def submit_bulk_user_creation(admin_user_id: str, users_data: List[Dict[str, Any]]) -> str:
    """Submit bulk user creation operation"""
    if not bulk_manager:
        raise ValueError("Bulk operations manager not available")
    return bulk_manager.submit_operation('bulk_user_creation', admin_user_id, users_data)

def submit_bulk_email_send(user_id: str, recipients: List[Dict[str, Any]], template: str, subject: str) -> str:
    """Submit bulk email sending operation"""
    if not bulk_manager:
        raise ValueError("Bulk operations manager not available")
    parameters = {'template': template, 'subject': subject}
    return bulk_manager.submit_operation('bulk_email_send', user_id, recipients, parameters)
