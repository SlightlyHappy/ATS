# Railway Deployment Guide - Lightweight HR Backend

## 🚀 Quick Deploy to Railway

### 1. **Connect Repository to Railway**
1. Go to [Railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `SlightlyHappy/BackEndHRTOOLs`
4. **Important:** Select the `railway-lightweight-deployment` branch
5. Choose the `hr_backend_deploy` folder as the root directory

### 2. **Environment Variables**
Set these environment variables in Railway dashboard:

```bash
# Required - Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# Required - AI Provider Keys (at least one)
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_gemini_key
ANTHROPIC_API_KEY=your_anthropic_key

# Required - Security
JWT_SECRET_KEY=your_random_jwt_secret_key_here
ADMIN_SECRET_KEY=your_admin_secret_key_here

# Optional - Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_email_password
SUPPORT_EMAIL=support@yourcompany.com

# Optional - File Upload Limits
MAX_FILE_SIZE=10485760
UPLOAD_FOLDER=/tmp/uploads
PROCESSED_FOLDER=/tmp/processed

# Railway-specific
PORT=5000
RAILWAY_ENVIRONMENT=production
```

### 3. **Railway Configuration**
The `railway.toml` file is already configured:
```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python railway_start.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
```

### 4. **Deployment Process**
1. Railway will automatically detect Python
2. Install dependencies from `requirements.txt`
3. Run the startup command: `python railway_start.py`
4. The app will be available at your Railway-provided URL

### 5. **Health Check**
- Endpoint: `https://your-app.railway.app/health`
- Should return: `{"status": "healthy", "timestamp": "..."}`

## 📊 Resource Usage (Railway Optimized)

### **Memory Usage**
- **Startup:** ~150-200MB
- **Runtime:** ~200-400MB
- **Peak:** ~500MB (during AI processing)

### **Build Time**
- **Dependencies:** ~2-3 minutes
- **Startup:** ~30-60 seconds
- **Total:** ~3-4 minutes from code to live

### **Storage**
- **Code:** ~0.42MB
- **Dependencies:** ~50-100MB
- **Total:** ~100MB

## 🔧 Post-Deployment Setup

### 1. **Initialize Admin Account**
```bash
# Make a POST request to create admin
curl -X POST https://your-app.railway.app/api/admin/init \
  -H "Content-Type: application/json" \
  -d '{"admin_secret": "your_admin_secret_key_here"}'
```

### 2. **Test File Upload**
- Only `.docx` files are supported
- Maximum size: 10MB
- Upload endpoint: `/api/upload`

### 3. **Monitor Performance**
- Check Railway metrics dashboard
- Monitor response times and error rates
- Watch memory usage patterns

## ⚠️ Current Limitations

### **File Processing**
- ✅ DOCX files only
- ❌ PDF files (disabled)
- ❌ Image files (disabled)
- ❌ OCR processing (disabled)

### **AI Features**
- ✅ Basic resume analysis
- ✅ Multi-provider AI (OpenAI, Google, Anthropic)
- ✅ Email templates
- ❌ Advanced RAG/Legal queries (placeholder responses)
- ❌ ML-based scoring (basic scoring only)

## 🔄 Future Enhancements (Phase 2)

When ready to add advanced features:

### **Option 1: Railway PostgreSQL + pgvector**
```bash
# Add Railway PostgreSQL service
# Enable pgvector extension
# Implement RAG with PostgreSQL vector search
```

### **Option 2: External Vector Database**
- Pinecone (managed vector DB)
- Weaviate (open source)
- Qdrant (high performance)

### **Option 3: Microservices Architecture**
- Keep core backend lightweight
- Deploy AI/RAG services separately
- Use Railway's service linking

## 🎯 Success Metrics

Your deployment is successful when:
- ✅ Health check returns 200 OK
- ✅ Admin can login at `/admin`
- ✅ DOCX files can be uploaded and processed
- ✅ AI analysis returns structured results
- ✅ Memory stays under 500MB
- ✅ Response times under 5 seconds

## 🆘 Troubleshooting

### **Common Issues**
1. **Import Errors:** Check that all placeholder classes are working
2. **Memory Issues:** Monitor Railway metrics, restart if needed
3. **AI Timeouts:** Check API keys and provider status
4. **File Upload Fails:** Ensure DOCX format and size limits

### **Logs Access**
```bash
# In Railway dashboard
railway logs --tail
```

**Your lightweight HR backend is now ready for Railway deployment! 🚀**
