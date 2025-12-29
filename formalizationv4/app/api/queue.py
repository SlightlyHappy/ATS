import os
import uuid
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.utils import secure_filename
from app import db
from app.models.user import User
from app.models.resume import Resume
from app.models.queue import AnalysisQueue, BatchUpload
from app.services.queue_service import QueueService
from app.services.resume_parsing_service import ResumeParsingService
from app.services.auth_manager import require_auth, require_credits, get_current_user
from app.services.error_handler import ValidationError, AuthorizationError
import zipfile
import tempfile
import shutil

queue_bp = Blueprint('queue', __name__)
queue_service = QueueService()

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
ALLOWED_ARCHIVE_EXTENSIONS = {'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_archive(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_ARCHIVE_EXTENSIONS

@queue_bp.route('/upload', methods=['POST'])
@require_auth
@require_credits(1)
def upload_resume():
    """Upload a single resume for analysis."""
    try:
        # Get user from JWT context instead of form data
        user = get_current_user()
        if not user:
            raise AuthorizationError("User authentication required")
        
        # Check credits for non-admin users (already checked by decorator but double-check)
        if not user.is_admin and not user.has_sufficient_credits(1):
            return jsonify({'error': 'Insufficient credits'}), 402
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Create resume record
        resume = Resume(
            user_id=str(user.id),
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=filename.rsplit('.', 1)[1].lower(),
            processing_status='pending'
        )
        
        db.session.add(resume)
        db.session.commit()
        
        # Add to queue for immediate processing (single file)
        queue_entry = queue_service.add_to_queue(str(user.id), str(resume.id))
        
        return jsonify({
            'message': 'Resume uploaded successfully',
            'resume_id': str(resume.id),
            'queue_id': str(queue_entry.id),
            'queue_position': queue_entry.queue_position,
            'estimated_completion': queue_entry.estimated_completion_time.isoformat() if queue_entry.estimated_completion_time else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@queue_bp.route('/upload/batch', methods=['POST'])
@require_auth
def upload_batch():
    """Upload multiple resumes as a zip file or individual files."""
    try:
        # Get user from JWT context
        user = get_current_user()
        if not user:
            raise AuthorizationError("User authentication required")
        
        batch_name = request.form.get('batch_name', None)
        
        uploaded_resumes = []
        
        # Handle zip file upload
        if 'zip_file' in request.files:
            zip_file = request.files['zip_file']
            if zip_file.filename != '' and allowed_archive(zip_file.filename):
                uploaded_resumes = process_zip_upload(zip_file, str(user.id))
        
        # Handle multiple individual files
        elif 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file.filename != '' and allowed_file(file.filename):
                    resume = process_single_file_upload(file, str(user.id))
                    if resume:
                        uploaded_resumes.append(resume)
        
        if not uploaded_resumes:
            return jsonify({'error': 'No valid files uploaded'}), 400
        
        # Check credits for non-admin users
        if not user.is_admin and not user.has_sufficient_credits(len(uploaded_resumes)):
            # Clean up uploaded files
            for resume in uploaded_resumes:
                try:
                    os.remove(resume.file_path)
                    db.session.delete(resume)
                except:
                    pass
            db.session.commit()
            return jsonify({'error': 'Insufficient credits for batch analysis'}), 402
        
        # Create batch and add to queue
        resume_ids = [str(resume.id) for resume in uploaded_resumes]
        batch = queue_service.add_batch_to_queue(str(user.id), resume_ids, batch_name)
        
        return jsonify({
            'message': f'Batch of {len(uploaded_resumes)} resumes uploaded successfully',
            'batch_id': str(batch.id),
            'batch_name': batch.batch_name,
            'total_resumes': len(uploaded_resumes),
            'resume_ids': resume_ids,
            'credits_required': len(uploaded_resumes)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def process_zip_upload(zip_file, user_id):
    """Process a zip file containing multiple resumes."""
    resumes = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save zip file temporarily
        zip_path = os.path.join(temp_dir, secure_filename(zip_file.filename))
        zip_file.save(zip_path)
        
        # Extract zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Process each file in the zip
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.zip'):
                    continue  # Skip the zip file itself
                
                if allowed_file(file):
                    file_path = os.path.join(root, file)
                    
                    # Create permanent file
                    filename = secure_filename(file)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    permanent_path = os.path.join(upload_folder, unique_filename)
                    
                    # Copy to permanent location
                    shutil.copy2(file_path, permanent_path)
                    
                    # Create resume record
                    resume = Resume(
                        user_id=user_id,
                        filename=unique_filename,
                        original_filename=filename,
                        file_path=permanent_path,
                        file_size=os.path.getsize(permanent_path),
                        file_type=filename.rsplit('.', 1)[1].lower(),
                        processing_status='pending'
                    )
                    
                    db.session.add(resume)
                    resumes.append(resume)
        
        db.session.commit()
    
    return resumes

def process_single_file_upload(file, user_id):
    """Process a single file upload."""
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        resume = Resume(
            user_id=user_id,
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=filename.rsplit('.', 1)[1].lower(),
            processing_status='pending'
        )
        
        db.session.add(resume)
        return resume
        
    except Exception as e:
        print(f"Error processing file {file.filename}: {str(e)}")
        return None

@queue_bp.route('/status', methods=['GET'])
def get_queue_status():
    """Get overall queue status."""
    try:
        user_id = request.args.get('user_id')
        status = queue_service.get_queue_status(user_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@queue_bp.route('/user/<user_id>/queue', methods=['GET'])
def get_user_queue(user_id):
    """Get queue items for a specific user."""
    try:
        status = request.args.get('status')
        items = queue_service.get_user_queue_items(user_id, status)
        
        return jsonify({
            'items': [item.to_dict() for item in items]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@queue_bp.route('/user/<user_id>/batches', methods=['GET'])
def get_user_batches(user_id):
    """Get batch uploads for a specific user."""
    try:
        batches = BatchUpload.query.filter_by(user_id=user_id).order_by(
            BatchUpload.created_at.desc()
        ).all()
        
        return jsonify({
            'batches': [batch.to_dict() for batch in batches]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@queue_bp.route('/batch/<batch_id>/status', methods=['GET'])
def get_batch_status(batch_id):
    """Get status of a specific batch."""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        batch = queue_service.get_batch_status(batch_id, user_id)
        if not batch:
            return jsonify({'error': 'Batch not found'}), 404
        
        return jsonify(batch.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@queue_bp.route('/cancel/<queue_id>', methods=['POST'])
@require_auth
def cancel_queue_item(queue_id):
    """Cancel a pending queue item."""
    try:
        user = get_current_user()
        if not user:
            raise AuthorizationError("User authentication required")
        
        success = queue_service.cancel_queue_item(queue_id, str(user.id))
        if success:
            return jsonify({'message': 'Queue item cancelled successfully'})
        else:
            return jsonify({'error': 'Could not cancel queue item'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@queue_bp.route('/user/<user_id>/credits', methods=['GET'])
def get_user_credits(user_id):
    """Get user's credit balance and transaction history."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get recent transactions
        transactions = user.credit_transactions.order_by(
            db.desc('created_at')
        ).limit(20).all()
        
        return jsonify({
            'user_id': str(user.id),
            'credits_balance': user.credits_balance,
            'total_credits_purchased': user.total_credits_purchased,
            'total_credits_used': user.total_credits_used,
            'is_admin': user.is_admin,
            'recent_transactions': [t.to_dict() for t in transactions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@queue_bp.route('/user/<user_id>/credits/add', methods=['POST'])
def add_user_credits(user_id):
    """Add credits to a user's account (admin only or payment processing)."""
    try:
        amount = request.json.get('amount')
        description = request.json.get('description', 'Credit purchase')
        
        if not amount or amount <= 0:
            return jsonify({'error': 'Invalid credit amount'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.add_credits(amount, description)
        db.session.commit()
        
        return jsonify({
            'message': f'Added {amount} credits successfully',
            'new_balance': user.credits_balance
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
