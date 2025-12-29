#!/usr/bin/env python3
"""
Supabase Client for HR ATS System
Handles all database operations with Supabase
"""

import os
import json
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import logging
import bcrypt
import jwt
from supabase import create_client, Client
from postgrest import APIError

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Lightweight Supabase client for HR ATS operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.config = self._load_config()
        self.client = self._create_client()
        self.admin_client = self._create_admin_client()
        
    def _load_config(self) -> Dict[str, str]:
        """Load Supabase configuration from environment"""
        # Ensure environment variables are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        config = {
            'url': os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
            'anon_key': os.getenv('SUPABASE_ANON_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY'),
            'service_key': os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
            'jwt_secret': os.getenv('SUPABASE_JWT_SECRET')
        }
        
        if not config['url'] or not config['anon_key']:
            logger.error(f"Missing Supabase config - URL: {bool(config['url'])}, Key: {bool(config['anon_key'])}")
            raise ValueError("Missing required Supabase configuration")
            
        return config
        
    def _create_client(self) -> Client:
        """Create Supabase client with optimized connection settings"""
        # Use custom headers for connection optimization
        client = create_client(self.config['url'], self.config['anon_key'])
        
        # Configure client with optimized headers for Railway
        if hasattr(client, '_client') and hasattr(client._client, 'headers'):
            client._client.headers.update({
                'Connection': 'keep-alive',
                'Keep-Alive': 'timeout=60, max=1000'
            })
        
        return client
        
    def _create_admin_client(self) -> Optional[Client]:
        """Create admin Supabase client with optimized connection settings"""
        if self.config['service_key']:
            client = create_client(self.config['url'], self.config['service_key'])
            
            # Configure client with optimized headers for Railway
            if hasattr(client, '_client') and hasattr(client._client, 'headers'):
                client._client.headers.update({
                    'Connection': 'keep-alive',
                    'Keep-Alive': 'timeout=60, max=1000'
                })
            
            return client
        return None
        
    def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health"""
        try:
            # Use a simple RPC call or system_config query to avoid RLS issues
            if self.admin_client:
                # Use service role client for health check to bypass RLS
                response = self.admin_client.table('system_config').select('id').limit(1).execute()
                # Check if response and data exist
                if response and hasattr(response, 'data'):
                    return {"status": "healthy", "connected": True}
                else:
                    # If no data but no error, still consider healthy (empty table is ok)
                    return {"status": "healthy", "connected": True, "note": "Empty system_config table"}
            else:
                # Fallback to a basic connection test
                try:
                    response = self.client.rpc('version').execute()
                    return {"status": "healthy", "connected": True}
                except:
                    # If RPC fails, try a simple table list
                    response = self.client.table('users').select('id').limit(1).execute()
                    return {"status": "healthy", "connected": True}
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return {"status": "unhealthy", "connected": False, "error": str(e)}
            
    # ========================================================================
    # AUTHENTICATION METHODS
    # ========================================================================
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            # Use Supabase Auth
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Get user profile
                profile = self._get_user_profile(response.user.id)
                
                return {
                    "success": True,
                    "user": profile,
                    "token": response.session.access_token if response.session else None
                }
            else:
                return {"success": False, "error": "Invalid credentials"}
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}
            
    def create_user(self, email: str, password: str, full_name: str = "") -> Dict[str, Any]:
        """Create new user account"""
        try:
            # Create user in Supabase Auth
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            if response.user:
                # Create user profile
                profile_data = {
                    "user_id": response.user.id,
                    "email": email,
                    "full_name": full_name,
                    "access_type": "trial",
                    "trial_resumes_analyzed": 0,
                    "trial_limit": 100,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                self.client.table('user_profiles').insert(profile_data).execute()
                
                return {
                    "success": True,
                    "user": profile_data,
                    "message": "User created successfully"
                }
            else:
                return {"success": False, "error": "User creation failed"}
                
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return {"success": False, "error": str(e)}
            
    def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user ID"""
        try:
            response = self.client.table('user_profiles').select('*').eq('user_id', user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Get user profile error: {e}")
            return None
            
    # ========================================================================
    # RESUME MANAGEMENT METHODS
    # ========================================================================
    
    def store_resume(self, user_id: str, filename: str, content: str, file_path: str) -> str:
        """Store resume in database"""
        try:
            resume_data = {
                "user_id": user_id,
                "filename": filename,
                "processed_content": content,
                "processing_status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table('resumes').insert(resume_data).execute()
            
            if response.data:
                resume_id = response.data[0]['id']
                
                # Update user activity
                self._log_user_activity(user_id, "upload", {
                    "filename": filename,
                    "resume_id": resume_id
                })
                
                return str(resume_id)
            else:
                raise Exception("Failed to insert resume")
                
        except Exception as e:
            logger.error(f"Store resume error: {e}")
            raise
            
    def get_resume_by_id(self, resume_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get resume by ID with optional user filtering"""
        try:
            if self.admin_client:
                # Use admin client for broader access
                query = self.admin_client.table('resumes').select('*').eq('id', resume_id)
                
                # Add user filter if provided (for security)
                if user_id:
                    query = query.eq('user_id', user_id)
                
                response = query.execute()
                
                if response.data:
                    resume_data = response.data[0]
                    logger.info(f"Retrieved resume {resume_id} from Supabase")
                    return resume_data
                else:
                    logger.warning(f"Resume {resume_id} not found in Supabase")
                    return None
            else:
                logger.error("Admin client not available for resume retrieval")
                return None
                
        except Exception as e:
            logger.error(f"Get resume by ID error: {e}")
            return None
            
    def get_user_resumes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all resumes for a user"""
        try:
            response = self.client.table('resumes').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Get user resumes error: {e}")
            return []
            
    def delete_user_resume(self, resume_id: str, user_id: str) -> bool:
        """Delete a user's resume"""
        try:
            response = self.client.table('resumes').delete().eq('id', resume_id).eq('user_id', user_id).execute()
            
            # Log deletion activity
            self._log_user_activity(user_id, "delete", {
                "resume_id": resume_id
            })
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Delete resume error: {e}")
            return False
            
    def store_analysis_result(self, resume_id: str, analysis: Dict[str, Any], user_id: str):
        """Store AI analysis results"""
        try:
            update_data = {
                "ai_analysis": analysis,
                "agent_insights": analysis.get('agent_insights', {}),
                "consensus_score": analysis.get('consensus_score', 0.0),
                "legal_compliance": analysis.get('legal_compliance', {}),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.client.table('resumes').update(update_data).eq('id', resume_id).execute()
            
            # Log analysis activity
            self._log_user_activity(user_id, "analysis", {
                "resume_id": resume_id,
                "consensus_score": analysis.get('consensus_score', 0.0)
            })
            
        except Exception as e:
            logger.error(f"Store analysis error: {e}")
            raise
            
    # ========================================================================
    # HR LEGAL METHODS
    # ========================================================================
    
    def store_legal_query(self, user_id: str, query_text: str, response_data: Dict[str, Any]):
        """Store HR legal query and response"""
        try:
            query_data = {
                "user_id": user_id,
                "query_text": query_text,
                "response_data": response_data,
                "confidence_score": response_data.get('confidence_score', 0.0),
                "sources": response_data.get('sources', []),
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.client.table('hr_legal_queries').insert(query_data).execute()
            
            # Log legal query activity
            self._log_user_activity(user_id, "legal_query", {
                "query_length": len(query_text),
                "confidence_score": response_data.get('confidence_score', 0.0)
            })
            
        except Exception as e:
            logger.error(f"Store legal query error: {e}")
            raise
            
    def get_user_legal_queries(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's legal queries"""
        try:
            response = self.client.table('hr_legal_queries').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Get legal queries error: {e}")
            return []
            
    # ========================================================================
    # ADMIN METHODS
    # ========================================================================
    
    def get_admin_stats(self) -> Dict[str, Any]:
        """Get system statistics for admin dashboard"""
        try:
            if not self.admin_client:
                raise Exception("Admin client not available")
                
            # Get user counts
            users_response = self.admin_client.table('user_profiles').select('count').execute()
            total_users = len(users_response.data) if users_response.data else 0
            
            # Get resume counts
            resumes_response = self.admin_client.table('resumes').select('count').execute()
            total_resumes = len(resumes_response.data) if resumes_response.data else 0
            
            # Get legal query counts
            legal_response = self.admin_client.table('hr_legal_queries').select('count').execute()
            total_legal_queries = len(legal_response.data) if legal_response.data else 0
            
            return {
                "total_users": total_users,
                "total_resumes": total_resumes,
                "total_legal_queries": total_legal_queries,
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get admin stats error: {e}")
            return {}
            
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users for admin"""
        try:
            if not self.admin_client:
                raise Exception("Admin client not available")
                
            response = self.admin_client.table('user_profiles').select('*').order('created_at', desc=True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Get all users error: {e}")
            return []
    
    def get_all_resumes(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get all resumes for admin with pagination"""
        try:
            if not self.admin_client:
                raise Exception("Admin client not available")
            
            # Calculate offset
            offset = (page - 1) * limit
            
            # Get total count
            count_response = self.admin_client.table('resumes').select('*', count='exact').execute()
            total_count = count_response.count if hasattr(count_response, 'count') else len(count_response.data or [])
            
            # Get paginated resumes
            response = self.admin_client.table('resumes').select('''
                id, filename, upload_date, user_id, file_size, 
                extracted_text, analysis_results, created_at
            ''').order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            resumes = []
            for resume in (response.data or []):
                resumes.append({
                    'id': resume.get('id'),
                    'filename': resume.get('filename'),
                    'upload_date': resume.get('upload_date') or resume.get('created_at'),
                    'user_id': resume.get('user_id'),
                    'file_size': resume.get('file_size'),
                    'content_preview': (resume.get('extracted_text') or '')[:200] if resume.get('extracted_text') else None,
                    'has_analysis': bool(resume.get('analysis_results'))
                })
            
            return {
                'resumes': resumes,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit if total_count > 0 else 1
                }
            }
            
        except Exception as e:
            logger.error(f"Get all resumes error: {e}")
            return {'resumes': [], 'pagination': {'page': page, 'limit': limit, 'total': 0, 'pages': 1}}
    
    def get_all_legal_queries(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get all legal queries for admin with pagination"""
        try:
            if not self.admin_client:
                raise Exception("Admin client not available")
            
            # Calculate offset
            offset = (page - 1) * limit
            
            # Get total count
            count_response = self.admin_client.table('hr_legal_queries').select('*', count='exact').execute()
            total_count = count_response.count if hasattr(count_response, 'count') else len(count_response.data or [])
            
            # Get paginated queries
            response = self.admin_client.table('hr_legal_queries').select('''
                id, query_text, response, user_id, created_at, processing_time
            ''').order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            queries = []
            for query in (response.data or []):
                queries.append({
                    'id': query.get('id'),
                    'query_text': (query.get('query_text') or '')[:200] + '...' if len(query.get('query_text') or '') > 200 else query.get('query_text'),
                    'response_preview': (query.get('response') or '')[:300] + '...' if len(query.get('response') or '') > 300 else query.get('response'),
                    'user_id': query.get('user_id'),
                    'created_at': query.get('created_at'),
                    'processing_time': query.get('processing_time')
                })
            
            return {
                'legal_queries': queries,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit if total_count > 0 else 1
                }
            }
            
        except Exception as e:
            logger.error(f"Get all legal queries error: {e}")
            return {'legal_queries': [], 'pagination': {'page': page, 'limit': limit, 'total': 0, 'pages': 1}}
    
    def delete_resume_admin(self, resume_id: str) -> bool:
        """Delete a resume (admin function)"""
        try:
            if not self.admin_client:
                raise Exception("Admin client not available")
            
            # First check if the resume exists
            check_response = self.admin_client.table('resumes').select('id').eq('id', resume_id).execute()
            
            if not check_response.data:
                logger.warning(f"Resume {resume_id} not found for deletion")
                return False
            
            # Delete the resume
            response = self.admin_client.table('resumes').delete().eq('id', resume_id).execute()
            
            # Check if deletion was successful (response.data will contain deleted records)
            if response.data:
                logger.info(f"Successfully deleted resume {resume_id}")
                return True
            else:
                logger.warning(f"Resume {resume_id} was not deleted - no matching records")
                return False
            
        except Exception as e:
            logger.error(f"Delete resume error: {e}")
            return False
    
    def delete_legal_query_admin(self, query_id: str) -> bool:
        """Delete a legal query (admin function)"""
        try:
            if not self.admin_client:
                raise Exception("Admin client not available")
            
            # First check if the legal query exists
            check_response = self.admin_client.table('hr_legal_queries').select('id').eq('id', query_id).execute()
            
            if not check_response.data:
                logger.warning(f"Legal query {query_id} not found for deletion")
                return False
            
            # Delete the legal query
            response = self.admin_client.table('hr_legal_queries').delete().eq('id', query_id).execute()
            
            # Check if deletion was successful (response.data will contain deleted records)
            if response.data:
                logger.info(f"Successfully deleted legal query {query_id}")
                return True
            else:
                logger.warning(f"Legal query {query_id} was not deleted - no matching records")
                return False
            
        except Exception as e:
            logger.error(f"Delete legal query error: {e}")
            return False
            
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _log_user_activity(self, user_id: str, action: str, details: Dict[str, Any]):
        """Log user activity"""
        try:
            activity_data = {
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": "0.0.0.0",  # Would get from request in real implementation
                "user_agent": "HR-ATS-System"
            }
            
            self.client.table('user_activity').insert(activity_data).execute()
            
        except Exception as e:
            logger.error(f"Log activity error: {e}")
            # Don't raise here as it's not critical
            
    def get_user_trial_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's trial status"""
        try:
            profile = self._get_user_profile(user_id)
            
            if profile:
                return {
                    "access_type": profile.get('access_type', 'trial'),
                    "trial_resumes_analyzed": profile.get('trial_resumes_analyzed', 0),
                    "trial_limit": profile.get('trial_limit', 100),
                    "remaining": profile.get('trial_limit', 100) - profile.get('trial_resumes_analyzed', 0)
                }
            else:
                return {"access_type": "unknown", "remaining": 0}
                
        except Exception as e:
            logger.error(f"Get trial status error: {e}")
            return {"access_type": "unknown", "remaining": 0}
            
    def update_trial_usage(self, user_id: str):
        """Update user's trial usage count"""
        try:
            # Increment trial resume count
            response = self.client.rpc('increment_trial_usage', {'user_id_param': user_id}).execute()
            
            if not response.data:
                # Fallback manual update
                profile = self._get_user_profile(user_id)
                if profile:
                    new_count = profile.get('trial_resumes_analyzed', 0) + 1
                    self.client.table('user_profiles').update({
                        'trial_resumes_analyzed': new_count,
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('user_id', user_id).execute()
                    
        except Exception as e:
            logger.error(f"Update trial usage error: {e}")
            # Don't raise as this is not critical
