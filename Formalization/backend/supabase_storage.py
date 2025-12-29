import os
import gzip
import base64
import json
import hashlib
from datetime import datetime, timezone
from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SupabaseStorage:
    """
    Supabase persistent storage for resume data with compression
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        try:
            url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for backend operations
            
            if not url or not key:
                raise ValueError("Supabase credentials not found in environment variables")
            
            self.client: Client = create_client(url, key)
            self.table_name = "resumes"
            logger.info("Supabase storage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase storage: {e}")
            raise
    
    def compress_data(self, data: Any) -> str:
        """
        Compress data for storage efficiency
        Returns base64 encoded compressed string
        """
        try:
            # Convert to JSON string
            json_str = json.dumps(data, ensure_ascii=False, default=str)
            
            # Compress with gzip
            compressed = gzip.compress(json_str.encode('utf-8'))
            
            # Encode to base64 for storage
            encoded = base64.b64encode(compressed).decode('utf-8')
            
            # Calculate compression ratio
            original_size = len(json_str.encode('utf-8'))
            compressed_size = len(encoded.encode('utf-8'))
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            logger.debug(f"Data compressed: {original_size} -> {compressed_size} bytes ({compression_ratio:.1f}% saved)")
            
            return encoded
            
        except Exception as e:
            logger.error(f"Error compressing data: {e}")
            raise
    
    def decompress_data(self, compressed_data: str) -> Any:
        """
        Decompress data from storage
        """
        try:
            # Decode from base64
            compressed = base64.b64decode(compressed_data.encode('utf-8'))
            
            # Decompress with gzip
            decompressed = gzip.decompress(compressed)
            
            # Parse JSON
            data = json.loads(decompressed.decode('utf-8'))
            
            return data
            
        except Exception as e:
            logger.error(f"Error decompressing data: {e}")
            raise
    
    def generate_file_hash(self, content: str) -> str:
        """Generate MD5 hash for deduplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def save_resume(self, resume_data: Dict) -> Optional[Dict]:
        """
        Save resume to Supabase with compression
        
        Args:
            resume_data: Dictionary containing all resume information
            
        Returns:
            Supabase record or None if failed
        """
        try:
            # Generate file hash for deduplication
            content_for_hash = resume_data.get('text_content', '') + resume_data.get('filename', '')
            file_hash = self.generate_file_hash(content_for_hash)
            
            # Check if resume already exists
            existing = self.client.table(self.table_name).select('id').eq('file_hash', file_hash).execute()
            if existing.data:
                logger.info(f"Resume with hash {file_hash} already exists, skipping")
                return existing.data[0]
            
            # Compress the full resume data
            compressed_content = self.compress_data(resume_data)
            
            # Extract key fields for easy querying
            extracted_info = resume_data.get('extracted_info', {})
            ai_analysis = resume_data.get('ai_analysis', {})
            
            # Prepare record for insertion
            record = {
                'filename': resume_data.get('filename', 'unknown'),
                'compressed_content': compressed_content,
                'file_hash': file_hash,
                'upload_date': datetime.now(timezone.utc).isoformat(),
                'file_size': resume_data.get('file_size', 0),
                'user_type': 'free',  # For now, all users are 'free'
                'processing_status': 'completed',
                
                # Extracted fields for easy filtering/searching
                'candidate_name': extracted_info.get('name', ''),
                'candidate_email': extracted_info.get('email', ''),
                'skills': extracted_info.get('skills', []),
                'experience_years': extracted_info.get('experience', {}).get('years', 0),
                'education_level': extracted_info.get('education', {}).get('level', ''),
                
                # AI Analysis scores for sorting
                'overall_score': ai_analysis.get('scores', {}).get('overall', 0),
                'technical_score': ai_analysis.get('scores', {}).get('technical_skills', 0),
                'experience_score': ai_analysis.get('scores', {}).get('experience', 0),
                'education_score': ai_analysis.get('scores', {}).get('education', 0),
                'role_fit_score': ai_analysis.get('scores', {}).get('role_fit', 0),
            }
            
            # Insert into Supabase
            result = self.client.table(self.table_name).insert(record).execute()
            
            if result.data:
                logger.info(f"Resume saved to Supabase: {result.data[0]['id']}")
                return result.data[0]
            else:
                logger.error("Failed to save resume - no data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error saving resume to Supabase: {e}")
            return None
    
    async def get_all_resumes(self, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """
        Get all resumes from Supabase with pagination
        
        Args:
            limit: Maximum number of resumes to fetch
            offset: Number of resumes to skip
            
        Returns:
            List of decompressed resume data
        """
        try:
            # Fetch resumes with pagination
            result = self.client.table(self.table_name)\
                .select('*')\
                .order('upload_date', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            if not result.data:
                logger.info("No resumes found in Supabase")
                return []
            
            # Decompress the data
            resumes = []
            for record in result.data:
                try:
                    # Decompress the full resume data
                    decompressed = self.decompress_data(record['compressed_content'])
                    
                    # Add metadata from the record
                    decompressed['supabase_id'] = record['id']
                    decompressed['upload_date'] = record['upload_date']
                    decompressed['user_type'] = record['user_type']
                    decompressed['processing_status'] = record['processing_status']
                    
                    resumes.append(decompressed)
                    
                except Exception as e:
                    logger.error(f"Error decompressing resume {record['id']}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(resumes)} resumes from Supabase")
            return resumes
            
        except Exception as e:
            logger.error(f"Error fetching resumes from Supabase: {e}")
            return []
    
    async def get_resume_by_id(self, resume_id: str) -> Optional[Dict]:
        """
        Get a specific resume by its Supabase ID
        
        Args:
            resume_id: Supabase record ID
            
        Returns:
            Decompressed resume data or None
        """
        try:
            result = self.client.table(self.table_name)\
                .select('*')\
                .eq('id', resume_id)\
                .execute()
            
            if not result.data:
                logger.warning(f"Resume {resume_id} not found")
                return None
            
            record = result.data[0]
            decompressed = self.decompress_data(record['compressed_content'])
            
            # Add metadata
            decompressed['supabase_id'] = record['id']
            decompressed['upload_date'] = record['upload_date']
            
            return decompressed
            
        except Exception as e:
            logger.error(f"Error fetching resume {resume_id}: {e}")
            return None
    
    async def get_resume_stats(self) -> Dict:
        """
        Get statistics about stored resumes
        
        Returns:
            Dictionary with statistics
        """
        try:
            # Get total count
            count_result = self.client.table(self.table_name)\
                .select('id', count='exact')\
                .execute()
            
            total_resumes = count_result.count if count_result.count else 0
            
            # Get average scores
            stats_result = self.client.table(self.table_name)\
                .select('overall_score,technical_score,experience_score,education_score,role_fit_score')\
                .execute()
            
            if stats_result.data:
                scores = stats_result.data
                avg_overall = sum(r['overall_score'] or 0 for r in scores) / len(scores) if scores else 0
                avg_technical = sum(r['technical_score'] or 0 for r in scores) / len(scores) if scores else 0
                avg_experience = sum(r['experience_score'] or 0 for r in scores) / len(scores) if scores else 0
                avg_education = sum(r['education_score'] or 0 for r in scores) / len(scores) if scores else 0
                avg_role_fit = sum(r['role_fit_score'] or 0 for r in scores) / len(scores) if scores else 0
            else:
                avg_overall = avg_technical = avg_experience = avg_education = avg_role_fit = 0
            
            return {
                'total_resumes': total_resumes,
                'average_scores': {
                    'overall': round(avg_overall, 2),
                    'technical': round(avg_technical, 2),
                    'experience': round(avg_experience, 2),
                    'education': round(avg_education, 2),
                    'role_fit': round(avg_role_fit, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting resume stats: {e}")
            return {'total_resumes': 0, 'average_scores': {}}
    
    async def search_resumes(self, 
                           query: str = "", 
                           min_score: int = 0, 
                           skills: List[str] = None,
                           limit: int = 100) -> List[Dict]:
        """
        Search resumes by various criteria
        
        Args:
            query: Text search in name, email, or filename
            min_score: Minimum overall score
            skills: List of required skills
            limit: Maximum results to return
            
        Returns:
            List of matching resumes
        """
        try:
            # Start with base query
            supabase_query = self.client.table(self.table_name).select('*')
            
            # Add score filter
            if min_score > 0:
                supabase_query = supabase_query.gte('overall_score', min_score)
            
            # Add text search filter
            if query:
                supabase_query = supabase_query.or_(
                    f"candidate_name.ilike.%{query}%,"
                    f"candidate_email.ilike.%{query}%,"
                    f"filename.ilike.%{query}%"
                )
            
            # Execute query
            result = supabase_query.order('overall_score', desc=True).limit(limit).execute()
            
            if not result.data:
                return []
            
            # Decompress and filter by skills if needed
            resumes = []
            for record in result.data:
                try:
                    decompressed = self.decompress_data(record['compressed_content'])
                    
                    # Filter by skills if specified
                    if skills:
                        resume_skills = decompressed.get('extracted_info', {}).get('skills', [])
                        if not any(skill.lower() in [s.lower() for s in resume_skills] for skill in skills):
                            continue
                    
                    # Add metadata
                    decompressed['supabase_id'] = record['id']
                    decompressed['upload_date'] = record['upload_date']
                    
                    resumes.append(decompressed)
                    
                except Exception as e:
                    logger.error(f"Error processing search result {record['id']}: {e}")
                    continue
            
            logger.info(f"Search returned {len(resumes)} resumes")
            return resumes
            
        except Exception as e:
            logger.error(f"Error searching resumes: {e}")
            return []
    
    async def delete_resume(self, resume_id: str) -> bool:
        """
        Delete a resume by ID
        
        Args:
            resume_id: Supabase record ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table(self.table_name)\
                .delete()\
                .eq('id', resume_id)\
                .execute()
            
            success = bool(result.data)
            if success:
                logger.info(f"Resume {resume_id} deleted successfully")
            else:
                logger.warning(f"Resume {resume_id} not found for deletion")
                
            return success
            
        except Exception as e:
            logger.error(f"Error deleting resume {resume_id}: {e}")
            return False
    
    async def clear_all_resumes(self) -> bool:
        """
        Clear all resumes from storage (use with caution!)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table(self.table_name).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logger.warning("All resumes cleared from Supabase storage")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all resumes: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Supabase connection
        
        Returns:
            Dictionary with connection status and info
        """
        try:
            # Try a simple query to test connection
            result = self.client.table(self.table_name).select('id').limit(1).execute()
            
            return {
                'status': 'connected',
                'message': 'Supabase connection successful',
                'table_exists': True,
                'sample_query_success': True
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Supabase connection failed: {e}',
                'table_exists': False,
                'sample_query_success': False
            }
