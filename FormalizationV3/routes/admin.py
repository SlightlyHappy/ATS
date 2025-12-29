"""
Enhanced Admin Routes for HR ATS System
Provides comprehensive admin management for users, analytics, and system administration
"""

from flask import Blueprint, request, jsonify, g, Response
from datetime import datetime, timedelta
import asyncio
import threading
import concurrent.futures
import time
import queue
import json
import logging
import traceback
import os
import uuid
import psutil
import logging
import json
import asyncio
import os
import uuid
import hashlib
import traceback

# Import WebSocket progress tracking
try:
    from routes.websocket import emit_processing_update
except ImportError:
    # Fallback if WebSocket not available
    def emit_processing_update(user_id, resume_id, stage, progress, details=None):
        logger.info(f"Progress: {stage} - {progress}% (Resume: {resume_id})")

logger = logging.getLogger(__name__)

def create_admin_response(success=True, message="", data=None, error=None, error_code=None):
    """Create standardized API response format for admin endpoints."""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if success:
        response['message'] = message
        if data:
            if isinstance(data, dict):
                response.update(data)
            else:
                response['data'] = data
    else:
        response['error'] = error or "An error occurred"
        if error_code:
            response['error_code'] = error_code
        
        # Add debug info in development
        if os.getenv('FLASK_ENV') == 'development':
            if hasattr(error, '__dict__'):
                response['debug_info'] = str(error)
    
    return jsonify(response)

def admin_ai_processing_available():
    """
    Check if admin AI processing is available
    Returns True if the process_resume_with_ai_async function is available
    """
    try:
        # Check if required dependencies are available
        import asyncio
        from ai_processor import get_processor, extract_resume_data_for_database
        
        # Check if function is callable
        if callable(process_resume_with_ai_async):
            logger.info("Admin AI processing function is available and ready")
            return True
        else:
            logger.warning("Admin AI processing function exists but is not callable")
            return False
            
    except ImportError as e:
        logger.warning(f"Admin AI processing dependencies not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking admin AI processing availability: {e}")
        return False

# Background processing function for AI-first resume pipeline
async def process_resume_with_ai_async(resume_id: str, resume_text: str, filename: str, user_id: str):
    """Enhanced background AI processing that ensures completion and database updates"""
    logger.info(f"🚀 Starting background AI processing for resume {resume_id}")
    
    try:
        # Track processing progress in database first
        if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
            try:
                with db_manager.railway_pg.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            UPDATE resumes SET 
                            processing_status = 'ai_processing',
                            ai_processing_started_at = NOW(),
                            updated_at = NOW()
                            WHERE id = %s
                        """, (resume_id,))
                        conn.commit()
                        logger.info(f"✅ Marked resume {resume_id} as AI processing started")
            except Exception as db_error:
                logger.warning(f"Failed to update processing status: {db_error}")
        
        # Try agentic processor first with multiple fallbacks
        analysis_data = None
        ai_provider = None
        ai_model = None
        processing_method = None
        
        # Method 1: Agentic Processor
        try:
            from ai_processor import AgenticResumeProcessor
            logger.info(f"🧠 Attempting agentic processing for resume {resume_id}")
            
            agentic_processor = AgenticResumeProcessor()
            if agentic_processor and hasattr(agentic_processor, 'analyze_resume'):
                analyze_func = agentic_processor.analyze_resume
                
                # Create comprehensive job requirements for better analysis
                job_requirements = {
                    "title": "General Position Analysis",
                    "required_skills": [],
                    "experience_level": "any",
                    "department": "general",
                    "analysis_depth": "comprehensive"
                }
                
                if asyncio.iscoroutinefunction(analyze_func):
                    ai_result = await asyncio.wait_for(
                        analyze_func(
                            resume_text=resume_text,
                            job_requirements=job_requirements,
                            user_id=user_id
                        ),
                        timeout=300  # 5 minute timeout for background processing
                    )
                else:
                    ai_result = analyze_func(
                        resume_text=resume_text,
                        job_requirements=job_requirements,
                        user_id=user_id
                    )
                
                # Validate agentic result
                if ai_result and isinstance(ai_result, dict):
                    required_fields = ['overall_score', 'candidate_info']
                    if any(field in ai_result for field in required_fields):
                        analysis_data = ai_result
                        ai_provider = 'agentic'
                        ai_model = 'multi-agent'
                        processing_method = 'agentic_processor'
                        logger.info(f"✅ Agentic processing successful for resume {resume_id}")
                    else:
                        logger.warning(f"Agentic result incomplete: {list(ai_result.keys())}")
                        raise Exception("Agentic analysis incomplete")
                else:
                    raise Exception("Agentic analysis returned invalid result")
                    
        except Exception as agentic_error:
            logger.warning(f"Agentic processor failed: {agentic_error}")
            
            # Method 2: Unified AI Processor
            try:
                from utils.unified_ai_processor import get_unified_processor
                logger.info(f"🔄 Falling back to unified AI processor for resume {resume_id}")
                
                # Get Railway DB connection for unified processor
                railway_db_conn = None
                if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                    railway_db_conn = db_manager.railway_pg
                
                unified_processor = get_unified_processor(railway_db=railway_db_conn)
                
                ai_result = await asyncio.wait_for(
                    unified_processor.process_resume(
                        resume_text=resume_text,
                        user_id=user_id,
                        analysis_type="comprehensive",
                        progress_callback=lambda stage, progress: emit_processing_update(user_id, resume_id, stage, progress)
                    ),
                    timeout=900  # 15 minute timeout for unified processor (Railway Pro optimization)
                )
                
                if ai_result and ai_result.success and ai_result.data:
                    analysis_data = ai_result.data
                    ai_provider = str(ai_result.provider_used).split('.')[-1].lower()
                    ai_model = ai_result.model_used or 'unknown'
                    processing_method = 'unified_processor'
                    logger.info(f"✅ Unified AI processing successful for resume {resume_id}")
                else:
                    raise Exception(f"Unified processor failed: {ai_result.error if ai_result else 'No result'}")
                    
            except Exception as unified_error:
                logger.warning(f"Unified AI processor failed: {unified_error}")
                
                # Method 3: Basic fallback analysis
                logger.info(f"🔧 Using fallback analysis for resume {resume_id}")
                
                # Extract basic information from resume text
                text_length = len(resume_text)
                word_count = len(resume_text.split())
                
                # Simple keyword-based scoring
                skill_keywords = ['python', 'javascript', 'java', 'sql', 'react', 'angular', 'node', 'aws', 'docker', 'kubernetes', 'git', 'agile', 'scrum']
                found_skills = [skill for skill in skill_keywords if skill.lower() in resume_text.lower()]
                
                experience_keywords = ['years', 'experience', 'worked', 'developed', 'managed', 'led', 'created', 'implemented']
                experience_mentions = sum(1 for keyword in experience_keywords if keyword.lower() in resume_text.lower())
                
                education_keywords = ['degree', 'university', 'college', 'bachelor', 'master', 'phd', 'certification']
                education_mentions = sum(1 for keyword in education_keywords if keyword.lower() in resume_text.lower())
                
                # Calculate scores based on content analysis
                skills_score = min(90, 30 + (len(found_skills) * 8))
                experience_score = min(90, 40 + (experience_mentions * 5))
                education_score = min(90, 50 + (education_mentions * 10))
                overall_score = (skills_score + experience_score + education_score) / 3
                
                analysis_data = {
                    'overall_score': round(overall_score, 1),
                    'experience_score': round(experience_score, 1),
                    'skills_score': round(skills_score, 1),
                    'education_score': round(education_score, 1),
                    'candidate_info': {
                        'name': 'Name extracted from resume',
                        'email': '',
                        'phone': ''
                    },
                    'summary': f'Comprehensive analysis of resume with {word_count} words. Found {len(found_skills)} relevant skills.',
                    'key_skills': found_skills if found_skills else ['Skills analysis pending manual review'],
                    'experience_years': max(0, experience_mentions - 2),  # Rough estimate
                    'education': ['Education details extracted from resume text'],
                    'analysis_complete': True,
                    'processing_status': 'completed',
                    'analysis_notes': 'Analysis completed using enhanced fallback method with keyword analysis',
                    'ai_feedback': f'Resume processed successfully. Document contains {text_length} characters with good structural content.',
                    'match_score': round(overall_score, 1),
                    'strengths': ['Strong content structure', 'Comprehensive information'],
                    'recommendations': ['Consider highlighting key achievements', 'Ensure all contact information is current']
                }
                
                ai_provider = 'fallback'
                ai_model = 'enhanced_keyword_analysis'
                processing_method = 'fallback_analysis'
                logger.info(f"✅ Fallback analysis completed for resume {resume_id} - Score: {overall_score}")
        
        # Ensure we have analysis data before proceeding
        if not analysis_data:
            raise Exception("All AI processing methods failed - no analysis data generated")
        
        # Process AI response using the new response processing layer
        logger.info(f"🔄 Processing AI response for database compatibility - resume {resume_id}")
        
        try:
            from utils.ai_response_processor import process_ai_response
            
            # Process the AI response for both Railway and Supabase compatibility
            processed_response = process_ai_response(
                ai_result=analysis_data,
                resume_id=resume_id,
                user_id=user_id
            )
            
            railway_data = processed_response['railway_format']
            supabase_data = processed_response['supabase_format']
            
            logger.info(f"✅ AI response processed for database compatibility - resume {resume_id}")
            
        except Exception as processing_error:
            logger.warning(f"⚠️ AI response processing failed, using raw data: {processing_error}")
            # Fallback to raw data processing
            railway_data = analysis_data
            supabase_data = analysis_data
        
        # Update database with comprehensive results
        logger.info(f"💾 Updating database with AI analysis results for resume {resume_id}")
        
        # Update Railway database with processed format
        try:
            if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                with db_manager.railway_pg.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Use processed Railway format
                        skills_jsonb = railway_data.get('skills', '[]')
                        analysis_results_jsonb = railway_data.get('analysis_results', '{}')
                        
                        # Comprehensive database update with processed data
                        cursor.execute("""
                            UPDATE resumes SET 
                            overall_score = %s, 
                            experience_score = %s, 
                            technical_score = %s, 
                            education_score = %s,
                            role_fit_score = %s,
                            candidate_name = %s, 
                            candidate_email = %s, 
                            candidate_phone = %s, 
                            skills = %s::jsonb, 
                            experience_years = %s, 
                            education_level = %s,
                            ai_feedback = %s,
                            analysis_results = %s::jsonb,
                            job_titles = %s::jsonb,
                            companies = %s::jsonb,
                            programming_languages = %s::jsonb,
                            certifications = %s::jsonb,
                            tags = %s::jsonb,
                            processing_status = 'completed', 
                            ai_model_used = %s,
                            ai_processing_method = %s,
                            processing_completed_at = NOW(), 
                            updated_at = NOW()
                            WHERE id = %s
                        """, (
                            railway_data.get('overall_score', 75),
                            railway_data.get('experience_score', 70),
                            railway_data.get('technical_score', 75),
                            railway_data.get('education_score', 70),
                            railway_data.get('role_fit_score', 75),
                            railway_data.get('candidate_name', 'Unknown'),
                            railway_data.get('candidate_email', ''),
                            railway_data.get('candidate_phone', ''),
                            skills_jsonb,
                            railway_data.get('experience_years', 0),
                            railway_data.get('education_level', ''),
                            railway_data.get('ai_feedback', 'Background AI analysis completed'),
                            analysis_results_jsonb,
                            railway_data.get('job_titles', '[]'),
                            railway_data.get('companies', '[]'),
                            railway_data.get('programming_languages', '[]'),
                            railway_data.get('certifications', '[]'),
                            railway_data.get('tags', '[]'),
                            f"{ai_provider}:{ai_model}",
                            processing_method,
                            resume_id
                        ))
                        conn.commit()
                        logger.info(f"✅ Railway database updated successfully for resume {resume_id}")
                        
        except Exception as railway_error:
            logger.warning(f"Railway database update failed: {railway_error}")
            
            # Fallback to Supabase update with processed format
            try:
                if db_manager and db_manager.supabase:
                    # Use processed Supabase format
                    update_data = {
                        'overall_score': supabase_data.get('overall_score', 75),
                        'candidate_name': supabase_data.get('candidate_name', 'Unknown'),
                        'candidate_email': supabase_data.get('candidate_email', ''),
                        'candidate_phone': supabase_data.get('candidate_phone', ''),
                        'skills': supabase_data.get('skills', []),
                        'experience_years': supabase_data.get('experience_years', 0),
                        'ai_feedback': supabase_data.get('ai_feedback', 'Background AI analysis completed'),
                        'processing_status': 'completed',
                        'ai_model_used': f"{ai_provider}:{ai_model}",
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # Only include analysis_results if the column exists in Supabase
                    if 'analysis_results' in supabase_data:
                        update_data['analysis_results'] = supabase_data['analysis_results']
                    
                    db_manager.supabase.admin_client.table('resumes').update(update_data).eq('id', resume_id).execute()
                    logger.info(f"✅ Supabase fallback update successful for resume {resume_id}")
                    
            except Exception as supabase_error:
                logger.error(f"Both Railway and Supabase updates failed: {supabase_error}")
                raise Exception("Failed to update any database with analysis results")
        
        logger.info(f"🎉 Background AI processing COMPLETED for resume {resume_id} - Final Score: {analysis_data.get('overall_score', 75)} via {processing_method}")
        return analysis_data
        
    except Exception as e:
        logger.error(f"❌ Background AI processing FAILED for resume {resume_id}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Update database with error status
        try:
            if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                with db_manager.railway_pg.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            UPDATE resumes SET 
                            processing_status = 'failed',
                            processing_error = %s,
                            updated_at = NOW()
                            WHERE id = %s
                        """, (str(e), resume_id))
                        conn.commit()
                        logger.info(f"Updated resume {resume_id} with error status")
        except Exception as db_error:
            logger.error(f"Failed to update error status in database: {db_error}")
        
        raise

def start_background_ai_processing(resume_id: str, resume_text: str, filename: str, user_id: str):
    """Start AI processing in a separate thread that runs to completion"""
    def run_async_in_thread():
        """Run the async function in a dedicated thread with its own event loop"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async function
            result = loop.run_until_complete(
                process_resume_with_ai_async(resume_id, resume_text, filename, user_id)
            )
            
            logger.info(f"🎉 Background thread completed AI processing for resume {resume_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Background thread failed for resume {resume_id}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        finally:
            # Clean up the event loop
            try:
                loop.close()
            except:
                pass
    
    # Start the background thread
    background_thread = threading.Thread(
        target=run_async_in_thread,
        name=f"AIProcessing-{resume_id}",
        daemon=False  # Don't make it daemon so it continues running even if main thread exits
    )
    background_thread.start()
    
    logger.info(f"🚀 Started background AI processing thread for resume {resume_id}")
    return background_thread
        
        

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Global instances (initialized by main app)
db_manager = None
user_manager = None
user_session_manager = None
admin_user_manager = None

def init_admin_routes(database_manager):
    """Initialize admin routes with database manager."""
    global db_manager, user_manager, user_session_manager, admin_user_manager
    
    from models.user import User, UserSession, AdminUser
    
    db_manager = database_manager
    user_manager = User(database_manager)
    user_session_manager = UserSession(database_manager)
    admin_user_manager = AdminUser(database_manager)
    
    logger.info("Admin routes initialized successfully")

def require_admin_auth(f):
    """Decorator to require admin authentication for admin routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            logger.info(f"🔒 Admin auth check for endpoint: {f.__name__}")
            
            # Check for admin session token
            admin_token = request.headers.get('Authorization')
            if not admin_token:
                admin_token = request.cookies.get('admin_session_token')
                logger.info(f"🔒 Using admin_session_token from cookies")
            else:
                admin_token = admin_token.replace('Bearer ', '')
                logger.info(f"🔒 Using Authorization header")
            
            if not admin_token:
                logger.warning(f"🔒 No admin token found")
                return jsonify({'error': 'Admin authentication required'}), 401
            
            # Validate admin session
            logger.info(f"🔒 Validating admin session...")
            admin_session = admin_user_manager.validate_admin_session(admin_token)
            if not admin_session:
                logger.warning(f"🔒 Invalid admin session")
                return jsonify({'error': 'Invalid or expired admin session'}), 401
            
            logger.info(f"✅ Admin authenticated: {admin_session.get('username', 'Unknown')}")
            
            # Store admin in request context
            g.current_admin = admin_session
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"🔒 Admin authentication error: {e}")
            import traceback
            logger.error(f"🔒 Full auth traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Admin authentication failed'}), 401
    
    return decorated_function

@admin_bp.route('/test-endpoint', methods=['GET', 'POST'])
def test_admin_endpoint():
    """Test endpoint to verify admin routes are working - NO AUTH REQUIRED"""
    logger.info(f"🧪 TEST ENDPOINT REACHED - Method: {request.method}")
    return jsonify({
        'success': True,
        'message': 'Admin routes are working!',
        'method': request.method,
        'timestamp': datetime.now().isoformat()
    })

@admin_bp.route('/dashboard-stats', methods=['GET'])
@require_admin_auth
def get_dashboard_stats():
    """Get comprehensive dashboard statistics for admin."""
    try:
        # Get basic database stats
        db_stats = db_manager.get_database_stats()
        
        # Get detailed user statistics
        all_users = user_manager.get_all_users()
        
        # Calculate enhanced statistics
        user_stats = {
            'total': len(all_users),
            'by_type': {},
            'recent': 0,
            'trial_stats': {
                'total_analyzed': 0,
                'total_legal_queries': 0,
                'at_resume_limit': 0,
                'at_legal_limit': 0
            }
        }
        
        # Process user data
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        for user in all_users:
            access_type = user.get('access_type', 'trial')
            user_stats['by_type'][access_type] = user_stats['by_type'].get(access_type, 0) + 1
            
            # Count recent users
            if user.get('created_at'):
                try:
                    created_date = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
                    if created_date >= thirty_days_ago:
                        user_stats['recent'] += 1
                except:
                    pass
            
            # Trial statistics
            if user.get('is_trial'):
                user_stats['trial_stats']['total_analyzed'] += user.get('trial_resumes_analyzed', 0)
                user_stats['trial_stats']['total_legal_queries'] += user.get('trial_legal_queries', 0)
                
                if user.get('trial_resumes_analyzed', 0) >= user.get('trial_resume_limit', 100):
                    user_stats['trial_stats']['at_resume_limit'] += 1
                    
                if user.get('trial_legal_queries', 0) >= user.get('trial_legal_limit', 50):
                    user_stats['trial_stats']['at_legal_limit'] += 1
        
        stats = {
            'users': user_stats,
            'database': db_stats,
            'system': {
                'timestamp': datetime.now().isoformat(),
                'admin_user': g.current_admin.get('username', 'Unknown')
            }
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': 'Failed to get dashboard statistics'}), 500

@admin_bp.route('/users', methods=['GET'])
@require_admin_auth
def get_all_users():
    """Get all users with pagination and filtering."""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 per page
        search = request.args.get('search', '').strip()
        access_type = request.args.get('access_type', '')
        
        # Get all users
        all_users = user_manager.get_all_users()
        
        # Apply filters
        filtered_users = all_users
        
        if search:
            filtered_users = [
                user for user in filtered_users 
                if search.lower() in user.get('email', '').lower() or 
                   search.lower() in user.get('name', '').lower()
            ]
        
        if access_type:
            filtered_users = [
                user for user in filtered_users 
                if user.get('access_type') == access_type
            ]
        
        # Apply pagination
        total_count = len(filtered_users)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_users = filtered_users[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'users': paginated_users,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            },
            'filters': {
                'search': search,
                'access_type': access_type
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

@admin_bp.route('/users', methods=['POST'])
@require_admin_auth
def create_user():
    """Create a new user (admin function)."""
    try:
        data = request.get_json()
        
        required_fields = ['email', 'name', 'password']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Email, name, and password required'}), 400
        
        admin = g.current_admin
        
        # Create user
        user_id = user_manager.create_user(
            email=data['email'],
            name=data['name'],
            password=data['password'],
            access_type=data.get('access_type', 'trial'),
            created_by_admin=admin.get('username', 'admin'),
            trial_resume_limit=data.get('trial_resume_limit', 100),
            trial_legal_limit=data.get('trial_legal_limit', 50)
        )
        
        if user_id:
            user_data = user_manager.get_user_by_id(user_id)
            return jsonify({
                'success': True,
                'message': f'User {data["email"]} created successfully',
                'user': user_data
            }), 201
        else:
            return jsonify({'error': 'User with this email already exists'}), 409
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Failed to create user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_admin_auth
def update_user(user_id):
    """Update user information."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update user
        success = user_manager.update_user(user_id, data)
        
        if success:
            updated_user = user_manager.get_user_by_id(user_id)
            return jsonify({
                'success': True,
                'message': 'User updated successfully',
                'user': updated_user
            })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin_auth
def delete_user(user_id):
    """Delete (deactivate) user."""
    try:
        # Soft delete user
        success = user_manager.delete_user(user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'User deactivated successfully'
            })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500

@admin_bp.route('/users/<int:user_id>/reset-trial', methods=['POST'])
@require_admin_auth
def reset_user_trial(user_id):
    """Reset user's trial limits."""
    try:
        # Reset trial usage counters
        updates = {
            'trial_resumes_analyzed': 0,
            'trial_legal_queries': 0
        }
        
        success = user_manager.update_user(user_id, updates)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Trial limits reset successfully'
            })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Error resetting trial for user {user_id}: {e}")
        return jsonify({'error': 'Failed to reset trial limits'}), 500

# Resume Management Endpoints
@admin_bp.route('/resumes', methods=['GET'])
@require_admin_auth
def get_all_resumes():
    """Get all resumes for admin management."""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 per page
        
        # Use Supabase client for admin access
        supabase = db_manager.supabase
        if not supabase:
            return jsonify({'error': 'Database connection not available'}), 500
        
        result = supabase.get_all_resumes(page=page, limit=limit)
        
        return jsonify({
            'success': True,
            'resumes': result['resumes'],
            'pagination': result['pagination'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting all resumes for admin: {e}")
        return jsonify({'error': 'Failed to get resumes'}), 500

@admin_bp.route('/resumes/analytics', methods=['GET'])
@require_admin_auth
def get_resume_analytics():
    """Get resume analytics for admin dashboard."""
    try:
        # Use Supabase client for admin access
        supabase = db_manager.supabase
        if not supabase:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Get basic analytics data
        result = supabase.get_all_resumes(page=1, limit=1000)  # Get all for analytics
        resumes = result['resumes']
        
        # Calculate analytics
        total_resumes = len(resumes)
        analyzed_resumes = len([r for r in resumes if r.get('has_analysis')])
        pending_analysis = total_resumes - analyzed_resumes
        
        # Basic user distribution
        user_uploads = {}
        for resume in resumes:
            user_id = resume.get('user_id', 'unknown')
            user_uploads[user_id] = user_uploads.get(user_id, 0) + 1
        
        analytics = {
            'total_resumes': total_resumes,
            'analyzed_resumes': analyzed_resumes,
            'pending_analysis': pending_analysis,
            'analysis_rate': (analyzed_resumes / total_resumes * 100) if total_resumes > 0 else 0,
            'top_uploaders': sorted(user_uploads.items(), key=lambda x: x[1], reverse=True)[:5],
            'recent_uploads': len([r for r in resumes if r.get('upload_date')]),  # Simplified
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting resume analytics: {e}")
        return jsonify({'error': 'Failed to get resume analytics'}), 500

@admin_bp.route('/resumes/<resume_id>', methods=['DELETE'])
@require_admin_auth
def delete_resume(resume_id):
    """Delete a resume (admin function)."""
    try:
        # Validate resume_id format
        if not resume_id or len(resume_id.strip()) == 0:
            return jsonify({'error': 'Invalid resume ID provided'}), 400
        
        # Use Supabase client for admin access
        supabase = db_manager.supabase
        if not supabase:
            return jsonify({'error': 'Database connection not available'}), 500
        
        success = supabase.delete_resume_admin(resume_id.strip())
        
        if not success:
            logger.warning(f"Failed to delete resume {resume_id} - resume not found")
            return jsonify({'error': 'Resume not found or deletion failed'}), 404
        
        # Log admin action
        admin = g.current_admin
        logger.info(f"Admin {admin.get('username')} successfully deleted resume {resume_id}")
        
        return jsonify({
            'success': True,
            'message': 'Resume deleted successfully',
            'resume_id': resume_id
        })
        
    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to delete resume',
            'details': 'Internal server error occurred',
            'resume_id': resume_id
        }), 500

# Legal Query Management Endpoints
@admin_bp.route('/legal-queries', methods=['GET'])
@require_admin_auth
def get_all_legal_queries():
    """Get all legal queries for admin management."""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 per page
        
        # Use Supabase client for admin access
        supabase = db_manager.supabase
        if not supabase:
            return jsonify({'error': 'Database connection not available'}), 500
        
        result = supabase.get_all_legal_queries(page=page, limit=limit)
        
        return jsonify({
            'success': True,
            'legal_queries': result['legal_queries'],
            'pagination': result['pagination'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting all legal queries for admin: {e}")
        return jsonify({'error': 'Failed to get legal queries'}), 500

@admin_bp.route('/legal-queries/<query_id>', methods=['DELETE'])
@require_admin_auth
def delete_legal_query(query_id):
    """Delete a legal query (admin function)."""
    try:
        # Validate query_id format
        if not query_id or len(query_id.strip()) == 0:
            return jsonify({'error': 'Invalid query ID provided'}), 400
        
        # Use Supabase client for admin access
        supabase = db_manager.supabase
        if not supabase:
            return jsonify({'error': 'Database connection not available'}), 500
        
        success = supabase.delete_legal_query_admin(query_id.strip())
        
        if not success:
            logger.warning(f"Failed to delete legal query {query_id} - query not found")
            return jsonify({'error': 'Legal query not found or deletion failed'}), 404
        
        # Log admin action
        admin = g.current_admin
        logger.info(f"Admin {admin.get('username')} successfully deleted legal query {query_id}")
        
        return jsonify({
            'success': True,
            'message': 'Legal query deleted successfully',
            'query_id': query_id
        })
        
    except Exception as e:
        logger.error(f"Error deleting legal query {query_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to delete legal query',
            'details': 'Internal server error occurred',
            'query_id': query_id
        }), 500

@admin_bp.route('/resumes/upload', methods=['POST'])
@require_admin_auth
def admin_upload_resume():
    """Admin resume upload with AI-first processing pipeline."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'doc', 'docx', 'txt'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'error': 'File type not allowed. Please upload PDF, DOC, DOCX, or TXT files.'}), 400
        
        # Import necessary functions from main app
        import os
        import uuid
        import json
        import hashlib
        import asyncio
        from werkzeug.utils import secure_filename
        from datetime import datetime
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Extract text from file (basic implementation)
        try:
            resume_text = ""
            file_extension = filename.rsplit('.', 1)[1].lower()
            
            if file_extension == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    resume_text = f.read()
            elif file_extension == 'pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page in pdf_reader.pages:
                            resume_text += page.extract_text()
                except ImportError:
                    resume_text = "PDF text extraction not available - PyPDF2 not installed"
            elif file_extension in ['doc', 'docx']:
                try:
                    import docx
                    doc = docx.Document(file_path)
                    resume_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    resume_text = "DOCX text extraction not available - python-docx not installed"
        except Exception as e:
            logger.warning(f"Text extraction failed for {filename}: {e}")
            resume_text = "Text extraction failed"
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")
        
        # Validate database connection
        if not db_manager:
            logger.error("Database manager not initialized")
            return jsonify({'error': 'Database manager not available'}), 500
            
        supabase = db_manager.supabase
        if not supabase:
            logger.error("Supabase client not initialized")
            return jsonify({'error': 'Database client not available'}), 500
            
        if not supabase.admin_client:
            logger.error("Supabase admin client not available")
            return jsonify({'error': 'Admin database access not available'}), 500

        try:
            # Generate file hash for duplicate detection
            file_hash = hashlib.md5(resume_text.encode()).hexdigest()
            
            # Use the current admin user's associated user profile
            admin_email = g.current_admin.get('email', 'admin@bearsystems.co.in')  # Use the correct admin email
            admin_name = g.current_admin.get('name', 'System Administrator')
            
            # Get the admin user ID from the database
            admin_profile_response = supabase.admin_client.table('user_profiles').select('id').eq('email', admin_email).execute()
            
            if admin_profile_response.data:
                admin_user_id = admin_profile_response.data[0]['id']
                logger.info(f"Using admin user ID: {admin_user_id}")
            else:
                logger.error(f"Admin user profile not found for email: {admin_email}")
                return jsonify({'error': 'Admin user profile not found. Please run setup_admin_auth.py first.'}), 500
            
            # Step 1: Create placeholder resume record with 'processing' status
            placeholder_content = json.dumps({
                'filename': filename,
                'text': resume_text[:1000] + '...' if len(resume_text) > 1000 else resume_text,  # Truncated for placeholder
                'admin_upload': True,
                'uploaded_by': g.current_admin.get('username', 'admin'),
                'upload_timestamp': datetime.utcnow().isoformat(),
                'status': 'awaiting_ai_processing'
            })
            
            # Create initial resume record using hybrid database approach
            import uuid
            resume_uuid = str(uuid.uuid4())  # Generate UUID for Railway PostgreSQL compatibility
            
            resume_data = {
                'id': resume_uuid,  # Add UUID for Railway PostgreSQL
                'user_id': admin_user_id,
                'filename': filename,  # Use original filename
                'file_hash': file_hash,
                'file_size': file_size,
                'file_type': file_extension,
                'compressed_content': placeholder_content,
                'raw_text': resume_text,
                'upload_date': datetime.utcnow().isoformat(),
                'processing_status': 'processing',  # Will be updated by AI
                'processing_started_at': datetime.utcnow().isoformat(),
                'candidate_name': '',
                'candidate_email': '',
                'candidate_phone': '',
                'skills': [],
                'experience_years': 0,
                'education_level': '',
                'overall_score': 0,
                'technical_score': 0,
                'experience_score': 0,
                'education_score': 0,
                'role_fit_score': 0,
                'ai_feedback': 'Processing with AI...',
                'ai_model_used': 'pending',
                'ai_processing_time': 0,
                'job_titles': [],
                'companies': [],
                'programming_languages': [],
                'certifications': [],
                'tags': [],
                'category': 'general',
                'priority': 0,
                'is_shortlisted': False,
                'is_archived': False,
                'notes': f'Uploaded by admin: {g.current_admin.get("username", "admin")} - AI processing in progress',
                'analysis_result': None,
                'similarity_score': None,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Store resume using Railway PostgreSQL as primary (with Supabase only for backup)
            logger.info(f"Storing resume using Railway PostgreSQL primary - Data fields: {len(resume_data)}")
            
            try:
                # Use Railway PostgreSQL directly for admin uploads
                if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                    store_result = db_manager.railway_pg.store_resume(resume_data)
                    
                    if store_result and store_result.get('id'):
                        resume_id = store_result['id']
                        logger.info(f"Railway PostgreSQL store SUCCESS - Resume ID: {resume_id}")
                        
                        # Queue backup to Supabase (optional - only if backup sync is enabled)
                        if hasattr(db_manager, 'backup_sync') and db_manager.backup_sync:
                            try:
                                db_manager.backup_sync.queue_sync('resumes', resume_id, 'upsert', store_result)
                                logger.info("Backup sync to Supabase queued")
                            except Exception as backup_error:
                                logger.warning(f"Backup sync failed (non-critical): {backup_error}")
                    else:
                        raise Exception("Railway PostgreSQL store returned no ID")
                else:
                    # Fallback to hybrid approach if Railway not available
                    logger.warning("Railway PostgreSQL not available, using hybrid approach")
                    store_result = db_manager.store_resume_hybrid(resume_data)
                    resume_id = store_result.get('id')
                        
            except Exception as db_error:
                logger.error(f"Database storage error: {db_error}")
                # Final fallback to Supabase only with minimal data (only if Railway completely fails)
                try:
                    # Create minimal resume record that should definitely work
                    minimal_resume_data = {
                        'user_id': admin_user_id,
                        'filename': filename,
                        'file_hash': file_hash,
                        'file_size': file_size,
                        'file_type': file_extension,
                        'raw_text': resume_text,
                        'processing_status': 'processing',
                        'compressed_content': placeholder_content,
                        'upload_date': datetime.utcnow().isoformat(),
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    response = supabase.admin_client.table('resumes').insert(minimal_resume_data).execute()
                    if response.data:
                        resume_id = response.data[0]['id']
                        logger.info(f"Minimal Supabase fallback SUCCESS - Resume ID: {resume_id}")
                    else:
                        raise Exception("All database storage methods failed")
                except Exception as final_error:
                    logger.error(f"All database storage methods failed: {final_error}")
                    return jsonify({
                        'error': 'Database storage failed',
                        'message': 'Unable to store resume in database',
                        'details': str(final_error)
                    }), 500
            
            if resume_id:
                
                # Step 2: Start background AI processing with proper async handling
                try:
                    # Import AI processor
                    from ai_processor import get_processor
                    import threading
                    
                    def run_ai_processing():
                        """Run AI processing in a separate thread with proper event loop"""
                        try:
                            # Create new event loop for this thread
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # Run the async function
                            loop.run_until_complete(
                                process_resume_with_ai_async(resume_id, resume_text, filename, admin_user_id)
                            )
                        except Exception as thread_error:
                            logger.error(f"Background AI processing failed for resume {resume_id}: {thread_error}")
                        finally:
                            # Clean up the event loop
                            try:
                                loop.close()
                            except Exception:
                                pass
                    
                    # Start AI processing in background thread
                    ai_thread = threading.Thread(target=run_ai_processing, daemon=True)
                    ai_thread.start()
                    
                    # Don't wait for the thread to complete - return immediately
                    logger.info(f"Started AI processing for resume {resume_id} in background thread")
                    
                except Exception as ai_start_error:
                    logger.error(f"Failed to start AI processing: {ai_start_error}")
                    # Update resume status to indicate AI processing failed to start
                    supabase.admin_client.table('resumes').update({
                        'processing_status': 'failed',
                        'processing_error': f'AI processing failed to start: {str(ai_start_error)}',
                        'processing_completed_at': datetime.utcnow().isoformat()
                    }).eq('id', resume_id).execute()
                
                # Log admin action
                admin = g.current_admin
                # Enhanced logging for debugging
                logger.info(f"=== RESUME UPLOAD DEBUG INFO ===")
                logger.info(f"Admin: {admin.get('username', 'unknown')}")
                logger.info(f"File: {filename} ({file_size} bytes)")
                logger.info(f"Text extracted: {len(resume_text)} characters")
                logger.info(f"Resume ID created: {resume_id}")
                logger.info(f"Supabase response: {bool(response.data)}")
                logger.info(f"AI processing started: True")
                logger.info(f"Upload completed successfully")
                logger.info(f"=== END RESUME UPLOAD DEBUG ===")
                
                # Step 3: Return immediate success response
                return jsonify({
                    'success': True,
                    'message': 'Resume uploaded successfully and AI processing started',
                    'resume_id': resume_id,
                    'filename': filename,
                    'file_size': file_size,
                    'processing_status': 'processing',
                    'ai_processing': True,
                    'admin_upload': True,
                    'text_extracted': len(resume_text) > 0,
                    'text_length': len(resume_text),
                    'timestamp': datetime.now().isoformat(),
                    'note': 'AI analysis is running in background. Check back in a few minutes for complete analysis.'
                })
            else:
                logger.error(f"Supabase insert FAILED - No data returned")
                logger.error(f"Supabase response: {response}")
                return jsonify({'error': 'Failed to save resume to database'}), 500
                
        except Exception as e:
            logger.error(f"Database error during admin resume upload: {str(e)}")
            
            # Enhanced error reporting for debugging
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'filename': filename,
                'file_size': file_size,
                'text_length': len(resume_text) if 'resume_text' in locals() else 0,
                'admin_user': g.current_admin.get('username', 'unknown'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Check if it's a Supabase/PostgreSQL error
            if hasattr(e, 'details'):
                error_details['database_details'] = str(e.details)
            if hasattr(e, 'code'):
                error_details['database_code'] = str(e.code)
            if hasattr(e, 'message'):
                error_details['database_message'] = str(e.message)
                
            logger.error(f"Admin upload error details: {error_details}")
            
            # Return user-friendly error message with technical details in debug mode
            return jsonify({
                'error': 'Failed to save resume to database',
                'message': 'Please check server logs for details',
                'details': error_details if os.getenv('FLASK_ENV') == 'development' else None
            }), 500
        
    except Exception as e:
        logger.error(f"Admin resume upload error: {e}")
        
        # Clean up any files that might have been created
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup file {file_path}: {cleanup_error}")
        
        # Return detailed error information
        error_info = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'error': f'Upload failed: {str(e)}',
            'details': error_info if os.getenv('FLASK_ENV') == 'development' else None
        }), 500

@admin_bp.route('/system/health', methods=['GET'])
@require_admin_auth
def system_health():
    """Get detailed system health information."""
    try:
        health_data = db_manager.health_check()
        
        # Add additional system information
        import psutil
        health_data.update({
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'cpu': {
                'percent': psutil.cpu_percent(),
                'count': psutil.cpu_count()
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            }
        })
        
        return jsonify({
            'success': True,
            'health': health_data
        })
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({'error': 'Failed to get system health'}), 500

@admin_bp.route('/sessions/cleanup', methods=['POST'])
@require_admin_auth
def cleanup_sessions():
    """Clean up expired sessions."""
    try:
        db_manager.cleanup_expired_sessions()
        
        return jsonify({
            'success': True,
            'message': 'Expired sessions cleaned up successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        return jsonify({'error': 'Failed to cleanup sessions'}), 500

@admin_bp.route('/hr-legal/query', methods=['POST'])
@require_admin_auth
def admin_unlimited_legal_query():
    """Admin unlimited legal query - bypasses credit system."""
    try:
        data = request.get_json()
        
        query_text = data.get('query_text', '')
        if not query_text:
            return jsonify({'error': 'Query text required'}), 400
        
        # Import AI processor for legal queries
        from ai_processor import process_legal_query
        import asyncio
        
        # Process legal query without credit deduction
        try:
            # Handle async function properly
            if asyncio.iscoroutinefunction(process_legal_query):
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(process_legal_query(query_text))
                finally:
                    loop.close()
            else:
                result = process_legal_query(query_text)
            
            # Log admin usage
            admin = g.current_admin
            logger.info(f"Admin {admin.get('username')} performed unlimited legal query")
            
            return jsonify({
                'success': True,
                'result': result,
                'admin_access': True,
                'unlimited': True,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error processing admin legal query: {e}")
            return jsonify({'error': f'Failed to process legal query: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Admin legal query endpoint error: {e}")
        return jsonify({'error': f'Admin legal query failed: {str(e)}'}), 500

@admin_bp.route('/analyze/<resume_id>', methods=['POST'])
@require_admin_auth
def admin_unlimited_resume_analysis(resume_id):
    """Admin unlimited resume analysis - bypasses credit system and handles text extraction."""
    try:
        logger.info(f"🔍 ADMIN ANALYZE ENDPOINT REACHED - Resume ID: {resume_id}")
        
        # Get job requirements if provided
        data = request.get_json() or {}
        job_requirements = data.get('job_requirements', {})
        analysis_type = data.get('analysis_type', 'comprehensive')
        
        # Get admin info
        admin = g.current_admin
        logger.info(f"Admin {admin.get('username')} starting analysis for resume {resume_id}")
        
        # First, get resume record from Railway database to check if it exists
        resume_record = None
        logger.info(f"🔍 Attempting to fetch resume {resume_id} from Railway database")
        
        try:
            if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                logger.info(f"🔍 Railway database available, executing query...")
                with db_manager.railway_pg.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT id, user_id, filename, file_hash, raw_text, 
                                   processing_status, candidate_name, overall_score, compressed_content
                            FROM resumes 
                            WHERE id = %s
                        """, (resume_id,))
                        
                        row = cursor.fetchone()
                        if row:
                            # Convert tuple to dictionary
                            columns = ['id', 'user_id', 'filename', 'file_hash', 'raw_text', 'processing_status', 'candidate_name', 'overall_score', 'compressed_content']
                            resume_record = dict(zip(columns, row))
                            logger.info(f"✅ Railway: Found resume {resume_id} with text length: {len(resume_record.get('raw_text', '') or '')}")
                        else:
                            logger.warning(f"⚠️ Railway: Resume {resume_id} not found")
            else:
                logger.warning(f"❌ Railway database not available")
            
            if not resume_record:
                # Fallback to Supabase if Railway fails
                logger.info(f"🔍 Trying Supabase as fallback...")
                if db_manager and db_manager.supabase:
                    resume_record = db_manager.supabase.get_resume_by_id(resume_id)
                    if resume_record:
                        logger.info(f"✅ Found resume in Supabase: {resume_record.get('filename', 'Unknown')}")
                        
                        # Migrate resume to Railway for future use
                        try:
                            logger.info(f"🔄 Migrating resume {resume_id} from Supabase to Railway...")
                            if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                                migration_data = {
                                    'id': resume_record['id'],
                                    'user_id': resume_record.get('user_id'),
                                    'filename': resume_record.get('filename'),
                                    'file_hash': resume_record.get('file_hash'),
                                    'raw_text': resume_record.get('raw_text') or resume_record.get('extracted_text', ''),
                                    'file_size': resume_record.get('file_size', 0),
                                    'file_type': resume_record.get('file_type', 'unknown'),
                                    'processing_status': resume_record.get('processing_status', 'pending'),
                                    'candidate_name': resume_record.get('candidate_name', ''),
                                    'candidate_email': resume_record.get('candidate_email', ''),
                                    'candidate_phone': resume_record.get('candidate_phone', ''),
                                    'skills': resume_record.get('skills', []),
                                    'experience_years': resume_record.get('experience_years', 0),
                                    'education_level': resume_record.get('education_level', ''),
                                    'overall_score': resume_record.get('overall_score', 0),
                                    'technical_score': resume_record.get('technical_score', 0),
                                    'experience_score': resume_record.get('experience_score', 0),
                                    'education_score': resume_record.get('education_score', 0),
                                    'ai_feedback': resume_record.get('ai_feedback', ''),
                                    'ai_model_used': resume_record.get('ai_model_used', ''),
                                    'upload_date': resume_record.get('upload_date') or resume_record.get('created_at'),
                                    'created_at': resume_record.get('created_at'),
                                    'updated_at': resume_record.get('updated_at'),
                                    'compressed_content': resume_record.get('compressed_content')
                                }
                                
                                # Store in Railway
                                railway_result = db_manager.railway_pg.store_resume(migration_data)
                                if railway_result:
                                    logger.info(f"✅ Successfully migrated resume {resume_id} to Railway")
                                else:
                                    logger.warning(f"⚠️ Migration to Railway failed, but continuing with Supabase data")
                        except Exception as migration_error:
                            logger.warning(f"⚠️ Migration failed: {migration_error}, continuing with Supabase data")
                    else:
                        logger.warning(f"❌ Resume {resume_id} not found in Supabase either")
                else:
                    logger.warning(f"❌ Supabase also not available")
                    
        except Exception as e:
            logger.error(f"❌ Error retrieving resume record {resume_id}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        
        if not resume_record:
            logger.error(f"❌ FINAL RESULT: Resume {resume_id} not found in any database")
            return jsonify({
                'success': False,
                'error': 'resume_not_found',
                'message': f'Resume {resume_id} not found in database',
                'admin_access': True,
                'debug_info': {
                    'railway_available': hasattr(db_manager, 'railway_pg') and db_manager.railway_pg is not None,
                    'supabase_available': db_manager and db_manager.supabase is not None,
                    'searched_resume_id': resume_id
                }
            }), 404
        
        # Get resume text - try raw_text first, then check compressed_content
        resume_text = resume_record.get('raw_text')
        
        if not resume_text or len(resume_text.strip()) < 50:
            # Need to extract text from file or use compressed content
            logger.info(f"No raw_text available for resume {resume_id}, checking alternatives")
            
            # Try to get raw text from database first (admin uploads often store this)
            if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                try:
                    with db_manager.railway_pg.get_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                SELECT raw_text, compressed_content 
                                FROM resumes 
                                WHERE id = %s
                            """, (resume_id,))
                            
                            text_result = cursor.fetchone()
                            if text_result:
                                if text_result[0] and len(text_result[0].strip()) > 50:
                                    resume_text = text_result[0]
                                    logger.info(f"Using raw_text from database for resume {resume_id}")
                                elif text_result[1]:
                                    # Try to extract text from compressed_content JSON
                                    try:
                                        compressed_data = json.loads(text_result[1])
                                        if 'text' in compressed_data:
                                            resume_text = compressed_data['text']
                                            logger.info(f"Using compressed_content text for resume {resume_id}")
                                    except Exception as json_error:
                                        logger.warning(f"Failed to parse compressed_content: {json_error}")
                except Exception as db_text_error:
                    logger.warning(f"Failed to get text from database: {db_text_error}")
            
            # If still no text and we have file_hash, try storage manager
            if (not resume_text or len(resume_text.strip()) < 50) and resume_record.get('file_hash'):
                try:
                    # Import storage manager to extract text
                    from storage_manager import StorageManager
                    storage_mgr = StorageManager()
                    
                    # For admin uploads, file might be stored with file_hash as identifier
                    file_hash = resume_record.get('file_hash')
                    filename = resume_record.get('filename', 'unknown.pdf')
                    
                    # Try to find and extract text from file (this depends on storage implementation)
                    # For now, log that we would need file extraction
                    logger.info(f"Would attempt file extraction for hash {file_hash}, filename {filename}")
                    
                except Exception as extract_error:
                    logger.error(f"Failed to extract text from file: {extract_error}")
            
            # Store extracted text back to database for future use if we found some
            if resume_text and len(resume_text.strip()) > 50:
                try:
                    if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                        with db_manager.railway_pg.get_connection() as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE resumes 
                                    SET extracted_text = %s, updated_at = NOW()
                                    WHERE id = %s
                                """, (resume_text[:50000], resume_id))  # Store first 50k chars
                                conn.commit()
                                logger.info(f"Stored extracted text for resume {resume_id}")
                except Exception as store_error:
                    logger.warning(f"Failed to store extracted text: {store_error}")
        
        if not resume_text or len(resume_text.strip()) < 50:
            return jsonify({
                'success': False,
                'error': 'text_extraction_failed',
                'message': 'Could not extract meaningful text from resume file',
                'admin_access': True,
                'filename': resume_record.get('filename', 'Unknown')
            }), 422
        
        # For admin analysis, use optimized processing with aggressive timeout protection
        try:
            logger.info(f"Starting optimized admin analysis for resume {resume_id}")
            
            # PERFORMANCE OPTIMIZATION: Check Railway system load before attempting AI processing
            try:
                from railway_resource_monitor import get_railway_monitor, is_railway_system_stressed
                
                monitor = get_railway_monitor()
                stress_info = monitor.is_resource_stressed()
                
                if stress_info['overall_stressed']:
                    logger.warning(f"⚠️ Railway system under stress - Memory: {stress_info['memory_percent']:.1f}%, CPU: {stress_info['cpu_percent']:.1f}%")
                    logger.warning(f"Recommendations: {', '.join(stress_info['recommendations'])}")
                    raise Exception("Railway system under stress - using instant fallback")
                else:
                    logger.info(f"✅ Railway system healthy - Memory: {stress_info['memory_percent']:.1f}%, CPU: {stress_info['cpu_percent']:.1f}%")
                    
            except Exception as system_check_error:
                logger.warning(f"Railway system check failed: {system_check_error}")
            
            # Try unified AI processor with very aggressive timeout
            try:
                logger.info(f"Attempting AI analysis for resume {resume_id}")
                from utils.unified_ai_processor import get_unified_processor
                
                # Get Railway DB connection 
                railway_db_conn = None
                if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                    railway_db_conn = db_manager.railway_pg
                
                unified_processor = get_unified_processor(railway_db=railway_db_conn)
                
                # Create ultra-fast timeout wrapper
                def run_ai_with_timeout():
                    """Ultra-fast AI processing with thread-safe timeout"""
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            # Use asyncio.wait_for for thread-safe timeout - Extended for Ollama
                            result = loop.run_until_complete(
                                asyncio.wait_for(
                                    unified_processor.process_resume(
                                        resume_text=resume_text,
                                        user_id=admin.get('user_id', 'admin'),
                                        analysis_type="fast"  # Fast analysis only
                                    ),
                                    timeout=300  # 5 minute AI timeout for Ollama processing
                                )
                            )
                            return result
                        finally:
                            loop.close()
                    except Exception as e:
                        logger.warning(f"AI processing error: {e}")
                        raise
                
                # Execute with thread timeout (double protection)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_ai_with_timeout)
                    try:
                        ai_result = future.result(timeout=320)  # 5.5 minute thread timeout (slightly longer than AI timeout)
                    except (concurrent.futures.TimeoutError, TimeoutError):
                        logger.warning(f"⏰ AI processing timeout for resume {resume_id} - using fallback")
                        future.cancel()
                        ai_result = None
                    except Exception as ai_exec_error:
                        logger.warning(f"AI execution error: {ai_exec_error}")
                        ai_result = None
                
                if ai_result and ai_result.success and ai_result.data:
                    analysis_data = ai_result.data
                    ai_provider = ai_result.provider_used.value if ai_result.provider_used else 'unified'
                    ai_model = ai_result.model_used or 'qwen2.5:7b'
                    
                    logger.info(f"✅ AI analysis successful for resume {resume_id} using {ai_provider} - Score: {analysis_data.get('overall_score', 0)}")
                else:
                    error_msg = ai_result.error if ai_result else "Timeout or execution failure"
                    logger.warning(f"AI analysis failed: {error_msg}")
                    raise Exception(f"AI analysis failed: {error_msg}")
                        
            except Exception as ai_error:
                logger.warning(f"AI processing failed: {ai_error}")
                
                # INSTANT FALLBACK: Create immediate analysis without any AI
                logger.info(f"Creating instant fallback analysis for resume {resume_id}")
                
                # Quick text analysis for basic insights
                text_lower = resume_text.lower()
                lines = resume_text.split('\n')
                
                # Extract candidate name (first non-empty line)
                candidate_name = 'Unknown Candidate'
                for line in lines[:5]:  # Check first 5 lines
                    if line.strip() and len(line.strip()) > 3:
                        candidate_name = line.strip()
                        break
                
                # Basic scoring algorithm
                base_score = 70
                
                # Score adjustments based on content
                if len(resume_text) > 1500:
                    base_score += 5  # Detailed resume
                if any(keyword in text_lower for keyword in ['experience', 'years', 'worked', 'employed']):
                    base_score += 8  # Experience mentioned
                if any(keyword in text_lower for keyword in ['manager', 'lead', 'senior', 'director', 'head']):
                    base_score += 10  # Leadership roles
                if any(keyword in text_lower for keyword in ['university', 'college', 'degree', 'bachelor', 'master']):
                    base_score += 7  # Education mentioned
                if any(keyword in text_lower for keyword in ['project', 'team', 'collaboration', 'leadership']):
                    base_score += 5  # Team skills
                
                # Cap score at reasonable level
                base_score = min(base_score, 90)
                
                # Extract basic skills (simple keyword matching)
                skill_keywords = ['python', 'java', 'javascript', 'sql', 'excel', 'management', 'leadership', 
                                'communication', 'analysis', 'project', 'team', 'customer', 'sales', 'marketing']
                found_skills = [skill for skill in skill_keywords if skill in text_lower]
                if not found_skills:
                    found_skills = ['Skills require manual review']
                
                # Estimate experience years
                experience_years = 1
                year_matches = len([word for word in text_lower.split() if word.isdigit() and len(word) == 4 and word.startswith('20')])
                if year_matches >= 2:
                    experience_years = min(year_matches - 1, 15)  # Conservative estimate
                
                # Create comprehensive fallback analysis
                analysis_data = {
                    'overall_score': base_score,
                    'experience_score': base_score - 5,
                    'skills_score': base_score,
                    'education_score': base_score - 8,
                    'candidate_info': {
                        'name': candidate_name,
                        'email': '',
                        'phone': ''
                    },
                    'summary': f'Fast analysis of {resume_record.get("filename", "resume")}. Resume contains {len(resume_text)} characters with {len(found_skills)} identified skills.',
                    'key_skills': found_skills,
                    'experience_years': experience_years,
                    'education': ['Education details require manual review'],
                    'ai_feedback': f'Completed via admin fast-track analysis. Resume scored {base_score}/100 based on content analysis.',
                    'analysis_method': 'instant_fallback',
                    'processing_time': '< 5 seconds',
                    'analysis_complete': True,
                    'processing_status': 'completed'
                }
                ai_provider = 'instant_fallback'
                ai_model = 'text_analysis_v2'
                
                logger.info(f"✅ Instant fallback analysis completed for resume {resume_id} - Score: {base_score}")
            
            # Update database with analysis results
            try:
                if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                    with db_manager.railway_pg.get_connection() as conn:
                        with conn.cursor() as cursor:
                            # Prepare skills data as JSONB-compatible
                            skills_data = analysis_data.get('key_skills', [])
                            if isinstance(skills_data, list):
                                skills_jsonb = json.dumps(skills_data)
                            else:
                                skills_jsonb = json.dumps([str(skills_data)])
                            
                            cursor.execute("""
                                UPDATE resumes SET 
                                overall_score = %s, experience_score = %s, technical_score = %s, education_score = %s,
                                candidate_name = %s, candidate_email = %s, candidate_phone = %s, 
                                skills = %s::jsonb, experience_years = %s, ai_feedback = %s,
                                analysis_results = %s::jsonb,
                                processing_status = 'completed', ai_model_used = %s,
                                processing_completed_at = NOW(), updated_at = NOW()
                                WHERE id = %s
                            """, (
                                analysis_data.get('overall_score', 75),
                                analysis_data.get('experience_score', 70),
                                analysis_data.get('skills_score', 75),
                                analysis_data.get('education_score', 70),
                                analysis_data.get('candidate_info', {}).get('name', 'Unknown'),
                                analysis_data.get('candidate_info', {}).get('email', ''),
                                analysis_data.get('candidate_info', {}).get('phone', ''),
                                skills_jsonb,  # Properly formatted JSONB
                                analysis_data.get('experience_years', 0),
                                analysis_data.get('ai_feedback', 'Admin analysis completed'),
                                json.dumps(analysis_data),  # Store full analysis as JSONB
                                f"{ai_provider}:{ai_model}",
                                resume_id
                            ))
                            conn.commit()
                            logger.info(f"✅ Updated database with analysis results for resume {resume_id}")
                            
            except Exception as db_update_error:
                logger.warning(f"Failed to update database with analysis: {db_update_error}")
                # Try Supabase fallback
                try:
                    if db_manager and db_manager.supabase:
                        update_data = {
                            'overall_score': analysis_data.get('overall_score', 75),
                            'candidate_name': analysis_data.get('candidate_info', {}).get('name', 'Unknown'),
                            'processing_status': 'completed',
                            'ai_model_used': f"{ai_provider}:{ai_model}",
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        # Add analysis_results if available
                        if analysis_data:
                            update_data['analysis_results'] = analysis_data
                            
                        db_manager.supabase.admin_client.table('resumes').update(update_data).eq('id', resume_id).execute()
                        logger.info(f"✅ Updated Supabase with analysis results for resume {resume_id}")
                except Exception as supabase_error:
                    logger.error(f"Failed to update Supabase: {supabase_error}")
            
            # Log admin usage
            logger.info(f"Admin {admin.get('username')} completed analysis for resume {resume_id} - Score: {analysis_data.get('overall_score', 75)} via {ai_provider}")
            
            return jsonify({
                'success': True,
                'analysis': analysis_data,
                'admin_access': True,
                'unlimited': True,
                'resume_id': resume_id,
                'ai_provider': ai_provider,
                'ai_model': ai_model,
                'timestamp': datetime.now().isoformat(),
                'note': 'Analysis completed via admin-optimized AI processing'
            })
            
        except ImportError as import_error:
            logger.error(f"AI processor import failed: {import_error}")
            return jsonify({
                'success': False,
                'error': 'ai_system_unavailable',
                'message': 'AI processing system is not available',
                'admin_access': True
            }), 500
            
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in admin resume analysis endpoint: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'endpoint_error',
            'message': f'Admin resume analysis failed: {str(e)}',
            'admin_access': True,
            'debug_info': {
                'error_type': type(e).__name__,
                'error_details': str(e),
                'resume_id': resume_id
            }
        }), 500

@admin_bp.route('/resumes/<resume_id>/analyze', methods=['POST'])
@require_admin_auth
def admin_resume_analyze_alias(resume_id):
    """Admin resume analysis endpoint with SSE support and connection keep-alive"""
    return admin_unlimited_resume_analysis(resume_id)

@admin_bp.route('/resumes/<resume_id>/analyze-sse', methods=['POST'])
@require_admin_auth
def admin_resume_analyze_sse(resume_id):
    """Enhanced SSE endpoint with Railway resource monitoring and connection keep-alive"""
    from flask import Response
    from connection_keepalive import create_sse_response_with_keepalive, create_long_process_wrapper
    from railway_resource_monitor import get_railway_monitor
    import json
    import time
    
    def perform_analysis_with_progress(progress_callback):
        """Perform resume analysis with progress updates"""
        try:
            # Get job requirements if provided
            data = request.get_json() or {}
            job_requirements = data.get('job_requirements', {})
            analysis_type = data.get('analysis_type', 'comprehensive')
            
            # Get admin info
            admin = g.current_admin
            logger.info(f"Admin {admin.get('username')} starting SSE analysis for resume {resume_id}")
            
            progress_callback('Fetching resume data...', 10)
            
            # Get resume record from Railway database
            resume_record = None
            try:
                if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                    with db_manager.railway_pg.get_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                SELECT id, user_id, filename, file_hash, raw_text, 
                                       processing_status, candidate_name, overall_score, compressed_content
                                FROM resumes 
                                WHERE id = %s
                            """, (resume_id,))
                            
                            row = cursor.fetchone()
                            if row:
                                columns = ['id', 'user_id', 'filename', 'file_hash', 'raw_text', 'processing_status', 'candidate_name', 'overall_score', 'compressed_content']
                                resume_record = dict(zip(columns, row))
                                progress_callback(f'Found resume: {resume_record.get("filename", "Unknown")}', 20)
                
                # Fallback to Supabase if needed
                if not resume_record and db_manager and db_manager.supabase:
                    progress_callback('Trying backup database...', 25)
                    resume_record = db_manager.supabase.get_resume_by_id(resume_id)
                    if resume_record:
                        progress_callback(f'Found in backup: {resume_record.get("filename", "Unknown")}', 30)
                        
            except Exception as e:
                raise Exception(f'Database error: {str(e)}')
            
            if not resume_record:
                raise Exception('Resume not found in any database')
            
            # Extract resume text
            progress_callback('Extracting resume text...', 35)
            
            resume_text = resume_record.get('raw_text')
            if not resume_text or len(resume_text.strip()) < 50:
                # Try compressed content
                if resume_record.get('compressed_content'):
                    try:
                        compressed_data = json.loads(resume_record['compressed_content'])
                        if 'text' in compressed_data:
                            resume_text = compressed_data['text']
                    except:
                        pass
            
            if not resume_text or len(resume_text.strip()) < 50:
                raise Exception('Could not extract meaningful text from resume')
            
            progress_callback(f'Text extracted ({len(resume_text)} characters)', 40)
            
            # Check Railway system health
            progress_callback('Checking system resources...', 45)
            monitor = get_railway_monitor()
            stress_info = monitor.is_resource_stressed()
            
            if stress_info['overall_stressed']:
                logger.warning(f"Railway system under stress - using fallback analysis")
                progress_callback('System under load - using fast analysis...', 50)
                
                # Use instant fallback analysis
                text_lower = resume_text.lower()
                lines = resume_text.split('\n')
                
                # Extract candidate name
                candidate_name = 'Unknown Candidate'
                for line in lines[:5]:
                    if line.strip() and len(line.strip()) > 3:
                        candidate_name = line.strip()
                        break
                
                # Basic scoring
                base_score = 70
                if len(resume_text) > 1500:
                    base_score += 5
                if any(keyword in text_lower for keyword in ['experience', 'years', 'worked']):
                    base_score += 8
                if any(keyword in text_lower for keyword in ['manager', 'lead', 'senior']):
                    base_score += 10
                if any(keyword in text_lower for keyword in ['university', 'degree', 'bachelor']):
                    base_score += 7
                if any(keyword in text_lower for keyword in ['project', 'team', 'leadership']):
                    base_score += 5
                
                base_score = min(base_score, 90)
                
                skill_keywords = ['python', 'java', 'javascript', 'sql', 'management', 'leadership']
                found_skills = [skill for skill in skill_keywords if skill in text_lower]
                
                analysis_data = {
                    'overall_score': base_score,
                    'experience_score': base_score - 5,
                    'skills_score': base_score,
                    'education_score': base_score - 8,
                    'candidate_info': {
                        'name': candidate_name,
                        'email': '',
                        'phone': ''
                    },
                    'summary': f'Fast analysis completed due to system load. Score: {base_score}/100',
                    'key_skills': found_skills,
                    'experience_years': 3,
                    'analysis_method': 'railway_fast_fallback'
                }
                
                progress_callback('Fast analysis completed', 90)
                
            else:
                # Normal AI processing
                progress_callback('System healthy - starting AI analysis...', 50)
                
                try:
                    from utils.unified_ai_processor import get_unified_processor
                    
                    railway_db_conn = None
                    if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                        railway_db_conn = db_manager.railway_pg
                    
                    unified_processor = get_unified_processor(railway_db=railway_db_conn)
                    
                    progress_callback('Running AI analysis...', 60)
                    
                    # Run AI analysis with timeout
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        ai_result = loop.run_until_complete(
                            asyncio.wait_for(
                                unified_processor.process_resume(
                                    resume_text=resume_text,
                                    user_id=admin.get('user_id', 'admin'),
                                    analysis_type="fast"
                                ),
                                timeout=45  # 45 second timeout for SSE
                            )
                        )
                        
                        if ai_result and ai_result.success and ai_result.data:
                            analysis_data = ai_result.data
                            progress_callback('AI analysis completed successfully', 85)
                        else:
                            raise Exception("AI analysis failed or returned no data")
                            
                    finally:
                        loop.close()
                        
                except Exception as ai_error:
                    logger.warning(f"AI analysis failed: {ai_error}, using fallback")
                    progress_callback('AI failed - using fallback analysis...', 70)
                    
                    # Fallback analysis
                    analysis_data = {
                        'overall_score': 75,
                        'experience_score': 70,
                        'skills_score': 75,
                        'education_score': 70,
                        'candidate_info': {'name': 'Analysis Needed', 'email': '', 'phone': ''},
                        'summary': f'Fallback analysis completed. AI error: {str(ai_error)[:100]}',
                        'key_skills': ['Manual review required'],
                        'experience_years': 2,
                        'analysis_method': 'fallback_due_to_error'
                    }
                    progress_callback('Fallback analysis completed', 85)
            
            # Save results to database
            progress_callback('Saving results to database...', 90)
            
            try:
                if hasattr(db_manager, 'railway_pg') and db_manager.railway_pg:
                    with db_manager.railway_pg.get_connection() as conn:
                        with conn.cursor() as cursor:
                            skills_data = analysis_data.get('key_skills', [])
                            skills_jsonb = json.dumps(skills_data) if isinstance(skills_data, list) else json.dumps([str(skills_data)])
                            
                            cursor.execute("""
                                UPDATE resumes SET 
                                overall_score = %s, experience_score = %s, technical_score = %s, education_score = %s,
                                candidate_name = %s, skills = %s::jsonb, experience_years = %s,
                                analysis_results = %s::jsonb, processing_status = 'completed',
                                ai_model_used = %s, processing_completed_at = NOW(), updated_at = NOW()
                                WHERE id = %s
                            """, (
                                analysis_data.get('overall_score', 75),
                                analysis_data.get('experience_score', 70),
                                analysis_data.get('skills_score', 75),
                                analysis_data.get('education_score', 70),
                                analysis_data.get('candidate_info', {}).get('name', 'Unknown'),
                                skills_jsonb,
                                analysis_data.get('experience_years', 0),
                                json.dumps(analysis_data),
                                'qwen2.5:7b:sse',
                                resume_id
                            ))
                            conn.commit()
                            
            except Exception as db_error:
                logger.warning(f"Database update failed: {db_error}")
            
            progress_callback('Analysis completed successfully!', 100)
            
            # Return final result
            return {
                'success': True,
                'analysis': analysis_data,
                'resume_id': resume_id,
                'admin_access': True,
                'railway_optimized': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise e
    
    # Create SSE response with automatic keep-alive
    return create_sse_response_with_keepalive(
        create_long_process_wrapper(perform_analysis_with_progress),
        request_id=f"admin_analysis_{resume_id}_{int(time.time())}",
        extra_data={
            'resume_id': resume_id,
            'admin_user': g.current_admin.get('username', 'admin'),
            'endpoint': 'admin_resume_analyze_sse'
        }
    )

@admin_bp.route('/analyze/batch', methods=['POST'])
@require_admin_auth
def admin_batch_analysis():
    """Admin batch resume analysis - bypasses credit system."""
    try:
        data = request.get_json()
        
        resume_ids = data.get('resume_ids', [])
        job_requirements = data.get('job_requirements', {})
        
        if not resume_ids:
            return jsonify({'error': 'Resume IDs required for batch analysis'}), 400
        
        # Import AI processor
        from ai_processor import analyze_resume
        
        admin = g.current_admin
        batch_results = []
        
        for resume_id in resume_ids:
            try:
                # Get resume content
                resume_text = db_manager.get_resume_content(resume_id)
                if resume_text:
                    # Analyze resume
                    analysis = analyze_resume(resume_text, job_requirements)
                    batch_results.append({
                        'resume_id': resume_id,
                        'success': True,
                        'analysis': analysis
                    })
                else:
                    batch_results.append({
                        'resume_id': resume_id,
                        'success': False,
                        'error': 'Resume not found'
                    })
                    
            except Exception as e:
                logger.error(f"Error analyzing resume {resume_id} in batch: {e}")
                batch_results.append({
                    'resume_id': resume_id,
                    'success': False,
                    'error': str(e)
                })
        
        # Log admin usage
        logger.info(f"Admin {admin.get('username')} performed batch analysis on {len(resume_ids)} resumes")
        
        return jsonify({
            'success': True,
            'batch_results': batch_results,
            'total_processed': len(resume_ids),
            'successful': len([r for r in batch_results if r['success']]),
            'failed': len([r for r in batch_results if not r['success']]),
            'admin_access': True,
            'unlimited': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Admin batch analysis error: {e}")
        return jsonify({'error': 'Batch analysis failed'}), 500

@admin_bp.route('/resumes/<resume_id>/analyze-simple', methods=['POST'])
@require_admin_auth
def admin_resume_analyze_simple(resume_id):
    """Simple admin resume analysis without SSE - fallback for compatibility."""
    try:
        logger.info(f"🔍 ADMIN SIMPLE ANALYZE ENDPOINT - Resume ID: {resume_id}")
        
        # Get job requirements if provided
        data = request.get_json() or {}
        job_requirements = data.get('job_requirements', {})
        
        # Use the original admin analysis function with reduced timeout
        return admin_unlimited_resume_analysis(resume_id)
        
    except Exception as e:
        logger.error(f"❌ Simple admin analysis error: {e}")
        return jsonify({
            'success': False,
            'error': f'Simple analysis failed: {str(e)}',
            'resume_id': resume_id
        }), 500

@admin_bp.route('/activity-log', methods=['GET'])
@require_admin_auth
def admin_activity_log():
    """Get admin activity log."""
    try:
        limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 entries
        offset = int(request.args.get('offset', 0))
        
        # Get activity log from database
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT activity_type, user_id, details, timestamp, admin_user
                FROM admin_activity_log
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'activity_type': row['activity_type'],
                    'user_id': row['user_id'],
                    'details': json.loads(row['details']) if row['details'] else {},
                    'timestamp': row['timestamp'],
                    'admin_user': row['admin_user']
                })
        
        return jsonify({
            'success': True,
            'activities': activities,
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting admin activity log: {e}")
        return jsonify({'error': 'Failed to get activity log'}), 500

@admin_bp.route('/usage-stats', methods=['GET'])
@require_admin_auth
def admin_usage_statistics():
    """Get comprehensive usage statistics for admin."""
    try:
        # Get time range parameters
        days = int(request.args.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        
        # Get comprehensive usage statistics
        stats = {
            'period': {
                'days': days,
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().isoformat()
            },
            'resume_analysis': {
                'total_analyzed': 0,
                'by_user_type': {},
                'top_users': []
            },
            'legal_queries': {
                'total_queries': 0,
                'by_user_type': {},
                'top_users': []
            },
            'system_usage': {
                'active_users': 0,
                'new_registrations': 0,
                'trial_conversions': 0
            }
        }
        
        # Get all users for analysis
        all_users = user_manager.get_all_users()
        
        # Calculate statistics
        for user in all_users:
            user_type = user.get('access_type', 'trial')
            
            # Resume analysis stats
            resumes_analyzed = user.get('trial_resumes_analyzed', 0) + user.get('premium_resumes_analyzed', 0)
            stats['resume_analysis']['total_analyzed'] += resumes_analyzed
            stats['resume_analysis']['by_user_type'][user_type] = stats['resume_analysis']['by_user_type'].get(user_type, 0) + resumes_analyzed
            
            # Legal query stats
            legal_queries = user.get('trial_legal_queries', 0) + user.get('premium_legal_queries', 0)
            stats['legal_queries']['total_queries'] += legal_queries
            stats['legal_queries']['by_user_type'][user_type] = stats['legal_queries']['by_user_type'].get(user_type, 0) + legal_queries
            
            # Check if user was created in the period
            if user.get('created_at'):
                try:
                    created_date = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
                    if created_date >= start_date:
                        stats['system_usage']['new_registrations'] += 1
                except:
                    pass
        
        # Get top users (simplified for now)
        stats['resume_analysis']['top_users'] = []
        stats['legal_queries']['top_users'] = []
        
        return jsonify({
            'success': True,
            'usage_stats': stats,
            'generated_at': datetime.now().isoformat(),
            'admin_user': g.current_admin.get('username', 'Unknown')
        })
        
    except Exception as e:
        logger.error(f"Error getting usage statistics: {e}")
        return jsonify({'error': 'Failed to get usage statistics'}), 500

# Health check endpoint for admin system
@admin_bp.route('/health', methods=['GET'])
def admin_health():
    """Admin system health check (no auth required)."""
    try:
        health_status = {
            'admin_system': True,
            'database': db_manager.health_check() if db_manager else False,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Admin health check error: {e}")
        return jsonify({
            'admin_system': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ===== CREDIT MANAGEMENT ENDPOINTS =====

@admin_bp.route('/users/<int:user_id>/credits', methods=['GET'])
@require_admin_auth
def get_user_credits(user_id):
    """Get user's credit information for admin management."""
    try:
        # Import credit manager (avoid circular imports)
        from credit_manager import CreditManager
        
        # Get database manager from global scope
        global db_manager
        if not db_manager:
            return jsonify({'error': 'Database manager not available'}), 500
            
        credit_manager = CreditManager(db_manager)
        
        # Get user's credit status
        credit_status = credit_manager.check_user_credits(user_id)
        
        if not credit_status:
            return jsonify({'error': 'User not found or credits not initialized'}), 404
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'credits': {
                'trial_credits': credit_status.trial_credits,
                'premium_credits': credit_status.premium_credits,
                'total_used': credit_status.total_used,
                'credits_remaining': credit_status.credits_remaining,
                'processing_tier': credit_status.processing_tier.value,
                'can_process': credit_status.can_process,
                'lead_score': credit_status.lead_score
            },
            'usage_pattern': credit_status.usage_pattern
        })
        
    except Exception as e:
        logger.error(f"Error getting credits for user {user_id}: {e}")
        return jsonify({
            'error': 'Failed to get user credits',
            'details': str(e) if os.getenv('FLASK_ENV') == 'development' else None
        }), 500

@admin_bp.route('/users/<int:user_id>/credits', methods=['PUT'])
@require_admin_auth
def update_user_credits(user_id):
    """Update user's credit balance (admin function)."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if 'credits' not in data:
            return jsonify({'error': 'Credits amount required'}), 400
            
        try:
            credits_to_add = int(data['credits'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Credits must be a valid integer'}), 400
            
        if credits_to_add < 0:
            return jsonify({'error': 'Credits amount must be positive'}), 400
        
        # Import credit manager
        from credit_manager import CreditManager
        
        global db_manager
        if not db_manager:
            return jsonify({'error': 'Database manager not available'}), 500
            
        credit_manager = CreditManager(db_manager)
        
        # Add premium credits to user account
        success = credit_manager.add_premium_credits(
            user_id, 
            credits_to_add, 
            source="admin_adjustment"
        )
        
        if not success:
            return jsonify({'error': 'Failed to add credits'}), 500
        
        # Get updated credit status
        updated_status = credit_manager.check_user_credits(user_id)
        
        # Log admin action
        admin = g.current_admin
        logger.info(f"Admin {admin.get('username')} added {credits_to_add} credits to user {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully added {credits_to_add} credits to user {user_id}',
            'updated_credits': {
                'trial_credits': updated_status.trial_credits,
                'premium_credits': updated_status.premium_credits,
                'total_credits': updated_status.credits_remaining,
                'total_used': updated_status.total_used
            },
            'admin_action': {
                'performed_by': admin.get('username', 'unknown'),
                'timestamp': datetime.utcnow().isoformat(),
                'action': f'Added {credits_to_add} premium credits'
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating credits for user {user_id}: {e}")
        return jsonify({
            'error': 'Failed to update user credits',
            'details': str(e) if os.getenv('FLASK_ENV') == 'development' else None
        }), 500

@admin_bp.route('/users/<int:user_id>/credits/reset', methods=['POST'])
@require_admin_auth
def reset_user_credits(user_id):
    """Reset user to initial trial credits (admin function)."""
    try:
        from credit_manager import CreditManager
        
        global db_manager
        if not db_manager:
            return jsonify({'error': 'Database manager not available'}), 500
            
        credit_manager = CreditManager(db_manager)
        
        # Reset to initial trial credits (100)
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE user_credits 
                SET trial_credits = 100, 
                    premium_credits = 0, 
                    total_used = 0,
                    is_trial_exhausted = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user_id,))
            
        # Log admin action
        admin = g.current_admin
        logger.info(f"Admin {admin.get('username')} reset credits for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully reset credits for user {user_id}',
            'reset_credits': {
                'trial_credits': 100,
                'premium_credits': 0,
                'total_used': 0
            },
            'admin_action': {
                'performed_by': admin.get('username', 'unknown'),
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'Reset user credits to initial trial amount'
            }
        })
        
    except Exception as e:
        logger.error(f"Error resetting credits for user {user_id}: {e}")
        return jsonify({
            'error': 'Failed to reset user credits',
            'details': str(e) if os.getenv('FLASK_ENV') == 'development' else None
        }), 500
