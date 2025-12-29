# Railway Deployment with Embedded Ollama

This guide covers deploying your HR AI application to Railway with Ollama embedded in the same container.

## 🏗️ Architecture Overview

**Single Container Approach:**
- Flask Application (Port 8000)
- Ollama AI Service (Port 11434)
- PostgreSQL Database (Railway Add-on)
- Redis Cache (Railway Add-on)

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Docker Support**: Railway will build using your Dockerfile

## 🚀 Deployment Steps

### 1. **Prepare Your Repository**

Ensure these files are in your repository root:
- `Dockerfile` (updated with Ollama)
- `.env.production` (production environment variables)
- `requirements.txt` (Python dependencies)
- `start.py` (application entry point)

### 2. **Railway Environment Variables**

Set these environment variables in Railway dashboard:

#### **Required Variables:**
```bash
# Security (CHANGE THESE!)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-production
SECRET_KEY=your-flask-secret-key-production

# Flask Configuration
FLASK_ENV=production
PORT=8000

# Ollama Configuration (embedded)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
AI_TIMEOUT=300
MAX_CONCURRENT_AI_REQUESTS=2

# File Upload
MAX_FILE_SIZE=52428800
UPLOAD_FOLDER=uploads
PROCESSED_FOLDER=processed

# Credit System
DEFAULT_USER_CREDITS=10
ADMIN_UNLIMITED_CREDITS=true
CREDIT_COST_PER_ANALYSIS=1

# Admin Configuration
DEFAULT_ADMIN_EMAIL=admin@yourdomain.com

# CORS (Replace with your actual frontend URL)
FRONTEND_URL=https://your-frontend-domain.com
ADDITIONAL_CORS_ORIGINS=https://hrtool-sable.vercel.app

# Performance
MAX_CONCURRENT_QUEUE_JOBS=2
QUEUE_PROCESSING_INTERVAL=5
ESTIMATED_ANALYSIS_TIME=120

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Health Check
HEALTH_CHECK_TIMEOUT=10
SIMPLE_HEALTH_ONLY=true

# Rate Limiting
RATE_LIMIT_REQUESTS=100
```

#### **Auto-Generated Variables (Railway provides):**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string (if using Redis add-on)

### 3. **Deploy to Railway**

#### **Option A: Deploy from GitHub**
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect your Dockerfile

#### **Option B: Deploy with Railway CLI**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

### 4. **Add Database Services**

#### **PostgreSQL Database:**
1. In Railway dashboard, click "Add Service"
2. Choose "PostgreSQL"
3. Railway will automatically set `DATABASE_URL`

#### **Redis Cache (Optional but recommended):**
1. Click "Add Service"
2. Choose "Redis"
3. Railway will automatically set `REDIS_URL`

### 5. **Configure Custom Domain (Optional)**

1. In your service settings, go to "Settings" → "Domains"
2. Add your custom domain
3. Update `FRONTEND_URL` environment variable

## ⚙️ Configuration Details

### **Container Startup Process:**
1. **Ollama Service** starts in background (port 11434)
2. **AI Model Download** - `qwen2.5:7b` is pulled automatically
3. **Flask Application** starts (port 8000)
4. **Health Checks** verify both services are running

### **Resource Requirements:**
- **CPU**: 2+ vCPUs recommended
- **RAM**: 4+ GB recommended (AI model requires significant memory)
- **Storage**: 10+ GB for AI model and application data

### **Environment Variables Explained:**

| Variable | Purpose | Default |
|----------|---------|---------|
| `OLLAMA_MODEL` | AI model to use | `qwen2.5:7b` |
| `AI_TIMEOUT` | AI request timeout (seconds) | `300` |
| `MAX_CONCURRENT_AI_REQUESTS` | Concurrent AI requests | `2` |
| `PORT` | Flask application port | `8000` |

## 🔍 Monitoring & Health Checks

### **Health Check Endpoints:**
- **Application**: `https://your-app.railway.app/api/v1/health/simple`
- **Ollama**: `https://your-app.railway.app:11434/api/tags` (internal)

### **Logs Monitoring:**
```bash
# View live logs
railway logs

# View specific service logs
railway logs --service your-service-name
```

## 🐛 Troubleshooting

### **Common Issues:**

#### **Ollama Not Starting:**
- Check logs for Ollama installation errors
- Verify `OLLAMA_HOST=0.0.0.0` environment variable
- Ensure sufficient memory allocation

#### **Model Download Fails:**
- Check internet connectivity in container
- Verify model name in `OLLAMA_MODEL`
- Monitor logs during startup

#### **Memory Issues:**
- Upgrade Railway plan for more RAM
- Consider using smaller AI model (e.g., `qwen2.5:1.5b`)
- Reduce `MAX_CONCURRENT_AI_REQUESTS`

#### **Application Won't Start:**
- Check `start.py` exists and is executable
- Verify all environment variables are set
- Check database connection

### **Performance Optimization:**

#### **For Better Performance:**
1. **Use Railway Pro Plan** - More resources
2. **Optimize AI Model** - Use smaller model if acceptable
3. **Enable Redis Caching** - Add Redis service
4. **Tune Concurrency** - Adjust `MAX_CONCURRENT_AI_REQUESTS`

#### **Cost Optimization:**
1. **Scale Down During Low Usage**
2. **Use Smaller AI Models**
3. **Implement Request Queuing**

## 📊 Scaling Considerations

### **Horizontal Scaling:**
- Railway can auto-scale based on load
- Consider separating Ollama to dedicated service for better scaling

### **Vertical Scaling:**
- Increase CPU/RAM for better AI performance
- Monitor resource usage in Railway dashboard

## 🔐 Security Notes

1. **Change Default Secrets** - Update `JWT_SECRET_KEY` and `SECRET_KEY`
2. **CORS Configuration** - Set proper `FRONTEND_URL`
3. **Rate Limiting** - Configure appropriate limits
4. **Admin Access** - Secure admin endpoints

## 📝 Deployment Checklist

- [ ] Repository contains updated Dockerfile
- [ ] Environment variables configured in Railway
- [ ] PostgreSQL service added
- [ ] Redis service added (optional)
- [ ] Custom domain configured (optional)
- [ ] Health checks passing
- [ ] Admin user created
- [ ] AI model working correctly
- [ ] Frontend integration tested

## 🎯 Next Steps

1. **Test AI Analysis** - Upload a resume and verify AI processing
2. **Monitor Performance** - Check response times and resource usage
3. **Set Up Monitoring** - Configure alerts for downtime
4. **Backup Strategy** - Set up database backups
5. **Documentation** - Update API documentation for your team

## 🆘 Support

If you encounter issues:
1. Check Railway logs: `railway logs`
2. Verify environment variables in Railway dashboard
3. Test health endpoints
4. Check database connectivity
5. Monitor resource usage

Railway automatically handles SSL certificates, load balancing, and basic monitoring for your deployment.
