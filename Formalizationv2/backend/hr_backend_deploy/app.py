"""
Enhanced Resume Screening Backend for Railway Deployment
Multi-provider AI, market-based scoring, email templates, and comprehensive admin features
"""

import os
import json
import logging
import asyncio
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, List

# Flask imports
from flask import Flask, request, jsonify, g, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

# Enhanced local imports
from config import config
from supabase_manager import supabase_manager
from file_processor import file_processor
from enhanced_ai_analyzer import ai_analyzer
from email_templates import email_template_manager, EmailType
from admin_manager import admin_manager
from auth_utils import (
    auth_manager, require_auth, require_admin, require_user, 
    optional_auth, check_trial_limits, get_current_user_context,

# HR Legal System imports
try:
    from hr_legal import (
        EnhancedRAGEngine, AgenticRAGConfig, LegalQueryContext, 
        LegalResponse, ResponseLength, ResponseStyle, DetailLevel, AudienceLevel
    )
    HR_LEGAL_AVAILABLE = True
except ImportError as e:
    HR_LEGAL_AVAILABLE = False
    print(f"HR Legal dependencies not available: {e}")
    print("Install with: pip install sentence-transformers faiss-cpu")
    validate_session_token
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Enhanced CORS configuration
CORS(app, origins=config.ALLOWED_ORIGINS)

# Rate limiting with enhanced configuration
if config.ENABLE_RATE_LIMITING:
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
else:
    limiter = None

# =====================================================================
# HR LEGAL SYSTEM INITIALIZATION
# =====================================================================

hr_legal_engine = None
hr_legal_error = None

def initialize_hr_legal_system():
    """Initialize the HR Legal RAG system."""
    global hr_legal_engine, hr_legal_error
    
    if not HR_LEGAL_AVAILABLE:
        hr_legal_error = "HR Legal dependencies not available"
        return False
    
    try:
        print("🔧 Initializing HR Legal System...")
        
        # Initialize with multi-provider AI support
        hr_legal_engine = EnhancedRAGEngine(
            ai_provider=ai_analyzer.multi_provider_ai,
            vector_db_path="hr_legal/vector_db",
            hrlaw_path="HRlaw",
            auto_initialize=True,
            enable_smart_routing=True
        )
        
        if hr_legal_engine and hr_legal_engine.is_initialized:
            print("✅ HR Legal System initialized successfully")
            return True
        else:
            error_msg = getattr(hr_legal_engine, 'initialization_error', 'Unknown initialization error')
            hr_legal_error = f"Initialization failed: {error_msg}"
            print(f"❌ HR Legal initialization failed: {hr_legal_error}")
            return False
            
    except Exception as e:
        hr_legal_error = str(e)
        print(f"❌ HR Legal initialization error: {e}")
        return False

# Initialize HR Legal system
if HR_LEGAL_AVAILABLE:
    initialize_hr_legal_system()

# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================

def async_route(f):
    """Decorator to handle async routes in Flask"""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    wrapper.__name__ = f.__name__
    return wrapper

def create_error_response(message: str, status_code: int = 400, details: dict = None) -> tuple:
    """Create standardized error response"""
    response = {
        'error': message,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    if details:
        response.update(details)
    return jsonify(response), status_code

def create_success_response(data: dict, message: str = None) -> dict:
    """Create standardized success response"""
    response = {
        'success': True,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    if message:
        response['message'] = message
    response.update(data)
    return jsonify(response)

# =====================================================================
# AUTHENTICATION ENDPOINTS
# =====================================================================

@app.route('/api/auth/admin-login', methods=['POST'])
@async_route
@limiter.limit("5 per minute")
async def admin_login():
    """Admin authentication endpoint"""
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return create_error_response('Username and password required', 400)
        
        # Verify admin credentials
        result = await supabase_manager.verify_admin_credentials(
            data['username'], 
            data['password']
        )
        
        if not result['success']:
            return create_error_response(result['error'], 401)
        
        # Generate admin token
        token = auth_manager.generate_token(
            user_id=f"admin_{data['username']}",
            email=f"{data['username']}@admin.local",
            user_type='admin'
        )
        
        return create_success_response({
            'token': token,
            'user': {
                'username': result['username'],
                'role': result['role'],
                'user_type': 'admin'
            }
        })
        
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        return create_error_response('Authentication failed', 500)

@app.route('/api/auth/create-user', methods=['POST'])
@async_route
@require_admin()
async def create_user():
    """Create new user account (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'name', 'password']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', 400)
        
        # Create user
        result = await supabase_manager.create_user(
            email=data['email'],
            password=data['password'],
            name=data['name'],
            access_type=data.get('access_type', 'trial')
        )
        
        if not result['success']:
            return create_error_response(result['error'], 400)
        
        return create_success_response({
            'user': {
                'id': result['user'].id,
                'email': result['user'].email,
                'profile': result['profile']
            }
        }, 'User created successfully')
        
    except Exception as e:
        logger.error(f"Create user error: {str(e)}")
        return create_error_response('Failed to create user', 500)

@app.route('/api/auth/user-login', methods=['POST'])
@async_route
@limiter.limit("10 per minute")
async def user_login():
    """User authentication endpoint"""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return create_error_response('Email and password required', 400)
        
        # Authenticate user
        result = await supabase_manager.authenticate_user(
            data['email'], 
            data['password']
        )
        
        if not result['success']:
            return create_error_response(result['error'], 401)
        
        # Get user profile
        profile = await supabase_manager.get_user_profile(result['user'].id)
        if not profile:
            return create_error_response('User profile not found', 404)
        
        # Generate token
        token = auth_manager.generate_token(
            user_id=result['user'].id,
            email=result['user'].email,
            user_type='user'
        )
        
        # Get trial status
        trial_status = await supabase_manager.get_trial_status(result['user'].id)
        
        return create_success_response({
            'token': token,
            'user': {
                'id': result['user'].id,
                'email': result['user'].email,
                'profile': profile
            },
            'trial_status': trial_status
        })
        
    except Exception as e:
        logger.error(f"User login error: {str(e)}")
        return create_error_response('Authentication failed', 500)

@app.route('/api/auth/session', methods=['GET'])
@async_route
@require_auth()
async def validate_session():
    """Validate session token"""
    try:
        user_context = await get_current_user_context()
        
        return create_success_response({
            'valid': True,
            'user': user_context
        })
        
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return create_error_response('Session validation failed', 500)

@app.route('/api/auth/logout', methods=['POST'])
@async_route
@require_auth()
async def logout():
    """User logout endpoint"""
    try:
        # Log logout activity
        if g.current_user and g.current_user.get('user_type') == 'user':
            await supabase_manager.log_user_activity(
                g.current_user['user_id'],
                'logout',
                'User logged out'
            )
        
        return create_success_response({}, 'Logout successful')
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return create_error_response('Logout failed', 500)

# =====================================================================
# RESUME PROCESSING ENDPOINTS
# =====================================================================

@app.route('/api/upload', methods=['POST'])
@async_route
@require_user()
@check_trial_limits('resume_analysis')
@limiter.limit("10 per hour")
async def upload_resumes():
    """Resume upload and processing endpoint"""
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return create_error_response('No files uploaded', 400)
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return create_error_response('No files selected', 400)
        
        results = []
        
        for file in files:
            if file.filename == '':
                continue
                
            try:
                # Read file content
                file_content = file.read()
                filename = secure_filename(file.filename)
                
                # Process file
                processing_result = file_processor.process_file(file_content, filename)
                
                if not processing_result['valid']:
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': processing_result['error']
                    })
                    continue
                
                # Analyze with AI
                ai_result = await ai_analyzer.analyze_resume(processing_result['content'])
                
                if not ai_result['success']:
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': f"AI analysis failed: {ai_result['error']}"
                    })
                    continue
                
                # Store in database
                resume_data = {
                    'filename': filename,
                    'content': processing_result['content'],
                    'analysis': ai_result['analysis'],
                    'file_size': processing_result['file_size'],
                    'file_type': processing_result['file_type']
                }
                
                stored_resume = await supabase_manager.store_resume(
                    g.current_user['user_id'],
                    resume_data
                )
                
                if stored_resume:
                    # Track usage for trial users
                    usage_result = await supabase_manager.track_resume_usage(g.current_user['user_id'])
                    
                    # Log activity
                    await supabase_manager.log_user_activity(
                        g.current_user['user_id'],
                        'resume_upload',
                        f'Successfully processed resume: {filename}'
                    )
                    
                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'id': stored_resume['id'],
                        'analysis_summary': {
                            'overall_score': ai_result['analysis']['scores']['overall_score'],
                            'name': ai_result['analysis']['basic_info']['name']
                        }
                    })
                else:
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': 'Failed to store resume'
                    })
                    
            except Exception as e:
                logger.error(f"File processing error for {filename}: {str(e)}")
                results.append({
                    'filename': filename or 'unknown',
                    'status': 'error',
                    'error': str(e)
                })
        
        return create_success_response({'results': results})
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return create_error_response('Upload failed', 500)

@app.route('/api/resumes', methods=['GET'])
@async_route
@require_user()
async def get_resumes():
    """Get all resumes for authenticated user"""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        
        resumes = await supabase_manager.get_user_resumes(g.current_user['user_id'], limit)
        
        # Parse AI analysis for each resume
        processed_resumes = []
        for resume in resumes:
            try:
                analysis = json.loads(resume.get('ai_analysis', '{}'))
                processed_resume = {
                    'id': resume['id'],
                    'filename': resume['filename'],
                    'created_at': resume['created_at'],
                    'status': resume['status'],
                    'file_size': resume.get('file_size', 0),
                    'file_type': resume.get('file_type', ''),
                    'summary': {
                        'name': analysis.get('basic_info', {}).get('name', 'Unknown'),
                        'overall_score': analysis.get('scores', {}).get('overall_score', 0),
                        'skills_count': len(analysis.get('skills', [])),
                        'experience_count': len(analysis.get('experience', []))
                    }
                }
                processed_resumes.append(processed_resume)
            except Exception as e:
                logger.error(f"Error processing resume {resume['id']}: {str(e)}")
                continue
        
        return create_success_response({'resumes': processed_resumes})
        
    except Exception as e:
        logger.error(f"Get resumes error: {str(e)}")
        return create_error_response('Failed to fetch resumes', 500)

@app.route('/api/resumes/<int:resume_id>', methods=['GET'])
@async_route
@require_user()
async def get_resume_details(resume_id: int):
    """Get detailed resume analysis"""
    try:
        resume = await supabase_manager.get_resume_by_id(resume_id, g.current_user['user_id'])
        
        if not resume:
            return create_error_response('Resume not found', 404)
        
        # Parse AI analysis
        try:
            analysis = json.loads(resume.get('ai_analysis', '{}'))
        except:
            analysis = {}
        
        detailed_resume = {
            'id': resume['id'],
            'filename': resume['filename'],
            'created_at': resume['created_at'],
            'status': resume['status'],
            'file_size': resume.get('file_size', 0),
            'file_type': resume.get('file_type', ''),
            'processed_content': resume.get('processed_content', ''),
            'analysis': analysis
        }
        
        return create_success_response({'resume': detailed_resume})
        
    except Exception as e:
        logger.error(f"Get resume details error: {str(e)}")
        return create_error_response('Failed to fetch resume details', 500)

@app.route('/api/resumes/<int:resume_id>/markdown', methods=['GET'])
@async_route
@require_user()
async def get_resume_markdown(resume_id: int):
    """Get resume analysis in Markdown format"""
    try:
        resume = await supabase_manager.get_resume_by_id(resume_id, g.current_user['user_id'])
        
        if not resume:
            return create_error_response('Resume not found', 404)
        
        # Parse AI analysis
        try:
            analysis = json.loads(resume.get('ai_analysis', '{}'))
        except:
            return create_error_response('Invalid resume analysis data', 500)
        
        # Generate Markdown
        markdown = generate_resume_markdown(analysis, resume['filename'])
        
        return create_success_response({'markdown': markdown})
        
    except Exception as e:
        logger.error(f"Get resume markdown error: {str(e)}")
        return create_error_response('Failed to generate markdown', 500)

def generate_resume_markdown(analysis: dict, filename: str) -> str:
    """Generate Markdown representation of resume analysis"""
    basic_info = analysis.get('basic_info', {})
    scores = analysis.get('scores', {})
    
    markdown = f"""# Resume Analysis: {filename}

## Basic Information
- **Name:** {basic_info.get('name', 'N/A')}
- **Email:** {basic_info.get('email', 'N/A')}
- **Phone:** {basic_info.get('phone', 'N/A')}
- **Location:** {basic_info.get('location', 'N/A')}

## Summary
{analysis.get('summary', 'No summary available')}

## Scores
- **Overall Score:** {scores.get('overall_score', 0)}/100
- **Technical Score:** {scores.get('technical_score', 0)}/100
- **Experience Score:** {scores.get('experience_score', 0)}/100
- **Education Score:** {scores.get('education_score', 0)}/100
- **Skills Match:** {scores.get('skills_match', 0)}/100

## Skills
{chr(10).join([f'- {skill}' for skill in analysis.get('skills', [])]) or '- No skills identified'}

## Experience
"""
    
    for exp in analysis.get('experience', []):
        markdown += f"""
### {exp.get('title', 'Unknown Position')} at {exp.get('company', 'Unknown Company')}
**Duration:** {exp.get('duration', 'Unknown')}

{exp.get('description', 'No description available')}
"""
    
    markdown += "\n## Education\n"
    for edu in analysis.get('education', []):
        markdown += f"- **{edu.get('degree', 'Unknown Degree')}** from {edu.get('institution', 'Unknown Institution')} ({edu.get('year', 'Unknown Year')})\n"
    
    if analysis.get('certifications'):
        markdown += "\n## Certifications\n"
        markdown += chr(10).join([f'- {cert}' for cert in analysis.get('certifications', [])])
    
    if analysis.get('projects'):
        markdown += "\n## Projects\n"
        for project in analysis.get('projects', []):
            markdown += f"""
### {project.get('name', 'Unknown Project')}
{project.get('description', 'No description available')}

**Technologies:** {', '.join(project.get('technologies', []))}
"""
    
    analysis_section = analysis.get('analysis', {})
    if analysis_section:
        markdown += f"""
## Analysis

### Strengths
{chr(10).join([f'- {strength}' for strength in analysis_section.get('strengths', [])]) or '- No strengths identified'}

### Areas for Improvement
{chr(10).join([f'- {weakness}' for weakness in analysis_section.get('weaknesses', [])]) or '- No areas identified'}

### Recommendations
{chr(10).join([f'- {rec}' for rec in analysis_section.get('recommendations', [])]) or '- No recommendations available'}
"""
    
    return markdown

@app.route('/api/export', methods=['GET'])
@async_route
@require_user()
async def export_resumes():
    """Export resumes to CSV (full users only)"""
    try:
        # Check if user has full access
        profile = g.current_user.get('profile', {})
        if profile.get('access_type') == 'trial':
            return create_error_response('Export feature requires full access', 403)
        
        resumes = await supabase_manager.get_user_resumes(g.current_user['user_id'], 1000)
        
        if not resumes:
            return create_error_response('No resumes to export', 404)
        
        # Generate CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Filename', 'Name', 'Email', 'Phone', 'Overall Score',
            'Technical Score', 'Skills', 'Experience Count', 'Created At'
        ])
        
        # Write data
        for resume in resumes:
            try:
                analysis = json.loads(resume.get('ai_analysis', '{}'))
                basic_info = analysis.get('basic_info', {})
                scores = analysis.get('scores', {})
                
                writer.writerow([
                    resume['id'],
                    resume['filename'],
                    basic_info.get('name', ''),
                    basic_info.get('email', ''),
                    basic_info.get('phone', ''),
                    scores.get('overall_score', 0),
                    scores.get('technical_score', 0),
                    ', '.join(analysis.get('skills', [])),
                    len(analysis.get('experience', [])),
                    resume['created_at']
                ])
            except Exception as e:
                logger.error(f"Error exporting resume {resume['id']}: {str(e)}")
                continue
        
        # Create file response
        output.seek(0)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as temp_file:
            temp_file.write(output.getvalue())
            temp_file_path = temp_file.name
        
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=f'resumes_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return create_error_response('Export failed', 500)

@app.route('/api/stats', methods=['GET'])
@async_route
@require_user()
async def get_statistics():
    """Get user statistics"""
    try:
        stats = await supabase_manager.get_user_statistics(g.current_user['user_id'])
        
        # Add trial status for trial users
        profile = g.current_user.get('profile', {})
        if profile.get('access_type') == 'trial':
            trial_status = await supabase_manager.get_trial_status(g.current_user['user_id'])
            stats['trial_status'] = trial_status
        
        return create_success_response({'stats': stats})
        
    except Exception as e:
        logger.error(f"Statistics error: {str(e)}")
        return create_error_response('Failed to fetch statistics', 500)

@app.route('/api/clear', methods=['DELETE'])
@async_route
@require_user()
@limiter.limit("3 per hour")
async def clear_resumes():
    """Clear all resumes for user"""
    try:
        deleted_count = await supabase_manager.delete_user_resumes(g.current_user['user_id'])
        
        # Log activity
        await supabase_manager.log_user_activity(
            g.current_user['user_id'],
            'clear_resumes',
            f'Deleted {deleted_count} resumes'
        )
        
        return create_success_response({
            'deleted_count': deleted_count
        }, f'Cleared {deleted_count} resumes')
        
    except Exception as e:
        logger.error(f"Clear resumes error: {str(e)}")
        return create_error_response('Failed to clear resumes', 500)

# =====================================================================
# TRIAL MANAGEMENT ENDPOINTS
# =====================================================================

@app.route('/api/trial/status', methods=['GET'])
@async_route
@require_user()
async def get_trial_status():
    """Get trial status for user"""
    try:
        trial_status = await supabase_manager.get_trial_status(g.current_user['user_id'])
        return create_success_response(trial_status)
        
    except Exception as e:
        logger.error(f"Trial status error: {str(e)}")
        return create_error_response('Failed to fetch trial status', 500)

@app.route('/api/trial/upgrade-info', methods=['GET'])
@async_route
@require_user()
async def get_upgrade_info():
    """Get upgrade information"""
    try:
        upgrade_info = {
            'upgrade_options': [
                {
                    'plan': 'Professional',
                    'price': '$29/month',
                    'features': [
                        'Unlimited resume analysis',
                        'Advanced AI insights',
                        'Export functionality',
                        'Priority support'
                    ]
                },
                {
                    'plan': 'Enterprise',
                    'price': '$99/month',
                    'features': [
                        'Everything in Professional',
                        'HR Legal assistance',
                        'Custom integrations',
                        'Dedicated support'
                    ]
                }
            ],
            'contact_info': {
                'email': 'support@hrtool.com',
                'phone': '+1-555-0123'
            }
        }
        
        return create_success_response(upgrade_info)
        
    except Exception as e:
        logger.error(f"Upgrade info error: {str(e)}")
        return create_error_response('Failed to fetch upgrade info', 500)

# =====================================================================
# HR LEGAL ENDPOINTS - Enhanced Agentic RAG System
# =====================================================================

@app.route('/api/legal/status', methods=['GET'])
def get_legal_system_status():
    """Get the comprehensive status of the HR Legal system."""
    try:
        if not HR_LEGAL_AVAILABLE:
            return jsonify({
                "available": False,
                "error": "HR Legal dependencies not installed",
                "install_command": "pip install sentence-transformers faiss-cpu",
                "status": "dependencies_missing"
            }), 503
            
        if not hr_legal_engine:
            return jsonify({
                "available": False,
                "error": hr_legal_error or "HR Legal engine not initialized",
                "status": "engine_not_initialized"
            }), 503
        
        # Get comprehensive system status
        try:
            status = hr_legal_engine.get_system_status()
            return jsonify({
                "available": True,
                "status": "operational",
                "engine_status": status,
                "capabilities": [
                    "Legal query processing",
                    "Compliance checking", 
                    "Document generation",
                    "Multi-step reasoning",
                    "Smart AI routing"
                ]
            })
        except Exception as e:
            return jsonify({
                "available": False,
                "error": f"Status check failed: {str(e)}",
                "status": "error"
            }), 500
            
    except Exception as e:
        return jsonify({
            "available": False,
            "error": f"Unexpected error: {str(e)}",
            "status": "error"
        }), 500

@app.route('/api/legal/query', methods=['POST'])
@require_user()
@limiter.limit("20 per hour") if limiter else lambda f: f
def legal_query():
    """Process a legal query with full customization."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
            
        data = request.get_json()
        query = data.get('query', '')
        
        if not query.strip():
            return jsonify({"error": "Query cannot be empty"}), 400
        
        # Create query configuration
        config = AgenticRAGConfig(
            response_length=ResponseLength(data.get('response_length', 'medium')),
            response_style=ResponseStyle(data.get('response_style', 'professional')),
            detail_level=DetailLevel(data.get('detail_level', 'balanced')),
            audience_level=AudienceLevel(data.get('audience_level', 'intermediate')),
            retrieval_depth=data.get('retrieval_depth', 7),
            similarity_threshold=data.get('similarity_threshold', 0.65),
            include_citations=data.get('include_citations', True),
            include_confidence=data.get('include_confidence', True),
            show_reasoning_chain=data.get('show_reasoning_chain', True)
        )
        
        # Create query context
        context = LegalQueryContext(
            query=query,
            query_type=data.get('query_type', 'general'),
            user_role=data.get('user_role', 'hr_professional'),
            urgency=data.get('urgency', 'normal')
        )
        
        # Process query
        response = hr_legal_engine.query(context, config)
        
        if response:
            return jsonify({
                "success": True,
                "response": response.to_dict()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate response"
            }), 500
            
    except Exception as e:
        logger.error(f"Legal query error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Query processing failed: {str(e)}"
        }), 500

@app.route('/api/legal/compliance-check', methods=['POST'])
@require_user()
@limiter.limit("15 per hour") if limiter else lambda f: f
def compliance_check():
    """Check content for legal compliance."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
            
        data = request.get_json()
        content = data.get('content', '')
        content_type = data.get('content_type', 'policy')
        
        if not content.strip():
            return jsonify({"error": "Content cannot be empty"}), 400
        
        # Create compliance check query
        query = f"Please perform a comprehensive legal compliance analysis of the following {content_type}:\\n\\n{content}\\n\\nProvide specific recommendations for compliance improvements."
        
        config = AgenticRAGConfig(
            response_length=ResponseLength.DETAILED,
            response_style=ResponseStyle.LEGAL,
            detail_level=DetailLevel.COMPREHENSIVE,
            retrieval_depth=8,
            similarity_threshold=0.6,
            include_legal_disclaimers=True,
            include_risk_assessment=True
        )
        
        context = LegalQueryContext(
            query=query,
            query_type="compliance_check",
            user_role=data.get('user_role', 'hr_professional'),
            urgency=data.get('urgency', 'normal')
        )
        
        response = hr_legal_engine.query(context, config)
        
        if response:
            return jsonify({
                "success": True,
                "compliance_analysis": response.to_dict(),
                "content_type": content_type
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate compliance analysis"
            }), 500
            
    except Exception as e:
        logger.error(f"Compliance check error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Compliance check failed: {str(e)}"
        }), 500

@app.route('/api/legal/generate-document', methods=['POST'])
@require_user()
@limiter.limit("10 per hour") if limiter else lambda f: f
def generate_document():
    """Generate legal documents using AI."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
            
        data = request.get_json()
        document_type = data.get('document_type', '')
        requirements = data.get('requirements', '')
        
        if not document_type or not requirements:
            return jsonify({
                "error": "Document type and requirements are required"
            }), 400
        
        # Create document generation query
        query = f"Generate a {document_type} document with the following requirements:\\n\\n{requirements}\\n\\nEnsure the document is legally compliant and professionally formatted."
        
        config = AgenticRAGConfig(
            response_length=ResponseLength.DETAILED,
            response_style=ResponseStyle.LEGAL,
            detail_level=DetailLevel.COMPREHENSIVE,
            retrieval_depth=6,
            similarity_threshold=0.65,
            include_legal_disclaimers=True,
            structured_output=True
        )
        
        context = LegalQueryContext(
            query=query,
            query_type="document_generation",
            user_role=data.get('user_role', 'hr_professional'),
            urgency=data.get('urgency', 'normal')
        )
        
        response = hr_legal_engine.query(context, config)
        
        if response:
            return jsonify({
                "success": True,
                "document": response.to_dict(),
                "document_type": document_type
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate document"
            }), 500
            
    except Exception as e:
        logger.error(f"Document generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Document generation failed: {str(e)}"
        }), 500

@app.route('/api/legal/stats', methods=['GET'])
@require_admin()
def get_legal_stats():
    """Get HR Legal system statistics."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
        
        # Get comprehensive system statistics
        status = hr_legal_engine.get_system_status()
        
        legal_stats = {
            "success": True,
            "system_status": status,
            "engine_initialized": hr_legal_engine is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(legal_stats)
        
    except Exception as e:
        logger.error(f"Legal stats error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Stats retrieval failed: {str(e)}"
        }), 500

@app.route('/api/hr-legal/query', methods=['POST'])
@async_route
@require_user()
@limiter.limit("20 per hour") if limiter else lambda f: f
async def hr_legal_query():
    """Legacy HR Legal query endpoint (backward compatibility)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('query'):
            return create_error_response('Query is required', 400)
        
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return create_error_response('HR Legal system not available', 503)
        
        query = data['query']
        
        # Use simplified configuration for legacy compatibility  
        config = AgenticRAGConfig(
            response_length=ResponseLength.MEDIUM,
            response_style=ResponseStyle.PROFESSIONAL,
            detail_level=DetailLevel.BALANCED
        )
        
        context = LegalQueryContext(
            query=query,
            query_type=data.get('query_type', 'general'),
            user_role='hr_professional'
        )
        
        # Process query using HR Legal engine
        response = hr_legal_engine.query(context, config)
        
        if response:
            # Convert to legacy format
            legacy_response = {
                'response': response.content,
                'sources': response.metadata.sources_used,
                'confidence': response.metadata.confidence_score,
                'timestamp': response.timestamp
            }
            
            # Store query for analytics
            await supabase_manager.store_legal_query(
                g.current_user['user_id'],
                query,
                response.content,
                data.get('context', {})
            )
            
            return create_success_response(legacy_response)
        else:
            return create_error_response('Failed to process legal query', 500)
        
    except Exception as e:
        logger.error(f"HR Legal query error: {str(e)}")
        return create_error_response(f'Query processing failed: {str(e)}', 500)

@app.route('/api/hr-legal/compliance-check', methods=['POST'])
@async_route  
@require_user()
async def compliance_check_legacy():
    """Legacy compliance check endpoint (backward compatibility)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('content'):
            return create_error_response('Content is required', 400)
        
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            # Placeholder response for backward compatibility
            response = {
                'compliant': True,
                'issues': [],
                'recommendations': ['HR Legal compliance checking will be implemented'],
                'note': 'Compliance system is under development'
            }
            return create_success_response(response)
        
        content = data['content']
        content_type = data.get('content_type', 'policy')
        
        # Use simplified configuration for legacy compatibility
        query = f"Please perform a legal compliance analysis of the following {content_type}:\\n\\n{content}"
        
        config = AgenticRAGConfig(
            response_length=ResponseLength.MEDIUM,
            response_style=ResponseStyle.LEGAL,
            detail_level=DetailLevel.BALANCED
        )
        
        context = LegalQueryContext(
            query=query,
            query_type="compliance_check",
            user_role='hr_professional'
        )
        
        response = hr_legal_engine.query(context, config)
        
        if response:
            # Convert to legacy format
            legacy_response = {
                'compliant': response.metadata.confidence_score > 0.7,
                'issues': [],  # Extract from response content if needed
                'recommendations': response.metadata.follow_up_suggestions[:3],
                'analysis': response.content,
                'confidence': response.metadata.confidence_score
            }
            return create_success_response(legacy_response)
        else:
            return create_error_response('Failed to analyze compliance', 500)
        
    except Exception as e:
        logger.error(f"Compliance check error: {str(e)}")
        return create_error_response('Compliance check failed', 500)

# =====================================================================
# SYSTEM ENDPOINTS
# =====================================================================

@app.route('/api/health', methods=['GET'])
@async_route
async def health_check():
    """System health check"""
    try:
        # Check database health
        db_health = await supabase_manager.check_database_health()
        
        # Check AI service health
        ai_health = await ai_analyzer.check_ai_service_health()
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0',
            'services': {
                'database': db_health,
                'ai_service': ai_health
            },
            'environment': os.getenv('FLASK_ENV', 'development')
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/api/debug', methods=['GET'])
@async_route
@optional_auth()
async def debug_info():
    """Debug information (development only)"""
    try:
        if os.getenv('FLASK_ENV') != 'development':
            return create_error_response('Debug endpoint not available in production', 403)
        
        debug_info = {
            'environment': dict(os.environ),
            'current_user': g.current_user if hasattr(g, 'current_user') else None,
            'request_headers': dict(request.headers),
            'system_info': {
                'python_version': '3.11',
                'flask_version': '3.0.3'
            }
        }
        
        return create_success_response(debug_info)
        
    except Exception as e:
        logger.error(f"Debug info error: {str(e)}")
        return create_error_response('Debug info failed', 500)

# =====================================================================
# ENHANCED FEATURES ENDPOINTS
# =====================================================================

@app.route('/api/admin/dashboard', methods=['GET'])
@async_route
@require_admin()
async def admin_dashboard():
    """Get comprehensive admin dashboard metrics"""
    try:
        metrics = await admin_manager.get_dashboard_metrics()
        
        return create_success_response({
            'metrics': {
                'users': {
                    'total': metrics.total_users,
                    'active': metrics.active_users,
                    'trial': metrics.trial_users,
                    'full': metrics.full_users
                },
                'resumes': {
                    'total': metrics.total_resumes,
                    'today': metrics.resumes_today,
                    'avg_processing_time': metrics.avg_processing_time
                },
                'ai_providers': metrics.ai_provider_stats,
                'storage': metrics.storage_usage,
                'error_rate': metrics.error_rate
            }
        })
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {str(e)}")
        return create_error_response('Failed to get dashboard metrics', 500)

@app.route('/api/email-templates', methods=['GET'])
@async_route
@require_auth()
async def get_email_templates():
    """Get available email templates"""
    try:
        templates = email_template_manager.get_templates()
        
        return create_success_response({'templates': templates})
        
    except Exception as e:
        logger.error(f"Get email templates error: {str(e)}")
        return create_error_response('Failed to get email templates', 500)

@app.route('/api/email-templates/generate', methods=['POST'])
@async_route
@require_auth()
async def generate_email():
    """Generate personalized email from template"""
    try:
        data = request.get_json()
        
        required_fields = ['template_type', 'candidate_data', 'company_data']
        for field in required_fields:
            if field not in data:
                return create_error_response(f'{field} is required', 400)
        
        # Parse template type
        try:
            template_type = EmailType(data['template_type'])
        except ValueError:
            return create_error_response('Invalid template type', 400)
        
        # Generate email
        generated_email = email_template_manager.generate_email(
            template_type=template_type,
            candidate_data=data['candidate_data'],
            company_data=data['company_data'],
            custom_data=data.get('custom_data')
        )
        
        return create_success_response({
            'email': {
                'id': generated_email.email_id,
                'subject': generated_email.subject,
                'body': generated_email.body,
                'recipient_name': generated_email.recipient_name,
                'recipient_email': generated_email.recipient_email,
                'generated_at': generated_email.generated_at.isoformat()
            }
        }, 'Email generated successfully')
        
    except Exception as e:
        logger.error(f"Generate email error: {str(e)}")
        return create_error_response('Failed to generate email', 500)

@app.route('/api/ai/providers', methods=['GET'])
@async_route
@require_auth()
async def get_ai_providers():
    """Get AI provider status and statistics"""
    try:
        provider_stats = ai_analyzer.get_provider_status()
        
        return create_success_response({
            'providers': provider_stats,
            'default_provider': config.DEFAULT_AI_PROVIDER,
            'features': {
                'multi_provider_support': True,
                'market_based_scoring': config.ENABLE_MARKET_SCORING,
                'batch_processing': config.ENABLE_BATCH_PROCESSING
            }
        })
        
    except Exception as e:
        logger.error(f"Get AI providers error: {str(e)}")
        return create_error_response('Failed to get AI provider information', 500)

# =====================================================================
# ERROR HANDLERS
# =====================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return create_error_response('Endpoint not found', 404)

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return create_error_response('Method not allowed', 405)

@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large errors"""
    return create_error_response('File too large', 413)

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit errors"""
    return create_error_response('Rate limit exceeded', 429)

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    return create_error_response('Internal server error', 500)

# =====================================================================
# APPLICATION STARTUP
# =====================================================================

if __name__ == '__main__':
    # Get port from environment (Railway sets this)
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"Starting Resume Screening Backend on port {port}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"Frontend URL: {os.getenv('FRONTEND_URL', 'https://hrtool-sable.vercel.app')}")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
