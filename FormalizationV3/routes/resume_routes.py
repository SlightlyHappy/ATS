"""
Core resume processing routes - extracted from monolithic app.py
Handles: upload, analysis, batch processing, CRUD operations
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Create blueprint
resume_bp = Blueprint('resume', __name__, url_prefix='/api')

# Global dependencies (will be injected during initialization)
db_manager = None
storage_manager = None
auth_middleware = None
ai_processor = None
cache_manager = None
credit_manager = None
queue_manager = None
railway_db = None

def init_resume_routes(database_manager, storage_mgr, auth_mid, ai_proc, cache_mgr=None, 
                      credit_mgr=None, queue_mgr=None, railway_database=None):
    """Initialize resume routes with dependencies"""
    global db_manager, storage_manager, auth_middleware, ai_processor, cache_manager
    global credit_manager, queue_manager, railway_db
    
    db_manager = database_manager
    storage_manager = storage_mgr
    auth_middleware = auth_mid
    ai_processor = ai_proc
    cache_manager = cache_mgr
    credit_manager = credit_mgr
    queue_manager = queue_mgr
    railway_db = railway_database
    
    logger.info("✅ Resume routes initialized with all dependencies")

@resume_bp.route('/upload', methods=['POST'])
def upload_resume():
    """Upload and process resume files with automatic AI analysis"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Check trial limits
        if not auth_middleware.check_trial_limits(user['user_id']):
            return jsonify({"error": "Trial limit exceeded"}), 403
        
        # Handle both 'files' and 'file' field names for compatibility
        files = []
        if 'files' in request.files:
            files = request.files.getlist('files')
        elif 'file' in request.files:
            files = [request.files['file']]
        
        if not files:
            return jsonify({"error": "No files provided"}), 400
        
        results = []
        successful_uploads = 0
        
        for file in files:
            if file and file.filename and is_allowed_file(file.filename):
                try:
                    result = process_resume_file(file, user)
                    results.append(result)
                    
                    # Increment trial usage if successful
                    if result.get('status') == 'uploaded':
                        successful_uploads += 1
                        auth_middleware.increment_trial_usage(user['user_id'], 'resume')
                        
                except Exception as file_error:
                    logger.error(f"Error processing file {file.filename}: {file_error}")
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "error": str(file_error)
                    })
            else:
                results.append({
                    "filename": file.filename if file else "unknown",
                    "status": "error",
                    "error": "File type not allowed or invalid file"
                })
        
        # Enhanced response format
        response_data = {
            "success": successful_uploads > 0,
            "results": results,
            "processed_count": len(results),
            "successful_uploads": successful_uploads,
            "ai_processing_enabled": True,
            "message": f"Processed {len(results)} files, {successful_uploads} successful uploads with AI analysis"
        }
        
        # Add individual result details for single file uploads
        if len(results) == 1:
            single_result = results[0]
            if single_result.get('status') == 'uploaded':
                response_data.update({
                    "resume_id": single_result.get('resume_id'),
                    "filename": single_result.get('filename'),
                    "processing_status": single_result.get('processing_status'),
                    "ai_processing": single_result.get('ai_processing', True),
                    "note": single_result.get('note', 'AI analysis is running in background')
                })
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({
            "success": False,
            "error": "Upload failed",
            "message": str(e)
        }), 500

@resume_bp.route('/analyze/<resume_id>', methods=['POST'])
def analyze_resume(resume_id):
    """Analyze resume with enhanced AI system - Credit system integration"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
            
        user_id = user['user_id']
        
        # Get job requirements if provided
        data = request.get_json() or {}
        job_requirements = data.get('job_requirements', {})
        
        # B2B SaaS Enhancement: Credit-aware processing
        if credit_manager:
            try:
                # Check credit status
                credit_status = credit_manager.check_user_credits(user_id)
                
                # If no credits available, return monetization options
                if not credit_status.can_process:
                    return jsonify({
                        "success": False,
                        "error": "insufficient_credits",
                        "message": "Your trial credits have been exhausted",
                        "credit_status": {
                            "trial_credits": credit_status.trial_credits,
                            "premium_credits": credit_status.premium_credits,
                            "total_used": credit_status.total_used,
                            "credits_remaining": credit_status.credits_remaining
                        },
                        "monetization_options": get_premium_options(credit_status),
                        "trial_completed": True
                    }), 402  # Payment Required
                
                # Check queue status if available
                if queue_manager:
                    queue_status = queue_manager.get_queue_status()
                    from queue_manager import QueueStatus
                    from credit_manager import ProcessingTier
                    
                    if (queue_status in [QueueStatus.BUSY, QueueStatus.OVERLOADED] and 
                        credit_status.processing_tier == ProcessingTier.FREE_TRIAL):
                        # Queue the request
                        request_data = {
                            'resume_id': resume_id,
                            'resume_text': get_resume_text(resume_id, user_id),
                            'job_requirements': job_requirements
                        }
                        
                        request_id, queue_info = queue_manager.add_request(
                            str(user_id), "resume_analysis", request_data, credit_status.processing_tier
                        )
                        
                        return jsonify({
                            "success": False,
                            "status": "queued",
                            "message": "System is busy. Request queued for processing.",
                            "request_id": request_id,
                            "queue_info": queue_info,
                            "options": {
                                "wait_in_queue": {
                                    "description": "Free - wait in queue for processing",
                                    "estimated_wait": f"{queue_info.get('estimated_wait_minutes', 2)} minutes"
                                },
                                "skip_queue": {
                                    "description": "Skip the queue for instant processing",
                                    "price_inr": 40,
                                    "action": "POST /api/payment/queue-skip"
                                }
                            }
                        }), 202  # Accepted - will be processed later
                
                # Deduct credits for immediate processing
                if not credit_manager.deduct_credits(user_id, 1, "resume_analysis", credit_status.processing_tier):
                    return jsonify({
                        "success": False,
                        "error": "credit_deduction_failed",
                        "message": "Failed to deduct credits"
                    }), 402
                
            except Exception as credit_error:
                logger.error(f"Credit system error (non-breaking): {credit_error}")
                # Continue with legacy processing if credit system fails
        
        # Original processing logic
        if not ai_processor:
            return jsonify({"error": "AI processor not available"}), 500
            
        analysis_result = ai_processor.analyze_resume(
            resume_id, job_requirements, user_id
        )
        
        # Store analysis results
        if db_manager:
            db_manager.store_analysis_result(resume_id, analysis_result, user_id)
        
        # Enhanced response with credit info
        response_data = {
            "success": True,
            "analysis": analysis_result
        }
        
        # Add credit status if available
        if credit_manager:
            try:
                updated_status = credit_manager.check_user_credits(user_id)
                response_data["credit_status"] = {
                    "credits_remaining": updated_status.credits_remaining,
                    "total_used": updated_status.total_used
                }
            except Exception:
                pass  # Non-breaking
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({"error": "Analysis failed"}), 500

@resume_bp.route('/analyze/batch', methods=['POST'])
def analyze_resume_batch():
    """Analyze multiple resumes with comparative ranking - Enhanced with B2B credit system"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
            
        user_id = user['user_id']
        
        # Get request data
        data = request.get_json() or {}
        resume_batch = data.get('resumes', [])
        job_requirements = data.get('job_requirements', {})
        
        if not resume_batch:
            return jsonify({"error": "No resumes provided for batch analysis"}), 400
        
        # Validate batch size
        max_batch_size = 20
        if len(resume_batch) > max_batch_size:
            return jsonify({
                "error": f"Batch size too large. Maximum {max_batch_size} resumes allowed"
            }), 400
        
        # B2B SaaS Enhancement: Credit-aware processing (5 credits for batch)
        credits_needed = 5
        if credit_manager:
            try:
                credit_status = credit_manager.check_user_credits(user_id)
                
                if credit_status.credits_remaining < credits_needed:
                    return jsonify({
                        "success": False,
                        "error": "insufficient_credits",
                        "message": f"Batch analysis requires {credits_needed} credits. You have {credit_status.credits_remaining}.",
                        "feature": "batch_analysis",
                        "credits_needed": credits_needed,
                        "credit_status": {
                            "trial_credits": credit_status.trial_credits,
                            "premium_credits": credit_status.premium_credits,
                            "credits_remaining": credit_status.credits_remaining
                        },
                        "monetization_options": get_premium_options(credit_status)
                    }), 402
                
                # Queue handling for batch analysis
                if queue_manager:
                    queue_status = queue_manager.get_queue_status()
                    from queue_manager import QueueStatus
                    from credit_manager import ProcessingTier
                    
                    if (queue_status in [QueueStatus.BUSY, QueueStatus.OVERLOADED] and 
                        credit_status.processing_tier == ProcessingTier.FREE_TRIAL):
                        
                        request_data = {
                            'resumes': resume_batch,
                            'job_requirements': job_requirements
                        }
                        
                        request_id, queue_info = queue_manager.add_request(
                            str(user_id), "batch_analysis", request_data, credit_status.processing_tier
                        )
                        
                        return jsonify({
                            "success": False,
                            "status": "queued", 
                            "message": f"System is busy. Batch analysis queued for processing (will use {credits_needed} credits).",
                            "request_id": request_id,
                            "queue_info": queue_info,
                            "feature": "batch_analysis",
                            "credits_required": credits_needed
                        }), 202
                
                # Deduct credits for immediate processing
                if not credit_manager.deduct_credits(user_id, credits_needed, "batch_analysis", credit_status.processing_tier):
                    return jsonify({
                        "success": False,
                        "error": "credit_deduction_failed",
                        "message": f"Failed to deduct {credits_needed} credits for batch analysis"
                    }), 402
                
            except Exception as credit_error:
                logger.error(f"Credit system error (non-breaking): {credit_error}")
        
        # Concurrent batch processing
        async def concurrent_batch_processing():
            """Async wrapper for concurrent batch processing"""
            max_workers = min(4, len(resume_batch))
            
            async def process_single_resume(resume_item, job_requirements, user_id):
                """Process single resume in the batch"""
                try:
                    if not ai_processor:
                        return {"error": "AI processor not available", "overall_score": 0}
                        
                    return await ai_processor.analyze_resume(
                        resume_item.get('text', ''), 
                        job_requirements, 
                        user_id
                    )
                except Exception as e:
                    logger.error(f"Error processing resume in batch: {e}")
                    return {
                        "error": str(e),
                        "overall_score": 0,
                        "processing_status": "failed"
                    }
            
            try:
                logger.info(f"Starting concurrent batch processing for {len(resume_batch)} resumes with {max_workers} workers")
                
                # Create tasks for concurrent execution
                tasks = [
                    process_single_resume(resume_item, job_requirements, user_id)
                    for resume_item in resume_batch
                ]
                
                # Execute with timeout and gather results
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter out exceptions and process results
                processed_results = []
                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        processed_results.append({
                            "original_id": resume_batch[i].get('id', f'resume_{i}'),
                            "error": str(result),
                            "overall_score": 0,
                            "processing_status": "failed"
                        })
                    else:
                        result['original_id'] = resume_batch[i].get('id', f'resume_{i}')
                        processed_results.append(result)
                
                # Sort by overall score for ranking
                processed_results.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
                
                logger.info(f"Concurrent batch processing completed for {len(processed_results)} resumes")
                return processed_results
                
            except asyncio.TimeoutError:
                logger.error("Batch processing timeout - falling back to sequential processing")
                # Fallback to sequential processing
                return await ai_processor.analyze_resume_batch(resume_batch, job_requirements, user_id)
            
            except Exception as concurrent_error:
                logger.error(f"Concurrent processing failed: {concurrent_error}, falling back to sequential")
                # Fallback to sequential processing
                return await ai_processor.analyze_resume_batch(resume_batch, job_requirements, user_id)
        
        # Run the concurrent processing
        processed_results = asyncio.run(concurrent_batch_processing())
        
        # Store batch analysis results
        if db_manager:
            for result in processed_results:
                if result.get('original_id'):
                    try:
                        db_manager.store_analysis_result(result['original_id'], result, user_id)
                    except Exception as e:
                        logger.warning(f"Failed to store batch result: {e}")
        
        # Enhanced response with credit info
        response_data = {
            "success": True,
            "batch_analysis": {
                "total_resumes": len(processed_results),
                "results": processed_results,
                "analysis_type": "enhanced_concurrent_batch_with_ranking",
                "scoring_calibrated": True,
                "concurrent_processing": True
            }
        }
        
        # Add credit status if available
        if credit_manager:
            try:
                updated_status = credit_manager.check_user_credits(user_id)
                response_data["credit_status"] = {
                    "credits_remaining": updated_status.credits_remaining,
                    "total_used": updated_status.total_used,
                    "credits_used_for_batch": credits_needed
                }
            except Exception:
                pass  # Non-breaking
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        return jsonify({"error": "Batch analysis failed"}), 500

@resume_bp.route('/resumes', methods=['GET'])
def get_user_resumes():
    """Get all resumes for current user"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        if not db_manager:
            return jsonify({"error": "Database not available"}), 500
            
        resumes = db_manager.get_user_resumes(user['user_id'])
        
        return jsonify({
            "success": True,
            "resumes": resumes
        })
        
    except Exception as e:
        logger.error(f"Get resumes error: {e}")
        return jsonify({"error": "Failed to get resumes"}), 500

@resume_bp.route('/resumes/<resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    """Delete a specific resume"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
            
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        if not db_manager:
            return jsonify({"error": "Database not available"}), 500
            
        success = db_manager.delete_user_resume(resume_id, user['user_id'])
        
        if success:
            return jsonify({"success": True, "message": "Resume deleted"})
        else:
            return jsonify({"error": "Resume not found"}), 404
            
    except Exception as e:
        logger.error(f"Delete resume error: {e}")
        return jsonify({"error": "Delete failed"}), 500

# Helper functions
def is_allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}

def process_resume_file(file, user):
    """Process resume file with AI analysis - extracted from monolithic app.py"""
    try:
        import uuid
        import hashlib
        from werkzeug.utils import secure_filename
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file temporarily
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Get file size and extract text
        file_size = os.path.getsize(file_path)
        resume_text = extract_text_from_file(file_path)
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")
        
        # Validate extraction
        if not resume_text or len(resume_text.strip()) < 50:
            return {
                "filename": filename,
                "status": "error",
                "error": "Failed to extract meaningful text from file"
            }
        
        # Generate file hash for duplicate detection
        file_hash = hashlib.md5(resume_text.encode()).hexdigest()
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
        
        # Create resume record
        user_id = user['user_id']
        resume_uuid = str(uuid.uuid4())
        
        resume_data = {
            'id': resume_uuid,
            'user_id': user_id,
            'filename': filename,
            'file_hash': file_hash,
            'file_size': file_size,
            'file_type': file_extension,
            'raw_text': resume_text,
            'upload_date': datetime.utcnow().isoformat(),
            'processing_status': 'processing',
            'processing_started_at': datetime.utcnow().isoformat(),
            'candidate_name': '',
            'candidate_email': '',
            'overall_score': 0,
            'ai_feedback': 'Processing with AI...',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Store in database
        if not db_manager:
            return {
                "filename": filename,
                "status": "error",
                "error": "Database manager not available"
            }
        
        resume_id = db_manager.store_resume_hybrid(resume_data)
        
        if resume_id:
            # Start background AI processing
            try:
                async def safe_ai_processing():
                    try:
                        await process_user_resume_unified_ai(resume_id, resume_text, filename, user_id)
                    except Exception as ai_error:
                        logger.error(f"AI processing error for resume {resume_id}: {ai_error}")
                        # Update status to failed
                        if railway_db:
                            railway_db.execute_write(
                                "UPDATE resumes SET processing_status = %s, processing_error = %s WHERE id = %s",
                                ('failed', str(ai_error), resume_id)
                            )
                
                # Start background task
                background_task = asyncio.create_task(safe_ai_processing())
                logger.info(f"Started AI processing for resume {resume_id} in background")
                
            except Exception as ai_start_error:
                logger.error(f"Failed to start AI processing: {ai_start_error}")
                return {
                    "filename": filename,
                    "status": "error",
                    "error": f"Failed to start AI processing: {str(ai_start_error)}",
                    "resume_id": resume_id,
                    "retry_recommended": True
                }
            
            # Return success response
            return {
                "resume_id": resume_id,
                "filename": filename,
                "status": "uploaded",
                "processing_status": "processing",
                "ai_processing": True,
                "user_upload": True,
                "file_size": file_size,
                "text_length": len(resume_text),
                "message": "Resume uploaded successfully and AI processing started",
                "note": "AI analysis is running in background. Check back in a few minutes for complete analysis."
            }
        else:
            return {
                "filename": filename,
                "status": "error",
                "error": "Failed to store resume in database"
            }
        
    except Exception as e:
        logger.error(f"Resume file processing error: {e}")
        return {
            "filename": file.filename,
            "status": "error",
            "error": str(e)
        }

def extract_text_from_file(file_path):
    """Extract text from uploaded file"""
    try:
        file_ext = file_path.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            return extract_text_from_pdf(file_path)
        elif file_ext in ['docx', 'doc']:
            return extract_text_from_docx(file_path)
        elif file_ext in ['png', 'jpg', 'jpeg']:
            return extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
            
    except Exception as e:
        logger.error(f"Text extraction error: {e}")
        return ""

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    import fitz
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    from docx import Document
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\\n"
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
    return text

def extract_text_from_image(file_path):
    """Extract text from image using OCR"""
    import pytesseract
    from PIL import Image
    text = ""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
    return text

async def process_user_resume_unified_ai(resume_id: str, resume_text: str, filename: str, user_id: str):
    """Process user resume using unified AI processor - extracted from monolithic app.py"""
    try:
        logger.info(f"🤖 Starting unified AI processing for resume {resume_id} (user: {user_id})")
        
        if not ai_processor:
            raise Exception("AI processor not available")
        
        # Process resume with AI
        start_time = datetime.utcnow()
        ai_result = await ai_processor.process_resume(
            resume_text=resume_text,
            user_id=user_id,
            analysis_type="comprehensive"
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Update database with results
        if ai_result.success and railway_db:
            database_record = extract_database_record(ai_result.data, processing_time)
            
            update_query = """
                UPDATE resumes SET 
                    overall_score = %s, experience_score = %s, skills_score = %s, education_score = %s,
                    technical_score = %s, role_fit_score = %s, candidate_name = %s, candidate_email = %s,
                    processing_status = %s, ai_provider_used = %s, ai_processing_time = %s,
                    processing_completed_at = %s, updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """
            
            railway_db.execute_write(update_query, (
                database_record.get('overall_score', 75),
                database_record.get('experience_score', 70),
                database_record.get('skills_score', 75),
                database_record.get('education_score', 70),
                database_record.get('technical_score', 65),
                database_record.get('role_fit_score', 70),
                database_record.get('candidate_name', 'Unknown'),
                database_record.get('candidate_email', ''),
                'completed',
                ai_result.provider_used.value if ai_result.provider_used else 'unknown',
                int(processing_time),
                datetime.utcnow().isoformat(),
                resume_id,
                user_id
            ))
            
            logger.info(f"✅ Database updated successfully for resume {resume_id}")
        
    except Exception as e:
        logger.error(f"❌ AI processing failed for resume {resume_id}: {e}")
        
        # Update status to failed
        if railway_db:
            railway_db.execute_write(
                "UPDATE resumes SET processing_status = %s, processing_error = %s WHERE id = %s",
                ('failed', str(e), resume_id)
            )

def extract_database_record(ai_data, processing_time):
    """Extract database record from AI result"""
    try:
        scores = ai_data.get('scores', {})
        candidate_info = ai_data.get('candidate_info', {})
        
        return {
            'overall_score': scores.get('overall_score', 75),
            'experience_score': scores.get('experience_score', 70),
            'skills_score': scores.get('skills_score', 75),
            'education_score': scores.get('education_score', 70),
            'technical_score': scores.get('technical_score', 65),
            'role_fit_score': scores.get('role_fit_score', 70),
            'candidate_name': candidate_info.get('name', 'Unknown'),
            'candidate_email': candidate_info.get('email', ''),
            'processing_time': processing_time
        }
    except Exception as e:
        logger.error(f"Failed to extract database record: {e}")
        return {
            'overall_score': 60,
            'experience_score': 60,
            'skills_score': 60,
            'education_score': 60,
            'technical_score': 60,
            'role_fit_score': 60,
            'candidate_name': 'Unknown',
            'candidate_email': '',
            'processing_time': processing_time
        }

def get_premium_options(credit_status):
    """Get premium monetization options"""
    return {
        "trial_exhausted": True,
        "recommended_plan": "Professional",
        "plans": [
            {
                "name": "Professional",
                "price_monthly": 2500,
                "credits_included": 100,
                "features": ["Advanced AI Analysis", "Batch Processing", "Priority Queue"]
            },
            {
                "name": "Enterprise", 
                "price_monthly": 7500,
                "credits_included": 500,
                "features": ["All Professional Features", "Custom Models", "API Access"]
            }
        ]
    }

def get_resume_text(resume_id: str, user_id: str) -> str:
    """Helper method to get resume text for queue processing"""
    try:
        if db_manager:
            resume_data = db_manager.get_resume_by_id(resume_id, user_id)
            if resume_data and 'raw_text' in resume_data:
                return resume_data['raw_text']
        return ""
    except Exception as e:
        logger.error(f"Failed to get resume text for {resume_id}: {e}")
        return ""
