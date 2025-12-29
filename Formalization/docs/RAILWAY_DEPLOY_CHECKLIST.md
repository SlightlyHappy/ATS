# Railway Deployment Checklist & Commands

## 🎯 Quick Deploy Commands

### 1. Prepare for Deployment
```powershell
# Run deployment preparation
.\deploy-railway.ps1 -BackendUrl "https://your-backend.railway.app" -FrontendUrl "https://your-frontend.railway.app"
```

### 2. Create Railway Services

#### Backend Service:
```bash
# Create new project
railway new resume-screening-backend

# Connect GitHub repo
railway connect

# Set environment variables
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=your-super-secret-key-here
railway variables set CORS_ORIGINS=*
railway variables set PORT=8000

# Deploy
railway up
```

#### Frontend Service:
```bash
# Create new project  
railway new resume-screening-frontend

# Connect GitHub repo (same repo, different service)
railway connect

# Set environment variables
railway variables set REACT_APP_API_URL=https://your-backend-url.railway.app
railway variables set NODE_ENV=production
railway variables set GENERATE_SOURCEMAP=false

# Deploy
railway up
```

## 🔧 Configuration Files Status

- [x] `frontend/Dockerfile` ✅ Created
- [x] `frontend/Dockerfile.production` ✅ Created  
- [x] `frontend/railway.json` ✅ Created
- [x] `frontend/.env.production` ✅ Created
- [x] `backend/start.py` ✅ Updated for Railway
- [x] `backend/requirements.railway.txt` ✅ Exists
- [x] `railway.json` (root) ✅ Backend config
- [x] `nixpacks.toml` ✅ Build config

## 🚀 Deployment Steps

### Step 1: Prerequisites
- [ ] Install Railway CLI: `npm install -g @railway/cli`
- [ ] Login to Railway: `railway login`
- [ ] Push code to GitHub

### Step 2: Create Services
- [ ] Create backend Railway service
- [ ] Create frontend Railway service
- [ ] Connect both to GitHub repo

### Step 3: Configure Services

#### Backend Configuration:
- [ ] Set root directory to `backend`
- [ ] Use Nixpacks builder
- [ ] Set environment variables:
  - `FLASK_ENV=production`
  - `SECRET_KEY=your-secret-key`
  - `CORS_ORIGINS=https://your-frontend-url.railway.app`
  - `PORT=8000` (optional, Railway sets automatically)

#### Frontend Configuration:
- [ ] Set root directory to `frontend`
- [ ] Use Dockerfile builder
- [ ] Set environment variables:
  - `REACT_APP_API_URL=https://your-backend-url.railway.app`
  - `NODE_ENV=production`
  - `GENERATE_SOURCEMAP=false`

### Step 4: Deploy
- [ ] Deploy backend service
- [ ] Wait for backend to be healthy
- [ ] Deploy frontend service
- [ ] Test the application

## 🔍 Verification Commands

```bash
# Check backend health
curl https://your-backend-url.railway.app/api/health

# Check frontend
curl https://your-frontend-url.railway.app

# View logs
railway logs --service backend
railway logs --service frontend

# Check status
railway status
```

## 🛠️ Troubleshooting

### Common Issues:

1. **Build Fails**:
   ```bash
   # Check build logs
   railway logs --service=your-service
   
   # Verify dependencies
   cat backend/requirements.railway.txt
   ```

2. **Frontend Can't Connect to Backend**:
   - Verify `REACT_APP_API_URL` is set correctly
   - Check CORS settings in backend
   - Ensure backend is deployed and healthy

3. **Backend Health Check Fails**:
   ```bash
   # Test health endpoint locally
   cd backend && python start.py
   curl http://localhost:8000/api/health
   ```

### Debug Steps:
1. Check Railway dashboard for errors
2. Review build and deployment logs
3. Verify environment variables
4. Test services individually
5. Check network connectivity between services

## 📊 Monitoring

After deployment, monitor:
- [ ] Service health status
- [ ] Response times
- [ ] Error rates
- [ ] Resource usage
- [ ] Costs

## 🎉 Success Criteria

- [ ] Backend health check returns 200
- [ ] Frontend loads successfully
- [ ] File upload works
- [ ] Resume processing works
- [ ] All API endpoints respond correctly
- [ ] No CORS errors in browser console

---

**Ready to deploy?** Follow the steps above in order!
