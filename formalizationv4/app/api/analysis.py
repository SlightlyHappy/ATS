from flask import request, jsonify, current_app, g
import asyncio
import json
from app.api import api_bp
from app import db, limiter
from app.models import Resume, Analysis
from app.services import AnalysisService
from app.services.auth_manager import require_auth, require_credits, get_current_user
from app.services.error_handler import ValidationError, AuthorizationError
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/analysis', methods=['GET'])
@require_auth
def get_analysis_info():
    """Get analysis service information and user's analysis history."""
    try:
        user = get_current_user()
        if not user:
            raise AuthorizationError("User authentication required")
        
        # Get user's recent analyses
        recent_analyses = Analysis.query.filter_by(user_id=user.id)\
            .order_by(Analysis.created_at.desc())\
            .limit(10)\
            .all()
        
        analysis_data = {
            'service': 'Analysis Service',
            'status': 'active',
            'user_credits': user.credits,
            'recent_analyses': [
                {
                    'id': str(analysis.id),
                    'resume_id': str(analysis.resume_id),
                    'status': analysis.status,
                    'created_at': analysis.created_at.isoformat(),
                    'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None
                }
                for analysis in recent_analyses
            ],
            'endpoints': {
                'analyze_resume': '/api/v1/resumes/<resume_id>/analyze',
                'get_analysis': '/api/v1/analyses/<analysis_id>'
            }
        }
        
        return jsonify(analysis_data), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Analysis info error: {e}")
        return jsonify({'error': 'Failed to get analysis information'}), 500

@api_bp.route('/resumes/<resume_id>/analyze', methods=['POST'])
@limiter.limit("5 per minute")
@require_auth
@require_credits(1)
def analyze_resume(resume_id):
    """Trigger comprehensive resume analysis."""
    try:
        # Get authenticated user
        user = get_current_user()
        if not user:
            raise AuthorizationError("User authentication required")
        
        # Check if resume exists
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Check if user owns the resume or is admin
        if not user.is_admin and str(resume.user_id) != str(user.id):
            raise AuthorizationError("Not authorized to analyze this resume")
        
        if not resume.raw_text:
            return jsonify({'error': 'Resume text not available. Please reprocess the resume.'}), 400
        
        # Get analysis context from request
        context = request.get_json() or {}
        
        # Initialize analysis service
        config = {
            'upload_folder': current_app.config['UPLOAD_FOLDER'],
            'model': current_app.config.get('OLLAMA_MODEL'),
            'max_concurrent_agents': current_app.config.get('MAX_CONCURRENT_AGENTS', 4),
            'agent_timeout': current_app.config.get('AGENT_TIMEOUT', 60)
        }
        
        analysis_service = AnalysisService(config)
        
        # Run analysis asynchronously
        try:
            # Create event loop for async analysis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            analysis = loop.run_until_complete(
                analysis_service.analyze_resume(resume_id, context)
            )
            
            loop.close()
            
            return jsonify({
                'message': 'Analysis completed successfully',
                'analysis_id': str(analysis.id),
                'overall_score': analysis.overall_score,
                'status': analysis.status,
                'processing_time': analysis.processing_time,
                'summary': {
                    'strengths': analysis.strengths,
                    'weaknesses': analysis.weaknesses,
                    'recommendations': analysis.recommendations
                }
            }), 201
            
        except Exception as e:
            logger.error(f"Analysis execution failed: {str(e)}")
            return jsonify({
                'error': 'Analysis failed',
                'details': str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Analysis request failed: {str(e)}")
        return jsonify({'error': 'Analysis request failed'}), 500

@api_bp.route('/analyses/<analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Get analysis results by ID."""
    try:
        analysis = Analysis.query.get(analysis_id)
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Build comprehensive response
        response_data = analysis.to_dict()
        
        # Add detailed agent results
        response_data['agent_results'] = analysis.get_agent_results()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Get analysis failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analysis'}), 500

@api_bp.route('/resumes/<resume_id>/analyses', methods=['GET'])
def list_resume_analyses(resume_id):
    """List all analyses for a specific resume."""
    try:
        # Verify resume exists
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        
        # Get analyses
        analyses_query = Analysis.query.filter_by(resume_id=resume_id)\
                                     .order_by(Analysis.created_at.desc())
        
        paginated = analyses_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        analyses = [analysis.to_dict() for analysis in paginated.items]
        
        return jsonify({
            'resume_id': resume_id,
            'analyses': analyses,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"List analyses failed: {str(e)}")
        return jsonify({'error': 'Failed to list analyses'}), 500

@api_bp.route('/resumes/<resume_id>/reanalyze', methods=['POST'])
@limiter.limit("3 per minute")
def reanalyze_resume(resume_id):
    """Re-run analysis with optional agent selection."""
    try:
        # Check if resume exists
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        if not resume.raw_text:
            return jsonify({'error': 'Resume text not available'}), 400
        
        # Get request data
        data = request.get_json() or {}
        agent_types = data.get('agent_types')  # Optional: specific agents to run
        context = data.get('context', {})
        
        # Initialize analysis service
        config = {
            'upload_folder': current_app.config['UPLOAD_FOLDER'],
            'model': current_app.config.get('OLLAMA_MODEL'),
            'max_concurrent_agents': current_app.config.get('MAX_CONCURRENT_AGENTS', 4),
            'agent_timeout': current_app.config.get('AGENT_TIMEOUT', 60)
        }
        
        analysis_service = AnalysisService(config)
        
        # Run re-analysis
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            analysis = loop.run_until_complete(
                analysis_service.reanalyze_resume(resume_id, agent_types, context)
            )
            
            loop.close()
            
            return jsonify({
                'message': 'Re-analysis completed successfully',
                'analysis_id': str(analysis.id),
                'overall_score': analysis.overall_score,
                'status': analysis.status,
                'processing_time': analysis.processing_time
            }), 201
            
        except Exception as e:
            logger.error(f"Re-analysis execution failed: {str(e)}")
            return jsonify({
                'error': 'Re-analysis failed',
                'details': str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Re-analysis request failed: {str(e)}")
        return jsonify({'error': 'Re-analysis request failed'}), 500

@api_bp.route('/analyses/<analysis_id1>/compare/<analysis_id2>', methods=['GET'])
def compare_analyses(analysis_id1, analysis_id2):
    """Compare two analyses and show differences."""
    try:
        config = {
            'upload_folder': current_app.config['UPLOAD_FOLDER']
        }
        
        analysis_service = AnalysisService(config)
        comparison = analysis_service.compare_analyses(analysis_id1, analysis_id2)
        
        return jsonify(comparison), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Analysis comparison failed: {str(e)}")
        return jsonify({'error': 'Comparison failed'}), 500

@api_bp.route('/analyses/<analysis_id>/agent/<agent_name>', methods=['GET'])
def get_agent_result(analysis_id, agent_name):
    """Get specific agent result from an analysis."""
    try:
        analysis = Analysis.query.get(analysis_id)
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Map agent names to result fields
        agent_results = {
            'technical_skills': analysis.technical_skills_result,
            'experience': analysis.experience_result,
            'education': analysis.education_result,
            'soft_skills': analysis.soft_skills_result
        }
        
        if agent_name not in agent_results:
            return jsonify({
                'error': f'Invalid agent name. Available: {list(agent_results.keys())}'
            }), 400
        
        result = agent_results[agent_name]
        if not result:
            return jsonify({'error': f'No result available for agent {agent_name}'}), 404
        
        return jsonify({
            'analysis_id': str(analysis.id),
            'agent_name': agent_name,
            'result': result,
            'agent_score': analysis.scores_breakdown.get(agent_name, {}).get('score') if analysis.scores_breakdown else None
        }), 200
        
    except Exception as e:
        logger.error(f"Get agent result failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve agent result'}), 500

@api_bp.route('/analyses', methods=['GET'])
def list_analyses():
    """List all analyses with optional filtering."""
    try:
        # Get query parameters
        resume_id = request.args.get('resume_id')
        status = request.args.get('status')
        min_score = request.args.get('min_score', type=float)
        max_score = request.args.get('max_score', type=float)
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Build query
        query = Analysis.query
        
        if resume_id:
            query = query.filter_by(resume_id=resume_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if min_score is not None:
            query = query.filter(Analysis.overall_score >= min_score)
        
        if max_score is not None:
            query = query.filter(Analysis.overall_score <= max_score)
        
        # Order by creation date (newest first)
        query = query.order_by(Analysis.created_at.desc())
        
        # Paginate
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        analyses = [analysis.to_dict() for analysis in paginated.items]
        
        return jsonify({
            'analyses': analyses,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"List analyses failed: {str(e)}")
        return jsonify({'error': 'Failed to list analyses'}), 500
