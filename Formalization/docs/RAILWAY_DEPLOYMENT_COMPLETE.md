# Railway Deployment Guide for Resume Screening App

## 🚀 Quick Start

### Prerequisites
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login to Railway: `railway login`
3. Have your GitHub repository ready

## 📦 Deployment Strategy

We'll deploy as **two separate services**:
1. **Backend Service** - Python Flask API
2. **Frontend Service** - React + Nginx

## 🔧 Step-by-Step Deployment

### 1. Deploy Backend Service

1. **Create new Railway project**:
   ```bash
   railway new resume-screening-backend
   ```

2. **Connect GitHub repository**:
   - Go to Railway dashboard
   - Connect your GitHub repo
   - Set root directory to `/backend`

3. **Set environment variables**:
   ```bash
   FLASK_ENV=production
   SECRET_KEY=your-super-secret-key-here
   PORT=8000
   CORS_ORIGINS=*
   PYTHONPATH=/app/backend
   ```

4. **Use this railway.json** (place in root):
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "cd backend && python start.py",
       "healthcheckPath": "/api/health",
       "healthcheckTimeout": 100,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 3
     }
   }
   ```

### 2. Deploy Frontend Service

1. **Create new Railway project**:
   ```bash
   railway new resume-screening-frontend
   ```

2. **Connect GitHub repository**:
   - Go to Railway dashboard
   - Connect your GitHub repo
   - Set root directory to `/frontend`

3. **Set environment variables**:
   ```bash
   REACT_APP_API_URL=https://backend-production-7fe0.up.railway.app
   NODE_ENV=production
   GENERATE_SOURCEMAP=false
   ```

4. **Use this railway.json** (place in frontend folder):
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile"
     },
     "deploy": {
       "healthcheckPath": "/",
       "healthcheckTimeout": 30,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 3
     }
   }
   ```

## 🔗 Environment Variables

### Backend (.env)
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
PORT=8000
CORS_ORIGINS=https://frontend-production-e3df.up.railway.app
DATABASE_URL=sqlite:///resume_screening.db
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
```

### Frontend (.env.production)
```bash
REACT_APP_API_URL=https://your-backend-domain.railway.app
NODE_ENV=production
GENERATE_SOURCEMAP=false
```

## 📁 File Structure

Your project should have these files for Railway:

```
project-root/
├── railway.json                 # Backend config
├── nixpacks.toml               # Backend build config
├── backend/
│   ├── start.py                # Production start script
│   ├── app.py                  # Main Flask app
│   ├── requirements.railway.txt # Production dependencies
│   └── ...
├── frontend/
│   ├── railway.json            # Frontend config
│   ├── Dockerfile              # Production Docker config
│   ├── nginx.conf              # Nginx configuration
│   ├── package.json            # Dependencies
│   └── ...
```

## 🎯 Deployment Commands

### Option 1: Railway CLI
```bash
# Deploy backend
cd backend && railway up

# Deploy frontend  
cd frontend && railway up
```

### Option 2: GitHub Integration (Recommended)
1. Connect Railway to your GitHub repo
2. Push code to main branch
3. Railway auto-deploys

## 🔍 Troubleshooting

### Common Issues:

1. **Build Fails**:
   - Check `requirements.railway.txt` has all dependencies
   - Verify Python version (3.11)
   - Check start command in `railway.json`

2. **Frontend Can't Connect to Backend**:
   - Verify `REACT_APP_API_URL` points to backend Railway URL
   - Check CORS settings in backend
   - Ensure backend health check passes

3. **Backend Health Check Fails**:
   - Check `/api/health` endpoint works locally
   - Verify port configuration (Railway sets PORT automatically)
   - Check startup script `start.py`

### Debug Commands:
```bash
# Check service status
railway status

# View logs
railway logs

# Check environment variables
railway variables
```

## 🚀 Go Live Checklist

- [ ] Backend deploys successfully
- [ ] Frontend deploys successfully  
- [ ] Health checks pass
- [ ] Frontend can reach backend API
- [ ] File uploads work
- [ ] Resume processing works
- [ ] Environment variables set correctly
- [ ] Custom domain configured (optional)

## 💰 Cost Optimization

- Enable sleep mode for low-traffic periods
- Use Railway's usage-based pricing
- Monitor resource usage in dashboard

## 🔒 Security

- Use Railway's secret management
- Set proper CORS origins
- Use HTTPS (automatic with Railway)
- Secure your secret keys

---

**Need help?** Check Railway docs or reach out for support!
