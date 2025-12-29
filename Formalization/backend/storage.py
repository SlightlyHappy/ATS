"""
Memory-efficient resume storage and retrieval system.
Implements LRU cache with disk persistence for handling large volumes.
Now includes Supabase integration for persistent cloud storage.
"""

import os
import json
import gzip
import pickle
import sqlite3
import hashlib
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import OrderedDict
import psutil
import logging

# Import Supabase storage
try:
    from supabase_storage import SupabaseStorage
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"Supabase storage not available: {e}")

logger = logging.getLogger(__name__)

class ResumeStorage:
    """Memory-efficient storage system for processed resumes."""
    
    def __init__(self, config):
        self.config = config
        self.memory_cache = OrderedDict()  # LRU cache
        self.lock = threading.RLock()
        self.storage_dir = "resume_storage"
        self.db_path = os.path.join(self.storage_dir, "resumes.db")
        
        # Initialize Supabase if available and enabled
        self.supabase = None
        if (SUPABASE_AVAILABLE and 
            getattr(config, 'ENABLE_PERSISTENT_STORAGE', False) and
            os.getenv('ENABLE_PERSISTENT_STORAGE') == 'True'):
            try:
                self.supabase = SupabaseStorage()
                logger.info("Supabase storage initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                self.supabase = None
        
        # Create storage directory
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Load recent resumes into memory
        self._load_recent_resumes()
    
    def _init_database(self):
        """Initialize SQLite database for resume metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_hash TEXT UNIQUE,
                    processed_at TIMESTAMP,
                    file_size INTEGER,
                    text_length INTEGER,
                    scores_summary TEXT,
                    storage_path TEXT,
                    last_accessed TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_at ON resumes(processed_at);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON resumes(last_accessed);
            """)
    
    def _generate_file_hash(self, content: str) -> str:
        """Generate hash for content deduplication."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        return psutil.virtual_memory().percent / 100.0
    
    def _cleanup_memory_if_needed(self):
        """Clean up memory cache if usage is high."""
        memory_usage = self._get_memory_usage()
        
        if memory_usage > self.config.MEMORY_WARNING_THRESHOLD:
            logger.warning(f"High memory usage: {memory_usage:.1%}")
            
            # Remove oldest entries from memory cache
            while (len(self.memory_cache) > self.config.MAX_MEMORY_CACHE_SIZE // 2 and 
                   self._get_memory_usage() > 0.7):
                self.memory_cache.popitem(last=False)
            
            logger.info(f"Memory cleanup completed. Cache size: {len(self.memory_cache)}")
    
    def _save_to_disk(self, resume_data: Dict[str, Any]) -> str:
        """Save resume data to disk with compression."""
        file_hash = resume_data.get('file_hash')
        storage_filename = f"{file_hash}.gz"
        storage_path = os.path.join(self.storage_dir, storage_filename)
        
        try:
            if self.config.COMPRESS_PROCESSED_FILES:
                with gzip.open(storage_path, 'wb') as f:
                    if self.config.STORAGE_FORMAT == 'json':
                        json_data = json.dumps(resume_data, ensure_ascii=False, indent=2)
                        f.write(json_data.encode('utf-8'))
                    else:
                        pickle.dump(resume_data, f)
            else:
                with open(storage_path, 'w', encoding='utf-8') as f:
                    if self.config.STORAGE_FORMAT == 'json':
                        json.dump(resume_data, f, ensure_ascii=False, indent=2)
                    else:
                        with open(storage_path, 'wb') as fb:
                            pickle.dump(resume_data, fb)
            
            return storage_path
        except Exception as e:
            logger.error(f"Error saving resume to disk: {e}")
            return None
    
    def _load_from_disk(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """Load resume data from disk."""
        try:
            if not os.path.exists(storage_path):
                return None
            
            if self.config.COMPRESS_PROCESSED_FILES:
                with gzip.open(storage_path, 'rb') as f:
                    if self.config.STORAGE_FORMAT == 'json':
                        json_data = f.read().decode('utf-8')
                        return json.loads(json_data)
                    else:
                        return pickle.load(f)
            else:
                if self.config.STORAGE_FORMAT == 'json':
                    with open(storage_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    with open(storage_path, 'rb') as f:
                        return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading resume from disk: {e}")
            return None
    
    def _load_recent_resumes(self):
        """Load recent resumes into memory cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, storage_path FROM resumes 
                    ORDER BY last_accessed DESC, processed_at DESC 
                    LIMIT ?
                """, (self.config.MAX_MEMORY_CACHE_SIZE,))
                
                for resume_id, storage_path in cursor.fetchall():
                    resume_data = self._load_from_disk(storage_path)
                    if resume_data:
                        self.memory_cache[resume_id] = resume_data
        except Exception as e:
            logger.error(f"Error loading recent resumes: {e}")
    
    def store_resume(self, resume_data: Dict[str, Any]) -> int:
        """Store resume with memory and disk management, and sync to Supabase."""
        with self.lock:
            # Generate file hash for deduplication
            content = resume_data.get('ai_analysis', {}).get('raw_text', '')
            file_hash = self._generate_file_hash(content)
            resume_data['file_hash'] = file_hash
            
            # Check for duplicates
            existing_id = self._find_duplicate(file_hash)
            if existing_id:
                logger.info(f"Duplicate resume detected: {resume_data.get('filename')}")
                return existing_id
            
            # Save to disk
            storage_path = self._save_to_disk(resume_data)
            if not storage_path:
                raise Exception("Failed to save resume to disk")
            
            # Save metadata to database
            resume_id = self._save_metadata(resume_data, storage_path)
            
            # Sync to Supabase if available
            if self.supabase:
                try:
                    # Run async sync in background
                    asyncio.create_task(self._sync_to_supabase(resume_data))
                    logger.info(f"Queued resume for Supabase sync: {resume_data.get('filename')}")
                except Exception as e:
                    logger.error(f"Failed to queue Supabase sync: {e}")
            
            # Add to memory cache
            self.memory_cache[resume_id] = resume_data
            
            # Cleanup if needed
            self._cleanup_memory_if_needed()
            
            return resume_id
    
    def _find_duplicate(self, file_hash: str) -> Optional[int]:
        """Check if resume already exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id FROM resumes WHERE file_hash = ?", 
                    (file_hash,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return None
    
    def _save_metadata(self, resume_data: Dict[str, Any], storage_path: str) -> int:
        """Save resume metadata to database."""
        ai_analysis = resume_data.get('ai_analysis', {})
        scores = ai_analysis.get('scores', {})
        scores_summary = json.dumps(scores)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO resumes (
                    filename, file_hash, processed_at, file_size, 
                    text_length, scores_summary, storage_path, last_accessed, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resume_data.get('filename'),
                resume_data.get('file_hash'),
                resume_data.get('processed_at'),
                resume_data.get('text_length', 0),
                len(str(ai_analysis)),
                scores_summary,
                storage_path,
                datetime.now().isoformat(),
                resume_data.get('user_id', 1)  # Default to user_id 1 if not provided
            ))
            return cursor.lastrowid
    
    def get_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """Get resume by ID with memory/disk management."""
        with self.lock:
            # Check memory cache first
            if resume_id in self.memory_cache:
                # Move to end (most recently used)
                resume_data = self.memory_cache.pop(resume_id)
                self.memory_cache[resume_id] = resume_data
                
                # Update last accessed time
                self._update_last_accessed(resume_id)
                return resume_data
            
            # Load from disk
            storage_path = self._get_storage_path(resume_id)
            if storage_path:
                resume_data = self._load_from_disk(storage_path)
                if resume_data:
                    # Add to memory cache
                    self.memory_cache[resume_id] = resume_data
                    
                    # Maintain cache size
                    if len(self.memory_cache) > self.config.MAX_MEMORY_CACHE_SIZE:
                        self.memory_cache.popitem(last=False)
                    
                    self._update_last_accessed(resume_id)
                    return resume_data
            
            return None
    
    def get_resume_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get resume by file hash."""
        resume_id = self._find_duplicate(file_hash)
        if resume_id:
            return self.get_resume(resume_id)
        return None
    
    def _get_storage_path(self, resume_id: int) -> Optional[str]:
        """Get storage path for resume ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT storage_path FROM resumes WHERE id = ?", 
                    (resume_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting storage path: {e}")
            return None
    
    def _update_last_accessed(self, resume_id: int):
        """Update last accessed timestamp."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE resumes SET last_accessed = ? WHERE id = ?",
                    (datetime.now().isoformat(), resume_id)
                )
        except Exception as e:
            logger.error(f"Error updating last accessed: {e}")
    
    def get_all_resumes_summary(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get summary of all resumes without loading full content."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT id, filename, processed_at, file_size, 
                           text_length, scores_summary, last_accessed
                    FROM resumes 
                    ORDER BY processed_at DESC
                """
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor = conn.execute(query)
                results = []
                
                for row in cursor.fetchall():
                    resume_id, filename, processed_at, file_size, text_length, scores_summary, last_accessed = row
                    
                    try:
                        scores = json.loads(scores_summary) if scores_summary else {}
                    except:
                        scores = {}
                    
                    results.append({
                        "id": resume_id,
                        "filename": filename,
                        "processed_at": processed_at,
                        "file_size": file_size,
                        "text_length": text_length,
                        "scores": scores,
                        "last_accessed": last_accessed,
                        "in_memory": resume_id in self.memory_cache
                    })
                
                return results
        except Exception as e:
            logger.error(f"Error getting resumes summary: {e}")
            return []
    
    def cleanup_old_files(self):
        """Clean up old resume files based on configuration."""
        cutoff_time = datetime.now() - timedelta(hours=self.config.MAX_FILE_AGE_HOURS)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get old files
                cursor = conn.execute("""
                    SELECT id, storage_path FROM resumes 
                    WHERE last_accessed < ?
                """, (cutoff_time.isoformat(),))
                
                for resume_id, storage_path in cursor.fetchall():
                    try:
                        if os.path.exists(storage_path):
                            os.remove(storage_path)
                        
                        # Remove from memory cache
                        self.memory_cache.pop(resume_id, None)
                        
                        # Remove from database
                        conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
                        
                        logger.info(f"Cleaned up old resume: {resume_id}")
                    except Exception as e:
                        logger.error(f"Error cleaning up resume {resume_id}: {e}")
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def _sync_to_supabase(self, resume_data: Dict[str, Any]):
        """Sync resume data to Supabase asynchronously."""
        try:
            if not self.supabase:
                return
            
            result = await self.supabase.save_resume(resume_data)
            if result:
                logger.info(f"Successfully synced resume to Supabase: {result['id']}")
            else:
                logger.warning(f"Failed to sync resume to Supabase: {resume_data.get('filename')}")
                
        except Exception as e:
            logger.error(f"Error syncing to Supabase: {e}")
    
    def sync_resume_to_supabase(self, resume_id: int) -> bool:
        """Manually sync a specific resume to Supabase."""
        try:
            resume_data = self.get_resume(resume_id)
            if not resume_data:
                logger.error(f"Resume {resume_id} not found for sync")
                return False
            
            if not self.supabase:
                logger.error("Supabase not available for sync")
                return False
            
            # Run sync
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.supabase.save_resume(resume_data))
                return result is not None
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error syncing resume {resume_id} to Supabase: {e}")
            return False
    
    def get_supabase_stats(self) -> Dict[str, Any]:
        """Get Supabase storage statistics."""
        if not self.supabase:
            return {"available": False, "message": "Supabase not configured"}
        
        try:
            # Test connection
            connection_test = self.supabase.test_connection()
            
            if connection_test['status'] == 'connected':
                # Get stats
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    stats = loop.run_until_complete(self.supabase.get_resume_stats())
                    stats['available'] = True
                    stats['connection'] = 'healthy'
                    return stats
                finally:
                    loop.close()
            else:
                return {
                    "available": False,
                    "connection": "failed",
                    "error": connection_test.get('message', 'Unknown error')
                }
                
        except Exception as e:
            return {
                "available": False,
                "connection": "error",
                "error": str(e)
            }
    
    def get_all_supabase_resumes(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all resumes from Supabase."""
        if not self.supabase:
            logger.error("Supabase not available")
            return []
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.supabase.get_all_resumes(limit=limit))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error fetching resumes from Supabase: {e}")
            return []
    
    def search_supabase_resumes(self, query: str = "", min_score: int = 0, 
                               skills: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Search resumes in Supabase."""
        if not self.supabase:
            logger.error("Supabase not available")
            return []
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.supabase.search_resumes(
                        query=query, 
                        min_score=min_score, 
                        skills=skills or [], 
                        limit=limit
                    )
                )
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error searching resumes in Supabase: {e}")
            return []

    def clear_all(self):
        """Clear all stored resumes."""
        with self.lock:
            try:
                # Clear memory cache
                self.memory_cache.clear()
                
                # Remove all files
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT storage_path FROM resumes")
                    for (storage_path,) in cursor.fetchall():
                        try:
                            if os.path.exists(storage_path):
                                os.remove(storage_path)
                        except Exception as e:
                            logger.error(f"Error removing file {storage_path}: {e}")
                    
                    # Clear database
                    conn.execute("DELETE FROM resumes")
                    conn.commit()
                
                logger.info("All resumes cleared successfully")
            except Exception as e:
                logger.error(f"Error clearing resumes: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM resumes")
                    total_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT SUM(file_size) FROM resumes")
                    total_size = cursor.fetchone()[0] or 0
                
                return {
                    "total_resumes": total_count,
                    "memory_cache_size": len(self.memory_cache),
                    "total_disk_size_bytes": total_size,
                    "memory_usage_percent": self._get_memory_usage() * 100,
                    "storage_directory": self.storage_dir
                }
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return {}

    def get_user_resumes_summary(self, user_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """Get summary of all resumes for a specific user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT id, filename, processed_at, file_size, text_length, scores_summary,
                           last_accessed, created_at
                    FROM resumes 
                    WHERE user_id = ?
                    ORDER BY processed_at DESC
                """
                params = [user_id]
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                resumes = []
                
                for row in cursor.fetchall():
                    try:
                        scores = json.loads(row[5]) if row[5] else {}
                    except json.JSONDecodeError:
                        scores = {}
                    
                    resumes.append({
                        "id": row[0],
                        "filename": row[1],
                        "processed_at": row[2],
                        "file_size": row[3],
                        "text_length": row[4],
                        "scores": scores,
                        "last_accessed": row[6],
                        "created_at": row[7],
                        "in_memory": row[0] in self.memory_cache
                    })
                
                return resumes
        except Exception as e:
            logger.error(f"Error getting user resumes summary for user {user_id}: {e}")
            return []

    def get_user_resume_count(self, user_id: int) -> int:
        """Get the total number of resumes processed by a specific user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM resumes WHERE user_id = ?", (user_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting user resume count for user {user_id}: {e}")
            return 0

    def get_user_storage_stats(self, user_id: int) -> Dict[str, Any]:
        """Get storage statistics for a specific user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*), SUM(file_size) FROM resumes WHERE user_id = ?", (user_id,))
                count, total_size = cursor.fetchone()
                total_size = total_size or 0
                
                return {
                    "user_resumes": count,
                    "user_storage_bytes": total_size,
                    "user_storage_mb": total_size / (1024 * 1024) if total_size else 0
                }
        except Exception as e:
            logger.error(f"Error getting user storage stats for user {user_id}: {e}")
            return {}

    def clear_user_resumes(self, user_id: int) -> int:
        """Clear all resumes for a specific user and return count of cleared resumes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get list of resume IDs to clear
                cursor = conn.execute("SELECT id, storage_path FROM resumes WHERE user_id = ?", (user_id,))
                resume_data = cursor.fetchall()
                
                cleared_count = 0
                for resume_id, storage_path in resume_data:
                    # Remove from memory cache
                    if resume_id in self.memory_cache:
                        del self.memory_cache[resume_id]
                    
                    # Remove storage file if exists
                    if storage_path and os.path.exists(storage_path):
                        try:
                            os.remove(storage_path)
                        except Exception as e:
                            logger.warning(f"Could not remove storage file {storage_path}: {e}")
                    
                    cleared_count += 1
                
                # Remove from database
                conn.execute("DELETE FROM resumes WHERE user_id = ?", (user_id,))
                
                logger.info(f"Cleared {cleared_count} resumes for user {user_id}")
                return cleared_count
        except Exception as e:
            logger.error(f"Error clearing user resumes for user {user_id}: {e}")
            return 0

    def update_database_schema_for_users(self):
        """Update database schema to include user_id field."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if user_id column exists
                cursor = conn.execute("PRAGMA table_info(resumes)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'user_id' not in columns:
                    # Add user_id column
                    conn.execute("ALTER TABLE resumes ADD COLUMN user_id INTEGER")
                    # Set default user_id to 1 for existing records (admin user)
                    conn.execute("UPDATE resumes SET user_id = 1 WHERE user_id IS NULL")
                    # Create index for better performance
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON resumes(user_id)")
                    logger.info("Database schema updated to include user_id")
                else:
                    logger.info("Database schema already includes user_id")
        except Exception as e:
            logger.error(f"Error updating database schema: {e}")
