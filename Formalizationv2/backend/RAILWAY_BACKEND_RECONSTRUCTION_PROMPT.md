# 🚀 COMPREHENSIVE BACKEND RECONSTRUCTION PROMPT
# Railway Deployment - Resume Screening Application

## 🎯 PROJECT OVERVIEW

You are tasked with creating a complete, production-ready Flask backend for a Resume Screening Application that will be deployed on Railway. This is a comprehensive AI-powered system that processes resumes, provides HR legal guidance, and manages user authentication with trial limitations.

## 🏗️ ARCHITECTURE REQUIREMENTS

### Core Technology Stack
- **Framework**: Flask 3.0.3 with CORS enabled
- **Deployment**: Railway (with automatic PORT detection)
- **Database**: Supabase (PostgreSQL) - **EXISTING PERSISTENT STORAGE**
- **AI Processing**: Ollama integration (local LLM)
- **File Processing**: OCR support (pytesseract), PDF processing (PyMuPDF), DOCX parsing
- **Authentication**: Supabase Auth + Session management
- **Security**: Comprehensive middleware, input validation, audit logging

### Existing Supabase Database Schema (DO NOT RECREATE)
### Existing Supabase Database Schema (DO NOT RECREATE)

**CRITICAL: The database schema is already deployed in Supabase. DO NOT recreate these tables. Use the existing Supabase connection to access the persistent storage.**

Your Supabase database contains these tables:
- `user_profiles` - User authentication and profile data
- `resumes` - Resume storage and analysis results
- `user_activity` - Activity tracking and analytics
- `hr_legal_queries` - Legal query history and responses
- `system_config` - Application configuration
- `admin_users` - Admin user management

Connection details:
- **Supabase URL**: `https://uxnbnxvvijockfkzsyck.supabase.co`
- **Project**: Already configured with complete schema
- **Auth**: Supabase Auth enabled with RLS policies

Use the existing `supabase_manager.py` patterns for database operations.

## 🗄️ SUPABASE INTEGRATION PATTERNS

### Connection Setup
```python
from supabase import create_client, Client
import os

class SupabaseManager:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY') 
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.admin_client = create_client(self.supabase_url, self.supabase_service_key)
```

### User Authentication (Existing Pattern)
```python
# User login
async def authenticate_user(self, email: str, password: str):
    response = self.client.auth.sign_in_with_password({
        'email': email, 'password': password
    })
    return response

# Get user profile
async def get_user_profile(self, user_id: str):
    result = self.client.table('user_profiles').select('*').eq('user_id', user_id).execute()
    return result.data[0] if result.data else None
```

### Resume Operations (Connect to Existing Tables)
```python
# Store resume
async def store_resume(self, user_id: str, resume_data: dict):
    result = self.client.table('resumes').insert({
        'user_id': user_id,
        'filename': resume_data['filename'],
        'processed_content': resume_data['content'],
        'ai_analysis': json.dumps(resume_data['analysis']),
        'status': 'completed'
    }).execute()
    return result.data[0]

# Get user resumes  
async def get_user_resumes(self, user_id: str):
    result = self.client.table('resumes').select('*').eq('user_id', user_id).execute()
    return result.data
```

### Activity Tracking (Existing Table)
```python
async def log_user_activity(self, user_id: str, action: str, details: str):
    self.client.table('user_activity').insert({
        'user_id': user_id,
        'action': action,
        'details': details,
        'timestamp': datetime.utcnow().isoformat()
    }).execute()
```

## 🔐 AUTHENTICATION SYSTEM

### Supabase Authentication Integration
- **Primary Auth**: Supabase Auth system (already configured)
- **Session Management**: Supabase sessions + JWT tokens
- **User Storage**: `user_profiles` table in Supabase
- **Admin Management**: `admin_users` table in Supabase
- **RLS Policies**: Row Level Security already enabled

### Authorization Levels
1. **Public**: Health check, debug endpoints
2. **User**: Resume processing, personal data access (via Supabase RLS)
3. **Admin**: User management, system administration
4. **Trial Users**: Limited to 100 resume analyses (tracked in `user_profiles.trial_resumes_analyzed`)

### Supabase Connection Pattern
```python
from supabase import create_client, Client

class SupabaseManager:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.client = create_client(self.supabase_url, self.supabase_key)
```

## 📄 FILE PROCESSING SYSTEM

### Supported File Types
- **PDF**: PyMuPDF for text extraction
- **DOCX**: python-docx for document parsing
- **Images**: pytesseract OCR (PNG, JPG, JPEG)

### Processing Pipeline
1. **Upload Validation**: File type, size (max 10MB), malware scanning
2. **Text Extraction**: Format-specific extraction
3. **Content Processing**: Clean and normalize text
4. **AI Analysis**: Structured analysis via Ollama
5. **Storage**: Secure file storage with metadata

### OCR Configuration
```python
# Tesseract configuration
TESSERACT_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()[]{}"\'-/@#$%^&*+=_|\\<>~ '
```

## 🤖 AI INTEGRATION SYSTEM

### Ollama Configuration
- **Base URL**: Environment-based (Railway auto-detection)
- **Model**: qwen2.5:7b (primary), qwen2.5:3b (fast processing)
- **Context Length**: 8192 tokens
- **Temperature**: 0.1 for consistent results

### AI Analysis Schema
```json
{
  "basic_info": {
    "name": "string",
    "email": "string", 
    "phone": "string",
    "location": "string"
  },
  "summary": "Executive summary of candidate",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name", 
      "duration": "2020-2023",
      "description": "Role description"
    }
  ],
  "education": [
    {
      "degree": "Degree",
      "institution": "School Name",
      "year": "2020"
    }
  ],
  "certifications": ["cert1", "cert2"],
  "projects": [
    {
      "name": "Project Name",
      "description": "Project description",
      "technologies": ["tech1", "tech2"]
    }
  ],
  "scores": {
    "overall_score": 85,
    "technical_score": 90,
    "experience_score": 80,
    "education_score": 85,
    "skills_match": 75
  },
  "keywords": ["keyword1", "keyword2"],
  "analysis": {
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "recommendations": ["rec1", "rec2"]
  },
  "role_match": {
    "fit_percentage": 85,
    "matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "experience_relevance": "High"
  }
}
```

## 🛠️ HR LEGAL SYSTEM (Advanced Feature)

### RAG Engine Integration
- **Knowledge Base**: HR legal documents, policies, compliance guidelines
- **Vector Store**: FAISS-based semantic search
- **Response Generation**: Context-aware legal guidance
- **Quality Analysis**: Response validation and scoring

### Legal Query Processing
```python
class LegalQueryContext:
    def __init__(self):
        self.query_type = ""  # "compliance", "policy", "document_review"
        self.urgency_level = ""  # "low", "medium", "high", "critical"
        self.response_length = ""  # "brief", "detailed", "comprehensive"
        self.audience_level = ""  # "hr_professional", "legal_expert", "executive"
```

## 🌐 API ENDPOINTS SPECIFICATION

### Authentication Endpoints
```python
# Admin Authentication
POST /api/auth/admin-login
Body: {"username": "admin", "password": "password"}
Response: {"success": true, "token": "session_token", "user": {...}}

# User Creation (Admin Only)
POST /api/auth/create-user
Headers: {"Authorization": "Bearer <admin_token>"}
Body: {"email": "user@example.com", "name": "User Name", "password": "password", "access_type": "trial"}
Response: {"success": true, "user": {...}}

# User Authentication
POST /api/auth/user-login
Body: {"email": "user@example.com", "password": "password"}
Response: {"success": true, "token": "session_token", "user": {...}, "trial_status": {...}}

# Session Validation
GET /api/auth/session
Headers: {"Authorization": "Bearer <token>"}
Response: {"valid": true, "user": {...}, "trial_status": {...}}

# Logout
POST /api/auth/logout
Headers: {"Authorization": "Bearer <token>"}
Response: {"message": "Logout successful"}
```

### Resume Processing Endpoints
```python
# Resume Upload
POST /api/upload
Headers: {"Authorization": "Bearer <token>"}
Body: FormData with files
Response: {"results": [{"filename": "resume.pdf", "status": "success", "id": 123}]}

# Get All Resumes
GET /api/resumes
Headers: {"Authorization": "Bearer <token>"}
Query: ?limit=50
Response: {"resumes": [...]}

# Get Single Resume
GET /api/resumes/<id>
Headers: {"Authorization": "Bearer <token>"}
Response: {"resume": {...}}

# Get Resume Markdown
GET /api/resumes/<id>/markdown
Headers: {"Authorization": "Bearer <token>"}
Response: {"markdown": "# Resume Content..."}

# Export Resumes (Full Users Only)
GET /api/export
Headers: {"Authorization": "Bearer <token>"}
Response: CSV file download

# Get Statistics
GET /api/stats
Headers: {"Authorization": "Bearer <token>"}
Response: {"total_resumes": 50, "avg_score": 75, "user_stats": {...}}

# Clear Resumes
DELETE /api/clear
Headers: {"Authorization": "Bearer <token>"}
Response: {"message": "Cleared X resumes"}
```

### Trial Management Endpoints
```python
# Get Trial Status
GET /api/trial/status
Headers: {"Authorization": "Bearer <token>"}
Response: {"trial_resumes_analyzed": 25, "trial_limit": 100, "remaining": 75}

# Track Usage (Internal)
POST /api/trial/track-usage
Headers: {"Authorization": "Bearer <token>"}
Body: {"action": "resume_analysis"}
Response: {"success": true, "remaining": 74}

# Get Upgrade Information
GET /api/trial/upgrade-info
Headers: {"Authorization": "Bearer <token>"}
Response: {"upgrade_options": [...], "contact_info": {...}}
```

### HR Legal Endpoints (Premium Feature)
```python
# Legal Query
POST /api/hr-legal/query
Headers: {"Authorization": "Bearer <token>"}
Body: {
  "query": "What are the legal requirements for background checks?",
  "context": {
    "query_type": "compliance",
    "urgency_level": "medium",
    "response_length": "detailed",
    "audience_level": "hr_professional"
  }
}
Response: {"response": "...", "sources": [...], "confidence": 0.85}

# Compliance Check
POST /api/hr-legal/compliance-check
Headers: {"Authorization": "Bearer <token>"}
Body: {"document_type": "job_posting", "content": "..."}
Response: {"compliant": true, "issues": [], "recommendations": [...]}

# Document Generation
POST /api/hr-legal/generate-document
Headers: {"Authorization": "Bearer <token>"}
Body: {"template_type": "offer_letter", "data": {...}}
Response: {"document": "...", "format": "markdown"}
```

### System Endpoints
```python
# Health Check
GET /api/health
Response: {"status": "healthy", "timestamp": "...", "version": "1.0.0"}

# Debug Information (Development)
GET /api/debug
Response: {"system_info": {...}, "ai_status": {...}, "database_status": {...}}
```

## 🚀 RAILWAY DEPLOYMENT CONFIGURATION

### Environment Variables (ACTUAL VALUES)
```bash
# ==========================================================================
# RAILWAY PRODUCTION ENVIRONMENT VARIABLES
# ==========================================================================

# Server Configuration
PORT=8000  # Railway auto-sets this
FLASK_ENV=production
NODE_ENV=production
FLASK_DEBUG=False

# Supabase Configuration (EXISTING PERSISTENT STORAGE)
SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTEyNjY5MSwiZXhwIjoyMDY0NzAyNjkxfQ.id-q8WoSmAAsdX5frY-egbY4PorDyxumPdeSQFuEDdc
SUPABASE_JWT_SECRET=your-jwt-secret-here

# AI Configuration (Ollama)
OLLAMA_URL=http://localhost:11434
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_MODEL=qwen2.5:7b
DEFAULT_AI_MODEL=qwen2.5:7b
AI_TIMEOUT=300

# Security Configuration
SECRET_KEY=your-secure-flask-secret-key-here
BCRYPT_LOG_ROUNDS=12
JWT_EXPIRATION_DELTA=7200  # 2 hours

# File Processing Configuration
MAX_CONTENT_LENGTH=16777216  # 16MB
MAX_FILE_SIZE=10485760      # 10MB
UPLOAD_FOLDER=/tmp/uploads
PROCESSED_FOLDER=/tmp/processed

# Trial System Configuration
DEFAULT_TRIAL_LIMIT=100
DEFAULT_TRIAL_DAYS=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/tmp/logs/application.log

# CORS Configuration (for frontend connection)
FRONTEND_URL=https://your-vercel-frontend.vercel.app

# HR Legal System (Optional)
HR_LEGAL_ENABLED=true
LEGAL_KNOWLEDGE_PATH=/app/legal_knowledge

# Redis Configuration (optional for caching)
REDIS_URL=redis://localhost:6379

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Production Requirements (Supabase-focused)
```txt
# Core Flask dependencies
Flask==3.0.3
Flask-CORS==4.0.1
Flask-Limiter==3.8.0
gunicorn==22.0.0

# Supabase Integration (PRIMARY DATABASE)
supabase==2.5.1
postgrest==0.16.8
gotrue==2.4.2
psycopg2-binary==2.9.9

# File processing dependencies
pytesseract==0.3.13
PyMuPDF==1.24.5
python-docx==1.1.2
Pillow==10.4.0

# AI and ML dependencies
requests==2.32.3
numpy>=1.24.0,<2.0.0
pandas>=2.2.0,<2.3.0
sentence-transformers>=3.0.0
faiss-cpu>=1.8.0

# Security and validation
bcrypt==4.2.0
cryptography==43.0.0
PyJWT==2.8.0
python-dotenv==1.0.1

# System utilities
psutil==6.0.0
python-dateutil==2.9.0.post0
```

### Docker Configuration
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/processed /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Expose port
EXPOSE 8000

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "300", "app:app"]
```

## 🔧 IMPLEMENTATION PRIORITIES

### Phase 1: Supabase Connection & Core Infrastructure (Day 1-2)
1. **Supabase Integration**: Connect to existing persistent storage
2. **Authentication System**: Supabase Auth integration
3. **Basic API Structure**: Flask app, CORS, error handling
4. **Environment Setup**: Railway-specific configuration

### Phase 2: Resume Processing APIs (Day 3-4)  
1. **File Upload Endpoint**: Connect to existing `resumes` table
2. **Text Extraction**: PDF, DOCX, OCR processing
3. **AI Integration**: Ollama connection, prompt engineering
4. **Data Storage**: Store results in existing Supabase schema

### Phase 3: User Management APIs (Day 5-6)
1. **Authentication Endpoints**: Login, logout, session validation
2. **User Profile Management**: Connect to `user_profiles` table
3. **Trial System**: Usage tracking via existing schema
4. **Admin Endpoints**: User creation and management

### Phase 4: Advanced Features (Day 7-8) 
1. **Export Functionality**: CSV generation for full users
2. **Statistics**: User-specific and admin dashboards
3. **HR Legal System**: RAG engine integration
4. **Performance Optimization**: Caching, connection pooling

### Phase 5: Production Hardening (Day 9-10)
1. **Security Audit**: Input validation, Supabase RLS verification
2. **Performance Testing**: Load testing, optimization
3. **Error Handling**: Comprehensive error responses
4. **Railway Deployment**: Production deployment and testing

## 🧪 TESTING REQUIREMENTS

### Unit Tests
- Authentication flow testing
- File processing validation
- AI response parsing
- Database operations

### Integration Tests
- End-to-end user workflows
- File upload to AI analysis pipeline
- Trial limitation enforcement
- Admin user management

### Performance Tests
- 100+ concurrent users
- Large file processing (10MB PDFs)
- AI response time optimization
- Database query performance

## 📊 MONITORING & LOGGING

### Application Logging
```python
# Structured logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/app/logs/application.log',
            'formatter': 'detailed'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}
```

### Health Monitoring
- **Endpoint**: `/api/health`
- **Metrics**: Database connection, AI service status, disk space
- **Alerts**: Failed authentication attempts, system errors
- **Performance**: Response times, throughput metrics

## 🎯 SUCCESS CRITERIA

### Functional Requirements
- ✅ All API endpoints operational
- ✅ File processing for PDF, DOCX, images
- ✅ AI analysis generating structured data
- ✅ User authentication and authorization
- ✅ Trial limitations properly enforced
- ✅ Admin user management functional

### Performance Requirements
- ✅ Resume processing under 30 seconds
- ✅ API response times under 2 seconds
- ✅ Support 100+ concurrent users
- ✅ 99.9% uptime on Railway

### Security Requirements
- ✅ All endpoints properly authenticated
- ✅ Input validation and sanitization
- ✅ Secure session management
- ✅ SQL injection prevention
- ✅ File upload security

## 🚨 CRITICAL CONSIDERATIONS

### Supabase Integration Specifics
- **Existing Schema**: DO NOT recreate database tables - use existing Supabase schema
- **RLS Policies**: Row Level Security is already configured - respect existing policies
- **Auth Integration**: Use Supabase Auth system for user management
- **Connection Pattern**: Follow existing `supabase_manager.py` patterns
- **Data Persistence**: All data stored in existing Supabase tables

### Railway Deployment Specifics  
- **PORT Detection**: Use `int(os.environ.get('PORT', 8000))`
- **File Storage**: Use `/tmp` for temporary files
- **Database**: Connect to existing Supabase PostgreSQL
- **Memory Limits**: Optimize for Railway's resource constraints
- **Startup Time**: Minimize cold start delays

### Frontend Connection Requirements
- **API Base URL**: `https://backend-production-7fe0.up.railway.app` 
- **CORS Configuration**: Allow frontend domain
- **Authentication**: Compatible with existing frontend auth flow
- **Response Format**: Maintain compatibility with existing frontend expectations

### Error Handling Strategy
- **Graceful Degradation**: Continue operation if AI service fails
- **User-Friendly Messages**: Clear error responses for frontend
- **Automatic Retry**: Implement retry logic for transient failures
- **Fallback Options**: Backup processing methods
- **Supabase Connectivity**: Handle Supabase connection failures gracefully

### Security Hardening
- **Input Validation**: Validate all user inputs
- **File Scanning**: Check uploaded files for malware  
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Audit Trail**: Log activities to existing `user_activity` table
- **Supabase RLS**: Leverage existing Row Level Security policies

---

**This prompt provides a complete specification for rebuilding the backend from scratch with a focus on connecting to your existing Supabase persistent storage. The database schema is already deployed and should NOT be recreated. Follow the Supabase integration patterns, use the provided environment variables, and ensure the backend APIs are compatible with your existing frontend. The resulting system should be production-ready for Railway deployment with comprehensive connection to your existing Supabase infrastructure.**

## 📋 **IMPLEMENTATION CHECKLIST**

### ✅ **Pre-Implementation Verification**
- [ ] Confirm Supabase connection with provided credentials
- [ ] Verify existing schema in Supabase dashboard
- [ ] Test existing `supabase_manager.py` patterns  
- [ ] Review frontend API expectations

### 🎯 **Core Implementation Requirements**
- [ ] Create Flask app with Supabase integration (not SQLite)
- [ ] Implement all 25+ API endpoints as specified
- [ ] Connect to existing `user_profiles`, `resumes`, `user_activity` tables
- [ ] Maintain frontend compatibility with existing auth flow
- [ ] Deploy to Railway with provided environment variables

### 🔗 **Frontend Integration Points**
- [ ] API Base URL: `https://backend-production-7fe0.up.railway.app`
- [ ] Authentication compatible with existing frontend context
- [ ] Response formats match frontend expectations
- [ ] CORS configured for Vercel frontend domain
