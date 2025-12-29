"""
Supabase Database Manager
Handles all database operations for the Resume Screening Application
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from gotrue import SyncAuthClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manages all Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client connections"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not all([self.supabase_url, self.supabase_key, self.supabase_service_key]):
            raise ValueError("Missing required Supabase environment variables")
        
        # Regular client for authenticated operations
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Admin client for administrative operations
        self.admin_client: Client = create_client(self.supabase_url, self.supabase_service_key)
        
        logger.info("Supabase clients initialized successfully")
    
    # =====================================================================
    # AUTHENTICATION METHODS
    # =====================================================================
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            response = self.client.auth.sign_in_with_password({
                'email': email, 
                'password': password
            })
            
            if response.user:
                # Log successful login
                await self.log_user_activity(
                    response.user.id, 
                    'login', 
                    f'User logged in from {email}'
                )
                
                return {
                    'success': True,
                    'user': response.user,
                    'session': response.session
                }
            
            return {'success': False, 'error': 'Invalid credentials'}
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_user(self, email: str, password: str, name: str, access_type: str = 'trial') -> Dict[str, Any]:
        """Create new user account (admin only)"""
        try:
            # Create user in Supabase Auth
            response = self.admin_client.auth.admin.create_user({
                'email': email,
                'password': password,
                'email_confirm': True
            })
            
            if response.user:
                # Create user profile
                profile_data = {
                    'user_id': response.user.id,
                    'name': name,
                    'email': email,
                    'access_type': access_type,
                    'trial_resumes_analyzed': 0,
                    'trial_limit': int(os.getenv('DEFAULT_TRIAL_LIMIT', 100)),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                profile_result = self.admin_client.table('user_profiles').insert(profile_data).execute()
                
                return {
                    'success': True,
                    'user': response.user,
                    'profile': profile_result.data[0] if profile_result.data else None
                }
            
            return {'success': False, 'error': 'Failed to create user'}
            
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user ID"""
        try:
            result = self.client.table('user_profiles').select('*').eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            return None
    
    async def verify_admin_credentials(self, username: str, password: str) -> Dict[str, Any]:
        """Verify admin credentials"""
        try:
            # Check against environment variables for now
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            
            if username == admin_username and password == admin_password:
                # Check if admin user exists in database
                result = self.admin_client.table('admin_users').select('*').eq('username', username).execute()
                
                if not result.data:
                    # Create admin user record
                    admin_data = {
                        'username': username,
                        'role': 'super_admin',
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'last_login': datetime.now(timezone.utc).isoformat()
                    }
                    self.admin_client.table('admin_users').insert(admin_data).execute()
                else:
                    # Update last login
                    self.admin_client.table('admin_users').update({
                        'last_login': datetime.now(timezone.utc).isoformat()
                    }).eq('username', username).execute()
                
                return {'success': True, 'username': username, 'role': 'super_admin'}
            
            return {'success': False, 'error': 'Invalid admin credentials'}
            
        except Exception as e:
            logger.error(f"Admin verification error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # =====================================================================
    # RESUME OPERATIONS
    # =====================================================================
    
    async def store_resume(self, user_id: str, resume_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Store resume analysis in database"""
        try:
            data = {
                'user_id': user_id,
                'filename': resume_data.get('filename'),
                'processed_content': resume_data.get('content', ''),
                'ai_analysis': json.dumps(resume_data.get('analysis', {})),
                'status': 'completed',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'file_size': resume_data.get('file_size', 0),
                'file_type': resume_data.get('file_type', '')
            }
            
            result = self.client.table('resumes').insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error storing resume: {str(e)}")
            return None
    
    async def get_user_resumes(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all resumes for a user"""
        try:
            result = self.client.table('resumes').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching user resumes: {str(e)}")
            return []
    
    async def get_resume_by_id(self, resume_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific resume by ID"""
        try:
            result = self.client.table('resumes').select('*').eq('id', resume_id).eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching resume: {str(e)}")
            return None
    
    async def delete_user_resumes(self, user_id: str) -> int:
        """Delete all resumes for a user"""
        try:
            result = self.client.table('resumes').delete().eq('user_id', user_id).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"Error deleting resumes: {str(e)}")
            return 0
    
    # =====================================================================
    # TRIAL MANAGEMENT
    # =====================================================================
    
    async def get_trial_status(self, user_id: str) -> Dict[str, Any]:
        """Get trial status for user"""
        try:
            profile = await self.get_user_profile(user_id)
            if not profile:
                return {'error': 'User profile not found'}
            
            trial_limit = profile.get('trial_limit', 100)
            trial_resumes_analyzed = profile.get('trial_resumes_analyzed', 0)
            
            return {
                'trial_resumes_analyzed': trial_resumes_analyzed,
                'trial_limit': trial_limit,
                'remaining': max(0, trial_limit - trial_resumes_analyzed),
                'access_type': profile.get('access_type', 'trial')
            }
        except Exception as e:
            logger.error(f"Error fetching trial status: {str(e)}")
            return {'error': str(e)}
    
    async def track_resume_usage(self, user_id: str) -> Dict[str, Any]:
        """Track resume analysis usage for trial users"""
        try:
            profile = await self.get_user_profile(user_id)
            if not profile:
                return {'success': False, 'error': 'User profile not found'}
            
            if profile.get('access_type') == 'full':
                return {'success': True, 'unlimited': True}
            
            current_count = profile.get('trial_resumes_analyzed', 0)
            trial_limit = profile.get('trial_limit', 100)
            
            if current_count >= trial_limit:
                return {'success': False, 'error': 'Trial limit exceeded'}
            
            # Increment count
            new_count = current_count + 1
            self.client.table('user_profiles').update({
                'trial_resumes_analyzed': new_count
            }).eq('user_id', user_id).execute()
            
            return {
                'success': True,
                'remaining': max(0, trial_limit - new_count),
                'used': new_count
            }
            
        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # =====================================================================
    # ACTIVITY LOGGING
    # =====================================================================
    
    async def log_user_activity(self, user_id: str, action: str, details: str) -> None:
        """Log user activity"""
        try:
            self.client.table('user_activity').insert({
                'user_id': user_id,
                'action': action,
                'details': details,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
    
    # =====================================================================
    # STATISTICS
    # =====================================================================
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific statistics"""
        try:
            resumes = await self.get_user_resumes(user_id)
            
            if not resumes:
                return {
                    'total_resumes': 0,
                    'avg_score': 0,
                    'processed_this_month': 0
                }
            
            # Calculate average score
            scores = []
            for resume in resumes:
                try:
                    analysis = json.loads(resume.get('ai_analysis', '{}'))
                    overall_score = analysis.get('scores', {}).get('overall_score', 0)
                    if overall_score:
                        scores.append(overall_score)
                except:
                    continue
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Count this month's resumes
            current_month = datetime.now(timezone.utc).strftime('%Y-%m')
            this_month_count = sum(1 for r in resumes if r.get('created_at', '').startswith(current_month))
            
            return {
                'total_resumes': len(resumes),
                'avg_score': round(avg_score, 1),
                'processed_this_month': this_month_count,
                'highest_score': max(scores) if scores else 0,
                'lowest_score': min(scores) if scores else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return {'error': str(e)}
    
    # =====================================================================
    # HR LEGAL QUERIES (Placeholder for now)
    # =====================================================================
    
    async def store_legal_query(self, user_id: str, query: str, response: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Store HR legal query and response"""
        try:
            data = {
                'user_id': user_id,
                'query': query,
                'response': response,
                'context': json.dumps(context),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table('hr_legal_queries').insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error storing legal query: {str(e)}")
            return None
    
    # =====================================================================
    # SYSTEM HEALTH
    # =====================================================================
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and health"""
        try:
            # Test basic query
            result = self.client.table('user_profiles').select('count').execute()
            
            return {
                'status': 'healthy',
                'connection': 'active',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

# Singleton instance
supabase_manager = SupabaseManager()
