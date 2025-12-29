# 🚀 HR ATS System - Production Deployment Guide

## 📋 Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Railway account created and CLI installed
- [ ] Supabase project created with required schema
- [ ] Domain configured (if using custom domain)
- [ ] SSL certificate configured

### 2. Database Schema Verification
Ensure these tables exist in your Supabase database:

```sql
-- Verify tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('user_profiles', 'resumes', 'hr_legal_queries', 'user_activity');
```

### 3. Environment Variables Configuration
Set these in Railway dashboard under Variables:

**Required Variables:**
```bash
FLASK_ENV=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SECRET_KEY=generate-secure-32-char-key
FRONTEND_URL=https://hrtool-sable.vercel.app
```

**Optional but Recommended:**
```bash
SUPABASE_SERVICE_KEY=your-service-role-key
OPENAI_API_KEY=your-openai-key
RATE_LIMIT_REQUESTS=100
MAX_FILE_SIZE=52428800
```

## 🚀 Deployment Steps

### Step 1: Repository Setup
```bash
# Clone and prepare repository
git clone <your-repo-url>
cd FormalizationV3

# Verify files are present
ls -la
# Should see: app.py, Dockerfile, requirements.txt, railway.toml
```

### Step 2: Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to project (or create new)
railway link

# Deploy
railway up
```

### Step 3: Environment Variables
1. Go to Railway dashboard
2. Select your project  
3. Navigate to Variables tab
4. Add all required environment variables
5. Redeploy: `railway up --detach`

### Step 4: Verification
```bash
# Test deployment locally
python test_deployment.py https://your-app.railway.app

# Check health endpoint
curl https://your-app.railway.app/health

# Verify CORS
curl -H "Origin: https://hrtool-sable.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS https://your-app.railway.app/api/auth/login
```

## 🔧 Post-Deployment Configuration

### 1. Domain Configuration (Optional)
```bash
# Add custom domain in Railway dashboard
# Update FRONTEND_URL to match your domain
# Configure DNS records as instructed
```

### 2. Monitoring Setup
- [ ] Enable Railway monitoring
- [ ] Set up log alerts for errors
- [ ] Configure uptime monitoring
- [ ] Set up Supabase monitoring

### 3. Security Hardening
```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set strong rate limits for production
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_HOURLY=500
```

## 📊 Performance Optimization

### 1. Railway Resource Configuration
```toml
# In railway.toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on-failure"
```

### 2. Application Performance
- [ ] Enable response caching
- [ ] Configure file cleanup
- [ ] Set appropriate timeouts
- [ ] Monitor memory usage

## 🐛 Troubleshooting Guide

### Common Deployment Issues

1. **Build Failures**
```bash
# Check build logs
railway logs --tail

# Common fixes:
# - Verify requirements.txt is present
# - Check Docker build context
# - Ensure system dependencies are listed
```

2. **Environment Variable Issues**
```bash
# List current variables
railway variables

# Test locally with same variables
export SUPABASE_URL=your-url
python app.py
```

3. **Database Connection Errors**
```bash
# Test Supabase connection
curl -H "apikey: your-anon-key" \
     "https://your-project.supabase.co/rest/v1/user_profiles?select=count"
```

4. **CORS Issues**
```bash
# Verify frontend URL is correct
echo $FRONTEND_URL

# Test CORS headers
curl -I -H "Origin: $FRONTEND_URL" your-app-url/health
```

### Health Check Failures
```bash
# Check specific service health
curl https://your-app.railway.app/health | jq .

# Common issues:
# - Supabase connectivity
# - Missing environment variables
# - File permission errors
```

## 📈 Monitoring and Maintenance

### 1. Regular Health Checks
```bash
# Automated health monitoring
*/5 * * * * curl -f https://your-app.railway.app/health || echo "Health check failed"
```

### 2. Log Monitoring
```bash
# View real-time logs
railway logs --tail

# Search for errors
railway logs | grep ERROR
```

### 3. Database Monitoring
- Monitor Supabase dashboard for:
  - Connection counts
  - Query performance
  - Storage usage
  - API limits

### 4. Performance Metrics
Track these metrics:
- Response times
- Error rates
- Memory usage
- File storage usage
- User activity patterns

## 🔄 Update Procedures

### Code Updates
```bash
# Push changes
git add .
git commit -m "Update: description"
git push origin main

# Railway auto-deploys from main branch
# Monitor deployment: railway logs --tail
```

### Environment Updates
```bash
# Update variables
railway variables set KEY=value

# Restart if needed
railway restart
```

### Database Updates
```sql
-- Run schema updates in Supabase SQL editor
-- Always backup before major changes
-- Test in development first
```

## 🚨 Emergency Procedures

### Rollback Procedure
```bash
# View deployment history
railway history

# Rollback to previous deployment
railway rollback <deployment-id>
```

### Quick Fixes
```bash
# Restart application
railway restart

# Scale down/up if needed
railway scale --replicas 1

# Emergency variable update
railway variables set FLASK_ENV=maintenance
```

## ✅ Go-Live Checklist

### Final Verification
- [ ] Health endpoint returns 200
- [ ] Authentication flow works
- [ ] File upload functions
- [ ] AI analysis completes
- [ ] Database operations succeed
- [ ] CORS configured correctly
- [ ] Security headers present
- [ ] Error handling works
- [ ] Logs are readable
- [ ] Performance is acceptable

### Communication
- [ ] Notify frontend team of backend URL
- [ ] Update documentation
- [ ] Inform stakeholders of go-live
- [ ] Set up monitoring alerts

## 📞 Support Contacts

- **Railway Issues**: Railway support or documentation
- **Supabase Issues**: Supabase support dashboard
- **Application Issues**: Development team
- **Infrastructure Issues**: DevOps team

---

**🎯 Production Ready**: Following this guide ensures a secure, scalable deployment suitable for production use with proper monitoring and maintenance procedures.
