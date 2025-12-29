# Railway Deployment Fix Guide

## Issues Fixed

### 1. Backend Supabase Environment Variables
**Problem**: Backend was falling back to SQLite because Supabase environment variables weren't properly configured.

**Solution**: Updated `supabase_manager.py` to support both naming conventions and standardized the `.env` file.

### 2. Frontend 502 Error  
**Problem**: Frontend Dockerfile had multiple stages but Railway didn't know which one to use.

**Solution**: Simplified Dockerfile to single production build with nginx.

## Railway Environment Variables to Set

### Backend Service
Set these environment variables in your Railway backend service:

```bash
# Supabase Configuration
SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTEyNjY5MSwiZXhwIjoyMDY0NzAyNjkxfQ.id-q8WoSmAAsdX5frY-egbY4PorDyxumPdeSQFuEDdc

# Application Configuration
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-here

# Production Optimization
MAX_MEMORY_CACHE_SIZE=50
CHUNK_SIZE=1
MAX_CONCURRENT_PROCESSING=1
COMPRESS_PROCESSED_FILES=True
ENABLE_AI_RESPONSE_CACHING=True
```

### Frontend Service
Set these environment variables in your Railway frontend service:

```bash
# API Configuration
REACT_APP_API_URL=https://backend-production-7fe0.up.railway.app
REACT_APP_ENVIRONMENT=production

# Supabase Configuration (for frontend auth if needed)
REACT_APP_SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
REACT_APP_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ
```

## Deployment Steps

1. **Push the fixed code** to your repository
2. **Set environment variables** in Railway dashboard for both services
3. **Redeploy both services** from Railway dashboard
4. **Monitor logs** to ensure Supabase connection is working

## Expected Results

### Backend Logs Should Show:
```
✅ Bear Systems Authentication System initialized successfully with Supabase
📦 HR Legal dependencies available
```

### Frontend Should:
- Load without 502 errors
- Serve the React application properly
- Health check at `/health` should return "healthy"

## Troubleshooting

### If backend still shows SQLite fallback:
1. Double-check environment variables are set in Railway (not just in .env file)
2. Verify Supabase project is active and accessible
3. Check that the Supabase keys haven't expired

### If frontend still shows 502:
1. Check build logs for any build failures
2. Verify nginx configuration is correct
3. Ensure the application builds successfully in Railway environment
