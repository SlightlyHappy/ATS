"""
Backup Health Manager - Railway PostgreSQL Backup System with Health Monitoring
Complete backup solution with automated health checks and recovery procedures

Created: August 3, 2025
Author: Production Engineering Team
"""

import asyncio
import json
import logging
import psycopg2
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import os
import shutil
import gzip
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupHealthStatus:
    """Backup health status constants"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class BackupHealthManager:
    """
    Comprehensive backup and health management system for Railway PostgreSQL
    Provides automated backups, health monitoring, and disaster recovery capabilities
    """
    
    def __init__(self, railway_db_manager=None, supabase_client=None, config=None):
        """
        Initialize backup health manager with database connections
        
        Args:
            railway_db_manager: Railway database manager instance
            supabase_client: Supabase client for backup sync
            config: Configuration dictionary
        """
        self.railway_db = railway_db_manager
        self.supabase_client = supabase_client
        self.config = config or {}
        
        # Backup configuration
        self.backup_config = {
            'max_backup_age_hours': self.config.get('max_backup_age_hours', 24),
            'backup_retention_days': self.config.get('backup_retention_days', 30),
            'backup_directory': self.config.get('backup_directory', 'data/backups'),
            'enable_compression': self.config.get('enable_compression', True),
            'enable_encryption': self.config.get('enable_encryption', False),
            'max_backup_size_gb': self.config.get('max_backup_size_gb', 5),
            'backup_verification': self.config.get('backup_verification', True),
            'supabase_sync_enabled': self.config.get('supabase_sync_enabled', True)
        }
        
        # Health monitoring configuration
        self.health_config = {
            'check_interval_minutes': self.config.get('health_check_interval', 15),
            'max_response_time_ms': self.config.get('max_response_time_ms', 5000),
            'max_connection_pool_usage': self.config.get('max_connection_pool_usage', 80),
            'min_free_space_gb': self.config.get('min_free_space_gb', 2),
            'alert_thresholds': {
                'warning': 70,  # 70% usage triggers warning
                'critical': 90  # 90% usage triggers critical alert
            }
        }
        
        # Initialize backup directory
        self.backup_dir = Path(self.backup_config['backup_directory'])
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Health monitoring state
        self.last_health_check = None
        self.health_status = BackupHealthStatus.UNKNOWN
        self.health_issues = []
        
        logger.info("Backup Health Manager initialized successfully")
    
    async def perform_full_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a complete PostgreSQL backup with verification
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Dict containing backup results and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Generate backup filename
            if not backup_name:
                timestamp = start_time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"railway_backup_{timestamp}"
            
            backup_path = self.backup_dir / f"{backup_name}.sql"
            compressed_path = self.backup_dir / f"{backup_name}.sql.gz"
            
            logger.info(f"Starting full backup: {backup_name}")
            
            # Pre-backup health check
            health_status = await self.check_database_health()
            if health_status['status'] == BackupHealthStatus.CRITICAL:
                logger.warning("Database health is critical, proceeding with backup anyway")
            
            # Execute pg_dump
            backup_result = await self._execute_pg_dump(backup_path)
            if not backup_result['success']:
                raise Exception(f"pg_dump failed: {backup_result['error']}")
            
            # Verify backup integrity
            if self.backup_config['backup_verification']:
                verification_result = await self._verify_backup_integrity(backup_path)
                if not verification_result['success']:
                    raise Exception(f"Backup verification failed: {verification_result['error']}")
            
            # Compress backup if enabled
            final_path = backup_path
            if self.backup_config['enable_compression']:
                compression_result = await self._compress_backup(backup_path, compressed_path)
                if compression_result['success']:
                    final_path = compressed_path
                    backup_path.unlink()  # Remove uncompressed file
            
            # Calculate backup metadata
            backup_size = final_path.stat().st_size
            backup_checksum = await self._calculate_checksum(final_path)
            
            # Sync to Supabase if enabled
            supabase_sync_result = None
            if self.backup_config['supabase_sync_enabled'] and self.supabase_client:
                supabase_sync_result = await self._sync_to_supabase(final_path, backup_name)
            
            # Store backup metadata
            backup_metadata = {
                'backup_name': backup_name,
                'file_path': str(final_path),
                'file_size_bytes': backup_size,
                'file_size_mb': round(backup_size / (1024 * 1024), 2),
                'checksum': backup_checksum,
                'created_at': start_time.isoformat(),
                'completed_at': datetime.utcnow().isoformat(),
                'duration_seconds': (datetime.utcnow() - start_time).total_seconds(),
                'compressed': self.backup_config['enable_compression'],
                'verified': self.backup_config['backup_verification'],
                'supabase_synced': supabase_sync_result['success'] if supabase_sync_result else False,
                'database_health': health_status['status']
            }
            
            # Save metadata to Railway PostgreSQL
            await self._save_backup_metadata(backup_metadata)
            
            # Cleanup old backups
            await self._cleanup_old_backups()
            
            logger.info(f"Backup completed successfully: {backup_name} ({backup_metadata['file_size_mb']} MB)")
            
            return {
                'success': True,
                'backup_metadata': backup_metadata,
                'message': f"Backup completed successfully: {backup_name}"
            }
            
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            logger.error(error_msg)
            
            # Log backup failure
            if hasattr(self, 'railway_db') and self.railway_db:
                try:
                    await self._log_backup_failure(backup_name, error_msg, start_time)
                except:
                    pass  # Don't fail on logging failure
            
            return {
                'success': False,
                'error': error_msg,
                'backup_name': backup_name,
                'started_at': start_time.isoformat()
            }
    
    async def check_database_health(self) -> Dict[str, Any]:
        """
        Comprehensive database health check
        
        Returns:
            Dict containing health status and detailed metrics
        """
        start_time = datetime.utcnow()
        health_issues = []
        metrics = {}
        
        try:
            if not self.railway_db:
                return {
                    'status': BackupHealthStatus.CRITICAL,
                    'message': 'Railway database connection not available',
                    'checked_at': start_time.isoformat()
                }
            
            # Test basic connectivity
            connectivity_result = await self._test_database_connectivity()
            metrics['connectivity'] = connectivity_result
            if not connectivity_result['success']:
                health_issues.append(f"Database connectivity failed: {connectivity_result['error']}")
            
            # Check response times
            response_time_result = await self._check_response_times()
            metrics['response_time'] = response_time_result
            if response_time_result['avg_response_ms'] > self.health_config['max_response_time_ms']:
                health_issues.append(f"High response time: {response_time_result['avg_response_ms']}ms")
            
            # Check connection pool status
            pool_result = await self._check_connection_pool()
            metrics['connection_pool'] = pool_result
            if pool_result['usage_percent'] > self.health_config['max_connection_pool_usage']:
                health_issues.append(f"High connection pool usage: {pool_result['usage_percent']}%")
            
            # Check disk space
            disk_result = await self._check_disk_space()
            metrics['disk_space'] = disk_result
            if disk_result['free_space_gb'] < self.health_config['min_free_space_gb']:
                health_issues.append(f"Low disk space: {disk_result['free_space_gb']} GB remaining")
            
            # Check backup status
            backup_result = await self._check_backup_status()
            metrics['backup_status'] = backup_result
            if backup_result['hours_since_last_backup'] > self.backup_config['max_backup_age_hours']:
                health_issues.append(f"Backup overdue: {backup_result['hours_since_last_backup']} hours since last backup")
            
            # Determine overall health status
            if len(health_issues) == 0:
                status = BackupHealthStatus.HEALTHY
                message = "All systems operational"
            elif len(health_issues) <= 2:
                status = BackupHealthStatus.WARNING
                message = f"Minor issues detected: {len(health_issues)} warnings"
            else:
                status = BackupHealthStatus.CRITICAL
                message = f"Multiple issues detected: {len(health_issues)} problems"
            
            # Update internal state
            self.last_health_check = start_time
            self.health_status = status
            self.health_issues = health_issues
            
            # Log health check to database
            await self._log_health_check(status, metrics, health_issues)
            
            return {
                'status': status,
                'message': message,
                'issues': health_issues,
                'metrics': metrics,
                'checked_at': start_time.isoformat(),
                'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
            }
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            
            self.health_status = BackupHealthStatus.CRITICAL
            self.health_issues = [error_msg]
            
            return {
                'status': BackupHealthStatus.CRITICAL,
                'message': error_msg,
                'checked_at': start_time.isoformat()
            }
    
    async def get_backup_history(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get backup history and status
        
        Args:
            limit: Maximum number of backups to return
            
        Returns:
            Dict containing backup history and statistics
        """
        try:
            if not self.railway_db:
                return {
                    'success': False,
                    'error': 'Database connection not available'
                }
            
            # Query backup history from Railway PostgreSQL
            with self.railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            backup_name,
                            file_path,
                            file_size_mb,
                            created_at,
                            completed_at,
                            duration_seconds,
                            compressed,
                            verified,
                            supabase_synced,
                            database_health
                        FROM backup_metadata 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (limit,))
                    
                    backups = []
                    for row in cursor.fetchall():
                        backup = {
                            'backup_name': row[0],
                            'file_path': row[1],
                            'file_size_mb': row[2],
                            'created_at': row[3].isoformat() if row[3] else None,
                            'completed_at': row[4].isoformat() if row[4] else None,
                            'duration_seconds': row[5],
                            'compressed': row[6],
                            'verified': row[7],
                            'supabase_synced': row[8],
                            'database_health': row[9]
                        }
                        backups.append(backup)
                    
                    # Get backup statistics
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_backups,
                            AVG(file_size_mb) as avg_size_mb,
                            AVG(duration_seconds) as avg_duration_seconds,
                            SUM(CASE WHEN verified = true THEN 1 ELSE 0 END) as verified_count,
                            SUM(CASE WHEN supabase_synced = true THEN 1 ELSE 0 END) as synced_count,
                            MAX(created_at) as last_backup_at
                        FROM backup_metadata
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                    
                    stats_row = cursor.fetchone()
                    stats = {
                        'total_backups_30_days': stats_row[0] or 0,
                        'avg_size_mb': round(float(stats_row[1] or 0), 2),
                        'avg_duration_seconds': round(float(stats_row[2] or 0), 1),
                        'verification_rate': round((stats_row[3] / stats_row[0]) * 100, 1) if stats_row[0] > 0 else 0,
                        'sync_rate': round((stats_row[4] / stats_row[0]) * 100, 1) if stats_row[0] > 0 else 0,
                        'last_backup_at': stats_row[5].isoformat() if stats_row[5] else None,
                        'hours_since_last_backup': (datetime.utcnow() - stats_row[5]).total_seconds() / 3600 if stats_row[5] else None
                    }
            
            return {
                'success': True,
                'backups': backups,
                'statistics': stats,
                'backup_config': self.backup_config
            }
            
        except Exception as e:
            logger.error(f"Error fetching backup history: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def restore_from_backup(self, backup_name: str, target_database: Optional[str] = None) -> Dict[str, Any]:
        """
        Restore database from backup
        
        Args:
            backup_name: Name of the backup to restore
            target_database: Optional target database name (defaults to current)
            
        Returns:
            Dict containing restore results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting database restore from backup: {backup_name}")
            
            # Find backup file
            backup_metadata = await self._get_backup_metadata(backup_name)
            if not backup_metadata:
                raise Exception(f"Backup not found: {backup_name}")
            
            backup_path = Path(backup_metadata['file_path'])
            if not backup_path.exists():
                # Try to restore from Supabase if available
                if backup_metadata.get('supabase_synced') and self.supabase_client:
                    logger.info("Local backup not found, attempting Supabase restore")
                    supabase_restore_result = await self._restore_from_supabase(backup_name, backup_path)
                    if not supabase_restore_result['success']:
                        raise Exception(f"Cannot restore from Supabase: {supabase_restore_result['error']}")
                else:
                    raise Exception(f"Backup file not found and Supabase restore not available: {backup_path}")
            
            # Verify backup integrity before restore
            if backup_metadata.get('verified', False):
                verification_result = await self._verify_backup_integrity(backup_path)
                if not verification_result['success']:
                    raise Exception(f"Backup verification failed: {verification_result['error']}")
            
            # Decompress if necessary
            restore_path = backup_path
            if backup_metadata.get('compressed', False):
                decompressed_path = backup_path.with_suffix('')
                decompression_result = await self._decompress_backup(backup_path, decompressed_path)
                if decompression_result['success']:
                    restore_path = decompressed_path
            
            # Execute restore
            restore_result = await self._execute_pg_restore(restore_path, target_database)
            if not restore_result['success']:
                raise Exception(f"Database restore failed: {restore_result['error']}")
            
            # Cleanup temporary files
            if restore_path != backup_path and restore_path.exists():
                restore_path.unlink()
            
            # Log successful restore
            restore_metadata = {
                'backup_name': backup_name,
                'restore_started_at': start_time.isoformat(),
                'restore_completed_at': datetime.utcnow().isoformat(),
                'duration_seconds': (datetime.utcnow() - start_time).total_seconds(),
                'target_database': target_database or 'default',
                'restored_by': 'backup_health_manager'
            }
            
            await self._log_restore_operation(restore_metadata)
            
            logger.info(f"Database restore completed successfully: {backup_name}")
            
            return {
                'success': True,
                'restore_metadata': restore_metadata,
                'message': f"Database restore completed successfully: {backup_name}"
            }
            
        except Exception as e:
            error_msg = f"Database restore failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'backup_name': backup_name,
                'started_at': start_time.isoformat()
            }
    
    # Private helper methods
    
    async def _execute_pg_dump(self, backup_path: Path) -> Dict[str, Any]:
        """Execute pg_dump command"""
        try:
            # Get database URL from Railway environment
            database_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
            if not database_url:
                raise Exception("Database URL not found in environment variables")
            
            cmd = [
                'pg_dump',
                '--no-password',
                '--verbose',
                '--clean',
                '--if-exists',
                '--format=plain',
                f'--file={backup_path}',
                database_url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {'success': True, 'output': stdout.decode()}
            else:
                return {'success': False, 'error': stderr.decode()}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _verify_backup_integrity(self, backup_path: Path) -> Dict[str, Any]:
        """Verify backup file integrity"""
        try:
            # Check file exists and has content
            if not backup_path.exists():
                return {'success': False, 'error': 'Backup file does not exist'}
            
            file_size = backup_path.stat().st_size
            if file_size < 1024:  # Less than 1KB is suspicious
                return {'success': False, 'error': f'Backup file too small: {file_size} bytes'}
            
            # Check for SQL content
            with open(backup_path, 'r', encoding='utf-8') as f:
                first_lines = f.read(1024)
                if 'PostgreSQL database dump' not in first_lines:
                    return {'success': False, 'error': 'File does not appear to be a valid PostgreSQL dump'}
            
            return {'success': True, 'file_size': file_size}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _compress_backup(self, source_path: Path, target_path: Path) -> Dict[str, Any]:
        """Compress backup file using gzip"""
        try:
            with open(source_path, 'rb') as src:
                with gzip.open(target_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
            
            original_size = source_path.stat().st_size
            compressed_size = target_path.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            return {
                'success': True,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': round(compression_ratio, 1)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def _sync_to_supabase(self, backup_path: Path, backup_name: str) -> Dict[str, Any]:
        """Sync backup to Supabase storage"""
        try:
            if not self.supabase_client:
                return {'success': False, 'error': 'Supabase client not available'}
            
            # Upload to Supabase storage
            with open(backup_path, 'rb') as f:
                file_data = f.read()
            
            storage_path = f"backups/{backup_name}.sql.gz"
            
            # Upload file to Supabase storage
            result = self.supabase_client.storage.from_('railway-backups').upload(
                storage_path, file_data
            )
            
            return {'success': True, 'storage_path': storage_path, 'result': result}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test basic database connectivity"""
        try:
            start_time = datetime.utcnow()
            
            with self.railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                'success': True,
                'response_time_ms': round(response_time, 2),
                'test_result': result[0] if result else None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _check_response_times(self) -> Dict[str, Any]:
        """Check database response times with sample queries"""
        try:
            response_times = []
            
            # Test queries
            test_queries = [
                "SELECT COUNT(*) FROM user_profiles",
                "SELECT COUNT(*) FROM resumes",
                "SELECT COUNT(*) FROM user_activity_detailed",
                "SELECT pg_database_size(current_database())"
            ]
            
            for query in test_queries:
                start_time = datetime.utcnow()
                
                with self.railway_db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query)
                        cursor.fetchone()
                
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                response_times.append(response_time)
            
            return {
                'success': True,
                'avg_response_ms': round(sum(response_times) / len(response_times), 2),
                'max_response_ms': round(max(response_times), 2),
                'min_response_ms': round(min(response_times), 2),
                'query_count': len(test_queries)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _check_connection_pool(self) -> Dict[str, Any]:
        """Check connection pool status"""
        try:
            with self.railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            count(*) as total_connections,
                            count(*) FILTER (WHERE state = 'active') as active_connections,
                            count(*) FILTER (WHERE state = 'idle') as idle_connections
                        FROM pg_stat_activity 
                        WHERE datname = current_database()
                    """)
                    
                    row = cursor.fetchone()
                    total = row[0] or 0
                    active = row[1] or 0
                    idle = row[2] or 0
                    
                    # Estimate usage percentage (assuming max 100 connections)
                    max_connections = 100
                    usage_percent = (total / max_connections) * 100
            
            return {
                'success': True,
                'total_connections': total,
                'active_connections': active,
                'idle_connections': idle,
                'usage_percent': round(usage_percent, 1)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            # Get database size
            with self.railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT pg_database_size(current_database())")
                    db_size_bytes = cursor.fetchone()[0]
            
            # Check local backup directory space
            backup_dir_stats = shutil.disk_usage(self.backup_dir)
            free_space_bytes = backup_dir_stats.free
            
            return {
                'success': True,
                'database_size_gb': round(db_size_bytes / (1024**3), 2),
                'free_space_gb': round(free_space_bytes / (1024**3), 2),
                'backup_dir_path': str(self.backup_dir)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _check_backup_status(self) -> Dict[str, Any]:
        """Check backup status and age"""
        try:
            with self.railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            MAX(created_at) as last_backup_at,
                            COUNT(*) as total_backups_24h
                        FROM backup_metadata 
                        WHERE created_at >= NOW() - INTERVAL '24 hours'
                    """)
                    
                    row = cursor.fetchone()
                    last_backup_at = row[0]
                    total_backups_24h = row[1] or 0
                    
                    hours_since_last_backup = None
                    if last_backup_at:
                        hours_since_last_backup = (datetime.utcnow() - last_backup_at.replace(tzinfo=None)).total_seconds() / 3600
            
            return {
                'success': True,
                'last_backup_at': last_backup_at.isoformat() if last_backup_at else None,
                'hours_since_last_backup': round(hours_since_last_backup, 1) if hours_since_last_backup else None,
                'backups_last_24h': total_backups_24h
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _save_backup_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save backup metadata to Railway PostgreSQL"""
        try:
            with self.railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO backup_metadata 
                        (backup_name, file_path, file_size_bytes, file_size_mb, checksum, 
                         created_at, completed_at, duration_seconds, compressed, verified, 
                         supabase_synced, database_health)
                        VALUES (%(backup_name)s, %(file_path)s, %(file_size_bytes)s, %(file_size_mb)s, 
                                %(checksum)s, %(created_at)s, %(completed_at)s, %(duration_seconds)s, 
                                %(compressed)s, %(verified)s, %(supabase_synced)s, %(database_health)s)
                    """, metadata)
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    async def _log_health_check(self, status: str, metrics: Dict[str, Any], issues: List[str]) -> None:
        """Log health check results to database"""
        try:
            with self.railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO system_health_logs 
                        (check_timestamp, health_status, metrics, issues, checked_by)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        datetime.utcnow(),
                        status,
                        json.dumps(metrics),
                        json.dumps(issues),
                        'backup_health_manager'
                    ))
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Failed to log health check: {e}")
    
    async def _cleanup_old_backups(self) -> None:
        """Cleanup old backup files based on retention policy"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.backup_config['backup_retention_days'])
            
            # Find old backup records
            with self.railway_db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT backup_name, file_path 
                        FROM backup_metadata 
                        WHERE created_at < %s
                    """, (cutoff_date,))
                    
                    old_backups = cursor.fetchall()
                    
                    for backup_name, file_path in old_backups:
                        # Delete local file
                        backup_file = Path(file_path)
                        if backup_file.exists():
                            backup_file.unlink()
                            logger.info(f"Deleted old backup file: {file_path}")
                        
                        # Delete metadata record
                        cursor.execute("DELETE FROM backup_metadata WHERE backup_name = %s", (backup_name,))
                    
                    conn.commit()
                    logger.info(f"Cleaned up {len(old_backups)} old backups")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

# Global backup health manager instance
backup_health_manager = None

def initialize_backup_health_manager(railway_db_manager=None, supabase_client=None, config=None):
    """Initialize the global backup health manager"""
    global backup_health_manager
    backup_health_manager = BackupHealthManager(railway_db_manager, supabase_client, config)
    return backup_health_manager

def get_backup_health_manager():
    """Get the global backup health manager instance"""
    return backup_health_manager
