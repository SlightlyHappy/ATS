# Railway Deployment Guide

## 🚀 Current Working Configuration

### Frontend Service
- **Builder**: Dockerfile
- **Path**: `frontend/Dockerfile`
- **Sleep Mode**: Enabled (cost optimization)
- **Region**: Europe West 4
- **URL**: Your frontend Railway URL

### Backend Service
- **Builder**: Nixpacks
- **Sleep Mode**: Disabled (always running)
- **Region**: Europe West 4
- **URL**: Your backend Railway URL

## 📋 Deployment Steps

### 1. Frontend Deployment
```bash
# Current working configuration
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "frontend/Dockerfile"
  },
  "deploy": {
    "runtime": "V2",
    "numReplicas": 1,
    "sleepApplication": true,
    "multiRegionConfig": {
      "europe-west4-drams3a": {
        "numReplicas": 1
      }
    },
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. Backend Deployment
```bash
# Current working configuration
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "runtime": "V2",
    "numReplicas": 1,
    "sleepApplication": false,
    "multiRegionConfig": {
      "europe-west4-drams3a": {
        "numReplicas": 1
      }
    },
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 🔧 Environment Variables to Set

### Frontend Service
```bash
REACT_APP_API_URL=https://your-backend-url.railway.app
NODE_ENV=production
GENERATE_SOURCEMAP=false
```

### Backend Service
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://your-frontend-url.railway.app
PORT=8000
```

## 📈 Optimizations Available

### Production Frontend (Optional Upgrade)
- Uses nginx for better performance
- Smaller image size
- Better caching
- File: `railway-frontend.json` (created)

### Enhanced Backend
- Health checks enabled
- Better timeout settings
- File: `railway-backend.json` (created)

## 🔄 Update Process

1. **Push to GitHub** - Railway auto-deploys on push
2. **Check Logs** - Monitor deployment in Railway dashboard
3. **Test Endpoints** - Verify both frontend and backend are working
4. **Environment Variables** - Ensure all variables are set correctly

## 🐛 Troubleshooting

### Common Issues:
1. **CORS Errors**: Check CORS_ORIGINS environment variable
2. **Build Failures**: Check Railway build logs
3. **Frontend Not Loading**: Verify REACT_APP_API_URL
4. **Backend Timeout**: Increase healthcheck timeout

### Logs Access:
```bash
# In Railway dashboard
- Click on service
- Go to "Deployments" tab
- Click on latest deployment
- View "Build Logs" and "Deploy Logs"
```

## 💡 Cost Optimization Tips

1. **Frontend Sleep Mode**: Enabled (wakes up automatically)
2. **Backend Always On**: Required for file processing
3. **Single Replica**: Sufficient for development/small scale
4. **Europe Region**: Closer to you, lower latency

## 🚀 Next Steps

1. Set up custom domain (optional)
2. Configure SSL certificates (automatic with Railway)
3. Set up monitoring and alerts
4. Consider upgrading to production Dockerfiles for better performance

Your current setup is working well! The configurations you have are solid for development and small-scale production use.
