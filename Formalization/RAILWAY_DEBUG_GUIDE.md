# Railway Deployment Debug Guide

## Current Issue: Frontend Application Failed to Respond

### What We've Added for Debugging

#### Frontend Debugging:
1. **Enhanced Dockerfile** with build-time debugging
2. **Debug HTML page** accessible at `/debug` 
3. **Comprehensive nginx logging**
4. **Environment variable validation**

#### Backend Debugging:
1. **Debug API endpoint** at `/api/debug` (JSON) and `/debug` (HTML)
2. **Enhanced Dockerfile** with dependency verification
3. **System information logging**

### Environment Variables That Must Be Set

#### Frontend Service (in Railway Dashboard):
```
REACT_APP_API_URL=https://your-backend-service.railway.app
NODE_ENV=production
GENERATE_SOURCEMAP=false
```

#### Backend Service (in Railway Dashboard):
```
PORT=8000 (Railway sets this automatically)
FLASK_ENV=production
FLASK_APP=start.py
SECRET_KEY=your-secret-key-here
DATABASE_URL=your-database-url (if using database)
SUPABASE_URL=your-supabase-url (if using Supabase)
SUPABASE_ANON_KEY=your-supabase-anon-key
OLLAMA_BASE_URL=your-ollama-url (for AI processing)
```

### Debugging Steps

#### Step 1: Check Frontend Build
1. **Access debug page**: `https://your-frontend-service.railway.app/debug`
2. **Check health**: `https://your-frontend-service.railway.app/health`
3. **List files**: `https://your-frontend-service.railway.app/files`

#### Step 2: Check Backend Status
1. **Access debug page**: `https://your-backend-service.railway.app/debug`
2. **Check API health**: `https://your-backend-service.railway.app/api/health`
3. **Check startup status**: `https://your-backend-service.railway.app/api/startup-status`

#### Step 3: Railway Deployment Logs
1. **Frontend logs**: Check for React build errors, nginx startup issues
2. **Backend logs**: Check for Python import errors, missing environment variables

### Common Issues and Solutions

#### Issue 1: Frontend Shows Blank Page
**Possible Causes:**
- React build failed during Docker build
- Missing REACT_APP_API_URL environment variable
- nginx configuration errors

**Solutions:**
- Check Railway build logs for React build errors
- Ensure REACT_APP_API_URL is set correctly
- Verify index.html exists in build folder

#### Issue 2: Backend API Not Responding
**Possible Causes:**
- Python dependencies missing
- Environment variables not set
- Port binding issues

**Solutions:**
- Check Railway logs for Python errors
- Verify all required environment variables are set
- Ensure start.py handles PORT environment variable

#### Issue 3: CORS Errors (Frontend can't reach Backend)
**Possible Causes:**
- Incorrect REACT_APP_API_URL
- CORS not properly configured
- Backend not running

**Solutions:**
- Verify backend service URL is correct
- Check CORS configuration in Flask app
- Ensure both services are deployed and running

### Quick Debugging Commands for Railway CLI

```bash
# Check service status
railway status

# View logs
railway logs --service frontend
railway logs --service backend

# Check environment variables
railway variables

# Deploy specific service
railway up --service frontend
railway up --service backend
```

### Files Modified for Debugging

1. **frontend/Dockerfile** - Added build-time debugging
2. **frontend/debug.html** - Debug information page
3. **frontend/nginx.conf** - Enhanced logging and debug routes
4. **frontend/railway.toml** - Environment variable comments
5. **backend/app.py** - Added /debug and /api/debug routes
6. **backend/Dockerfile** - Added build-time debugging
7. **backend/debug_info.py** - Standalone debug script

### Next Steps

1. **Deploy with new debugging**: Push changes and redeploy both services
2. **Check debug endpoints**: Access the debug pages to see what's failing
3. **Set missing environment variables**: Based on debug output
4. **Check Railway logs**: Look for specific error messages
5. **Test API connectivity**: Ensure frontend can reach backend

### Environment Variable Setup in Railway

1. Go to Railway Dashboard
2. Select your project
3. Click on each service (frontend/backend)
4. Go to "Variables" tab
5. Add the required environment variables listed above
6. Redeploy the service after adding variables

### Critical: REACT_APP_API_URL

The frontend MUST have the correct backend URL:
```
REACT_APP_API_URL=https://[your-backend-service-name].railway.app
```

Replace `[your-backend-service-name]` with your actual Railway backend service name.

This variable gets baked into the React build, so changes require a complete redeploy.
