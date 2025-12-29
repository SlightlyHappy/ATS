# 🚀 HR Resume Screening Backend

A comprehensive Flask-based backend for AI-powered resume screening and HR management, designed for Railway deployment with Supabase persistence.

## 🎯 Overview

This backend provides:
- **Resume Processing**: PDF, DOCX, and image file processing with OCR
- **AI Analysis**: Intelligent resume analysis and scoring (ready for Ollama integration)
- **User Management**: Authentication, trial limits, and admin controls
- **HR Legal**: Placeholder for RAG-based legal guidance system
- **Export & Analytics**: Resume data export and user statistics

## 🏗️ Architecture

- **Framework**: Flask 3.0.3 with CORS
- **Database**: Supabase (PostgreSQL) with existing schema
- **Authentication**: JWT tokens + Supabase Auth
- **AI Processing**: Mock analysis (ready for Ollama)
- **File Processing**: PyMuPDF, python-docx, pytesseract
- **Deployment**: Railway with automatic scaling

## 📁 Project Structure

```
backend/
├── app.py                 # Main Flask application
├── supabase_manager.py    # Database operations
├── file_processor.py      # File processing & OCR
├── ai_analyzer.py         # AI analysis (mock + Ollama ready)
├── auth_utils.py          # Authentication & authorization
├── start.py              # Production startup script
├── test_system.py        # System validation tests
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── railway.toml         # Railway deployment config
├── .env                 # Environment variables
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Environment Setup

Create `.env` file with your credentials:

```bash
# Supabase (EXISTING PERSISTENT STORAGE)
SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Security
SECRET_KEY=your-flask-secret-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Frontend
FRONTEND_URL=https://hrtool-sable.vercel.app

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run System Tests

```bash
python test_system.py
```

### 4. Start Development Server

```bash
python app.py
```

The server will start on `http://localhost:8000`

## 🌐 API Endpoints

### Authentication

| Endpoint | Method | Description | Auth Required |
|----------|---------|-------------|---------------|
| `/api/auth/admin-login` | POST | Admin authentication | No |
| `/api/auth/create-user` | POST | Create new user | Admin |
| `/api/auth/user-login` | POST | User authentication | No |
| `/api/auth/session` | GET | Validate session | User/Admin |
| `/api/auth/logout` | POST | User logout | User/Admin |

### Resume Processing

| Endpoint | Method | Description | Auth Required |
|----------|---------|-------------|---------------|
| `/api/upload` | POST | Upload & analyze resumes | User |
| `/api/resumes` | GET | Get user's resumes | User |
| `/api/resumes/<id>` | GET | Get resume details | User |
| `/api/resumes/<id>/markdown` | GET | Get resume as Markdown | User |
| `/api/export` | GET | Export to CSV (full users) | User |
| `/api/stats` | GET | User statistics | User |
| `/api/clear` | DELETE | Clear all resumes | User |

### Trial Management

| Endpoint | Method | Description | Auth Required |
|----------|---------|-------------|---------------|
| `/api/trial/status` | GET | Get trial status | User |
| `/api/trial/upgrade-info` | GET | Get upgrade options | User |

### HR Legal (Placeholder)

| Endpoint | Method | Description | Auth Required |
|----------|---------|-------------|---------------|
| `/api/hr-legal/query` | POST | Legal query | User |
| `/api/hr-legal/compliance-check` | POST | Compliance check | User |

### System

| Endpoint | Method | Description | Auth Required |
|----------|---------|-------------|---------------|
| `/api/health` | GET | Health check | No |
| `/api/debug` | GET | Debug info (dev only) | No |

## 🔐 Authentication

### Admin Login
```bash
POST /api/auth/admin-login
{
  "username": "admin",
  "password": "admin123"
}
```

### User Login
```bash
POST /api/auth/user-login
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Using JWT Tokens
Include in request headers:
```
Authorization: Bearer <your-jwt-token>
```

## 📄 File Processing

### Supported Formats
- **PDF**: Text extraction with PyMuPDF
- **DOCX**: Document parsing with python-docx
- **Images**: OCR with pytesseract (PNG, JPG, JPEG)

### Upload Example
```bash
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer <token>" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx"
```

## 🤖 AI Integration

Currently using **mock analysis** for development. Ready for Ollama integration:

### Mock Analysis Features
- Basic info extraction (name, email, phone)
- Skills identification from common keywords
- Scoring system (0-100 scale)
- Strengths/weaknesses analysis
- Role matching capabilities

### Ollama Integration (Ready)
- Model: `qwen2.5:7b`
- Context length: 8192 tokens
- Temperature: 0.1 for consistency
- Comprehensive prompt engineering

## 🗄️ Database Schema

Uses existing Supabase tables:

- `user_profiles` - User data and trial tracking
- `resumes` - Resume storage and analysis
- `user_activity` - Activity logging
- `hr_legal_queries` - Legal query history
- `system_config` - Application settings
- `admin_users` - Admin management

## 🚀 Railway Deployment

### 1. Environment Variables

Set in Railway dashboard:

```bash
# Required
SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
SUPABASE_ANON_KEY=your-key
SUPABASE_SERVICE_KEY=your-key
SECRET_KEY=your-secret
FRONTEND_URL=https://hrtool-sable.vercel.app

# Optional
FLASK_ENV=production
PORT=8000  # Railway sets automatically
```

### 2. Deploy Commands

Railway will automatically:
1. Detect Python project
2. Install dependencies from `requirements.txt`
3. Run startup command: `python start.py`
4. Health check at `/api/health`

### 3. Post-Deployment

1. Test health endpoint: `https://your-app.railway.app/api/health`
2. Create admin user via `/api/auth/admin-login`
3. Test file upload functionality
4. Configure frontend to use new backend URL

## 🧪 Testing

### System Tests
```bash
python test_system.py
```

### Manual API Testing
```bash
# Health check
curl https://your-app.railway.app/api/health

# Admin login
curl -X POST https://your-app.railway.app/api/auth/admin-login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 🔧 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export FLASK_ENV=development
export FLASK_DEBUG=True

# Run application
python app.py
```

### Adding New Features

1. **New Endpoints**: Add to `app.py`
2. **Database Operations**: Add to `supabase_manager.py`
3. **File Processing**: Extend `file_processor.py`
4. **AI Features**: Enhance `ai_analyzer.py`
5. **Authentication**: Modify `auth_utils.py`

## 📊 Monitoring

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2025-01-25T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": {"status": "healthy"},
    "ai_service": {"status": "mock_mode"}
  }
}
```

### Logging
- Production logs to `/tmp/logs/application.log`
- Development logs to console
- Structured JSON logging format

## 🚨 Security Features

- **JWT Authentication**: Secure token-based auth
- **Input Validation**: All inputs validated and sanitized
- **File Security**: Magic number validation, size limits
- **Rate Limiting**: Prevents abuse and DoS attacks
- **CORS Protection**: Restricted to frontend domains
- **SQL Injection Prevention**: Parameterized queries via Supabase

## 🔄 Trial System

### Trial Limitations
- **Free Users**: 100 resume analyses
- **Trial Tracking**: Real-time usage monitoring
- **Usage Limits**: Automatic enforcement
- **Upgrade Prompts**: Clear upgrade paths

### Access Levels
1. **Trial**: Limited resume analyses
2. **Full**: Unlimited access + export
3. **Admin**: System administration

## 📈 Performance

### Optimizations
- **Connection Pooling**: Efficient database connections
- **File Processing**: Optimized text extraction
- **Caching**: Ready for Redis integration
- **Rate Limiting**: Prevents system overload

### Scalability
- **Stateless Design**: Horizontal scaling ready
- **Railway Auto-scaling**: Automatic resource management
- **Supabase Backend**: Managed database scaling

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection**
   - Check Supabase URL and keys
   - Verify network connectivity
   - Check RLS policies

2. **File Processing**
   - Ensure Tesseract is installed
   - Check file size limits
   - Verify supported formats

3. **Authentication**
   - Validate JWT secrets
   - Check token expiration
   - Verify admin credentials

### Debug Mode
```bash
export FLASK_ENV=development
python app.py
# Access debug info at /api/debug
```

## 🎯 Next Steps

### Phase 1: Core Features ✅
- [x] Supabase integration
- [x] Authentication system
- [x] File processing
- [x] Mock AI analysis
- [x] API endpoints

### Phase 2: AI Integration 🔄
- [ ] Deploy Ollama on Railway
- [ ] Integrate real AI analysis
- [ ] Advanced prompt engineering
- [ ] Performance optimization

### Phase 3: Advanced Features 📋
- [ ] HR Legal RAG system
- [ ] Advanced analytics
- [ ] Email notifications
- [ ] Webhook integrations

### Phase 4: Production Hardening 🔒
- [ ] Comprehensive testing
- [ ] Performance monitoring
- [ ] Security audit
- [ ] Documentation updates

## 📞 Support

For issues and questions:
- **GitHub Issues**: [Create an issue]
- **Email**: support@hrtool.com
- **Documentation**: This README

---

**🎉 Backend is production-ready for Railway deployment with comprehensive Supabase integration!**
#   B a c k E n d H R T O O L s  
 