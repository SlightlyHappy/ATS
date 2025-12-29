"""
Backup Sync Manager for Railway to Supabase Data Synchronization
Handles background sync operations to maintain Supabase as backup
"""

import threading
import queue
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class BackupSyncManager:
    """Manages background synchronization from Railway PostgreSQL to Supabase"""
    
    def __init__(self, railway_db, supabase_client):
        """Initialize backup sync manager"""
        self.railway_db = railway_db
        self.supabase = supabase_client
        self.sync_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        
        # Sync configuration - optimized for Railway Pro tier (32GB RAM, 32 cores)
        self.sync_interval = 7200   # Back to 2 hours for Pro tier
        self.retry_limit = 3        # Back to 3 retries with more resources
        self.batch_size = 100       # Increased from 25 - Pro tier can handle larger batches
        
        # Sync tracking
        self.last_sync = {}
        self.sync_stats = {
            'total_synced': 0,
            'failed_syncs': 0,
            'last_sync_time': None,
            'sync_lag_seconds': 0
        }
        
        # Connection pool circuit breaker for sync operations
        self.circuit_breaker = {
            "failure_count": 0,
            "failure_threshold": 5,  # Stop sync after 5 consecutive failures
            "recovery_timeout": 300,  # 5 minutes recovery time
            "last_failure": None,
            "state": "closed"  # closed, open, half-open
        }
        
        # Tables that only have created_at (no updated_at column)
        self.created_at_only_tables = {
            'user_activity', 'credit_transactions', 'payment_transactions'
        }
        
        logger.info("Backup sync manager initialized")
    
    def start_background_sync(self):
        """Start background sync worker thread"""
        import os
        
        # CRITICAL: Check if backup sync is disabled
        if os.getenv('BACKUP_SYNC_ENABLED', 'false').lower() != 'true':
            logger.info("🚫 Backup sync is DISABLED via BACKUP_SYNC_ENABLED environment variable")
            logger.info("This prevents Railway PostgreSQL connection exhaustion")
            return
        
        if self.running:
            logger.warning("Background sync already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.worker_thread.start()
        logger.info("Background sync to Supabase started")
    
    def stop_background_sync(self):
        """Stop background sync worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Background sync to Supabase stopped")
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows sync operations"""
        if self.circuit_breaker["state"] == "closed":
            return True
            
        if self.circuit_breaker["state"] == "open":
            # Check if recovery timeout has passed
            if (self.circuit_breaker["last_failure"] and 
                (datetime.now() - self.circuit_breaker["last_failure"]).seconds > self.circuit_breaker["recovery_timeout"]):
                self.circuit_breaker["state"] = "half-open"
                logger.info("Backup sync circuit breaker entering HALF-OPEN state")
                return True
            return False
            
        # half-open state - allow one test request
        return True
    
    def _circuit_breaker_success(self):
        """Reset circuit breaker on successful operation"""
        if self.circuit_breaker["state"] in ["half-open", "open"]:
            self.circuit_breaker["state"] = "closed"
            self.circuit_breaker["failure_count"] = 0
            logger.info("Backup sync circuit breaker CLOSED - connection recovered")
    
    def _circuit_breaker_trip(self, error_msg: str):
        """Trip the circuit breaker on failure"""
        self.circuit_breaker["failure_count"] += 1
        self.circuit_breaker["last_failure"] = datetime.now()
        
        if self.circuit_breaker["failure_count"] >= self.circuit_breaker["failure_threshold"]:
            self.circuit_breaker["state"] = "open"
            logger.warning(f"Backup sync circuit breaker OPEN: {error_msg}")

    def queue_sync(self, table: str, record_id: str, operation: str, data: Dict[str, Any] = None):
        """Queue a record for backup sync"""
        # Check circuit breaker before queuing
        if not self._check_circuit_breaker():
            logger.warning(f"Backup sync circuit breaker OPEN - skipping sync for {table}:{record_id}")
            return
            
        sync_item = {
            'table': table,
            'record_id': record_id,
            'operation': operation,  # 'insert', 'update', 'delete'
            'data': data,
            'timestamp': datetime.now(),
            'retry_count': 0
        }
        
        try:
            self.sync_queue.put(sync_item, timeout=1)
        except queue.Full:
            logger.warning(f"Sync queue full, dropping sync for {table}:{record_id}")
    
    def _sync_worker(self):
        """Background worker that processes sync queue"""
        logger.info("Sync worker started")
        
        while self.running:
            try:
                # Process queued sync items
                self._process_sync_queue()
                
                # Periodic full sync
                self._periodic_full_sync()
                
                # Sleep for a short time to prevent busy waiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Sync worker error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _process_sync_queue(self):
        """Process items in the sync queue"""
        try:
            # Process up to batch_size items
            processed = 0
            while processed < self.batch_size and not self.sync_queue.empty():
                try:
                    sync_item = self.sync_queue.get(timeout=0.1)
                    success = self._process_sync_item(sync_item)
                    
                    if success:
                        self.sync_stats['total_synced'] += 1
                    else:
                        # Retry failed syncs
                        if sync_item['retry_count'] < self.retry_limit:
                            sync_item['retry_count'] += 1
                            time.sleep(2 ** sync_item['retry_count'])  # Exponential backoff
                            self.sync_queue.put(sync_item)
                        else:
                            self.sync_stats['failed_syncs'] += 1
                            logger.error(f"Max retries exceeded for sync: {sync_item}")
                    
                    self.sync_queue.task_done()
                    processed += 1
                    
                except queue.Empty:
                    break
                    
        except Exception as e:
            logger.error(f"Error processing sync queue: {e}")
    
    def _process_sync_item(self, sync_item: Dict[str, Any]) -> bool:
        """Process individual sync item"""
        try:
            table = sync_item['table']
            record_id = sync_item['record_id']
            operation = sync_item['operation']
            data = sync_item.get('data')
            
            if operation in ['insert', 'update']:
                # Get current record from Railway if data not provided
                if not data:
                    records = self.railway_db.execute_read(
                        f"SELECT * FROM {table} WHERE id = %s", 
                        (record_id,)
                    )
                    if not records:
                        logger.warning(f"Record not found in Railway: {table}:{record_id}")
                        return True  # Consider this successful (record was deleted)
                    data = records[0]
                
                # Upsert to Supabase
                result = self.supabase.client.table(table).upsert(data).execute()
                if result.data:
                    logger.debug(f"Synced {operation} to Supabase: {table}:{record_id}")
                    return True
                else:
                    logger.error(f"Failed to sync {operation} to Supabase: {table}:{record_id}")
                    return False
                    
            elif operation == 'delete':
                # Delete from Supabase
                result = self.supabase.client.table(table).delete().eq('id', record_id).execute()
                logger.debug(f"Synced delete to Supabase: {table}:{record_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to sync {sync_item}: {e}")
            return False
    
    def _periodic_full_sync(self):
        """Perform periodic full sync of recent changes"""
        # Check circuit breaker before starting sync
        if not self._check_circuit_breaker():
            logger.warning("Backup sync circuit breaker OPEN - skipping periodic sync")
            return
            
        current_time = datetime.now()
        
        # Check if it's time for a full sync
        last_full_sync = self.sync_stats.get('last_sync_time')
        if (last_full_sync and 
            (current_time - last_full_sync).seconds < self.sync_interval):
            return

        logger.info("Starting periodic full sync")
        
        try:
            # Sync recent changes from each table with rate limiting
            tables = ['user_profiles', 'resumes', 'user_activity', 'hr_legal_queries', 
                     'user_credits', 'credit_transactions', 'payment_orders', 'payment_transactions']
            
            for table in tables:
                if not self._check_circuit_breaker():
                    logger.warning("Circuit breaker opened during sync - stopping")
                    break
                    
                try:
                    self._sync_table_recent_changes(table)
                    self._circuit_breaker_success()  # Reset on success
                    # Rate limiting - wait between table syncs to prevent connection storms
                    time.sleep(2)  # 2 second delay between tables
                except Exception as e:
                    logger.error(f"Table sync failed for {table}: {e}")
                    self._circuit_breaker_trip(f"Table sync failure: {table}")
            
            self.sync_stats['last_sync_time'] = current_time
            logger.info("Completed periodic full sync")
            
        except Exception as e:
            logger.error(f"Periodic full sync failed: {e}")
            self._circuit_breaker_trip(f"Full sync failure: {e}")
    
    def _sync_table_recent_changes(self, table: str, hours: int = 1):
        """Sync recent changes for a specific table"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            last_sync_time = self.last_sync.get(table, cutoff_time)
            
            # Check if table has updated_at column or only created_at
            if table in self.created_at_only_tables:
                # Tables with only created_at column
                query = f"""
                    SELECT * FROM {table} 
                    WHERE created_at > %s
                    ORDER BY created_at ASC
                    LIMIT 100
                """
                params = (last_sync_time,)
            else:
                # Tables with both updated_at and created_at columns
                query = f"""
                    SELECT * FROM {table} 
                    WHERE updated_at > %s OR created_at > %s
                    ORDER BY COALESCE(updated_at, created_at) ASC
                    LIMIT 100
                """
                params = (last_sync_time, last_sync_time)
            
            recent_records = self.railway_db.execute_read(query, params)
            
            if recent_records:
                # Batch sync to Supabase
                try:
                    result = self.supabase.client.table(table).upsert(recent_records).execute()
                    if result.data:
                        logger.info(f"Synced {len(recent_records)} recent records from {table}")
                        self.last_sync[table] = datetime.now()
                        self.sync_stats['total_synced'] += len(recent_records)
                    else:
                        logger.error(f"Failed to batch sync {table} to Supabase")
                        self.sync_stats['failed_syncs'] += len(recent_records)
                except Exception as e:
                    logger.error(f"Batch sync failed for {table}: {e}")
                    self.sync_stats['failed_syncs'] += len(recent_records)
            
        except Exception as e:
            logger.error(f"Failed to sync recent changes for {table}: {e}")
    
    def manual_sync_table(self, table: str, hours: int = 24) -> Dict[str, Any]:
        """Manually trigger sync for a specific table"""
        logger.info(f"Manual sync triggered for {table} (last {hours} hours)")
        
        try:
            start_time = datetime.now()
            cutoff_time = start_time - timedelta(hours=hours)
            
            # Check if table has updated_at column or only created_at
            if table in self.created_at_only_tables:
                # Tables with only created_at column
                query = f"""
                    SELECT * FROM {table} 
                    WHERE created_at > %s
                    ORDER BY created_at ASC
                """
                params = (cutoff_time,)
            else:
                # Tables with both updated_at and created_at columns
                query = f"""
                    SELECT * FROM {table} 
                    WHERE updated_at > %s OR created_at > %s
                    ORDER BY COALESCE(updated_at, created_at) ASC
                """
                params = (cutoff_time, cutoff_time)
            
            records = self.railway_db.execute_read(query, params)
            
            if not records:
                return {
                    'status': 'success',
                    'message': f'No recent records to sync for {table}',
                    'synced_count': 0,
                    'duration_seconds': 0
                }
            
            # Batch sync to Supabase
            result = self.supabase.client.table(table).upsert(records).execute()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.data:
                self.sync_stats['total_synced'] += len(records)
                return {
                    'status': 'success',
                    'message': f'Successfully synced {len(records)} records',
                    'synced_count': len(records),
                    'duration_seconds': duration
                }
            else:
                self.sync_stats['failed_syncs'] += len(records)
                return {
                    'status': 'error',
                    'message': 'Failed to sync records to Supabase',
                    'synced_count': 0,
                    'duration_seconds': duration
                }
                
        except Exception as e:
            logger.error(f"Manual sync failed for {table}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'synced_count': 0,
                'duration_seconds': 0
            }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics"""
        queue_size = self.sync_queue.qsize()
        
        # Calculate sync lag
        sync_lag = 0
        if self.sync_stats['last_sync_time']:
            sync_lag = (datetime.now() - self.sync_stats['last_sync_time']).total_seconds()
        
        return {
            'running': self.running,
            'queue_size': queue_size,
            'sync_lag_seconds': sync_lag,
            'total_synced': self.sync_stats['total_synced'],
            'failed_syncs': self.sync_stats['failed_syncs'],
            'last_sync_time': self.sync_stats['last_sync_time'].isoformat() if self.sync_stats['last_sync_time'] else None,
            'success_rate': self._calculate_success_rate(),
            'last_table_sync': {table: time.isoformat() for table, time in self.last_sync.items()},
            'circuit_breaker_state': self.circuit_breaker['state'],
            'circuit_breaker_failures': self.circuit_breaker['failure_count'],
            'optimization_status': 'Railway optimized - 2hr intervals, 100 record batches, circuit breaker enabled',
            'sync_interval_hours': self.sync_interval / 3600,
            'batch_size': self.batch_size
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate sync success rate"""
        total = self.sync_stats['total_synced'] + self.sync_stats['failed_syncs']
        if total == 0:
            return 1.0
        return self.sync_stats['total_synced'] / total
    
    def verify_data_consistency(self, table: str, sample_size: int = 10) -> Dict[str, Any]:
        """Verify data consistency between Railway and Supabase"""
        try:
            # Get recent records from Railway
            railway_records = self.railway_db.execute_read(f"""
                SELECT * FROM {table} 
                ORDER BY COALESCE(updated_at, created_at) DESC 
                LIMIT {sample_size}
            """)
            
            if not railway_records:
                return {'status': 'success', 'message': 'No records to verify'}
            
            # Check each record in Supabase
            inconsistencies = []
            for record in railway_records:
                try:
                    supabase_result = self.supabase.client.table(table).select('*').eq('id', record['id']).execute()
                    
                    if not supabase_result.data:
                        inconsistencies.append({
                            'id': record['id'],
                            'issue': 'Record missing in Supabase'
                        })
                    elif len(supabase_result.data) > 1:
                        inconsistencies.append({
                            'id': record['id'],
                            'issue': 'Duplicate records in Supabase'
                        })
                    # Could add more detailed field comparison here
                    
                except Exception as e:
                    inconsistencies.append({
                        'id': record['id'],
                        'issue': f'Error checking record: {str(e)}'
                    })
            
            if inconsistencies:
                return {
                    'status': 'inconsistent',
                    'message': f'Found {len(inconsistencies)} inconsistencies',
                    'inconsistencies': inconsistencies,
                    'checked_records': len(railway_records)
                }
            else:
                return {
                    'status': 'consistent',
                    'message': f'All {len(railway_records)} records are consistent',
                    'checked_records': len(railway_records)
                }
                
        except Exception as e:
            logger.error(f"Data consistency check failed for {table}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'checked_records': 0
            }
