#!/usr/bin/env python3
"""
Storage Manager for HR ATS System
Handles file storage and data management
"""

import os
import json
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageManager:
    """Lightweight storage management for files and data"""
    
    def __init__(self):
        """Initialize storage manager"""
        self.base_path = Path.cwd()
        self.upload_path = self.base_path / 'uploads'
        self.processed_path = self.base_path / 'processed'
        self.temp_path = self.base_path / 'temp'
        self.logs_path = self.base_path / 'logs'
        
        # Create directories
        self._create_directories()
        
        # Storage configuration
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB
        self.cleanup_interval = int(os.getenv('CLEANUP_INTERVAL_HOURS', 24))  # 24 hours
        self.max_storage_size = int(os.getenv('MAX_STORAGE_SIZE', 1024 * 1024 * 1024))  # 1GB
        
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.upload_path,
            self.processed_path,
            self.temp_path,
            self.logs_path
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            logger.info(f"Directory ensured: {directory}")
            
    def store_file(self, file, user_id: str, file_type: str = 'resume') -> Dict[str, Any]:
        """Store uploaded file securely"""
        try:
            if not file or not file.filename:
                raise ValueError("No file provided")
                
            # Generate secure filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            file_hash = hashlib.md5(f"{user_id}_{timestamp}_{file.filename}".encode()).hexdigest()[:8]
            safe_filename = f"{timestamp}_{file_hash}_{self._sanitize_filename(file.filename)}"
            
            # Determine storage path based on type
            if file_type == 'resume':
                file_path = self.upload_path / safe_filename
            else:
                file_path = self.temp_path / safe_filename
                
            # Check file size
            if hasattr(file, 'content_length') and file.content_length:
                if file.content_length > self.max_file_size:
                    raise ValueError(f"File too large: {file.content_length} bytes")
                    
            # Save file
            file.save(str(file_path))
            
            # Get file info
            file_stats = file_path.stat()
            
            file_info = {
                'filename': file.filename,
                'safe_filename': safe_filename,
                'file_path': str(file_path),
                'file_size': file_stats.st_size,
                'file_type': file_type,
                'user_id': user_id,
                'upload_time': datetime.utcnow().isoformat(),
                'mime_type': self._get_mime_type(file.filename),
                'file_hash': self._calculate_file_hash(file_path)
            }
            
            logger.info(f"File stored: {safe_filename} for user {user_id}")
            return file_info
            
        except Exception as e:
            logger.error(f"File storage error: {e}")
            raise
            
    def retrieve_file(self, file_path: str, user_id: str) -> Optional[Path]:
        """Retrieve file if it belongs to the user"""
        try:
            file_path_obj = Path(file_path)
            
            # Security check: ensure file is in allowed directories
            if not (self.upload_path in file_path_obj.parents or 
                   self.processed_path in file_path_obj.parents):
                logger.warning(f"Unauthorized file access attempt: {file_path}")
                return None
                
            # Check if file exists
            if not file_path_obj.exists():
                return None
                
            # In a real implementation, you'd verify the user owns this file
            # by checking database records
            
            return file_path_obj
            
        except Exception as e:
            logger.error(f"File retrieval error: {e}")
            return None
            
    def delete_file(self, file_path: str, user_id: str) -> bool:
        """Delete file if it belongs to the user"""
        try:
            file_path_obj = Path(file_path)
            
            # Security check
            if not (self.upload_path in file_path_obj.parents or 
                   self.processed_path in file_path_obj.parents):
                return False
                
            if file_path_obj.exists():
                file_path_obj.unlink()
                logger.info(f"File deleted: {file_path} for user {user_id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"File deletion error: {e}")
            return False
            
    def cleanup_old_files(self):
        """Clean up old files"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.cleanup_interval)
            deleted_count = 0
            
            for directory in [self.upload_path, self.processed_path, self.temp_path]:
                for file_path in directory.iterdir():
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_time < cutoff_time:
                            file_path.unlink()
                            deleted_count += 1
                            
            logger.info(f"Cleanup completed: {deleted_count} files deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0
            
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'directories': {}
            }
            
            for directory in [self.upload_path, self.processed_path, self.temp_path]:
                dir_stats = self._get_directory_stats(directory)
                stats['directories'][directory.name] = dir_stats
                stats['total_files'] += dir_stats['file_count']
                stats['total_size'] += dir_stats['total_size']
                
            # Add percentage usage
            stats['usage_percentage'] = (stats['total_size'] / self.max_storage_size) * 100
            stats['available_space'] = self.max_storage_size - stats['total_size']
            
            return stats
            
        except Exception as e:
            logger.error(f"Storage stats error: {e}")
            return {}
            
    def _get_directory_stats(self, directory: Path) -> Dict[str, Any]:
        """Get statistics for a directory"""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in directory.iterdir():
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
                    
            return {
                'file_count': file_count,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Directory stats error: {e}")
            return {'file_count': 0, 'total_size': 0, 'total_size_mb': 0}
            
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:90] + ext
            
        return filename
        
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename"""
        import mimetypes
        
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for integrity checking"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
            
        except Exception as e:
            logger.error(f"Hash calculation error: {e}")
            return ""
            
    def store_processed_data(self, data: Dict[str, Any], user_id: str, data_type: str) -> str:
        """Store processed data (analysis results, etc.)"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"{data_type}_{user_id}_{timestamp}.json"
            file_path = self.processed_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Processed data stored: {filename}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Processed data storage error: {e}")
            raise
            
    def retrieve_processed_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Retrieve processed data"""
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return None
                
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Processed data retrieval error: {e}")
            return None
            
    def create_backup(self, user_id: str) -> Optional[str]:
        """Create backup of user data"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{user_id}_{timestamp}.zip"
            backup_path = self.temp_path / backup_filename
            
            # In a real implementation, you'd zip user's files and data
            # For now, just create a placeholder
            
            logger.info(f"Backup created: {backup_filename}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup creation error: {e}")
            return None
            
    def health_check(self) -> Dict[str, Any]:
        """Check storage system health"""
        try:
            stats = self.get_storage_stats()
            
            # Check if directories are writable
            writable_check = {}
            for directory in [self.upload_path, self.processed_path, self.temp_path]:
                try:
                    test_file = directory / 'health_check.tmp'
                    test_file.write_text('test')
                    test_file.unlink()
                    writable_check[directory.name] = True
                except:
                    writable_check[directory.name] = False
                    
            # Determine overall health
            all_writable = all(writable_check.values())
            storage_ok = stats.get('usage_percentage', 0) < 90  # Less than 90% full
            
            status = 'healthy' if all_writable and storage_ok else 'degraded'
            
            return {
                'status': status,
                'directories_writable': writable_check,
                'storage_stats': stats,
                'warnings': [] if storage_ok else ['Storage usage > 90%']
            }
            
        except Exception as e:
            logger.error(f"Storage health check error: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
