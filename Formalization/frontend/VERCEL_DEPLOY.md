# Vercel Deployment Guide

## Deploy Frontend to Vercel

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy from frontend directory
```bash
cd frontend
vercel
```

### 4. Set Environment Variables in Vercel Dashboard
Go to your Vercel project dashboard and add these environment variables:

- `REACT_APP_API_URL` = `https://your-railway-backend-url.railway.app`
- `REACT_APP_SUPABASE_URL` = `your-supabase-url`
- `REACT_APP_SUPABASE_ANON_KEY` = `your-supabase-anon-key`

### 5. Redeploy after setting env vars
```bash
vercel --prod
```

## Benefits of This Setup:
- ✅ Backend on Railway (Python/Flask optimized)
- ✅ Frontend on Vercel (React optimized with global CDN)
- ✅ Automatic deployments from Git
- ✅ Environment variables for different environments
- ✅ HTTPS by default on both platforms
- ✅ Easy scaling and monitoring

## CORS Configuration
Make sure your Railway backend allows requests from your Vercel domain:
- Add your Vercel domain to CORS origins in backend
- Vercel domains typically look like: `your-app-name.vercel.app`
