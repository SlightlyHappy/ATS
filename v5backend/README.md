# 🚂 Railway HR ATS Backend v5

**Production-ready Resume Analyzer API optimized exclusively for Railway cloud platform deployment.**

## 🌟 Features

- **AI-Powered Resume Analysis** - Extract skills, experience, and match candidates to job requirements
- **Vector Search** - Semantic search across resume database using pgvector
- **Async Processing** - Celery-based background task processing
- **Real-time Monitoring** - Comprehensive health checks and status monitoring
- **File Storage** - S3-compatible storage for resume files
- **Railway Optimized** - Streamlined for Railway cloud deployment

## 🚀 Railway Deployment

This application is designed exclusively for Railway cloud platform. All local development configurations have been removed for production focus.

### Quick Start

1. **Clone and Deploy**
   ```bash
   git clone <repository>
   cd v5backend
   railway login
   railway deploy
   ```

2. **Configure Services**
   - Set up Railway PostgreSQL, Redis, MinIO, and Ollama services
   - Copy environment variables from `.env.example`
   - Deploy API, worker, and optional beat services

3. **Verify Deployment**
   ```bash
   railway run python railway_verify.py
   ```

### Required Railway Services

- **PostgreSQL** - Database with pgvector extension
- **Redis** - Task queue and caching
- **MinIO** - S3-compatible file storage  
- **Ollama** - LLM inference engine

### Local Development
```bash
# 1. Setup environment
git clone <repository>
cd v5backend
pip install -r requirements.txt
## 📊 API Endpoints

### Health & Monitoring
- `GET /api/health` - Basic health check
- `GET /api/healthz/details` - Detailed service status
- `GET /api/healthz/stream` - Real-time health monitoring

### Resume Operations
- `POST /api/upload` - Upload resume files
- `GET /api/search` - Search resumes by criteria
- `POST /api/match` - Match resumes to job requirements
- `POST /api/chat` - Interactive resume analysis

### System
- `GET /api/metrics` - Prometheus metrics
- `GET /api/debug/config` - Configuration status

## 🔧 Architecture

```
Railway Cloud Platform
├── API Service (Gunicorn + Flask)
├── Worker Service (Celery)
├── Beat Service (Celery Beat)
├── PostgreSQL (with pgvector)
├── Redis (task queue)
├── MinIO (file storage)
└── Ollama (LLM inference)
```

## 📋 Railway Configuration

### Environment Variables
See `.env.example` for complete Railway configuration. Key variables:

```bash
# Service Configuration
ROLE=api|worker|beat
PORT=8000
LOG_LEVEL=info

# Railway Services
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
S3_ENDPOINT=http://bucket.railway.internal:9000
OLLAMA_HOST=http://ollama.railway.internal:11434
```

### Service Roles
- **api** - Web server handling HTTP requests
- **worker** - Background task processing
- **beat** - Periodic task scheduling

## 🔍 Monitoring

### Health Checks
The application provides comprehensive health monitoring:

- Database connectivity and schema status
- Redis connectivity and performance
- S3/MinIO bucket accessibility
- Ollama model availability
- Background task queue status

### Logging
Railway-optimized structured logging with:
- Service identification
- Request tracking
- Performance metrics
- Error context

## 📚 Documentation

- `RAILWAY_PRODUCTION_GUIDE.md` - Complete Railway deployment guide
- `RAILWAY_DEPLOYMENT_STATUS.md` - Current deployment status
- `railway_verify.py` - Deployment verification script

## 🆘 Support

For deployment issues:

1. Check Railway dashboard service status
2. Review deployment logs: `railway logs`
3. Run verification: `railway run python railway_verify.py`
4. Check service connectivity and environment variables

## � Security

- Production-ready security configurations
- Environment variable protection
- Railway internal networking
- Health check authentication ready

---

**Note**: This application is optimized exclusively for Railway cloud deployment. Local development configurations have been removed to maintain production focus and deployment reliability.
