# 🚀 Railway Deployment Guide for Enhanced HR Backend

## 📋 Pre-Deployment Checklist

### ✅ Files Ready
- [x] `railway_start.py` - Enhanced startup script
- [x] `railway.toml` - Railway configuration
- [x] `requirements.txt` - All dependencies included
- [x] `app.py` - Main application with enterprise features
- [x] `hr_legal/` - Complete HR Legal system
- [x] `HRlaw/` - Legal knowledge base with vector indices

### ✅ Critical Environment Variables

#### **REQUIRED - Must Set Before Deployment**
```bash
# Database (Supabase)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Security
SECRET_KEY=your_super_secret_key_here

# Frontend
FRONTEND_URL=https://hrtool-sable.vercel.app
```

#### **AI PROVIDERS - Set at least one API key**
```bash
# Primary (Ollama) - If you have Ollama running
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# OpenAI (Recommended)
OPENAI_API_KEY=sk-your-openai-key

# Google Gemini
GEMINI_API_KEY=your-gemini-key

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-key

# Together AI
TOGETHER_API_KEY=your-together-key
```

#### **OPTIONAL - Performance Tuning**
```bash
# AI Configuration
DEFAULT_AI_PROVIDER=openai  # or ollama, gemini, anthropic, together

# Performance
MAX_CONCURRENT_PROCESSING=2
MAX_MEMORY_CACHE_SIZE=100
MEMORY_WARNING_THRESHOLD=0.8

# Features (all enabled by default)
ENABLE_AGENTIC_ANALYSIS=true
ENABLE_MARKET_SCORING=true
HR_LEGAL_ENABLED=true
ENABLE_EMAIL_TEMPLATES=true
```

## 🚀 Deployment Commands

### 1. Test Local Configuration
```bash
# Verify all dependencies
python railway_start.py --check-only

# Test health endpoint
python -c "from app import app; print('✅ App loads successfully')"
```

### 2. Deploy to Railway
```bash
# Deploy the enhanced backend
npx @railway/cli up

# Monitor deployment logs
npx @railway/cli logs
```

### 3. Verify Deployment
```bash
# Check health endpoint
curl https://your-railway-domain.railway.app/api/health

# Test HR Legal system
curl -X GET https://your-railway-domain.railway.app/api/legal/status
```

## 🔧 Environment Variables Setup in Railway

### Via Railway Dashboard:
1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Variables" tab
4. Add the environment variables listed above

### Via Railway CLI:
```bash
# Set critical variables
npx @railway/cli variables set SUPABASE_URL=your_url
npx @railway/cli variables set SUPABASE_KEY=your_key
npx @railway/cli variables set SECRET_KEY=your_secret
npx @railway/cli variables set OPENAI_API_KEY=your_key

# Set frontend URL
npx @railway/cli variables set FRONTEND_URL=https://hrtool-sable.vercel.app
```

## 🧪 Post-Deployment Testing

### Health Checks
- `GET /api/health` - Overall system health
- `GET /api/legal/status` - HR Legal system status
- `GET /api/debug` - Debug information (development only)

### Feature Testing
- `POST /api/upload` - File upload and processing
- `POST /api/legal/query` - HR Legal queries
- `GET /api/email-templates` - Email template system
- `GET /api/admin/dashboard` - Admin dashboard (requires admin auth)

## 🔍 Troubleshooting

### Common Issues

1. **HR Legal System Not Available**
   - Check if FAISS and sentence-transformers are installed
   - Verify HRlaw folder is present
   - Error will be logged in startup

2. **AI Provider Errors**
   - Ensure at least one AI provider API key is set
   - Check DEFAULT_AI_PROVIDER matches available keys
   - System will automatically fallback to available providers

3. **Memory Issues**
   - Reduce MAX_CONCURRENT_PROCESSING to 1
   - Lower MAX_MEMORY_CACHE_SIZE to 50
   - Disable ENABLE_DISK_CACHE if needed

4. **Performance Issues**
   - Check AI provider response times
   - Monitor /api/health endpoint
   - Use smaller models for high volume

### Logs and Monitoring
```bash
# View real-time logs
npx @railway/cli logs -f

# Check specific service logs
npx @railway/cli logs --service your-service-name
```

## 📊 Available Endpoints

### Core Features
- `POST /api/upload` - Resume upload and analysis
- `GET /api/resumes` - List processed resumes
- `GET /api/stats` - System statistics

### HR Legal System (NEW!)
- `GET /api/legal/status` - System status
- `POST /api/legal/query` - Legal queries
- `POST /api/legal/compliance-check` - Compliance analysis
- `POST /api/legal/generate-document` - Document generation

### Admin Features (NEW!)
- `GET /api/admin/dashboard` - Comprehensive metrics
- `GET /api/email-templates` - Template management
- `POST /api/email-templates/generate` - Email generation

### AI System (NEW!)
- `GET /api/ai/providers` - Provider status and stats

## 🎯 Success Metrics

After deployment, you should see:
- ✅ Health endpoint responding with 200
- ✅ HR Legal system initialized
- ✅ Multiple AI providers available
- ✅ Enhanced admin dashboard accessible
- ✅ Email template system operational
- ✅ Market-based scoring active

## 🚨 Emergency Rollback

If deployment fails:
```bash
# View previous deployments
npx @railway/cli deployments

# Rollback to previous version
npx @railway/cli rollback <deployment-id>
```

---

**🎉 Your enhanced backend with enterprise features is ready for Railway deployment!**
