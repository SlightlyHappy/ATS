import os
import json
import tempfile
import atexit
import signal
import sys
import hashlib
import io
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from docx import Document
import requests
import pandas as pd
from typing import Dict, List, Optional
import logging
import psutil
import gc

# Import optimized modules
from config import config
from storage import ResumeStorage
from ai_processor import OptimizedAIProcessor
from secure_api_keys import secure_key_manager

# Import Supabase integration
try:
    from supabase_manager import SupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"Supabase not available: {e}")

# Import Bear Systems authentication system
from models.database import DatabaseManager
from models.user import User, UserSession, AdminUser
from middleware.auth import init_auth_middleware
from middleware.trial_limits import init_trial_middleware
from routes.auth import auth_bp, init_auth_routes
from routes.trial import trial_bp, init_trial_routes

# Import HR Legal modules
try:
    from hr_legal import (
        EnhancedRAGEngine, AgenticRAGConfig, LegalQueryContext, 
        ResponseLength, ResponseStyle, DetailLevel, AudienceLevel
    )
    HR_LEGAL_AVAILABLE = True
except ImportError as e:
    HR_LEGAL_AVAILABLE = False
    print(f"HR Legal modules not available: {e}")
    print("Install missing dependencies: pip install sentence-transformers faiss-cpu")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS configuration for production deployment
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://hrtool-sable.vercel.app",  # Vercel production (FIXED!)
    "https://*.vercel.app",   # Vercel deployments (backup)
    "https://*.railway.app"   # Railway deployments (if needed)
]

# Get production origins from environment
if os.getenv('FRONTEND_URL'):
    allowed_origins.append(os.getenv('FRONTEND_URL'))

CORS(app, 
     origins=allowed_origins,
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'Accept', 'Origin', 'X-Requested-With'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size (increased for larger resumes)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Ollama configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')  # Optimal for 6GB GPU

# Model alternatives for different use cases:
# qwen2.5:3b - Fast processing, good for high volume (1.9GB)
# qwen2.5:7b - Best balance of accuracy and speed (4.7GB) 
# qwen2.5:14b - Maximum accuracy but requires CPU fallback (9.0GB)

# Store processed resumes in memory (in production, use a database)
# processed_resumes = []  # Replaced with optimized storage
role_requirements = {
    "simple_description": "",
    "updated_at": None
}

# Store email templates and generated emails
email_templates = {
    "interview_invitation": {
        "name": "Interview Invitation",
        "description": "Invite candidate for an interview",
        "placeholders": ["interview_link", "interviewer_name", "company_name", "interview_date", "interview_time"]
    },
    "interview_scheduling": {
        "name": "Interview Scheduling (Calendly)",
        "description": "Send scheduling link for candidate to book interview",
        "placeholders": ["scheduling_link", "interviewer_name", "company_name"]
    },
    "rejection": {
        "name": "Application Rejection",
        "description": "Politely decline the application",
        "placeholders": ["company_name", "position_title"]
    },
    "offer": {
        "name": "Job Offer",
        "description": "Extend a job offer to the candidate",
        "placeholders": ["position_title", "salary", "start_date", "company_name", "hiring_manager"]
    },
    "follow_up": {
        "name": "Follow-up Email",
        "description": "Follow up on application status",
        "placeholders": ["company_name", "position_title", "next_steps"]
    },
    "custom": {
        "name": "Custom Email",
        "description": "Custom email with user-defined content",
        "placeholders": []
    }
}

generated_emails = []  # Store generated emails temporarily

# Store debug logs
debug_logs = []

# Track temporary files for cleanup
temp_files_created = []

# Initialize optimized components
resume_storage = ResumeStorage(config)
ai_processor = OptimizedAIProcessor(config, OLLAMA_URL, OLLAMA_MODEL)

# Update database schema for user support
resume_storage.update_database_schema_for_users()

# Initialize Bear Systems Authentication System with Supabase Primary
print("🔧 Initializing Bear Systems Authentication System...")
try:
    # Initialize Supabase manager first (primary auth)
    supabase_manager = None
    if SUPABASE_AVAILABLE:
        try:
            supabase_manager = SupabaseManager()
            print("✅ Supabase authentication initialized (Primary)")
        except Exception as e:
            print(f"⚠️  Supabase initialization failed: {e}")
            print("📌 Falling back to SQLite authentication")
    
    # Initialize local database (backup/sync)
    db_manager = DatabaseManager()
    
    # Initialize models
    user_manager = User(db_manager)
    user_session_manager = UserSession(db_manager)
    admin_user_manager = AdminUser(db_manager)
    
    # Initialize middleware
    init_auth_middleware(user_session_manager, admin_user_manager, supabase_manager)
    init_trial_middleware(user_manager)
    
    # Initialize routes with Supabase manager
    init_auth_routes(user_manager, user_session_manager, admin_user_manager, supabase_manager)
    init_trial_routes(user_manager)
    
    # Initialize admin routes
    from routes.admin import admin_bp, init_admin_routes
    init_admin_routes(user_manager, user_session_manager, admin_user_manager, db_manager, resume_storage, supabase_manager)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(trial_bp)
    app.register_blueprint(admin_bp)
    
    # Create default admin if none exists
    db_manager.create_default_admin()
    
    print("✅ Bear Systems Authentication System initialized successfully")
    
except Exception as e:
    print(f"❌ Failed to initialize authentication system: {e}")
    # Don't exit - continue with basic functionality
    user_manager = None
    user_session_manager = None
    admin_user_manager = None

# Initialize HR Legal components
hr_legal_engine = None
hr_legal_error = None

def auto_initialize_legal_system():
    """Auto-initialize the HR Legal system on startup."""
    global hr_legal_engine, hr_legal_error
    
    if not HR_LEGAL_AVAILABLE:
        hr_legal_error = "HR Legal dependencies not available"
        print("⚠️  HR Legal system: Dependencies not installed")
        return False
    
    try:
        print("🔄 Initializing HR Legal system...")
        
        # Initialize with the multi-provider AI system
        from multi_provider_ai import multi_provider_ai
        
        # Initialize the AI provider at startup with enhanced failover
        from multi_provider_ai import multi_provider_ai
        
        # Try to initialize Ollama first (primary)
        ollama_success = False
        try:
            multi_provider_ai.add_provider('ollama', OLLAMA_MODEL, base_url=OLLAMA_URL)
            print(f"✅ Primary AI provider (Ollama) initialized: {OLLAMA_MODEL}")
            ollama_success = True
        except Exception as ai_init_error:
            print(f"⚠️  Primary AI provider (Ollama) failed: {ai_init_error}")
        
        # Add backup providers if available
        backup_providers_added = 0
        
        if os.getenv('OPENAI_API_KEY'):
            try:
                multi_provider_ai.add_provider('openai', 'gpt-3.5-turbo', os.getenv('OPENAI_API_KEY'))
                print("✅ Backup AI provider (OpenAI) added")
                backup_providers_added += 1
            except Exception as e:
                print(f"⚠️  OpenAI provider failed: {e}")
        
        if os.getenv('GOOGLE_API_KEY'):
            try:
                multi_provider_ai.add_provider('gemini', 'gemini-1.5-flash', os.getenv('GOOGLE_API_KEY'))
                print("✅ Backup AI provider (Gemini) added")
                backup_providers_added += 1
            except Exception as e:
                print(f"⚠️  Gemini provider failed: {e}")
        
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                multi_provider_ai.add_provider('anthropic', 'claude-3-haiku-20240307', os.getenv('ANTHROPIC_API_KEY'))
                print("✅ Backup AI provider (Anthropic) added")
                backup_providers_added += 1
            except Exception as e:
                print(f"⚠️  Anthropic provider failed: {e}")
        
        # Check if we have at least one working provider
        if not ollama_success and backup_providers_added == 0:
            hr_legal_error = "No AI providers available. Please configure at least one AI provider."
            print("❌ Critical: No AI providers available!")
            return False
        
        print(f"✅ AI system ready with {1 if ollama_success else 0} primary + {backup_providers_added} backup providers")
        
        # Create HR Legal engine
        hr_legal_engine = EnhancedRAGEngine(
            ai_provider=multi_provider_ai,
            auto_initialize=True  # Auto-initialize on startup
        )
        print("✅ HR Legal engine created successfully")
        
        # Auto-initialize the system
        if hr_legal_engine:
            try:
                print("🔄 Auto-initializing HR Legal system...")
                success = hr_legal_engine.initialize()
                if success:
                    print("✅ HR Legal system auto-initialized successfully")
                    return True
                else:
                    error_msg = getattr(hr_legal_engine, 'initialization_error', 'Unknown initialization error')
                    hr_legal_error = f"Auto-initialization failed: {error_msg}"
                    print(f"❌ HR Legal auto-initialization failed: {error_msg}")
                    return False
            except Exception as init_error:
                hr_legal_error = f"Auto-initialization exception: {init_error}"
                print(f"❌ HR Legal auto-initialization exception: {init_error}")
                return False
        
    except Exception as e:
        hr_legal_error = str(e)
        print(f"❌ Failed to create HR Legal engine: {e}")
        return False

def startup_initialization():
    """Perform comprehensive startup initialization."""
    print("=" * 60)
    print("🚀 RESUME SCREENING APPLICATION - STARTUP INITIALIZATION")
    print("=" * 60)
    
    # 1. Initialize storage and load existing data
    try:
        print("📁 Loading existing resume storage...")
        resume_count = len(resume_storage.get_all_resumes_summary())
        print(f"✅ Resume storage loaded: {resume_count} existing resumes found")
    except Exception as e:
        print(f"⚠️  Warning: Resume storage initialization issue: {e}")
    
    # 2. Initialize AI processor
    try:
        print("🤖 Initializing AI processor...")
        ai_stats = ai_processor.get_stats()
        print(f"✅ AI processor ready: {ai_stats.get('total_processed', 0)} resumes processed in session")
    except Exception as e:
        print(f"⚠️  Warning: AI processor initialization issue: {e}")
    
    # 3. Auto-initialize HR Legal system
    legal_success = auto_initialize_legal_system()
    
    # 4. System health check
    print("🔍 System health check...")
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"💾 Memory: {memory.percent:.1f}% used ({memory.available / (1024**3):.1f}GB available)")
        
        # Check Ollama connection
        try:
            import requests
            response = requests.get(f"{OLLAMA_URL}/api/version", timeout=300)  # Increased from 30 to 300 seconds
            if response.status_code == 200:
                print(f"✅ Ollama connection: Available at {OLLAMA_URL}")
            else:
                print(f"⚠️  Ollama connection: Unexpected response code {response.status_code}")
        except Exception as ollama_error:
            print(f"❌ Ollama connection: Failed - {ollama_error}")
            
    except Exception as health_error:
        print(f"⚠️  Health check warning: {health_error}")
    
    # 5. Summary
    print("=" * 60)
    print("📊 STARTUP SUMMARY:")
    print(f"📁 Resume Storage: ✅ Ready ({resume_count} resumes)")
    print(f"🤖 AI Processor: ✅ Ready")
    if legal_success:
        print(f"⚖️  HR Legal System: ✅ Ready and Initialized")
    else:
        print(f"⚖️  HR Legal System: ❌ Failed ({hr_legal_error})")
    print("=" * 60)
    
    return legal_success

# Initialize components and perform startup sequence
if HR_LEGAL_AVAILABLE:
    try:
        # Initialize with the multi-provider AI system
        from multi_provider_ai import multi_provider_ai
        print("📦 HR Legal dependencies available")
    except Exception as e:
        hr_legal_error = str(e)
        print(f"❌ Failed to import HR Legal dependencies: {e}")
else:
    hr_legal_error = "HR Legal dependencies not available"

def cleanup_temp_files():
    """Clean up all temporary files created during app runtime."""
    logger.info("Starting comprehensive cleanup of temporary files...")
    
    try:
        # Clean up resume storage
        resume_storage.cleanup_old_files()
        
        # Clean up AI processor
        ai_processor.cleanup()
        
        # Clean up HR Legal system
        if HR_LEGAL_AVAILABLE and hr_legal_engine:
            try:
                hr_legal_engine.clear_cache()
                logger.info("HR Legal caches cleared")
            except Exception as e:
                logger.error(f"Error cleaning HR Legal system: {e}")
        
        # Clean up tracked temporary files
        for temp_file in temp_files_created[:]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    temp_files_created.remove(temp_file)
                    logger.info(f"Removed temp file: {temp_file}")
                except Exception as e:
                    logger.error(f"Error removing temp file {temp_file}: {e}")
        
        # Clean up any CSV files in temp directory that match our pattern
        try:
            temp_dir = tempfile.gettempdir()
            for filename in os.listdir(temp_dir):
                if filename.startswith('resume_analysis') and filename.endswith('.csv'):
                    csv_path = os.path.join(temp_dir, filename)
                    try:
                        # Only remove files older than 1 hour to avoid interfering with active downloads
                        file_age = datetime.now().timestamp() - os.path.getmtime(csv_path)
                        if file_age > 3600:  # 1 hour
                            os.remove(csv_path)
                            logger.info(f"Removed old CSV file: {csv_path}")
                    except Exception as e:
                        logger.error(f"Error removing CSV file {csv_path}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning temp directory: {e}")
        
        # Force garbage collection to free memory
        gc.collect()
        
        logger.info("Comprehensive cleanup completed.")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    cleanup_temp_files()
    sys.exit(0)

# Register cleanup functions
atexit.register(cleanup_temp_files)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def log_debug(source, level, message, data=None):
    """Add debug log entry."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "source": source,  # "backend" or "frontend"
        "level": level,    # "info", "warning", "error", "debug"
        "message": message,
        "data": data
    }
    debug_logs.append(log_entry)
    
    # Keep only last 1000 logs to prevent memory issues
    if len(debug_logs) > 1000:
        debug_logs.pop(0)
    
    # Enhanced console logging with visual separation for frontend logs
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if source.lower() == "frontend":
        # Make frontend logs more visible
        print(f"\n{'='*50}")
        print(f"🎨 [FRONTEND] {timestamp} - {level.upper()}")
        print(f"📝 {message}")
        if data:
            print(f"📊 Data: {data}")
        print(f"{'='*50}\n")
    else:
        # Standard backend logging
        logger.info(f"🔧 [BACKEND] {timestamp} - {level.upper()}: {message}")
        if data:
            logger.info(f"   📊 Data: {data}")
    
    return log_entry

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF using PyMuPDF, with OCR fallback for image-based PDFs."""
    try:
        print(f"🔍 [VERBOSE] Starting PDF text extraction from: {file_path}")
        text = ""
        doc = fitz.open(file_path)
        print(f"🔍 [VERBOSE] PDF opened successfully, pages: {len(doc)}")
        
        # First, try regular text extraction
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            print(f"🔍 [VERBOSE] Page {page_num + 1}: extracted {len(page_text)} characters")
            text += page_text
        
        total_chars = len(text.strip())
        print(f"🔍 [VERBOSE] Total characters from regular extraction: {total_chars}")
        print(f"🔍 [VERBOSE] Sample text (first 200 chars): {repr(text[:200])}")
        
        # If we got sufficient text, return it
        if text and len(text.strip()) >= 50:
            print(f"✅ [VERBOSE] Regular extraction successful, returning {total_chars} characters")
            doc.close()
            return text
        
        # If regular extraction failed or got very little text, try OCR
        print(f"⚠️ [VERBOSE] Regular PDF text extraction yielded insufficient text ({len(text.strip())} chars), trying OCR...")
        
        ocr_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            try:
                # Convert page to image
                print(f"🔍 [VERBOSE] Converting page {page_num + 1} to image for OCR...")
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Use OCR on the image
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_data))
                print(f"🔍 [VERBOSE] Running OCR on page {page_num + 1}...")
                page_ocr_text = pytesseract.image_to_string(img)
                print(f"🔍 [VERBOSE] OCR page {page_num + 1}: extracted {len(page_ocr_text)} characters")
                ocr_text += page_ocr_text + "\n"
            except Exception as ocr_error:
                print(f"❌ [VERBOSE] OCR failed for page {page_num + 1}: {ocr_error}")
                continue
        
        doc.close()
        
        ocr_chars = len(ocr_text.strip())
        print(f"🔍 [VERBOSE] Total OCR characters: {ocr_chars}")
        print(f"🔍 [VERBOSE] OCR sample text (first 200 chars): {repr(ocr_text[:200])}")
        
        # Return OCR text if we got any, otherwise return the original text
        if ocr_text.strip():
            print(f"✅ [VERBOSE] OCR extraction successful: {ocr_chars} characters")
            return ocr_text
        else:
            print(f"❌ [VERBOSE] Both regular and OCR extraction failed, returning {len(text.strip())} characters")
            return text
            
    except Exception as e:
        print(f"❌ [VERBOSE] Error extracting text from PDF: {e}")
        print(f"❌ [VERBOSE] Error type: {type(e).__name__}")
        import traceback
        print(f"❌ [VERBOSE] Full traceback: {traceback.format_exc()}")
        logger.error(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_image(file_path):
    """Extract text from image using pytesseract OCR."""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return None

def extract_text_from_docx(file_path):
    """Extract text from DOCX file."""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return None

def extract_text_from_file(file_path, filename):
    """Extract text from file based on its extension."""
    print(f"🎯 [VERBOSE] Starting text extraction for file: {filename}")
    print(f"🎯 [VERBOSE] File path: {file_path}")
    
    # Get file extension from filename
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    print(f"🎯 [VERBOSE] Detected file extension: {file_extension}")
    
    try:
        if file_extension == 'pdf':
            print(f"📄 [VERBOSE] Processing as PDF file")
            result = extract_text_from_pdf(file_path)
        elif file_extension == 'docx':
            print(f"📄 [VERBOSE] Processing as DOCX file")
            result = extract_text_from_docx(file_path)
        elif file_extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
            print(f"🖼️ [VERBOSE] Processing as image file")
            result = extract_text_from_image(file_path)
        else:
            print(f"❌ [VERBOSE] Unsupported file extension: {file_extension}")
            return None
        
        if result:
            result_length = len(result.strip())
            print(f"✅ [VERBOSE] Text extraction completed: {result_length} characters")
            print(f"📝 [VERBOSE] Preview (first 300 chars): {repr(result[:300])}")
        else:
            print(f"❌ [VERBOSE] Text extraction returned None")
            
        return result
        
    except Exception as e:
        print(f"❌ [VERBOSE] Exception in extract_text_from_file: {e}")
        import traceback
        print(f"❌ [VERBOSE] Full traceback: {traceback.format_exc()}")
        return None



def convert_to_markdown(text, filename):
    """Convert extracted text to simple markdown format for AI analysis."""
    markdown_content = f"""# Resume Analysis: {filename}

## Full Resume Content
---
{text}
---

*Processed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Note: All analysis and data extraction is performed by AI*
"""
    return markdown_content

def save_processed_resume(content, filename, format_type='md'):
    """Save processed resume in specified format."""
    try:
        base_name = os.path.splitext(filename)[0]
        processed_filename = f"{base_name}_processed.{format_type}"
        processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
        
        with open(processed_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Track this file for cleanup
        temp_files_created.append(processed_path)
        
        return processed_path, processed_filename
    except Exception as e:
        logger.error(f"Error saving processed resume: {e}")
        return None, None

def get_ai_analysis(markdown_content, filename):
    """Get comprehensive AI analysis using optimized processor."""
    log_debug("backend", "info", f"Starting optimized AI analysis for resume", {"filename": filename})
    
    try:
        # Use role requirements if available
        role_context = role_requirements.get("simple_description", "")
        
        # Use optimized AI processor
        result = ai_processor.process_single_resume(
            markdown_content, filename, role_context
        )
        
        log_debug("backend", "info", "Optimized AI analysis completed successfully", {
            "filename": filename,
            "has_analysis": bool(result)
        })
        
        return result
        
    except Exception as e:
        log_debug("backend", "error", f"Optimized AI analysis failed: {e}")
        raise

def get_batch_ai_analysis(resume_data_list):
    """Process multiple resumes using batch optimization."""
    log_debug("backend", "info", f"Starting batch AI analysis", {
        "resume_count": len(resume_data_list)
    })
    
    try:
        role_context = role_requirements.get("simple_description", "")
        
        # Use optimized batch processing
        results = ai_processor.process_batch_resumes(resume_data_list, role_context)
        
        log_debug("backend", "info", f"Batch AI analysis completed", {
            "processed_count": len(results),
            "success_count": len([r for r in results if not r.get('processing_error')])
        })
        
        return results
        
    except Exception as e:
        log_debug("backend", "error", f"Batch AI analysis failed: {e}")
        raise

def generate_email_with_ai(template_type, intent, placeholders, candidate_info):
    """Generate personalized email using AI."""
    try:
        # Get candidate information
        candidate_name = candidate_info.get('basic_info', {}).get('name', 'Candidate')
        candidate_email = candidate_info.get('basic_info', {}).get('email', '')
        
        # Create prompt for email generation
        template_info = email_templates.get(template_type, {})
        template_name = template_info.get('name', 'Email')
        
        # Build placeholder context
        placeholder_context = ""
        for key, value in placeholders.items():
            if value:
                placeholder_context += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        prompt = f"""You are a professional HR assistant. Generate a professional, personalized email for the following context:

Email Type: {template_name}
Intent: {intent}

Candidate Information:
- Name: {candidate_name}
- Email: {candidate_email}

Dynamic Information (use only the provided information):
{placeholder_context}

Please generate a professional email that:
1. Has an appropriate subject line
2. Is personalized with the candidate's name
3. Incorporates ONLY the provided dynamic information (don't make up missing details)
4. If interview_link is provided, use it as the main way to schedule/join the interview
5. If specific date/time is provided, mention it; otherwise keep it flexible
6. Maintains a professional yet friendly tone
7. Includes proper email structure (greeting, body, closing)
8. Is concise but complete
9. For interview invitations, focus on the scheduling link if provided

Return the response in the following JSON format:
{{
    "subject": "Email subject line",
    "body": "Email body content with proper formatting",
    "tone": "professional/friendly/formal",
    "estimated_reading_time": "X minutes"
}}"""

        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            },
            timeout=190  # Increased from 30 to 120 seconds for limited hardware
        )
        
        if response.status_code == 200:
            ai_response = response.json()
            email_content = ai_response.get('response', '')
            
            # Try to parse JSON response
            try:
                import re
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', email_content, re.DOTALL)
                if json_match:
                    email_data = json.loads(json_match.group())
                    return {
                        "success": True,
                        "email": email_data,
                        "raw_response": email_content
                    }
                else:
                    # Fallback: parse content manually
                    return {
                        "success": True,
                        "email": {
                            "subject": f"Re: Your Application - {template_name}",
                            "body": email_content,
                            "tone": "professional",
                            "estimated_reading_time": "1-2 minutes"
                        },
                        "raw_response": email_content
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, use the raw content
                return {
                    "success": True,
                    "email": {
                        "subject": f"Re: Your Application - {template_name}",
                        "body": email_content,
                        "tone": "professional",
                        "estimated_reading_time": "1-2 minutes"
                    },
                    "raw_response": email_content
                }
        else:
            return {
                "success": False,
                "error": f"AI service error: {response.status_code}"
            }
            
    except Exception as e:
        log_debug("backend", "error", f"Email generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def validate_ai_response(ai_response):
    """Legacy validation - now handled by OptimizedAIProcessor."""
    return ai_processor._validate_ai_response(ai_response)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint that verifies all system components."""
    try:
        from multi_provider_ai import multi_provider_ai
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "database": "healthy",
                "storage": "healthy",
                "ai_system": "checking..."
            }
        }
        
        # Check AI system status
        try:
            ai_status = multi_provider_ai.get_system_status()
            
            # Count healthy providers
            healthy_providers = sum(1 for provider in ai_status['providers'].values() if provider.get('healthy', False))
            total_providers = len(ai_status['providers'])
            
            if healthy_providers > 0:
                health_status["components"]["ai_system"] = "healthy"
                health_status["ai_providers"] = {
                    "healthy_count": healthy_providers,
                    "total_count": total_providers,
                    "primary_provider": ai_status.get('primary_provider'),
                    "providers": {k: v.get('healthy', False) for k, v in ai_status['providers'].items()}
                }
            else:
                health_status["components"]["ai_system"] = "degraded"
                health_status["ai_providers"] = {
                    "healthy_count": 0,
                    "total_count": total_providers,
                    "error": "No healthy AI providers available",
                    "recommendations": ai_status.get('recommendations', {})
                }
                health_status["status"] = "degraded"
                
        except Exception as ai_error:
            health_status["components"]["ai_system"] = "unhealthy"
            health_status["ai_error"] = str(ai_error)
            health_status["status"] = "degraded"
        
        # Check storage system
        try:
            resume_count = len(resume_storage.get_all_resumes_summary(limit=1))
            health_status["storage_info"] = {"resume_count": resume_count}
        except Exception as storage_error:
            health_status["components"]["storage"] = "degraded"
            health_status["storage_error"] = str(storage_error)
        
        # Overall status
        if health_status["status"] == "healthy":
            return jsonify(health_status), 200
        else:
            return jsonify(health_status), 503  # Service Unavailable but partially working
            
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Comprehensive debug information for Railway deployment."""
    debug_data = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "environment_variables": {
            "PORT": os.getenv("PORT", "Not set"),
            "FLASK_ENV": os.getenv("FLASK_ENV", "Not set"),
            "FLASK_APP": os.getenv("FLASK_APP", "Not set"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "Not set"),
            "RAILWAY_SERVICE_NAME": os.getenv("RAILWAY_SERVICE_NAME", "Not set"),
            "RAILWAY_DEPLOYMENT_ID": os.getenv("RAILWAY_DEPLOYMENT_ID", "Not set"),
            "DATABASE_URL": "Set" if os.getenv("DATABASE_URL") else "Not set",
            "SUPABASE_URL": "Set" if os.getenv("SUPABASE_URL") else "Not set",
            "SUPABASE_ANON_KEY": "Set" if os.getenv("SUPABASE_ANON_KEY") else "Not set",
            "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "Not set"),
            "SECRET_KEY": "Set" if os.getenv("SECRET_KEY") else "Not set"
        },
        "file_structure": {
            "app.py": os.path.exists("app.py"),
            "requirements.txt": os.path.exists("requirements.txt"),
            "Dockerfile": os.path.exists("Dockerfile"),
            "railway.toml": os.path.exists("railway.toml")
        },
        "supabase_status": SUPABASE_AVAILABLE,
        "ai_processor_status": ai_processor is not None,
        "storage_status": resume_storage is not None,
        "next_steps": [
            "1. Check Railway deployment logs for errors",
            "2. Verify all required environment variables are set",
            "3. Ensure Dockerfile builds successfully", 
            "4. Check if the app starts without errors",
            "5. Verify the health endpoint responds"
        ]
    }
    
    # Add system info
    try:
        debug_data["system_info"] = {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total // (1024**3),  # GB
            "memory_available": psutil.virtual_memory().available // (1024**3),  # GB
        }
    except:
        debug_data["system_info"] = "Unable to get system info"
    
    return jsonify(debug_data)

@app.route('/debug', methods=['GET'])
def debug_page():
    """HTML debug page for easier viewing."""
    debug_data = debug_info().get_json()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Backend Debug Information</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .debug-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ccc; border-radius: 5px; }}
            .env-var {{ background: #f0f0f0; padding: 5px; margin: 5px 0; }}
            .status-ok {{ color: green; }}
            .status-error {{ color: red; }}
            pre {{ background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <h1>Backend Debug Information</h1>
        <div class="debug-section">
            <h2>Environment Variables</h2>
            <div class="env-var">
                <strong>PORT:</strong> {debug_data['environment_variables']['PORT']} 
                <em>(Railway sets this automatically)</em>
            </div>
            <div class="env-var">
                <strong>FLASK_ENV:</strong> {debug_data['environment_variables']['FLASK_ENV']}
                <em>(Should be 'production')</em>
            </div>
            <div class="env-var">
                <strong>RAILWAY_ENVIRONMENT:</strong> {debug_data['environment_variables']['RAILWAY_ENVIRONMENT']}
                <em>(Should show Railway environment)</em>
            </div>
        </div>
        
        <div class="debug-section">
            <h2>Service Status</h2>
            <p>Supabase: {'✓ Available' if debug_data['supabase_status'] else '✗ Not Available'}</p>
            <p>AI Processor: {'✓ Ready' if debug_data['ai_processor_status'] else '✗ Not Ready'}</p>
            <p>Storage: {'✓ Ready' if debug_data['storage_status'] else '✗ Not Ready'}</p>
        </div>
        
        <div class="debug-section">
            <h2>Full Debug Data</h2>
            <pre>{json.dumps(debug_data, indent=2)}</pre>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/api/startup-status', methods=['GET'])
def get_startup_status():
    """Get comprehensive startup status for frontend to know when everything is ready."""
    try:
        # Check resume storage
        try:
            resume_count = len(resume_storage.get_all_resumes_summary())
            storage_ready = True
        except Exception as e:
            resume_count = 0
            storage_ready = False
        
        # Check AI processor
        try:
            ai_stats = ai_processor.get_stats()
            ai_ready = True
        except Exception as e:
            ai_stats = {}
            ai_ready = False
        
        # Check HR Legal system
        legal_ready = False
        legal_status = {}
        if HR_LEGAL_AVAILABLE and hr_legal_engine:
            try:
                legal_status = hr_legal_engine.get_system_status()
                legal_ready = legal_status.get('is_initialized', False)
            except Exception as e:
                legal_status = {"error": str(e)}
        
        # Check Ollama connection
        ollama_ready = False
        try:
            import requests
            response = requests.get(f"{OLLAMA_URL}/api/version", timeout=150)  # Increased from 3 to 15 seconds
            ollama_ready = response.status_code == 200
        except:
            pass
        
        # Overall system readiness
        all_systems_ready = storage_ready and ai_ready and legal_ready and ollama_ready
        
        startup_status = {
            "all_systems_ready": all_systems_ready,
            "systems": {
                "storage": {
                    "ready": storage_ready,
                    "resume_count": resume_count,
                    "message": "Resume storage operational" if storage_ready else "Resume storage error"
                },
                "ai_processor": {
                    "ready": ai_ready,
                    "stats": ai_stats,
                    "message": "AI processor operational" if ai_ready else "AI processor error"
                },
                "legal_system": {
                    "ready": legal_ready,
                    "available": HR_LEGAL_AVAILABLE,
                    "status": legal_status,
                    "message": "HR Legal system operational" if legal_ready else 
                               "HR Legal system not ready" if HR_LEGAL_AVAILABLE else 
                               "HR Legal dependencies not available"
                },
                "ollama": {
                    "ready": ollama_ready,
                    "url": OLLAMA_URL,
                    "model": OLLAMA_MODEL,
                    "message": "Ollama connection successful" if ollama_ready else "Ollama not available"
                }
            },
            "configuration": {
                "upload_folder": UPLOAD_FOLDER,
                "processed_folder": PROCESSED_FOLDER,
                "max_file_size_mb": MAX_CONTENT_LENGTH // (1024 * 1024),
                "allowed_extensions": list(ALLOWED_EXTENSIONS)
            },
            "checked_at": datetime.now().isoformat()
        }
        
        return jsonify(startup_status)
        
    except Exception as e:
        return jsonify({
            "all_systems_ready": False,
            "error": f"Startup status check failed: {str(e)}",
            "checked_at": datetime.now().isoformat()
        }), 500

@app.route('/api/debug/logs', methods=['GET'])
def get_debug_logs():
    """Get debug logs."""
    limit = request.args.get('limit', 100, type=int)
    source = request.args.get('source', None)  # Filter by source: 'backend' or 'frontend'
    level = request.args.get('level', None)    # Filter by level: 'info', 'warning', 'error', 'debug'
    
    filtered_logs = debug_logs
    
    if source:
        filtered_logs = [log for log in filtered_logs if log['source'] == source]
    
    if level:
        filtered_logs = [log for log in filtered_logs if log['level'] == level]
    
    # Return most recent logs first, limited by limit parameter
    return jsonify({
        "logs": filtered_logs[-limit:],
        "total_count": len(filtered_logs)
    })

# Track frontend connection
frontend_connected = False

@app.route('/api/debug/logs', methods=['POST'])
def add_debug_log():
    """Add debug log from frontend."""
    global frontend_connected
    
    try:
        # Check if this is the first frontend connection
        if not frontend_connected:
            frontend_connected = True
            print("\n" + "🎨" + "="*58)
            print("🎨 FRONTEND CONNECTED - Logs will now appear below")
            print("🎨" + "="*58 + "\n")
        
        data = request.get_json()
        log_entry = log_debug(
            source="frontend",
            level=data.get('level', 'info'),
            message=data.get('message', ''),
            data=data.get('data')
        )
        return jsonify({"status": "success", "log_id": len(debug_logs) - 1})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/debug/logs', methods=['DELETE'])
def clear_debug_logs():
    """Clear all debug logs."""
    global debug_logs
    debug_logs = []
    log_debug("backend", "info", "Debug logs cleared")
    return jsonify({"message": "Debug logs cleared"})

@app.route('/api/role-requirements', methods=['GET'])
def get_role_requirements():
    """Get current role requirements."""
    return jsonify(role_requirements)

@app.route('/api/role-requirements', methods=['POST'])
def set_role_requirements():
    """Set simple job requirements for AI comparison."""
    try:
        global role_requirements
        data = request.get_json()
        
        # Update role requirements with simple description
        role_requirements.update({
            "simple_description": data.get('simple_description', ''),
            "updated_at": datetime.now().isoformat()
        })
        
        log_debug("backend", "info", "Job requirements updated", {
            "description_length": len(role_requirements["simple_description"]),
            "description_preview": role_requirements["simple_description"][:100] + "..." if len(role_requirements["simple_description"]) > 100 else role_requirements["simple_description"]
        })
        
        return jsonify({
            "message": "Job requirements updated successfully",
            "role_requirements": role_requirements
        })
        
    except Exception as e:
        log_debug("backend", "error", f"Error updating job requirements: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/api/role-requirements', methods=['DELETE'])
def clear_role_requirements():
    """Clear job requirements."""
    global role_requirements
    role_requirements = {
        "simple_description": "",
        "updated_at": None
    }
    log_debug("backend", "info", "Job requirements cleared")
    return jsonify({"message": "Job requirements cleared"})

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle multiple file uploads with authentication and trial limits."""
    from middleware.auth import require_auth, get_current_user
    from middleware.trial_limits import check_trial_limits, track_resume_analysis, add_trial_info_to_response
    
    @require_auth
    @check_trial_limits
    @track_resume_analysis
    def _upload_files():
        """Internal upload function with authentication."""
        log_debug("backend", "info", "File upload request received")
        
        user = get_current_user()
        log_debug("backend", "info", f"Upload request from user: {user['email']} (Access: {user['access_type']})")
        
        if 'files' not in request.files:
            log_debug("backend", "error", "No files provided in request")
            return jsonify({"error": "No files provided"}), 400
        
        files = request.files.getlist('files')
        original_file_count = len(files)
        log_debug("backend", "info", f"Received {original_file_count} files for processing")
        
        # Get AI settings from request
        ai_settings = None
        if 'aiSettings' in request.form:
            try:
                ai_settings = json.loads(request.form['aiSettings'])
                log_debug("backend", "info", f"AI settings received: {ai_settings.get('provider', 'unknown')} - {ai_settings.get('model', 'unknown')}")
                
                # Generate user ID for secure key retrieval
                user_ip = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')
                user_id = hashlib.sha256(f"{user_ip}:{user_agent}".encode()).hexdigest()[:16]
                
                # Retrieve stored API key if needed
                if ai_settings.get('provider') != 'ollama':
                    stored_key = secure_key_manager.get_api_key(
                        ai_settings.get('provider'), 
                        ai_settings.get('model')
                    )
                    if stored_key:
                        ai_settings['apiKey'] = stored_key
                        log_debug("backend", "info", f"Retrieved stored API key for {ai_settings.get('provider')}")
                    else:
                        log_debug("backend", "warning", f"No stored API key found for {ai_settings.get('provider')}")
                        return jsonify({"error": f"No API key available for {ai_settings.get('provider')}"}), 400
                
            except json.JSONDecodeError:
                log_debug("backend", "error", "Invalid AI settings JSON")
                return jsonify({"error": "Invalid AI settings"}), 400
        
        if not ai_settings:
            log_debug("backend", "error", "No AI settings provided")
            return jsonify({"error": "AI settings are required"}), 400
        
        # Validate AI settings
        if not ai_settings.get('provider') or not ai_settings.get('model'):
            log_debug("backend", "error", "Incomplete AI settings")
            return jsonify({"error": "AI provider and model are required"}), 400
        
        # Update AI processor with new settings
        try:
            ai_processor.update_ai_settings(ai_settings)
            log_debug("backend", "info", "AI processor updated with new settings")
        except Exception as e:
            log_debug("backend", "error", f"Failed to update AI processor: {str(e)}")
            return jsonify({"error": f"Failed to configure AI provider: {str(e)}"}), 400
        
        # Deduplicate files to keep only unique resumes
        unique_files, duplicate_files = deduplicate_files(files)
        file_count = len(unique_files)
        
        # Log deduplication results
        if duplicate_files:
            duplicate_names = [f.filename for f in duplicate_files]
            log_debug("backend", "info", f"Removed {len(duplicate_files)} duplicate files: {duplicate_names}")
            log_debug("backend", "info", f"Processing {file_count} unique files (removed {len(duplicate_files)} duplicates)")
        else:
            log_debug("backend", "info", f"Processing {file_count} files (no duplicates found)")
        
        # Use unique files for processing
        files = unique_files
        
        # Check if we have any files left to process after deduplication
        if not files:
            response_data = {
                "results": [{"filename": f.filename, "status": "skipped", "message": "Duplicate filename - already processed"} for f in duplicate_files],
                "summary": {
                    "total_uploaded": original_file_count,
                    "processed": 0,
                    "errors": 0,
                    "duplicates_skipped": len(duplicate_files)
                },
                "message": "No unique files to process - all files were duplicates"
            }
            return jsonify(add_trial_info_to_response(response_data))
        
        # Memory check before processing
        memory_usage = psutil.virtual_memory().percent / 100.0
        if memory_usage > 0.85:
            log_debug("backend", "warning", f"High memory usage before processing: {memory_usage:.1%}")
            gc.collect()  # Force garbage collection
        
        # Determine processing strategy based on file count
        use_batch_processing = file_count >= config.BATCH_ANALYSIS_THRESHOLD
        
        if use_batch_processing:
            log_debug("backend", "info", f"Using batch processing for {file_count} files")
            return process_files_batch_authenticated(files, duplicate_files, user)
        else:
            log_debug("backend", "info", f"Using sequential processing for {file_count} files")
            return process_files_sequential_authenticated(files, duplicate_files, user)
    
    return _upload_files()
    
    # Log deduplication results
    if duplicate_files:
        duplicate_names = [f.filename for f in duplicate_files]
        log_debug("backend", "info", f"Removed {len(duplicate_files)} duplicate files: {duplicate_names}")
        log_debug("backend", "info", f"Processing {file_count} unique files (removed {len(duplicate_files)} duplicates)")
    else:
        log_debug("backend", "info", f"Processing {file_count} files (no duplicates found)")
    
    # Use unique files for processing
    files = unique_files
    
    # Check if we have any files left to process after deduplication
    if not files:
        return jsonify({
            "results": [{"filename": f.filename, "status": "skipped", "message": "Duplicate filename - already processed"} for f in duplicate_files],
            "summary": {
                "total_uploaded": original_file_count,
                "processed": 0,
                "errors": 0,
                "duplicates_skipped": len(duplicate_files)
            },
            "message": "No unique files to process - all files were duplicates"
        })
    
    # Memory check before processing
    memory_usage = psutil.virtual_memory().percent / 100.0
    if memory_usage > 0.85:
        log_debug("backend", "warning", f"High memory usage before processing: {memory_usage:.1%}")
        gc.collect()  # Force garbage collection
    
    # Determine processing strategy based on file count
    use_batch_processing = file_count >= config.BATCH_ANALYSIS_THRESHOLD
    
    if use_batch_processing:
        log_debug("backend", "info", f"Using batch processing for {file_count} files")
        return process_files_batch(files, duplicate_files)
    else:
        log_debug("backend", "info", f"Using sequential processing for {file_count} files")
        return process_files_sequential(files, duplicate_files)

def process_files_sequential_authenticated(files, duplicate_files, user):
    """Process files sequentially with user authentication."""
    from middleware.trial_limits import add_trial_info_to_response
    
    results = []
    
    # Add duplicate file notifications to results
    for dup_file in duplicate_files:
        results.append({
            "filename": dup_file.filename,
            "status": "skipped",
            "message": "Duplicate filename - already processed"
        })
    
    for file in files:
        if file.filename == '':
            continue
            
        log_debug("backend", "info", f"Processing file: {file.filename} for user: {user['email']}")
        
        if not allowed_file(file.filename):
            log_debug("backend", "warning", f"File type not allowed: {file.filename}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "File type not allowed"
            })
            continue
        
        try:
            result = process_single_file_authenticated(file, user)
            results.append(result)
            
            # Memory management - force cleanup after each file for large files
            if len(str(result)) > 50000:  # If result is very large
                gc.collect()
                
        except Exception as e:
            log_debug("backend", "error", f"Error processing file {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    log_debug("backend", "info", f"Sequential processing completed for user {user['email']}. {len([r for r in results if r['status'] == 'success'])} successful, {len([r for r in results if r['status'] == 'error'])} errors, {len([r for r in results if r['status'] == 'skipped'])} duplicates skipped")
    
    response_data = {
        "results": results,
        "summary": {
            "total_uploaded": len(files) + len(duplicate_files),
            "processed": len([r for r in results if r['status'] == 'success']),
            "errors": len([r for r in results if r['status'] == 'error']),
            "duplicates_skipped": len([r for r in results if r['status'] == 'skipped'])
        }
    }
    
    return jsonify(add_trial_info_to_response(response_data))

def process_files_batch_authenticated(files, duplicate_files, user):
    """Process files in batches for high volume with user authentication."""
    from middleware.trial_limits import add_trial_info_to_response
    
    all_results = []
    
    # Add duplicate file notifications to results
    for dup_file in duplicate_files:
        all_results.append({
            "filename": dup_file.filename,
            "status": "skipped",
            "message": "Duplicate filename - already processed"
        })
    
    # Process files in batches
    batch_size = config.BATCH_SIZE
    total_files = len(files)
    
    log_debug("backend", "info", f"Batch processing {total_files} files for user {user['email']} in batches of {batch_size}")
    
    for i in range(0, total_files, batch_size):
        batch = files[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_files + batch_size - 1) // batch_size
        
        log_debug("backend", "info", f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)")
        
        batch_results = []
        for file in batch:
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                batch_results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "File type not allowed"
                })
                continue
            
            try:
                result = process_single_file_authenticated(file, user)
                batch_results.append(result)
            except Exception as e:
                log_debug("backend", "error", f"Error processing file {file.filename}: {str(e)}")
                batch_results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": str(e)
                })
        
        all_results.extend(batch_results)
        
        # Memory management between batches
        gc.collect()
        memory_usage = psutil.virtual_memory().percent / 100.0
        log_debug("backend", "info", f"Batch {batch_num} completed. Memory usage: {memory_usage:.1%}")
        
        if memory_usage > 0.9:
            log_debug("backend", "warning", "High memory usage detected, forcing cleanup")
            gc.collect()
    
    log_debug("backend", "info", f"Batch processing completed for user {user['email']}. {len([r for r in all_results if r['status'] == 'success'])} successful, {len([r for r in all_results if r['status'] == 'error'])} errors")
    
    response_data = {
        "results": all_results,
        "summary": {
            "total_uploaded": len(files) + len(duplicate_files),
            "processed": len([r for r in all_results if r['status'] == 'success']),
            "errors": len([r for r in all_results if r['status'] == 'error']),
            "duplicates_skipped": len([r for r in all_results if r['status'] == 'skipped'])
        }
    }
    
    return jsonify(add_trial_info_to_response(response_data))

def process_single_file_authenticated(file, user):
    """Process a single file with user authentication and storage."""
    filename = secure_filename(file.filename)
    file_hash = None
    
    try:
        # Read file content
        file_content = file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Reset file pointer for further processing
        file.seek(0)
        
        # Check if this file was already processed
        existing_resume = resume_storage.get_resume_by_hash(file_hash)
        if existing_resume:
            log_debug("backend", "info", f"File {filename} already processed (hash: {file_hash[:8]})")
            return {
                "filename": filename,
                "status": "skipped",
                "message": "File already processed",
                "existing_data": existing_resume
            }
        
        # Save file temporarily for processing
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)
        temp_files_created.append(temp_path)
        
        # Extract text from file
        extracted_text = extract_text_from_file(temp_path, filename)
        
        if not extracted_text or len(extracted_text.strip()) < 5:  # Lowered from 20 to 5 for debugging
            print(f"❌ [VERBOSE] Text extraction insufficient: {len(extracted_text.strip()) if extracted_text else 0} characters")
            print(f"❌ [VERBOSE] Extracted text: {repr(extracted_text[:200]) if extracted_text else 'None'}")
            return {
                "filename": filename,
                "status": "error",
                "message": f"Could not extract sufficient text from file. Extracted {len(extracted_text.strip()) if extracted_text else 0} characters (minimum 5 required for debugging). Please ensure the PDF contains readable text or try a different file format."
            }
        
        # Get role requirements for analysis
        role_requirements_text = role_requirements.get("simple_description", "")
        
        # Process with AI
        ai_result = ai_processor.analyze_resume(extracted_text, role_requirements_text, filename)
        
        if "error" in ai_result:
            return {
                "filename": filename,
                "status": "error",
                "message": ai_result["error"]
            }
        
        # Store resume with user information
        resume_data = {
            **ai_result,
            "filename": filename,
            "extracted_text": extracted_text,
            "file_hash": file_hash,
            "processed_at": datetime.now().isoformat(),
            "user_id": user['user_id'],
            "user_email": user['email'],
            "is_trial_upload": user['access_type'] == 'trial',
            "access_level": user['access_type']
        }
        
        # Store in resume storage
        resume_data["filename"] = filename  # Ensure filename is in the resume_data
        resume_storage.store_resume(resume_data)
        
        # Also update database with user tracking
        if user_manager:
            try:
                # This would require updating the ResumeStorage to work with the new database schema
                # For now, we'll just log the successful processing
                log_debug("backend", "info", f"Resume {filename} processed and stored for user {user['email']}")
            except Exception as e:
                log_debug("backend", "warning", f"Failed to update database tracking: {e}")
        
        return {
            "filename": filename,
            "status": "success",
            "analysis": ai_result
        }
        
    except Exception as e:
        log_debug("backend", "error", f"Error processing {filename}: {str(e)}")
        return {
            "filename": filename,
            "status": "error",
            "message": str(e)
        }
    finally:
        # Clean up temporary file
        if file_hash:
            try:
                temp_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    if temp_path in temp_files_created:
                        temp_files_created.remove(temp_path)
            except Exception as e:
                log_debug("backend", "warning", f"Failed to clean up temp file {filename}: {e}")

def process_files_sequential(files, duplicate_files):
    """Process files sequentially (for smaller batches) - Legacy function."""
    results = []
    
    # Add duplicate file notifications to results
    for dup_file in duplicate_files:
        results.append({
            "filename": dup_file.filename,
            "status": "skipped",
            "message": "Duplicate filename - already processed"
        })
    
    for file in files:
        if file.filename == '':
            continue
            
        log_debug("backend", "info", f"Processing file: {file.filename}")
        
        if not allowed_file(file.filename):
            log_debug("backend", "warning", f"File type not allowed: {file.filename}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "File type not allowed"
            })
            continue
        
        try:
            result = process_single_file(file)
            results.append(result)
            
            # Memory management - force cleanup after each file for large files
            if len(str(result)) > 50000:  # If result is very large
                gc.collect()
                
        except Exception as e:
            log_debug("backend", "error", f"Error processing file {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    log_debug("backend", "info", f"Sequential processing completed. {len([r for r in results if r['status'] == 'success'])} successful, {len([r for r in results if r['status'] == 'error'])} errors, {len([r for r in results if r['status'] == 'skipped'])} duplicates skipped")
    return jsonify({
        "results": results,
        "summary": {
            "total_uploaded": len(files) + len(duplicate_files),
            "processed": len([r for r in results if r['status'] == 'success']),
            "errors": len([r for r in results if r['status'] == 'error']),
            "duplicates_skipped": len([r for r in results if r['status'] == 'skipped'])
        }
    })

def process_files_batch(files, duplicate_files):
    """Process files in batches for high volume (optimized)."""
    all_results = []
    
    # Add duplicate file notifications to results
    for dup_file in duplicate_files:
        all_results.append({
            "filename": dup_file.filename,
            "status": "skipped",
            "message": "Duplicate filename - already processed"
        })
    
    # First pass: extract text from all files
    file_data_list = []
    extraction_errors = []
    
    for file in files:
        if file.filename == '':
            continue
            
        if not allowed_file(file.filename):
            extraction_errors.append({
                "filename": file.filename,
                "status": "error",
                "message": "File type not allowed"
            })
            continue
        
        try:
            # Extract text and prepare for batch processing
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            file_extension = filename.rsplit('.', 1)[1].lower()
            extracted_text = extract_text_from_file(file_path, file_extension)
            
            if not extracted_text:
                extraction_errors.append({
                    "filename": filename,
                    "status": "error",
                    "message": "Could not extract text from file"
                })
                os.remove(file_path)  # Clean up
                continue
            
            markdown_content = convert_to_markdown(extracted_text, filename)
            
            file_data_list.append({
                "filename": filename,
                "markdown_content": markdown_content,
                "extracted_text": extracted_text,
                "file_path": file_path
            })
            
        except Exception as e:
            extraction_errors.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Text extraction failed: {str(e)}"
            })
    
    log_debug("backend", "info", f"Text extraction completed: {len(file_data_list)} successful, {len(extraction_errors)} errors")
    
    # Second pass: batch AI analysis
    if file_data_list:
        try:
            ai_results = get_batch_ai_analysis(file_data_list)
            
            # Third pass: store results and clean up
            for i, file_data in enumerate(file_data_list):
                try:
                    ai_analysis = ai_results[i] if i < len(ai_results) else None
                    
                    if not ai_analysis or ai_analysis.get('processing_error'):
                        all_results.append({
                            "filename": file_data["filename"],
                            "status": "error",
                            "message": ai_analysis.get('error_message', 'AI analysis failed') if ai_analysis else 'AI analysis failed'
                        })
                        continue
                    
                    # Create result object
                    result = {
                        "filename": file_data["filename"],
                        "status": "success",
                        "ai_analysis": ai_analysis,
                        "processed_at": datetime.now().isoformat(),
                        "text_length": len(file_data["extracted_text"]),
                        "markdown_length": len(file_data["markdown_content"])
                    }
                    
                    # Store using optimized storage
                    resume_id = resume_storage.store_resume(result)
                    result["id"] = resume_id
                    
                    all_results.append(result)
                    
                    # Clean up uploaded file
                    if os.path.exists(file_data["file_path"]):
                        os.remove(file_data["file_path"])
                    
                except Exception as e:
                    log_debug("backend", "error", f"Error storing result for {file_data['filename']}: {e}")
                    all_results.append({
                        "filename": file_data["filename"],
                        "status": "error",
                        "message": f"Storage failed: {str(e)}"
                    })
            
        except Exception as e:
            log_debug("backend", "error", f"Batch AI analysis failed: {e}")
            # Fall back to individual processing for remaining files
            for file_data in file_data_list:
                all_results.append({
                    "filename": file_data["filename"],
                    "status": "error",
                    "message": f"Batch processing failed: {str(e)}"
                })
    
    # Add extraction errors to results
    all_results.extend(extraction_errors)
    
    # Force memory cleanup after batch processing
    gc.collect()
    
    log_debug("backend", "info", f"Batch processing completed. {len([r for r in all_results if r['status'] == 'success'])} successful, {len([r for r in all_results if r['status'] == 'error'])} errors, {len([r for r in all_results if r['status'] == 'skipped'])} duplicates skipped")
    return jsonify({
        "results": all_results,
        "summary": {
            "total_uploaded": len(files) + len(duplicate_files),
            "processed": len([r for r in all_results if r['status'] == 'success']),
            "errors": len([r for r in all_results if r['status'] == 'error']),
            "duplicates_skipped": len([r for r in all_results if r['status'] == 'skipped'])
        }
    })

def process_single_file(file):
    """Process a single file (used by sequential processing)."""
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    try:
        # Extract text
        file_extension = filename.rsplit('.', 1)[1].lower()
        extracted_text = extract_text_from_file(file_path, file_extension)
        
        if not extracted_text:
            raise ValueError("Could not extract text from file")
        
        # Convert to markdown
        markdown_content = convert_to_markdown(extracted_text, filename)
        
        # Get AI analysis
        ai_analysis = get_ai_analysis(markdown_content, filename)
        
        # Create result object
        result = {
            "filename": filename,
            "status": "success",
            "ai_analysis": ai_analysis,
            "processed_at": datetime.now().isoformat(),
            "text_length": len(extracted_text),
            "markdown_length": len(markdown_content)
        }
        
        # Store using optimized storage
        resume_id = resume_storage.store_resume(result)
        result["id"] = resume_id
        
        log_debug("backend", "info", f"Successfully processed: {filename}")
        return result
        
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/api/resumes', methods=['GET'])
def get_resumes():
    """Get all processed resumes using optimized storage with user authentication."""
    from middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _authenticated_get_resumes():
        try:
            user = get_current_user()
            limit = request.args.get('limit', None, type=int)
            log_debug("backend", "info", f"Resumes requested by user: {user.get('email', user.get('username'))} (Access: {user['access_type']})")
            
            # Admin users can see all resumes, regular users see only their own
            if user.get('access_type') == 'admin' or user.get('is_admin') or user.get('admin_session'):
                log_debug("backend", "info", f"Admin user accessing all resumes")
                # For admin users, get all resumes from all users
                resumes_summary = resume_storage.get_all_resumes_summary(limit)
            else:
                # Get resumes for this specific user
                resumes_summary = resume_storage.get_user_resumes_summary(user['user_id'], limit)
            
            # Get full data for all resumes to ensure Dashboard compatibility
            resumes_with_data = []
            for resume_summary in resumes_summary:
                # Always try to get full resume data
                full_resume = resume_storage.get_resume(resume_summary['id'])
                if full_resume:
                    resumes_with_data.append(full_resume)
                else:
                    # Fallback: create a compatible structure from summary data
                    fallback_resume = {
                        "id": resume_summary['id'],
                        "filename": resume_summary['filename'],
                        "status": "success",  # Assume success if stored
                        "processed_at": resume_summary['processed_at'],
                        "text_length": resume_summary.get('text_length', 0),
                        "ai_analysis": {
                            "scores": resume_summary.get('scores', {}),
                            "basic_info": {},
                            "summary": "",
                            "skills": [],
                            "experience": [],
                            "education": [],
                            "certifications": [],
                            "projects": [],
                            "keywords": [],
                            "analysis": {},
                            "role_match": {},
                            "recommendations": {},
                            "executive_summary": "",
                            "raw_text": ""
                        }
                    }
                    resumes_with_data.append(fallback_resume)
            
            return jsonify({"resumes": resumes_with_data})
        except Exception as e:
            log_debug("backend", "error", f"Error getting resumes: {e}")
            return jsonify({"error": str(e)}), 500
    
    return _authenticated_get_resumes()

@app.route('/api/resumes/<int:resume_id>/markdown', methods=['GET'])
def get_resume_markdown(resume_id):
    """Get the processed markdown content of a specific resume with user authentication."""
    from middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _authenticated_get_resume_markdown():
        try:
            user = get_current_user()
            resume = resume_storage.get_resume(resume_id)
            if not resume:
                return jsonify({"error": "Resume not found"}), 404
            
            # Check if this resume belongs to the current user
            if resume.get('user_id') != user['user_id']:
                return jsonify({"error": "Access denied"}), 403
            
            # Extract markdown content from AI analysis
            markdown_content = resume.get('ai_analysis', {}).get('raw_text', '')
            if not markdown_content:
                return jsonify({"error": "Markdown content not available"}), 404
            
            return jsonify({
                "resume_id": resume_id,
                "filename": resume["filename"],
                "markdown_content": markdown_content
            })
        except Exception as e:
            log_debug("backend", "error", f"Error getting resume markdown: {e}")
            return jsonify({"error": str(e)}), 500
    
    return _authenticated_get_resume_markdown()

@app.route('/api/resumes/<int:resume_id>', methods=['GET'])
def get_resume(resume_id):
    """Get a specific resume by ID with user authentication."""
    from middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _authenticated_get_resume():
        try:
            user = get_current_user()
            resume = resume_storage.get_resume(resume_id)
            if not resume:
                return jsonify({"error": "Resume not found"}), 404
            
            # Check if this resume belongs to the current user
            if resume.get('user_id') != user['user_id']:
                return jsonify({"error": "Access denied"}), 403
            
            return jsonify(resume)
        except Exception as e:
            log_debug("backend", "error", f"Error getting resume {resume_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    return _authenticated_get_resume()

@app.route('/api/export', methods=['GET'])
def export_results():
    """Export results as CSV with trial access restrictions."""
    from middleware.auth import require_auth, get_current_user
    from middleware.trial_limits import check_export_access
    
    # Apply decorators to the actual function
    @require_auth
    @check_export_access
    def _authenticated_export():
        try:
            user = get_current_user()
            log_debug("backend", "info", f"CSV export requested by user: {user['email']} (Access: {user['access_type']})")
            
            # For trial users, this should be blocked by check_export_access decorator
            # But as additional safety, check again
            if user['access_type'] == 'trial':
                return jsonify({
                    "error": "CSV export not available in trial version",
                    "upgrade_required": True,
                    "message": "CSV export is only available to full access users. Contact Bear Systems to upgrade.",
                    "contact_info": "support@bearsystems.co.in"
                }), 403
            
            # Get all resumes for this user
            resumes_summary = resume_storage.get_user_resumes_summary(user['user_id'])
            
            if not resumes_summary:
                return jsonify({"error": "No data to export"}), 400
            
            log_debug("backend", "info", f"Exporting {len(resumes_summary)} resumes to CSV for user {user['email']}")
            
            # Prepare data for CSV with optimized loading
            data = []
            
            for resume_summary in resumes_summary:
                try:
                    # Get full resume data
                    resume = resume_storage.get_resume(resume_summary['id'])
                    if not resume:
                        continue
                    
                    ai_analysis = resume.get("ai_analysis", {})
                    
                    # Extract data from optimized structure
                    basic_info = ai_analysis.get("basic_info", {})
                    location = basic_info.get("location", {})
                    scores = ai_analysis.get("scores", {})
                    analysis = ai_analysis.get("analysis", {})
                    role_match = ai_analysis.get("role_match", {})
                    recommendations = ai_analysis.get("recommendations", {})
                    
                    # Get experience and education data
                    experience = ai_analysis.get("experience", [])
                    education = ai_analysis.get("education", [])
                    skills = ai_analysis.get("skills", [])
                    certifications = ai_analysis.get("certifications", [])
                    projects = ai_analysis.get("projects", [])
                    
                    # Current position info (first experience entry if available)
                    current_exp = experience[0] if experience else {}
                    
                    row = {
                        # Basic Information
                        "resume_id": resume_summary['id'],
                        "filename": resume.get("filename", ""),
                        "processed_at": resume.get("processed_at", ""),
                        "in_memory": resume_summary.get('in_memory', False),
                        
                        # Personal Data
                        "full_name": basic_info.get("name", ""),
                        "email": basic_info.get("email", ""),
                        "phone": basic_info.get("phone", ""),
                        "linkedin": basic_info.get("linkedin", ""),
                        "github": basic_info.get("github", ""),
                        "city": location.get("city", ""),
                        "state": location.get("state", ""),
                        "country": location.get("country", ""),
                        
                        # Current Position
                        "current_job_title": current_exp.get("job_title", ""),
                        "current_company": current_exp.get("company", ""),
                        "currently_working": current_exp.get("currently_working", False),
                        
                        # Summary and Skills
                        "professional_summary": ai_analysis.get("summary", ""),
                        "skills_count": len(skills),
                        "skills_list": " | ".join(skills[:20]),  # Limit for CSV readability
                        "keywords": " | ".join(ai_analysis.get("keywords", [])[:10]),
                        
                        # Experience
                        "total_positions": len(experience),
                        "experience_years": sum([exp.get("duration_months", 0) for exp in experience]) / 12 if experience else 0,
                        
                        # Education
                        "education_count": len(education),
                        "highest_degree": education[0].get("degree", "") if education else "",
                        "university": education[0].get("university", "") if education else "",
                        
                        # Certifications and Projects
                        "certifications_count": len(certifications),
                        "projects_count": len(projects),
                        
                        # Scores
                        "overall_score": scores.get("overall_score", 0),
                        "technical_skills_score": scores.get("technical_skills_score", 0),
                        "experience_score": scores.get("experience_score", 0),
                        "education_score": scores.get("education_score", 0),
                        "communication_score": scores.get("communication_score", 0),
                        "leadership_score": scores.get("leadership_score", 0),
                        "role_fit_score": scores.get("role_fit_score", 0),
                        "confidence_level": scores.get("confidence_level", 0),
                        
                        # Analysis
                        "experience_level": analysis.get("experience_level", ""),
                        "specialization_focus": analysis.get("specialization_focus", ""),
                        "strengths": " | ".join(analysis.get("strengths", [])),
                        "weaknesses": " | ".join(analysis.get("weaknesses", [])),
                        "career_trajectory": analysis.get("career_trajectory", ""),
                        
                        # Role Match
                        "requirements_match_percentage": role_match.get("requirements_match_percentage", 0),
                        "critical_requirements_met": " | ".join(role_match.get("critical_requirements_met", [])),
                        "missing_requirements": " | ".join(role_match.get("missing_requirements", [])),
                        "role_fit_rationale": role_match.get("role_fit_rationale", ""),
                        
                        # Recommendations
                        "hiring_decision": recommendations.get("hiring_decision", ""),
                        "decision_confidence": recommendations.get("decision_confidence", ""),
                        "key_decision_factors": " | ".join(recommendations.get("key_decision_factors", [])),
                        "interview_focus_areas": " | ".join(recommendations.get("interview_focus_areas", [])),
                        
                        # Executive Summary
                        "executive_summary": ai_analysis.get("executive_summary", ""),
                        
                        # Processing Info
                        "processing_error": ai_analysis.get("processing_error", False),
                        "error_message": ai_analysis.get("error_message", "")
                    }
                    data.append(row)
                    
                except Exception as e:
                    log_debug("backend", "error", f"Error processing resume {resume_summary['id']} for export: {e}")
                    continue
            
            if not data:
                return jsonify({"error": "No valid data to export"}), 400
            
            # Create DataFrame and save to CSV with timestamp
            df = pd.DataFrame(data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f'resume_analysis_{timestamp}.csv'
            csv_file = os.path.join(tempfile.gettempdir(), csv_filename)
            df.to_csv(csv_file, index=False)
            
            # Track this file for cleanup
            temp_files_created.append(csv_file)
            log_debug("backend", "info", f"Optimized CSV export created: {csv_filename} with {len(data)} resumes and {len(df.columns)} columns")
            
            return send_file(csv_file, as_attachment=True, download_name='resume_analysis.csv')
            
        except Exception as e:
            log_debug("backend", "error", f"Error during CSV export: {e}")
            return jsonify({"error": f"Export failed: {str(e)}"}), 500
    
    return _authenticated_export()

@app.route('/api/clear', methods=['DELETE'])
def clear_resumes():
    """Clear all processed resumes and their files for the current user."""
    from middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _authenticated_clear_resumes():
        try:
            user = get_current_user()
            log_debug("backend", "info", f"Clear resumes requested by user: {user['email']} (Access: {user['access_type']})")
            
            # Clear only resumes for this user
            cleared_count = resume_storage.clear_user_resumes(user['user_id'])
            log_debug("backend", "info", f"Cleared {cleared_count} resumes for user {user['email']}")
            return jsonify({"message": f"Cleared {cleared_count} resumes and processed files"})
        except Exception as e:
            log_debug("backend", "error", f"Error clearing resumes: {e}")
            return jsonify({"error": str(e)}), 500
    
    return _authenticated_clear_resumes()

@app.route('/api/stats', methods=['GET'])
def get_system_stats():
    """Get user-specific and system statistics with authentication."""
    from middleware.auth import require_auth, get_current_user
    
    @require_auth
    def _authenticated_get_stats():
        try:
            user = get_current_user()
            memory_usage = psutil.virtual_memory()
            
            # Get user-specific statistics
            user_resumes_count = resume_storage.get_user_resume_count(user['user_id'])
            user_storage_stats = resume_storage.get_user_storage_stats(user['user_id'])
            
            stats = {
                "user": {
                    "user_id": user['user_id'],
                    "email": user['email'],
                    "access_type": user['access_type'],
                    "resumes_processed": user_resumes_count,
                    "trial_usage": user.get('trial_usage', 0),
                    "trial_limit": 100 if user['access_type'] == 'trial' else None,
                    "remaining_analyses": (100 - user.get('trial_usage', 0)) if user['access_type'] == 'trial' else None
                },
                "system": {
                    "memory_usage_percent": memory_usage.percent,
                    "memory_available_gb": memory_usage.available / (1024**3),
                    "memory_total_gb": memory_usage.total / (1024**3)
                },
                "storage": user_storage_stats if user_storage_stats else resume_storage.get_stats(),
                "ai_processor": ai_processor.get_stats(),
                "configuration": {
                    "max_memory_cache_size": config.MAX_MEMORY_CACHE_SIZE,
                    "chunk_size": config.CHUNK_SIZE,
                    "max_concurrent_processing": config.MAX_CONCURRENT_PROCESSING,
                    "batch_analysis_threshold": config.BATCH_ANALYSIS_THRESHOLD,
                    "current_model": ai_processor.base_model
                }
            }
            
            return jsonify(stats)
        except Exception as e:
            log_debug("backend", "error", f"Error getting system stats: {e}")
            return jsonify({"error": str(e)}), 500
    
    return _authenticated_get_stats()

@app.route('/api/cleanup', methods=['POST'])
def manual_cleanup():
    """Manually trigger cleanup of temporary files."""
    try:
        cleanup_temp_files()
        return jsonify({"message": "Cleanup completed successfully"})
    except Exception as e:
        return jsonify({"error": f"Cleanup failed: {str(e)}"}), 500

# Email Management Endpoints

@app.route('/api/email/templates', methods=['GET'])
def get_email_templates():
    """Get available email templates."""
    return jsonify({"templates": email_templates})

@app.route('/api/email/candidates', methods=['GET'])
def get_candidates_for_email():
    """Get candidate list for email selection (simplified view)."""
    try:
        resumes_summary = resume_storage.get_all_resumes_summary()
        
        candidates = []
        for resume in resumes_summary:
            # Get basic candidate info for selection
            full_resume = resume_storage.get_resume(resume['id'])
            if full_resume:
                ai_analysis = full_resume.get("ai_analysis", {})
                basic_info = ai_analysis.get("basic_info", {})
                scores = ai_analysis.get("scores", {})
                
                candidate = {
                    "id": resume['id'],
                    "filename": full_resume.get("filename", ""),
                    "name": basic_info.get("name", "Unknown"),
                    "email": basic_info.get("email", ""),
                    "phone": basic_info.get("phone", ""),
                    "overall_score": scores.get("overall_score", 0),
                    "role_fit_score": scores.get("role_fit_score", 0),
                    "processed_at": full_resume.get("processed_at", ""),
                    "selected": False  # Default selection state
                }
                candidates.append(candidate)
        
        # Sort by overall score descending
        candidates.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return jsonify({"candidates": candidates})
    except Exception as e:
        log_debug("backend", "error", f"Error getting candidates for email: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/generate', methods=['POST'])
def generate_emails():
    """Generate emails for selected candidates."""
    try:
        data = request.get_json()
        candidate_ids = data.get('candidate_ids', [])
        template_type = data.get('template_type', 'custom')
        intent = data.get('intent', '')
        placeholders = data.get('placeholders', {})
        
        log_debug("backend", "info", f"Generating emails for {len(candidate_ids)} candidates", {
            "template_type": template_type,
            "intent": intent[:100]
        })
        
        if not candidate_ids:
            return jsonify({"error": "No candidates selected"}), 400
        
        if not intent.strip():
            return jsonify({"error": "Email intent is required"}), 400
        
        generated_batch = []
        
        for candidate_id in candidate_ids:
            try:
                # Get candidate information
                resume = resume_storage.get_resume(candidate_id)
                if not resume:
                    log_debug("backend", "warning", f"Resume not found for candidate {candidate_id}")
                    continue
                
                ai_analysis = resume.get("ai_analysis", {})
                
                # Generate email for this candidate
                email_result = generate_email_with_ai(
                    template_type, intent, placeholders, ai_analysis
                )
                
                if email_result["success"]:
                    email_data = {
                        "id": len(generated_emails) + len(generated_batch),
                        "candidate_id": candidate_id,
                        "candidate_name": ai_analysis.get("basic_info", {}).get("name", "Unknown"),
                        "candidate_email": ai_analysis.get("basic_info", {}).get("email", ""),
                        "template_type": template_type,
                        "intent": intent,
                        "placeholders": placeholders,
                        "subject": email_result["email"]["subject"],
                        "body": email_result["email"]["body"],
                        "tone": email_result["email"].get("tone", "professional"),
                        "estimated_reading_time": email_result["email"].get("estimated_reading_time", "1-2 minutes"),
                        "generated_at": datetime.now().isoformat(),
                        "status": "draft"  # draft, sent, failed
                    }
                    generated_batch.append(email_data)
                else:
                    log_debug("backend", "error", f"Failed to generate email for candidate {candidate_id}: {email_result.get('error')}")
            
            except Exception as e:
                log_debug("backend", "error", f"Error generating email for candidate {candidate_id}: {e}")
                continue
        
        # Store generated emails
        generated_emails.extend(generated_batch)
        
        log_debug("backend", "info", f"Generated {len(generated_batch)} emails successfully")
        
        return jsonify({
            "message": f"Generated {len(generated_batch)} emails",
            "emails": generated_batch,
            "total_generated": len(generated_batch),
            "total_requested": len(candidate_ids)
        })
        
    except Exception as e:
        log_debug("backend", "error", f"Error generating emails: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/generated', methods=['GET'])
def get_generated_emails():
    """Get all generated emails."""
    try:
        # Sort by generation time, most recent first
        sorted_emails = sorted(generated_emails, key=lambda x: x["generated_at"], reverse=True)
        
        return jsonify({
            "emails": sorted_emails,
            "total_count": len(sorted_emails)
        })
    except Exception as e:
        log_debug("backend", "error", f"Error getting generated emails: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/generated/<int:email_id>', methods=['GET'])
def get_generated_email(email_id):
    """Get a specific generated email."""
    try:
        email = next((e for e in generated_emails if e["id"] == email_id), None)
        if not email:
            return jsonify({"error": "Email not found"}), 404
        
        return jsonify(email)
    except Exception as e:
        log_debug("backend", "error", f"Error getting email {email_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/generated/<int:email_id>', methods=['PUT'])
def update_generated_email(email_id):
    """Update a generated email (e.g., edit content, change status)."""
    try:
        data = request.get_json()
        
        email_index = next((i for i, e in enumerate(generated_emails) if e["id"] == email_id), None)
        if email_index is None:
            return jsonify({"error": "Email not found"}), 404
        
        # Update allowed fields
        allowed_fields = ["subject", "body", "status", "notes"]
        for field in allowed_fields:
            if field in data:
                generated_emails[email_index][field] = data[field]
        
        generated_emails[email_index]["updated_at"] = datetime.now().isoformat()
        
        return jsonify({
            "message": "Email updated successfully",
            "email": generated_emails[email_index]
        })
    except Exception as e:
        log_debug("backend", "error", f"Error updating email {email_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/generated/<int:email_id>', methods=['DELETE'])
def delete_generated_email(email_id):
    """Delete a generated email."""
    try:
        email_index = next((i for i, e in enumerate(generated_emails) if e["id"] == email_id), None)
        if email_index is None:
            return jsonify({"error": "Email not found"}), 404
        
        deleted_email = generated_emails.pop(email_index)
        
        log_debug("backend", "info", f"Deleted email for candidate: {deleted_email['candidate_name']}")
        
        return jsonify({"message": "Email deleted successfully"})
    except Exception as e:
        log_debug("backend", "error", f"Error deleting email {email_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/clear', methods=['DELETE'])
def clear_generated_emails():
    """Clear all generated emails."""
    try:
        global generated_emails
        count = len(generated_emails)
        generated_emails = []
        
        log_debug("backend", "info", f"Cleared {count} generated emails")
        
        return jsonify({"message": f"Cleared {count} generated emails"})
    except Exception as e:
        log_debug("backend", "error", f"Error clearing generated emails: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/email/export', methods=['GET'])
def export_generated_emails():
    """Export generated emails as CSV."""
    try:
        if not generated_emails:
            return jsonify({"error": "No emails to export"}), 400
        
        # Prepare data for CSV
        export_data = []
        for email in generated_emails:
            export_data.append({
                "email_id": email["id"],
                "candidate_name": email["candidate_name"],
                "candidate_email": email["candidate_email"],
                "template_type": email["template_type"],
                "intent": email["intent"],
                "subject": email["subject"],
                "body": email["body"].replace('\n', ' '),  # Remove line breaks for CSV
                "tone": email["tone"],
                "estimated_reading_time": email["estimated_reading_time"],
                "status": email["status"],
                "generated_at": email["generated_at"],
                "updated_at": email.get("updated_at", ""),
                "notes": email.get("notes", "")
            })
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(export_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f'generated_emails_{timestamp}.csv'
        csv_file = os.path.join(tempfile.gettempdir(), csv_filename)
        df.to_csv(csv_file, index=False)
        
        # Track this file for cleanup
        temp_files_created.append(csv_file)
        
        log_debug("backend", "info", f"Exported {len(export_data)} emails to CSV")
        
        return send_file(csv_file, as_attachment=True, download_name='generated_emails.csv')
        
    except Exception as e:
        log_debug("backend", "error", f"Error exporting emails: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-ai', methods=['POST'])
def test_ai_connection():
    """Test AI provider connection with given settings."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        provider = data.get('provider')
        model = data.get('model')
        api_key = data.get('apiKey', '')
        
        if not provider or not model:
            return jsonify({"error": "Provider and model are required"}), 400
        
        # Check if this is admin code to list keys
        if api_key == "Eggp1an1F2shCvrry1!":
            stored_keys = secure_key_manager.list_stored_keys(api_key)
            if stored_keys is not None:
                return jsonify({
                    "admin_view": True,
                    "stored_keys": stored_keys,
                    "message": "Admin access granted"
                })
            else:
                return jsonify({"error": "Admin access denied"}), 403
        
        # Handle API key storage for cloud providers
        if provider != 'ollama' and api_key:
            success, message = secure_key_manager.store_api_key(provider, model, api_key)
            if not success and "already stored" in message:
                # Key already exists, retrieve it for testing
                stored_key = secure_key_manager.get_api_key(provider, model)
                if stored_key:
                    api_key = stored_key
                else:
                    return jsonify({"error": message}), 400
            elif not success:
                return jsonify({"error": message}), 400
        elif provider != 'ollama':
            # Try to get existing key
            stored_key = secure_key_manager.get_api_key(provider, model)
            if stored_key:
                api_key = stored_key
            else:
                return jsonify({"error": "No API key available for this provider/model"}), 400
        
        # Test the AI connection
        test_prompt = "Test connection. Please respond with 'Connection successful'."
        
        if provider == 'ollama':
            # Test Ollama connection
            try:
                response = requests.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": model,
                        "prompt": test_prompt,
                        "stream": False
                    },
                    timeout=190  # Increased from 30 to 120 seconds for limited hardware
                )
                
                if response.status_code == 200:
                    return jsonify({"message": "Ollama connection successful"})
                else:
                    return jsonify({"error": f"Ollama connection failed: {response.status_code}"}), 400
                    
            except requests.RequestException as e:
                return jsonify({"error": f"Ollama connection failed: {str(e)}"}), 400
        
        elif provider == 'openai':
            # Test OpenAI connection
            try:
                import openai
                openai.api_key = api_key
                
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=50
                )
                
                if response.choices:
                    return jsonify({"message": "OpenAI connection successful"})
                else:
                    return jsonify({"error": "OpenAI connection failed"}), 400
                    
            except Exception as e:
                return jsonify({"error": f"OpenAI connection failed: {str(e)}"}), 400
        
        elif provider == 'gemini':
            # Test Gemini connection
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                model_instance = genai.GenerativeModel(model)
                response = model_instance.generate_content(test_prompt)
                
                if response.text:
                    return jsonify({"message": "Gemini connection successful"})
                else:
                    return jsonify({"error": "Gemini connection failed"}), 400
                    
            except Exception as e:
                return jsonify({"error": f"Gemini connection failed: {str(e)}"}), 400
        
        else:
            return jsonify({"error": f"Unsupported AI provider: {provider}"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Test failed: {str(e)}"}), 500

def deduplicate_files(files):
    """Remove duplicate files based on filename, keeping only the first occurrence."""
    seen_names = set()
    unique_files = []
    duplicate_files = []
    
    for file in files:
        if file.filename == '':
            continue
            
        # Get the base filename without extension for comparison
        base_filename = os.path.splitext(file.filename)[0].lower().strip()
        
        if base_filename not in seen_names:
            seen_names.add(base_filename)
            unique_files.append(file)
        else:
            duplicate_files.append(file)
    
    return unique_files, duplicate_files

# =====================================================
# SUPABASE PERSISTENT STORAGE ENDPOINTS
# =====================================================

@app.route('/api/supabase/status', methods=['GET'])
def get_supabase_status():
    """Get Supabase connection status and statistics."""
    try:
        stats = resume_storage.get_supabase_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            "available": False,
            "error": str(e)
        }), 500

@app.route('/api/supabase/resumes', methods=['GET'])
def get_supabase_resumes():
    """Get all resumes from Supabase storage."""
    try:
        limit = request.args.get('limit', 1000, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        resumes = resume_storage.get_all_supabase_resumes(limit=limit)
        
        # Apply offset manually since we're getting all at once
        if offset > 0:
            resumes = resumes[offset:]
        
        return jsonify({
            "resumes": resumes,
            "total": len(resumes),
            "source": "supabase",
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "resumes": [],
            "total": 0
        }), 500

@app.route('/api/supabase/search', methods=['POST'])
def search_supabase_resumes():
    """Search resumes in Supabase storage."""
    try:
        data = request.get_json() or {}
        
        query = data.get('query', '')
        min_score = data.get('min_score', 0)
        skills = data.get('skills', [])
        limit = data.get('limit', 100)
        
        resumes = resume_storage.search_supabase_resumes(
            query=query,
            min_score=min_score,
            skills=skills,
            limit=limit
        )
        
        return jsonify({
            "resumes": resumes,
            "total": len(resumes),
            "search_params": {
                "query": query,
                "min_score": min_score,
                "skills": skills,
                "limit": limit
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "resumes": []
        }), 500

@app.route('/api/supabase/sync/<int:resume_id>', methods=['POST'])
def sync_resume_to_supabase(resume_id):
    """Manually sync a specific resume to Supabase."""
    try:
        success = resume_storage.sync_resume_to_supabase(resume_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Resume {resume_id} synced to Supabase successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Failed to sync resume {resume_id} to Supabase"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/supabase/sync-all', methods=['POST'])
def sync_all_resumes_to_supabase():
    """Sync all local resumes to Supabase."""
    try:
        local_resumes = resume_storage.get_all_resumes_summary()
        
        synced_count = 0
        failed_count = 0
        
        for resume in local_resumes:
            try:
                success = resume_storage.sync_resume_to_supabase(resume['id'])
                if success:
                    synced_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Error syncing resume {resume['id']}: {e}")
                failed_count += 1
        
        return jsonify({
            "success": True,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "total_processed": len(local_resumes)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/storage/combined', methods=['GET'])
def get_combined_resumes():
    """Get resumes from both local storage and Supabase."""
    try:
        # Get local resumes
        local_resumes = resume_storage.get_all_resumes_summary()
        
        # Get Supabase resumes
        supabase_resumes = resume_storage.get_all_supabase_resumes()
        
        # Mark the source for each resume
        for resume in local_resumes:
            resume['source'] = 'local'
        
        for resume in supabase_resumes:
            resume['source'] = 'supabase'
        
        # Combine and deduplicate based on file_hash
        combined = {}
        
        # Add local resumes first
        for resume in local_resumes:
            file_hash = resume.get('file_hash')
            if file_hash:
                combined[file_hash] = resume
        
        # Add Supabase resumes, avoiding duplicates
        for resume in supabase_resumes:
            file_hash = resume.get('file_hash')
            if file_hash and file_hash not in combined:
                combined[file_hash] = resume
        
        combined_resumes = list(combined.values())
        
        # Sort by upload/processed date
        combined_resumes.sort(
            key=lambda x: x.get('upload_date', x.get('processed_at', '')), 
            reverse=True
        )
        
        return jsonify({
            "resumes": combined_resumes,
            "total": len(combined_resumes),
            "local_count": len(local_resumes),
            "supabase_count": len(supabase_resumes),
            "source": "combined"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "resumes": []
        }), 500

# =====================================================
# HR LEGAL ENDPOINTS - Enhanced Agentic RAG System
# =====================================================

@app.route('/api/legal/status', methods=['GET'])
def get_legal_system_status():
    """Get the comprehensive status of the HR Legal system."""
    try:
        log_debug("backend", "info", "Checking HR Legal system status")
        
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
        except Exception as status_error:
            log_debug("backend", "error", f"Failed to get system status: {status_error}")
            status = {
                "initialized": False,
                "error": str(status_error),
                "status": "status_check_failed"
            }
        
        # Check AI provider status
        ai_status = {}
        try:
            from multi_provider_ai import multi_provider_ai
            if multi_provider_ai.current_provider:
                ai_status = {
                    "provider_available": True,
                    "provider_type": multi_provider_ai.current_provider.__class__.__name__,
                    "model": getattr(multi_provider_ai.current_provider, 'model', 'unknown')
                }
            else:
                ai_status = {
                    "provider_available": False,
                    "message": "No AI provider configured"
                }
        except Exception as ai_error:
            ai_status = {
                "provider_available": False,
                "error": str(ai_error)
            }
        
        # Check agent status
        agent_status = {}
        try:
            if hasattr(hr_legal_engine, 'agent') and hr_legal_engine.agent:
                agent_status = {
                    "agent_available": True,
                    "agent_type": hr_legal_engine.agent.__class__.__name__
                }
            else:
                agent_status = {
                    "agent_available": False,
                    "message": "Agent not initialized"
                }
        except Exception as agent_error:
            agent_status = {
                "agent_available": False,
                "error": str(agent_error)
            }
        
        # Determine overall availability
        overall_available = (
            HR_LEGAL_AVAILABLE and 
            hr_legal_engine is not None and 
            status.get('is_initialized', False) and
            ai_status.get('provider_available', False) and
            agent_status.get('agent_available', False)
        )
        
        comprehensive_status = {
            "available": overall_available,
            "status": status,
            "ai_provider": ai_status,
            "agent": agent_status,
            "dependencies": {
                "hr_legal_available": HR_LEGAL_AVAILABLE,
                "engine_created": hr_legal_engine is not None
            },
            "capabilities": {
                "advanced_query": overall_available,
                "compliance_check": overall_available,
                "document_generation": overall_available,
                "chat_interface": overall_available
            },
            "checked_at": datetime.now().isoformat()
        }
        
        log_debug("backend", "info", "HR Legal status check completed", {
            "overall_available": overall_available,
            "ai_provider_available": ai_status.get('provider_available', False),
            "agent_available": agent_status.get('agent_available', False)
        })
        
        return jsonify(comprehensive_status)
        
    except Exception as e:
        log_debug("backend", "error", f"Legal status check failed: {e}")
        return jsonify({
            "available": False,
            "error": f"Status check failed: {str(e)}",
            "status": "check_failed"
        }), 500

@app.route('/api/legal/initialize', methods=['POST'])
def initialize_legal_system():
    """Initialize the HR Legal system with proper error handling."""
    try:
        if not HR_LEGAL_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "HR Legal dependencies not installed",
                "required_packages": ["sentence-transformers", "faiss-cpu"],
                "install_command": "pip install sentence-transformers faiss-cpu"
            }), 503
        
        if not hr_legal_engine:
            return jsonify({
                "success": False,
                "error": hr_legal_error or "HR Legal engine not available",
                "suggestion": "Check system configuration and dependencies"
            }), 503
        
        log_debug("backend", "info", "Initializing HR Legal system")
        
        # Ensure the multi-provider AI system has a default provider set
        try:
            from multi_provider_ai import multi_provider_ai
            
            # If no provider is set, configure Ollama as default
            if not multi_provider_ai.current_provider:
                try:
                    multi_provider_ai.set_provider('ollama', OLLAMA_MODEL, base_url=OLLAMA_URL)
                    log_debug("backend", "info", f"Set default Ollama provider for HR Legal: {OLLAMA_MODEL}")
                except Exception as provider_error:
                    log_debug("backend", "warning", f"Failed to set default Ollama provider: {provider_error}")
                    return jsonify({
                        "success": False,
                        "error": f"Failed to configure AI provider: {str(provider_error)}"
                    }), 500
            else:
                log_debug("backend", "info", f"AI provider already configured: {multi_provider_ai.current_provider.__class__.__name__}")
        except ImportError as import_error:
            log_debug("backend", "error", f"Failed to import multi_provider_ai: {import_error}")
            return jsonify({
                "success": False,
                "error": "AI provider system not available"
            }), 503
        
        # Ensure the HR Legal engine has the AI provider properly set
        try:
            if hr_legal_engine and multi_provider_ai.current_provider:
                if hasattr(hr_legal_engine, 'set_ai_provider'):
                    hr_legal_engine.set_ai_provider(multi_provider_ai)
                    log_debug("backend", "info", "AI provider set for HR Legal engine")
                else:
                    log_debug("backend", "warning", "HR Legal engine does not have set_ai_provider method")
        except Exception as ai_set_error:
            log_debug("backend", "error", f"Failed to set AI provider for HR Legal: {ai_set_error}")
            return jsonify({
                "success": False,
                "error": f"Failed to configure HR Legal AI: {str(ai_set_error)}"
            }), 500
        
        # Initialize the system
        try:
            if hasattr(hr_legal_engine, 'initialize'):
                success = hr_legal_engine.initialize()
            else:
                log_debug("backend", "warning", "HR Legal engine does not have initialize method")
                success = True  # Assume initialized if method doesn't exist
                
            if success:
                try:
                    status = hr_legal_engine.get_system_status()
                except Exception as status_error:
                    log_debug("backend", "warning", f"Could not get status after init: {status_error}")
                    status = {"initialized": True, "status_check_failed": True}
                
                log_debug("backend", "info", "HR Legal system initialized successfully")
                
                return jsonify({
                    "success": True,
                    "message": "HR Legal system initialized successfully",
                    "status": status,
                    "initialized_at": datetime.now().isoformat()
                })
            else:
                error_msg = getattr(hr_legal_engine, 'initialization_error', 'Initialization failed')
                log_debug("backend", "error", f"HR Legal initialization failed: {error_msg}")
                return jsonify({
                    "success": False,
                    "error": error_msg or "Initialization failed"
                }), 500
                
        except Exception as init_error:
            log_debug("backend", "error", f"HR Legal initialization exception: {init_error}")
            return jsonify({
                "success": False,
                "error": f"Initialization failed: {str(init_error)}"
            }), 500
            
    except Exception as e:
        log_debug("backend", "error", f"Legal initialization failed with exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Initialization failed: {str(e)}"
        }), 500

@app.route('/api/legal/query', methods=['POST'])
def legal_query():
    """Process a legal query with customizable configuration."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Support both 'question' and 'query' fields for flexibility
        query = data.get('question', data.get('query', '')).strip()
        if not query:
            return jsonify({"error": "No question provided"}), 400
        
        log_debug("backend", "info", f"Processing legal query", {
            "query_length": len(query),
            "query_preview": query[:100] + "..." if len(query) > 100 else query
        })
        
        # Create configuration from request with proper validation
        config_data = data.get('config', {})
        
        try:
            # Validate enum values before creating config
            response_length_val = config_data.get('response_length', 'medium')
            if response_length_val not in [e.value for e in ResponseLength]:
                response_length_val = 'medium'
            
            response_style_val = config_data.get('response_style', 'professional')
            if response_style_val not in [e.value for e in ResponseStyle]:
                response_style_val = 'professional'
            
            detail_level_val = config_data.get('detail_level', 'balanced')
            if detail_level_val not in [e.value for e in DetailLevel]:
                detail_level_val = 'balanced'
            
            audience_level_val = config_data.get('audience_level', 'intermediate')
            if audience_level_val not in [e.value for e in AudienceLevel]:
                audience_level_val = 'intermediate'
            
            config = AgenticRAGConfig(
                response_length=ResponseLength(response_length_val),
                custom_word_count=config_data.get('custom_word_count'),
                response_style=ResponseStyle(response_style_val),
                detail_level=DetailLevel(detail_level_val),
                audience_level=AudienceLevel(audience_level_val),
                include_citations=config_data.get('include_citations', True),
                include_confidence=config_data.get('include_confidence', True),
                show_reasoning_chain=config_data.get('show_reasoning', False),
                include_follow_up_questions=config_data.get('include_follow_ups', True),
                include_case_examples=config_data.get('include_examples', True),
                structured_output=config_data.get('structured_output', True),
                retrieval_depth=min(config_data.get('retrieval_depth', 5), 10),  # Cap at 10
                similarity_threshold=max(0.3, min(config_data.get('similarity_threshold', 0.7), 1.0))  # Between 0.3-1.0
            )
        except Exception as config_error:
            log_debug("backend", "error", f"Invalid configuration provided: {config_error}")
            # Fall back to default configuration
            config = AgenticRAGConfig()
        
        # Create query context with validation
        context = LegalQueryContext(
            query=query,
            query_type=data.get('query_type', 'general'),
            conversation_id=data.get('conversation_id'),
            user_role=data.get('user_role', 'hr_professional'),
            urgency=data.get('urgency', 'normal')
        )
        
        # Check if HR Legal engine is properly initialized
        if not hasattr(hr_legal_engine, 'agent') or not hr_legal_engine.agent:
            log_debug("backend", "error", "HR Legal agent not available")
            return jsonify({
                "success": False,
                "error": "HR Legal agent not initialized"
            }), 503
        
        # Process query using the agent
        log_debug("backend", "info", "Sending query to HR Legal agent")
        response = hr_legal_engine.agent.process_query(query, config, context.conversation_id)
        
        if not response:
            log_debug("backend", "error", "HR Legal agent returned empty response")
            return jsonify({
                "success": False,
                "error": "Failed to generate response"
            }), 500
        
        # Validate response structure
        if not hasattr(response, 'to_dict'):
            log_debug("backend", "error", "Invalid response format from HR Legal agent")
            return jsonify({
                "success": False,
                "error": "Invalid response format"
            }), 500
        
        log_debug("backend", "info", "Legal query processed successfully", {
            "response_length": len(str(response.content)) if hasattr(response, 'content') else 0,
            "confidence": response.metadata.confidence_score if hasattr(response, 'metadata') else 0
        })
        
        # Return response
        return jsonify({
            "success": True,
            "response": response.to_dict()
        })
        
    except Exception as e:
        log_debug("backend", "error", f"Legal query processing failed: {e}")
        return jsonify({
            "success": False,
            "error": f"Query processing failed: {str(e)}"
        }), 500

@app.route('/api/legal/chat', methods=['POST'])
def legal_chat():
    """Handle conversational legal queries with memory."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        log_debug("backend", "info", f"Processing legal chat message", {
            "message_length": len(message),
            "message_preview": message[:100] + "..." if len(message) > 100 else message
        })
        
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            import uuid
            conversation_id = str(uuid.uuid4())
            log_debug("backend", "info", f"Generated new conversation ID: {conversation_id}")
        
        # Use default configuration for chat with user customizations
        config_data = data.get('config', {})
        config = AgenticRAGConfig(
            response_length=ResponseLength(config_data.get('response_length', 'medium')),
            response_style=ResponseStyle(config_data.get('response_style', 'professional')),
            include_follow_up_questions=config_data.get('include_follow_ups', True),
            include_citations=config_data.get('include_citations', True),
            structured_output=config_data.get('structured_output', False)  # More conversational for chat
        )
        
        # Check if HR Legal engine and agent are available
        if not hasattr(hr_legal_engine, 'agent') or not hr_legal_engine.agent:
            log_debug("backend", "error", "HR Legal agent not available for chat")
            return jsonify({
                "success": False,
                "error": "HR Legal agent not initialized"
            }), 503
        
        # Process query
        log_debug("backend", "info", "Sending chat message to HR Legal agent")
        response = hr_legal_engine.agent.process_query(
            message, config, conversation_id
        )
        
        if not response:
            log_debug("backend", "error", "HR Legal agent returned empty response for chat")
            return jsonify({
                "success": False,
                "error": "Failed to generate chat response"
            }), 500
        
        # Validate response structure
        if not hasattr(response, 'to_dict'):
            log_debug("backend", "error", "Invalid chat response format from HR Legal agent")
            return jsonify({
                "success": False,
                "error": "Invalid response format"
            }), 500
        
        log_debug("backend", "info", "Legal chat processed successfully", {
            "conversation_id": conversation_id,
            "response_length": len(str(response.content)) if hasattr(response, 'content') else 0
        })
        
        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "response": response.to_dict()
        })
        
    except Exception as e:
        log_debug("backend", "error", f"Legal chat failed: {e}")
        return jsonify({
            "success": False,
            "error": f"Chat processing failed: {str(e)}"
        }), 500

@app.route('/api/legal/compliance-check', methods=['POST'])
def compliance_check():
    """Check content for legal compliance."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        content = data.get('content', '').strip()
        content_type = data.get('type', 'general')  # job_description, policy, contract, etc.
        
        if not content:
            return jsonify({"error": "No content provided"}), 400
        
        if len(content) > 50000:  # Reasonable limit for compliance check
            return jsonify({"error": "Content too large. Please limit to 50,000 characters."}), 400
        
        log_debug("backend", "info", f"Processing compliance check", {
            "content_type": content_type,
            "content_length": len(content),
            "content_preview": content[:200] + "..." if len(content) > 200 else content
        })
        
        # Create compliance-focused query
        query = f"""Please review the following {content_type} for legal compliance with Indian labor laws. 

Content to review:
{content}

Please provide:
1. Compliance assessment (compliant/partially compliant/non-compliant)
2. Specific issues identified (if any)
3. Recommendations for improvement
4. Risk level assessment
5. Suggested modifications
6. Relevant legal references"""
        
        # Use compliance-focused configuration
        config = AgenticRAGConfig(
            response_length=ResponseLength.LONG,
            response_style=ResponseStyle.LEGAL,
            detail_level=DetailLevel.COMPREHENSIVE,
            include_citations=True,
            structured_output=True,
            include_case_examples=True,
            retrieval_depth=8,  # More thorough search for compliance
            similarity_threshold=0.6  # Lower threshold for broader compliance coverage
        )
        
        context = LegalQueryContext(
            query=query,
            query_type="compliance_check",
            user_role=data.get('user_role', 'hr_professional'),
            urgency=data.get('urgency', 'normal')
        )
        
        # Check if HR Legal engine and agent are available
        if not hasattr(hr_legal_engine, 'query'):
            if hasattr(hr_legal_engine, 'agent') and hr_legal_engine.agent:
                # Use agent if direct query method not available
                response = hr_legal_engine.agent.process_query(query, config, context.conversation_id)
            else:
                log_debug("backend", "error", "HR Legal query method not available")
                return jsonify({
                    "success": False,
                    "error": "HR Legal query system not available"
                }), 503
        else:
            response = hr_legal_engine.query(context, config)
        
        if not response:
            log_debug("backend", "error", "Compliance check returned empty response")
            return jsonify({
                "success": False,
                "error": "Failed to generate compliance analysis"
            }), 500
        
        # Validate response structure
        if not hasattr(response, 'to_dict'):
            log_debug("backend", "error", "Invalid compliance response format")
            return jsonify({
                "success": False,
                "error": "Invalid response format"
            }), 500
        
        response_dict = response.to_dict()
        
        # Enhance response with compliance-specific metadata
        compliance_result = {
            "success": True,
            "compliance_analysis": response_dict,
            "content_type": content_type,
            "content_stats": {
                "character_count": len(content),
                "word_count": len(content.split()),
                "analyzed_at": datetime.now().isoformat()
            }
        }
        
        log_debug("backend", "info", "Compliance check completed successfully", {
            "content_type": content_type,
            "response_length": len(str(response.content)) if hasattr(response, 'content') else 0,
            "confidence": response.metadata.confidence_score if hasattr(response, 'metadata') else 0
        })
        
        return jsonify(compliance_result)
        
    except Exception as e:
        log_debug("backend", "error", f"Compliance check failed: {e}")
        return jsonify({
            "success": False,
            "error": f"Compliance check failed: {str(e)}"
        }), 500

@app.route('/api/legal/document-templates', methods=['GET'])
def get_document_templates():
    """Get available legal document templates."""
    try:
        log_debug("backend", "info", "Retrieving document templates")
        
        templates = {
            "employment_contract": {
                "name": "Employment Contract",
                "description": "Standard employment contract template compliant with Indian labor laws",
                "category": "contracts",
                "required_fields": ["employee_name", "position", "salary", "start_date", "company_name"],
                "optional_fields": ["probation_period", "notice_period", "benefits", "working_hours"],
                "estimated_length": "3-5 pages"
            },
            "termination_letter": {
                "name": "Termination Letter",
                "description": "Employment termination letter template with proper legal notices",
                "category": "termination",
                "required_fields": ["employee_name", "position", "termination_date", "reason"],
                "optional_fields": ["notice_period", "final_settlement", "handover_details"],
                "estimated_length": "1-2 pages"
            },
            "policy_document": {
                "name": "HR Policy Document",
                "description": "HR policy document template for various organizational policies",
                "category": "policies",
                "required_fields": ["policy_name", "effective_date", "scope"],
                "optional_fields": ["procedures", "enforcement", "review_date", "exceptions"],
                "estimated_length": "2-4 pages"
            },
            "job_description": {
                "name": "Job Description",
                "description": "Compliant job description template with equal opportunity language",
                "category": "recruitment",
                "required_fields": ["job_title", "department", "qualifications", "responsibilities"],
                "optional_fields": ["experience_required", "salary_range", "benefits", "reporting_structure"],
                "estimated_length": "1-2 pages"
            },
            "offer_letter": {
                "name": "Job Offer Letter",
                "description": "Professional job offer letter template",
                "category": "recruitment",
                "required_fields": ["candidate_name", "position", "salary", "start_date", "company_name"],
                "optional_fields": ["benefits", "probation_details", "acceptance_deadline"],
                "estimated_length": "1-2 pages"
            },
            "nda_agreement": {
                "name": "Non-Disclosure Agreement",
                "description": "Standard NDA template for employees and contractors",
                "category": "agreements",
                "required_fields": ["party_name", "company_name", "effective_date"],
                "optional_fields": ["duration", "specific_information", "remedies"],
                "estimated_length": "2-3 pages"
            }
        }
        
        # Add metadata
        response_data = {
            "success": True,
            "templates": templates,
            "metadata": {
                "total_templates": len(templates),
                "categories": list(set(template["category"] for template in templates.values())),
                "retrieved_at": datetime.now().isoformat()
            }
        }
        
        log_debug("backend", "info", f"Retrieved {len(templates)} document templates")
        
        return jsonify(response_data)
        
    except Exception as e:
        log_debug("backend", "error", f"Failed to get document templates: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get templates: {str(e)}"
        }), 500

@app.route('/api/legal/generate-document', methods=['POST'])
def generate_legal_document():
    """Generate a legal document using AI."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        template_type = data.get('template_type', '').strip()
        fields = data.get('fields', {})
        
        if not template_type:
            return jsonify({"error": "No template type provided"}), 400
        
        # Validate template type
        valid_templates = ['employment_contract', 'termination_letter', 'policy_document', 'job_description']
        if template_type not in valid_templates:
            return jsonify({
                "error": f"Invalid template type. Must be one of: {', '.join(valid_templates)}"
            }), 400
        
        if not fields or not isinstance(fields, dict):
            return jsonify({"error": "Fields must be provided as a dictionary"}), 400
        
        log_debug("backend", "info", f"Generating legal document", {
            "template_type": template_type,
            "fields_count": len(fields),
            "fields": list(fields.keys())
        })
        
        # Create document generation query with detailed instructions
        fields_text = json.dumps(fields, indent=2)
        query = f"""Generate a professionally formatted {template_type.replace('_', ' ')} document using the following information:

Template Type: {template_type}
Required Information:
{fields_text}

Please ensure the document:
1. Follows Indian legal standards and requirements
2. Uses professional language and formatting
3. Includes all necessary legal clauses
4. Is complete and ready for use
5. Includes proper structure with headers and sections
6. Addresses compliance requirements
7. Uses clear and unambiguous language

Generate a complete document that can be directly used in professional HR contexts."""
        
        # Use document generation configuration
        config = AgenticRAGConfig(
            response_length=ResponseLength.DETAILED,  # Documents need to be comprehensive
            response_style=ResponseStyle.LEGAL,
            detail_level=DetailLevel.COMPREHENSIVE,
            structured_output=True,
            include_citations=True,
            include_case_examples=False,  # Focus on document content
            retrieval_depth=6,
            similarity_threshold=0.65
        )
        
        context = LegalQueryContext(
            query=query,
            query_type="document_generation",
            user_role=data.get('user_role', 'hr_professional'),
            urgency=data.get('urgency', 'normal')
        )
        
        # Check if HR Legal engine and agent are available
        if not hasattr(hr_legal_engine, 'query'):
            if hasattr(hr_legal_engine, 'agent') and hr_legal_engine.agent:
                # Use agent if direct query method not available
                response = hr_legal_engine.agent.process_query(query, config, context.conversation_id)
            else:
                log_debug("backend", "error", "HR Legal query method not available for document generation")
                return jsonify({
                    "success": False,
                    "error": "HR Legal query system not available"
                }), 503
        else:
            response = hr_legal_engine.query(context, config)
        
        if not response:
            log_debug("backend", "error", "Document generation returned empty response")
            return jsonify({
                "success": False,
                "error": "Failed to generate document"
            }), 500
        
        # Validate response structure
        if not hasattr(response, 'to_dict'):
            log_debug("backend", "error", "Invalid document generation response format")
            return jsonify({
                "success": False,
                "error": "Invalid response format"
            }), 500
        
        response_dict = response.to_dict()
        
        # Enhance response with document-specific metadata
        document_result = {
            "success": True,
            "document": response_dict,
            "template_type": template_type,
            "generation_info": {
                "fields_used": fields,
                "generated_at": datetime.now().isoformat(),
                "document_type": template_type.replace('_', ' ').title()
            }
        }
        
        log_debug("backend", "info", "Legal document generated successfully", {
            "template_type": template_type,
            "document_length": len(str(response.content)) if hasattr(response, 'content') else 0,
            "confidence": response.metadata.confidence_score if hasattr(response, 'metadata') else 0
        })
        
        return jsonify(document_result)
        
    except Exception as e:
        log_debug("backend", "error", f"Document generation failed: {e}")
        return jsonify({
            "success": False,
            "error": f"Document generation failed: {str(e)}"
        }), 500

@app.route('/api/legal/stats', methods=['GET'])
def get_legal_stats():
    """Get HR Legal system statistics."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "available": False,
                "error": "HR Legal system not available"
            })
        
        # Get comprehensive system status
        try:
            status = hr_legal_engine.get_system_status()
        except Exception as status_error:
            log_debug("backend", "error", f"Failed to get system status: {status_error}")
            status = {
                "initialized": False,
                "error": str(status_error)
            }
        
        # Get agent statistics if available
        agent_stats = {}
        try:
            if hasattr(hr_legal_engine, 'agent') and hr_legal_engine.agent:
                if hasattr(hr_legal_engine.agent, 'get_agent_stats'):
                    agent_stats = hr_legal_engine.agent.get_agent_stats()
                else:
                    agent_stats = {"message": "Agent stats method not available"}
            else:
                agent_stats = {"message": "Agent not initialized"}
        except Exception as agent_error:
            log_debug("backend", "error", f"Failed to get agent stats: {agent_error}")
            agent_stats = {"error": str(agent_error)}
        
        # Get AI provider information
        ai_provider_info = {}
        try:
            from multi_provider_ai import multi_provider_ai
            if multi_provider_ai.current_provider:
                ai_provider_info = {
                    "provider_type": multi_provider_ai.current_provider.__class__.__name__,
                    "model": getattr(multi_provider_ai.current_provider, 'model', 'unknown'),
                    "available": True
                }
            else:
                ai_provider_info = {
                    "provider_type": None,
                    "model": None,
                    "available": False,
                    "message": "No AI provider configured"
                }
        except Exception as ai_error:
            log_debug("backend", "error", f"Failed to get AI provider info: {ai_error}")
            ai_provider_info = {"error": str(ai_error)}
        
        # Compile comprehensive stats
        legal_stats = {
            "success": True,
            "system_status": status,
            "agent_stats": agent_stats,
            "ai_provider": ai_provider_info,
            "hr_legal_available": HR_LEGAL_AVAILABLE,
            "engine_initialized": hr_legal_engine is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        log_debug("backend", "info", "Legal stats retrieved successfully", {
            "system_initialized": status.get('initialized', False),
            "agent_available": bool(agent_stats and not agent_stats.get('error')),
            "ai_provider_available": ai_provider_info.get('available', False)
        })
        
        return jsonify(legal_stats)
        
    except Exception as e:
        log_debug("backend", "error", f"Legal stats retrieval failed: {e}")
        return jsonify({
            "success": False,
            "error": f"Stats retrieval failed: {str(e)}"
        }), 500

@app.route('/api/legal/rebuild-index', methods=['POST'])
def rebuild_legal_index():
    """Rebuild the legal knowledge base index."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
        
        log_debug("backend", "info", "Starting legal index rebuild")
        
        # Check if rebuild method exists
        if not hasattr(hr_legal_engine, 'rebuild_index'):
            log_debug("backend", "error", "Rebuild index method not available")
            return jsonify({
                "success": False,
                "error": "Rebuild index functionality not available"
            }), 503
        
        # Attempt to rebuild the index
        try:
            success = hr_legal_engine.rebuild_index()
        except Exception as rebuild_error:
            log_debug("backend", "error", f"Index rebuild failed: {rebuild_error}")
            return jsonify({
                "success": False,
                "error": f"Index rebuild failed: {str(rebuild_error)}"
            }), 500
        
        if success:
            # Get updated status after rebuild
            try:
                status = hr_legal_engine.get_system_status()
            except Exception as status_error:
                log_debug("backend", "warning", f"Failed to get status after rebuild: {status_error}")
                status = {"message": "Rebuild successful but status unavailable"}
            
            log_debug("backend", "info", "Legal index rebuilt successfully")
            
            return jsonify({
                "success": True,
                "message": "Legal index rebuilt successfully",
                "status": status,
                "rebuilt_at": datetime.now().isoformat()
            })
        else:
            log_debug("backend", "error", "Index rebuild returned false")
            return jsonify({
                "success": False,
                "error": "Failed to rebuild index - rebuild method returned false"
            }), 500
            
    except Exception as e:
        log_debug("backend", "error", f"Index rebuild failed with exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Index rebuild failed: {str(e)}"
        }), 500

@app.route('/api/legal/validate', methods=['POST'])
def validate_legal_system():
    """Validate the HR Legal system with a simple test query."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "valid": False,
                "error": "HR Legal system not available"
            }), 503
        
        log_debug("backend", "info", "Validating HR Legal system")
        
        # Simple test query
        test_query = "What are the basic requirements for an employment contract in India?"
        
        # Basic configuration for testing
        config = AgenticRAGConfig(
            response_length=ResponseLength.SHORT,
            response_style=ResponseStyle.PROFESSIONAL,
            include_citations=False,
            structured_output=False
        )
        
        context = LegalQueryContext(
            query=test_query,
            query_type="validation_test",
            user_role="system"
        )
        
        start_time = datetime.now()
        
        # Test the system
        if hasattr(hr_legal_engine, 'agent') and hr_legal_engine.agent:
            try:
                response = hr_legal_engine.agent.process_query(test_query, config, None)
                
                if response and hasattr(response, 'content'):
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    log_debug("backend", "info", "HR Legal system validation successful", {
                        "processing_time": processing_time,
                        "response_length": len(str(response.content))
                    })
                    
                    return jsonify({
                        "valid": True,
                        "message": "HR Legal system is working correctly",
                        "test_response_preview": str(response.content)[:200] + "...",
                        "processing_time_seconds": processing_time,
                        "validated_at": datetime.now().isoformat()
                    })
                else:
                    log_debug("backend", "error", "HR Legal validation failed - empty response")
                    return jsonify({
                        "valid": False,
                        "error": "System returned empty response"
                    }), 500
                    
            except Exception as test_error:
                log_debug("backend", "error", f"HR Legal validation failed: {test_error}")
                return jsonify({
                    "valid": False,
                    "error": f"System test failed: {str(test_error)}"
                }), 500
        else:
            log_debug("backend", "error", "HR Legal agent not available for validation")
            return jsonify({
                "valid": False,
                "error": "HR Legal agent not initialized"
            }), 503
        
    except Exception as e:
        log_debug("backend", "error", f"HR Legal validation exception: {e}")
        return jsonify({
            "valid": False,
            "error": f"Validation failed: {str(e)}"
        }), 500

@app.route('/api/legal/clear-cache', methods=['POST'])
def clear_legal_cache():
    """Clear all legal system caches."""
    try:
        if not HR_LEGAL_AVAILABLE or not hr_legal_engine:
            return jsonify({
                "error": "HR Legal system not available"
            }), 503
        
        log_debug("backend", "info", "Clearing legal system caches")
        
        # Check if clear_cache method exists
        if not hasattr(hr_legal_engine, 'clear_cache'):
            log_debug("backend", "warning", "Clear cache method not available on HR Legal engine")
            return jsonify({
                "success": True,
                "message": "Clear cache method not available - no action taken"
            })
        
        try:
            hr_legal_engine.clear_cache()
            log_debug("backend", "info", "Legal system caches cleared successfully")
            
            return jsonify({
                "success": True,
                "message": "Legal system caches cleared",
                "cleared_at": datetime.now().isoformat()
            })
        except Exception as cache_error:
            log_debug("backend", "error", f"Failed to clear legal caches: {cache_error}")
            return jsonify({
                "success": False,
                "error": f"Failed to clear caches: {str(cache_error)}"
            }), 500
        
    except Exception as e:
        log_debug("backend", "error", f"Cache clear operation failed: {e}")
        return jsonify({
            "success": False,
            "error": f"Cache clear failed: {str(e)}"
        }), 500

# =====================================================
# END HR LEGAL ENDPOINTS
# =====================================================

if __name__ == '__main__':
    # Perform comprehensive startup initialization
    startup_success = startup_initialization()
    
    # Get port from environment (Railway sets PORT automatically)
    port = int(os.environ.get('PORT', 8000))
    
    # Enhanced startup logging
    print("🔧 Backend Server Configuration")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Processed folder: {PROCESSED_FOLDER}")
    print(f"📁 Temp directory: {tempfile.gettempdir()}")
    print(f"🤖 Ollama URL: {OLLAMA_URL}")
    print(f"🤖 Ollama Model: {OLLAMA_MODEL}")
    print(f"🌐 Server port: {port}")
    print("🧹 Cleanup handlers registered for app shutdown")
    
    print("="*60)
    print(f"🚀 Starting Flask server on http://0.0.0.0:{port}")
    print("📊 All application logs (frontend + backend) will appear below:")
    print("="*60 + "\n")
    
    logger.info("=== Resume Screening Application Backend Started ===")
    log_debug("backend", "info", "Backend server initialization complete", {
        "legal_system_ready": startup_success,
        "resume_count": len(resume_storage.get_all_resumes_summary()),
        "ai_provider_ready": True if HR_LEGAL_AVAILABLE and hr_legal_engine else False,
        "port": port
    })
    
    try:
        # Use environment-based configuration for production
        is_production = os.environ.get('RAILWAY_ENVIRONMENT_NAME') or os.environ.get('NODE_ENV') == 'production'
        app.run(
            debug=not is_production,
            host='0.0.0.0',
            port=port,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n" + "="*60)
        print("🛑 Application interrupted by user")
        print("="*60)
        logger.info("Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        logger.error(f"Application error: {e}")
    finally:
        print("🧹 Cleaning up and shutting down...")
        logger.info("Application shutting down...")
        cleanup_temp_files()
