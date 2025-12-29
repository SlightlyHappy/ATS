# 🚀 HR Consultancy ATS - Deployment Guide

## Quick Start

### One-Command Deployment
```bash
python deploy.py
```

This unified script handles all deployment scenarios automatically.

---

## Environment-Specific Instructions

### 🖥️ Local Development
```bash
# 1. Clone and setup
git clone <repository-url>
cd formalizationv4

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Deploy
python deploy.py
```

### 🚂 Railway Production
```bash
# 1. Set environment variables in Railway dashboard:
JWT_SECRET_KEY=your-256-bit-secret
SECRET_KEY=your-flask-secret
DEFAULT_ADMIN_EMAIL=admin@bearsystems.co.in
DEFAULT_ADMIN_PASSWORD=your-secure-password

# 2. Add PostgreSQL service
# 3. Deploy via Git push (automatic)
```

### 🐳 Docker
```bash
# Build and run
docker build -t hr-ats .
docker run -p 8000:8000 hr-ats
```

---

## Architecture Overview

### Core Features
- **Multi-Agent AI Resume Analysis**: 4 specialized AI agents
- **Credit Management**: User-based credit system
- **Queue Management**: Priority processing with retry logic
- **Batch Processing**: ZIP file uploads
- **Pipeline Management**: Kanban-style candidate tracking
- **HR Templates**: AI-generated communication templates
- **Legal RAG**: Indian employment law consultation
- **Sales Intelligence**: Lead scoring and ROI calculation
- **Real-time Monitoring**: WebSocket-powered dashboards

### Technology Stack
- **Backend**: Flask 3.1.1 + SQLAlchemy 2.0.21
- **Database**: PostgreSQL (Railway) / SQLite (local)
- **AI**: Ollama (qwen2.5:7b model)
- **Queue**: In-memory with WebSocket notifications
- **OCR**: EasyOCR + PyTesseract
- **Authentication**: JWT tokens
- **Real-time**: Socket.IO

---

## Configuration

### Required Environment Variables
```bash
# Authentication
JWT_SECRET_KEY=your-256-bit-secret-key
SECRET_KEY=your-flask-secret-key

# Database (auto-provided by Railway)
DATABASE_URL=postgresql://...

# AI Service
OLLAMA_URL=http://localhost:11434  # or external service

# Admin Account
DEFAULT_ADMIN_EMAIL=admin@bearsystems.co.in
DEFAULT_ADMIN_PASSWORD=your-secure-password

# Optional
FRONTEND_URL=https://your-domain.com
RATE_LIMIT_REQUESTS=100
LOG_LEVEL=INFO
```

### Optional Services
- **Ollama**: For AI resume analysis (can run locally or externally)
- **Redis**: For enhanced caching (falls back to in-memory)

---

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Current user info

### Resume Analysis
- `POST /api/v1/queue/upload` - Single resume upload
- `POST /api/v1/queue/upload/batch` - Batch ZIP upload
- `GET /api/v1/resumes/{id}/analyses` - Get analysis results

### Pipeline Management
- `GET /api/v1/pipeline/candidates` - List candidates
- `PUT /api/v1/pipeline/candidates/{id}/stage` - Update stage

### HR Communication
- `GET /api/v1/communication/templates` - List templates
- `POST /api/v1/communication/templates/generate` - Generate new

### Legal Consultation
- `POST /api/legal/query` - Ask legal question
- `GET /api/legal/history` - Query history

### Sales Intelligence
- `GET /api/v1/sales/leads` - List leads
- `POST /api/v1/sales/roi/calculate` - ROI calculation

### Monitoring
- `GET /api/v1/monitoring/health/comprehensive` - Health check
- `GET /api/v1/monitoring/dashboard/enhanced` - Dashboard data

---

## Troubleshooting

### Common Issues

1. **PyTorch/torchvision compatibility errors**
   - **Fixed**: Using matched PyTorch 2.1.0+cpu with torchvision 0.16.0+cpu
   - **Dockerfile**: ML packages (torch, faiss-cpu, tiktoken, sentencepiece) installed separately with pre-built wheels
   - **Avoids**: "operator torchvision::nms does not exist" errors
   - See optimized installation order in Dockerfile

2. **Database connection errors**
   - Verify DATABASE_URL environment variable
   - Check PostgreSQL service status

3. **Docker build optimization**
   - **System deps**: Essential packages for OpenCV, EasyOCR, and PyTorch
   - **Installation order**: PyTorch ecosystem → ML packages → application dependencies
   - **Pre-built wheels**: Faster builds, fewer compilation errors
   - **Python 3.11**: Optimal compatibility with scientific packages

4. **EasyOCR compatibility**
   - **Version**: easyocr==1.7.1 with compatible PyTorch versions
   - **Alternative**: Consider PaddleOCR or TrOCR if issues persist

3. **Ollama service unavailable**
   - Application continues without AI analysis
   - Set OLLAMA_URL to external service

4. **Memory issues**
   - Reduce concurrent processing in config
   - Use smaller AI models

### Logs and Debugging
```bash
# View Railway logs
railway logs

# Local debugging
export LOG_LEVEL=DEBUG
python deploy.py
```

---

## Production Checklist

- [ ] Environment variables configured
- [ ] PostgreSQL database added
- [ ] Ollama service accessible (optional)
- [ ] Default admin user created
- [ ] SSL/HTTPS configured
- [ ] Domain name pointed to Railway
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured

---

## Support

For issues:
1. Check logs for error messages
2. Verify environment configuration
3. Test database connectivity
4. Ensure all required packages installed

Admin credentials (default):
- Email: admin@bearsystems.co.in
- Password: Set via DEFAULT_ADMIN_PASSWORD env var
