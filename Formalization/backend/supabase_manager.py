#!/usr/bin/env python3
"""
Complete Supabase Integration for Resume Screening App
Handles authentication, user management, resume storage, and activity tracking
"""

import os
import json
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import logging
from supabase import create_client, Client
from postgrest import APIError
import bcrypt
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseManager:
    def __init__(self):
        """Initialize Supabase client and configuration"""
        # Try both environment variable naming conventions
        self.supabase_url = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
        
        if not all([self.supabase_url, self.supabase_key]):
            raise ValueError("Missing required Supabase environment variables")
        
        # Create clients
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.admin_client: Client = create_client(self.supabase_url, self.supabase_service_key) if self.supabase_service_key else None
        
        logger.info("Supabase client initialized successfully")

    # ========================================================================
    # AUTHENTICATION METHODS
    # ========================================================================

    async def create_user(self, email: str, password: str, full_name: str = None, **kwargs) -> Dict[str, Any]:
        """Create a new user account"""
        try:
            # Create user in Supabase Auth
            user_data = {
                'email': email,
                'password': password
            }
            
            if full_name:
                user_data['data'] = {'full_name': full_name}
            
            response = self.client.auth.sign_up(user_data)
            
            if response.user:
                logger.info(f"User created successfully: {email}")
                return {
                    'success': True,
                    'user_id': response.user.id,
                    'email': response.user.email,
                    'message': 'User created successfully. Please check your email for verification.'
                }
            else:
                return {'success': False, 'error': 'Failed to create user'}
                
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return session info"""
        try:
            response = self.client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            if response.user and response.session:
                # Update last_login in user_profiles
                await self.update_user_profile(response.user.id, {
                    'last_login': datetime.utcnow().isoformat(),
                    'last_activity': datetime.utcnow().isoformat()
                })
                
                # Log login activity
                await self.log_user_activity(
                    response.user.id,
                    'login',
                    'User logged in successfully'
                )
                
                # Get user profile
                profile = await self.get_user_profile(response.user.id)
                
                return {
                    'success': True,
                    'user': profile,
                    'session': response.session,
                    'access_token': response.session.access_token
                }
            else:
                return {'success': False, 'error': 'Invalid credentials'}
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'error': 'Authentication failed'}

    async def logout_user(self, user_id: str) -> Dict[str, Any]:
        """Logout user and invalidate session"""
        try:
            # Log logout activity
            await self.log_user_activity(user_id, 'logout', 'User logged out')
            
            # Sign out from Supabase
            self.client.auth.sign_out()
            
            return {'success': True, 'message': 'Logged out successfully'}
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def validate_session(self, access_token: str) -> Dict[str, Any]:
        """Validate user session and return user info"""
        try:
            # Set the session
            self.client.auth.set_session(access_token, refresh_token=None)
            
            # Get current user
            user = self.client.auth.get_user()
            
            if user and user.user:
                profile = await self.get_user_profile(user.user.id)
                return {
                    'valid': True,
                    'user': profile
                }
            else:
                return {'valid': False, 'error': 'Invalid session'}
                
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return {'valid': False, 'error': str(e)}

    # ========================================================================
    # USER MANAGEMENT METHODS
    # ========================================================================

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            response = self.client.table('user_profiles').select('*').eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            return None

    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        try:
            response = self.client.table('user_profiles').update(updates).eq('id', user_id).execute()
            
            if response.data:
                return {'success': True, 'data': response.data[0]}
            else:
                return {'success': False, 'error': 'Update failed'}
                
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def check_trial_status(self, user_id: str) -> Dict[str, Any]:
        """Check user's trial status and usage"""
        try:
            profile = await self.get_user_profile(user_id)
            
            if not profile:
                return {'error': 'User not found'}
            
            # Calculate trial status
            trial_start = datetime.fromisoformat(profile['trial_start_date'].replace('Z', '+00:00'))
            trial_end = datetime.fromisoformat(profile['trial_end_date'].replace('Z', '+00:00'))
            now = datetime.utcnow()
            
            is_trial_active = (
                profile['access_type'] == 'trial' and 
                now < trial_end and 
                profile['trial_usage'] < profile['trial_limit']
            )
            
            return {
                'access_type': profile['access_type'],
                'trial_usage': profile['trial_usage'],
                'trial_limit': profile['trial_limit'],
                'trial_start_date': profile['trial_start_date'],
                'trial_end_date': profile['trial_end_date'],
                'is_trial_active': is_trial_active,
                'days_remaining': (trial_end - now).days if now < trial_end else 0,
                'uploads_remaining': max(0, profile['trial_limit'] - profile['trial_usage'])
            }
            
        except Exception as e:
            logger.error(f"Error checking trial status: {str(e)}")
            return {'error': str(e)}

    async def increment_trial_usage(self, user_id: str, count: int = 1) -> Dict[str, Any]:
        """Increment user's trial usage"""
        try:
            # This is handled automatically by the database trigger
            # But we can also do it manually if needed
            response = self.client.table('user_profiles').update({
                'trial_usage': self.client.table('user_profiles').select('trial_usage').eq('id', user_id).execute().data[0]['trial_usage'] + count,
                'last_activity': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
            if response.data:
                return {'success': True, 'new_usage': response.data[0]['trial_usage']}
            else:
                return {'success': False, 'error': 'Failed to increment usage'}
                
        except Exception as e:
            logger.error(f"Error incrementing trial usage: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # RESUME MANAGEMENT METHODS
    # ========================================================================

    async def store_resume(self, user_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store resume data in database"""
        try:
            # Generate file hash for deduplication
            content_hash = hashlib.md5(resume_data['compressed_content'].encode()).hexdigest()
            
            # Check if resume already exists
            existing = self.client.table('resumes').select('id').eq('file_hash', content_hash).eq('user_id', user_id).execute()
            
            if existing.data:
                return {'success': False, 'error': 'Resume already exists', 'duplicate': True}
            
            # Prepare resume data
            resume_record = {
                'user_id': user_id,
                'filename': resume_data['filename'],
                'file_hash': content_hash,
                'file_size': resume_data.get('file_size', 0),
                'file_type': resume_data.get('file_type', 'pdf'),
                'compressed_content': resume_data['compressed_content'],
                'raw_text': resume_data.get('raw_text', ''),
                'processing_status': 'pending'
            }
            
            # Add parsed data if available
            if 'parsed_info' in resume_data:
                parsed = resume_data['parsed_info']
                resume_record.update({
                    'candidate_name': parsed.get('name', ''),
                    'candidate_email': parsed.get('email', ''),
                    'candidate_phone': parsed.get('phone', ''),
                    'skills': parsed.get('skills', []),
                    'experience_years': parsed.get('experience_years', 0),
                    'education_level': parsed.get('education_level', ''),
                    'job_titles': parsed.get('job_titles', []),
                    'companies': parsed.get('companies', []),
                    'programming_languages': parsed.get('programming_languages', []),
                    'certifications': parsed.get('certifications', [])
                })
            
            # Insert resume
            response = self.client.table('resumes').insert(resume_record).execute()
            
            if response.data:
                return {'success': True, 'resume_id': response.data[0]['id'], 'data': response.data[0]}
            else:
                return {'success': False, 'error': 'Failed to store resume'}
                
        except Exception as e:
            logger.error(f"Error storing resume: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def update_resume_analysis(self, resume_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update resume with AI analysis results"""
        try:
            update_data = {
                'processing_status': 'completed',
                'processing_completed_at': datetime.utcnow().isoformat(),
                'overall_score': analysis_data.get('overall_score', 0),
                'technical_score': analysis_data.get('technical_score', 0),
                'experience_score': analysis_data.get('experience_score', 0),
                'education_score': analysis_data.get('education_score', 0),
                'role_fit_score': analysis_data.get('role_fit_score', 0),
                'ai_feedback': analysis_data.get('feedback', ''),
                'ai_model_used': analysis_data.get('model_used', ''),
                'ai_processing_time': analysis_data.get('processing_time', 0)
            }
            
            response = self.client.table('resumes').update(update_data).eq('id', resume_id).execute()
            
            if response.data:
                return {'success': True, 'data': response.data[0]}
            else:
                return {'success': False, 'error': 'Failed to update analysis'}
                
        except Exception as e:
            logger.error(f"Error updating resume analysis: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def get_user_resumes(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all resumes for a user"""
        try:
            response = self.client.table('resumes').select('*').eq('user_id', user_id).eq('is_archived', False).order('upload_date', desc=True).limit(limit).offset(offset).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error fetching user resumes: {str(e)}")
            return []

    async def search_resumes(self, user_id: str, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search resumes with full-text search and filters"""
        try:
            # Start with base query
            db_query = self.client.table('resumes').select('*').eq('user_id', user_id).eq('is_archived', False)
            
            # Add full-text search if query provided
            if query:
                db_query = db_query.text_search('raw_text', query)
            
            # Add filters
            if filters:
                if filters.get('min_score'):
                    db_query = db_query.gte('overall_score', filters['min_score'])
                if filters.get('max_score'):
                    db_query = db_query.lte('overall_score', filters['max_score'])
                if filters.get('experience_years'):
                    db_query = db_query.gte('experience_years', filters['experience_years'])
                if filters.get('skills'):
                    for skill in filters['skills']:
                        db_query = db_query.contains('skills', [skill])
            
            response = db_query.order('overall_score', desc=True).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error searching resumes: {str(e)}")
            return []

    # ========================================================================
    # ACTIVITY TRACKING METHODS
    # ========================================================================

    async def log_user_activity(self, user_id: str, activity_type: str, description: str, 
                               resource_type: str = None, resource_id: str = None, 
                               metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Log user activity"""
        try:
            activity_data = {
                'user_id': user_id,
                'activity_type': activity_type,
                'activity_description': description,
                'success': True
            }
            
            if resource_type:
                activity_data['resource_type'] = resource_type
            if resource_id:
                activity_data['resource_id'] = resource_id
            if metadata:
                activity_data['metadata'] = metadata
            
            response = self.client.table('user_activity').insert(activity_data).execute()
            
            if response.data:
                return {'success': True, 'activity_id': response.data[0]['id']}
            else:
                return {'success': False, 'error': 'Failed to log activity'}
                
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def get_user_activity(self, user_id: str, limit: int = 50, activity_type: str = None) -> List[Dict[str, Any]]:
        """Get user activity history"""
        try:
            query = self.client.table('user_activity').select('*').eq('user_id', user_id)
            
            if activity_type:
                query = query.eq('activity_type', activity_type)
            
            response = query.order('created_at', desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error fetching user activity: {str(e)}")
            return []

    # ========================================================================
    # HR LEGAL METHODS
    # ========================================================================

    async def store_hr_legal_query(self, user_id: str, query_text: str, query_category: str = 'general') -> str:
        """Store HR legal query and return query ID"""
        try:
            query_data = {
                'user_id': user_id,
                'query_text': query_text,
                'query_category': query_category,
                'processing_status': 'pending'
            }
            
            response = self.client.table('hr_legal_queries').insert(query_data).execute()
            
            if response.data:
                query_id = response.data[0]['id']
                
                # Log activity
                await self.log_user_activity(
                    user_id,
                    'hr_legal_query',
                    f'Submitted HR legal query: {query_category}',
                    'hr_legal_query',
                    query_id
                )
                
                return query_id
            else:
                raise Exception('Failed to store query')
                
        except Exception as e:
            logger.error(f"Error storing HR legal query: {str(e)}")
            raise e

    async def update_hr_legal_response(self, query_id: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update HR legal query with AI response"""
        try:
            update_data = {
                'response_text': response_data.get('response', ''),
                'confidence_score': response_data.get('confidence', 0.0),
                'sources': response_data.get('sources', []),
                'ai_model_used': response_data.get('model_used', ''),
                'processing_time': response_data.get('processing_time', 0),
                'processing_status': 'completed'
            }
            
            response = self.client.table('hr_legal_queries').update(update_data).eq('id', query_id).execute()
            
            if response.data:
                return {'success': True, 'data': response.data[0]}
            else:
                return {'success': False, 'error': 'Failed to update response'}
                
        except Exception as e:
            logger.error(f"Error updating HR legal response: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def get_user_hr_queries(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's HR legal queries"""
        try:
            response = self.client.table('hr_legal_queries').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error fetching HR legal queries: {str(e)}")
            return []

    # ========================================================================
    # SYSTEM CONFIGURATION METHODS
    # ========================================================================

    async def get_system_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """Get system configuration by key"""
        try:
            response = self.client.table('system_config').select('*').eq('config_key', config_key).eq('is_active', True).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['config_value']
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching system config: {str(e)}")
            return None

    async def update_system_config(self, config_key: str, config_value: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration"""
        try:
            response = self.client.table('system_config').update({
                'config_value': config_value
            }).eq('config_key', config_key).execute()
            
            if response.data:
                return {'success': True, 'data': response.data[0]}
            else:
                return {'success': False, 'error': 'Failed to update config'}
                
        except Exception as e:
            logger.error(f"Error updating system config: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # ANALYTICS METHODS
    # ========================================================================

    async def get_user_analytics(self) -> Dict[str, Any]:
        """Get user analytics from view"""
        try:
            response = self.client.table('user_analytics').select('*').execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error fetching user analytics: {str(e)}")
            return {}

    async def get_resume_stats(self) -> Dict[str, Any]:
        """Get resume statistics from view"""
        try:
            response = self.client.table('resume_stats').select('*').execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error fetching resume stats: {str(e)}")
            return {}

    async def get_system_analytics(self) -> Dict[str, Any]:
        """Get system analytics from view"""
        try:
            response = self.client.table('system_analytics').select('*').execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error fetching system analytics: {str(e)}")
            return {}

    # ========================================================================
    # ADMIN METHODS
    # ========================================================================

    async def setup_admin_user(self, user_email: str) -> Dict[str, Any]:
        """Setup admin privileges for a user"""
        try:
            if not self.admin_client:
                return {'success': False, 'error': 'Admin client not configured'}
            
            # Call the database function
            response = self.admin_client.rpc('setup_admin_user', {'user_email': user_email}).execute()
            
            return {'success': True, 'message': f'Admin privileges granted to {user_email}'}
            
        except Exception as e:
            logger.error(f"Error setting up admin user: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        try:
            if not self.admin_client:
                return []
            
            response = self.admin_client.table('user_profiles').select('*').order('created_at', desc=True).limit(limit).offset(offset).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error fetching all users: {str(e)}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on database"""
        try:
            # Test basic connectivity
            response = self.client.table('system_config').select('count', count='exact').limit(1).execute()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'config_count': response.count if hasattr(response, 'count') else 'unknown'
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global instance
supabase_manager = None

def get_supabase_manager() -> SupabaseManager:
    """Get or create global Supabase manager instance"""
    global supabase_manager
    if supabase_manager is None:
        supabase_manager = SupabaseManager()
    return supabase_manager

# Convenience functions for Flask integration
async def authenticate_request(access_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Authenticate a request and return user info"""
    manager = get_supabase_manager()
    result = await manager.validate_session(access_token)
    
    if result.get('valid'):
        return True, result.get('user')
    else:
        return False, None

async def require_auth(access_token: str) -> Dict[str, Any]:
    """Require authentication and return user info, raise exception if invalid"""
    is_valid, user = await authenticate_request(access_token)
    
    if not is_valid:
        raise Exception('Authentication required')
    
    return user

# Example usage and testing
if __name__ == "__main__":
    async def test_supabase():
        """Test Supabase integration"""
        manager = SupabaseManager()
        
        # Health check
        health = await manager.health_check()
        print(f"Health check: {health}")
        
        # Get system config
        config = await manager.get_system_config('trial_limits')
        print(f"Trial limits config: {config}")
        
        print("Supabase integration test completed!")
    
    # Run test
    asyncio.run(test_supabase())
