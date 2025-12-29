from flask import request, jsonify, current_app, g
from werkzeug.utils import secure_filename
import asyncio
import uuid
from datetime import datetime
from app.api import api_bp
from app import db, limiter
from app.models import Resume, User
from app.services import ResumeParsingService, AnalysisService
from app.services.auth_manager import require_auth, get_current_user
from app.services.error_handler import ValidationError, AuthorizationError
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/resumes', methods=['POST'])
@limiter.limit("10 per minute")
@require_auth
def upload_resume():
    """Upload and process a resume file."""
    try:
        # Get user from JWT context
        user = get_current_user()
        if not user:
            raise AuthorizationError("User authentication required")
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get optional metadata
        metadata = request.form.get('metadata', '{}')
        
        # Initialize services
        parsing_service = ResumeParsingService(
            upload_folder=current_app.config['UPLOAD_FOLDER']
        )
        
        # Validate and save file
        if not parsing_service.is_allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {parsing_service.allowed_extensions}'
            }), 400
        
        # Save file
        filename, file_path, file_metadata = parsing_service.save_file(file)
        
        # Create resume record
        resume = Resume(
            user_id=str(user.id),
            filename=filename,
            original_filename=file_metadata['original_filename'],
            file_path=file_path,
            file_size=file_metadata['file_size'],
            file_type=file_metadata['file_type'],
            processing_status='pending'
        )
        
        db.session.add(resume)
        db.session.commit()
        
        # Extract text in background (for now, synchronous)
        try:
            resume.raw_text = parsing_service.extract_text(file_path)
            resume.structured_data = parsing_service.parse_resume_structure(resume.raw_text)
            resume.processing_status = 'text_extracted'
            db.session.commit()
        except Exception as e:
            resume.processing_status = 'failed'
            resume.error_message = str(e)
            db.session.commit()
            logger.error(f"Text extraction failed for resume {resume.id}: {str(e)}")
        
        return jsonify({
            'message': 'Resume uploaded successfully',
            'resume_id': str(resume.id),
            'status': resume.processing_status,
            'metadata': {
                'filename': resume.original_filename,
                'file_size': resume.file_size,
                'file_type': resume.file_type
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Resume upload failed: {str(e)}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@api_bp.route('/resumes/<resume_id>', methods=['GET'])
def get_resume(resume_id):
    """Get resume details by ID."""
    try:
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        response_data = resume.to_dict()
        
        # Include structured data if available
        if resume.structured_data:
            response_data['structured_data'] = resume.structured_data
        
        # Include analysis count
        response_data['analyses_count'] = resume.analyses.count()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        # Rollback any pending transaction
        db.session.rollback()
        logger.error(f"Get resume failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve resume'}), 500

@api_bp.route('/resumes', methods=['GET'])
@require_auth
def list_resumes():
    """List resumes with optional filtering."""
    try:
        # Get query parameters
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 per page
        
        # Build query
        query = Resume.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(processing_status=status)
        
        # Order by creation date (newest first)
        query = query.order_by(Resume.created_at.desc())
        
        # Paginate
        paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        resumes = [resume.to_dict() for resume in paginated.items]
        
        return jsonify({
            'resumes': resumes,
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
        logger.error(f"List resumes failed: {str(e)}")
        return jsonify({'error': 'Failed to list resumes'}), 500

@api_bp.route('/resumes/<resume_id>', methods=['DELETE'])
@require_auth
def delete_resume(resume_id):
    """Delete a resume and its associated data."""
    try:
        user = get_current_user()
        if not user:
            raise AuthorizationError("User authentication required")
        
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Check if user owns the resume or is admin
        if not user.is_admin and str(resume.user_id) != str(user.id):
            raise AuthorizationError("Not authorized to delete this resume")
        
        # Initialize parsing service for file cleanup
        parsing_service = ResumeParsingService(
            upload_folder=current_app.config['UPLOAD_FOLDER']
        )
        
        # Delete file from filesystem
        file_deleted = parsing_service.cleanup_file(resume.file_path)
        
        # Delete from database (cascades to analyses)
        db.session.delete(resume)
        db.session.commit()
        
        return jsonify({
            'message': 'Resume deleted successfully',
            'file_deleted': file_deleted
        }), 200
        
    except Exception as e:
        logger.error(f"Delete resume failed: {str(e)}")
        return jsonify({'error': 'Failed to delete resume'}), 500

@api_bp.route('/resumes/<resume_id>/text', methods=['GET'])
def get_resume_text(resume_id):
    """Get the extracted text content of a resume."""
    try:
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        if not resume.raw_text:
            return jsonify({'error': 'Resume text not available'}), 404
        
        return jsonify({
            'resume_id': str(resume.id),
            'text': resume.raw_text,
            'extracted_at': resume.updated_at.isoformat(),
            'structured_data': resume.structured_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get resume text failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve resume text'}), 500

@api_bp.route('/resumes/<resume_id>/reprocess', methods=['POST'])
def reprocess_resume(resume_id):
    """Reprocess resume text extraction."""
    try:
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Initialize parsing service
        parsing_service = ResumeParsingService(
            upload_folder=current_app.config['UPLOAD_FOLDER']
        )
        
        # Re-extract text
        try:
            resume.raw_text = parsing_service.extract_text(resume.file_path)
            resume.structured_data = parsing_service.parse_resume_structure(resume.raw_text)
            resume.processing_status = 'text_extracted'
            resume.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'message': 'Resume reprocessed successfully',
                'status': resume.processing_status
            }), 200
            
        except Exception as e:
            resume.processing_status = 'failed'
            resume.error_message = str(e)
            db.session.commit()
            
            return jsonify({
                'error': 'Reprocessing failed',
                'details': str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Reprocess resume failed: {str(e)}")
        return jsonify({'error': 'Failed to reprocess resume'}), 500
