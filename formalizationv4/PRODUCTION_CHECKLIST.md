# Production Deployment Checklist

## Pre-Deployment Checklist

### ✅ Code Quality
- [ ] All lint errors resolved
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

### ✅ Configuration
- [ ] Environment variables configured in Railway
- [ ] Database URL configured
- [ ] Secret keys configured (JWT_SECRET_KEY, SECRET_KEY)
- [ ] AI service configuration (OLLAMA_URL, OLLAMA_MODEL)
- [ ] File upload limits configured

### ✅ Database
- [ ] Database connected and accessible
- [ ] Migrations prepared and tested
- [ ] Backup strategy in place

### ✅ Security
- [ ] Security headers configured
- [ ] CORS settings reviewed
- [ ] Rate limiting configured
- [ ] File upload security verified

## Railway Deployment Steps

### 1. Environment Variables Required
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
OLLAMA_URL=your-ollama-service-url
OLLAMA_MODEL=qwen2.5:7b
LOG_LEVEL=INFO
RAILWAY_ENVIRONMENT=production
```

### 2. Deploy Process
1. Push code to GitHub
2. Connect Railway to GitHub repository
3. Configure environment variables
4. Deploy using the Railway dashboard
5. Monitor deployment logs

### 3. Post-Deployment Verification
- [ ] Health check endpoint responds: `/health`
- [ ] Database connection working
- [ ] Model loading successful
- [ ] File upload functionality working
- [ ] Authentication working
- [ ] WebSocket connections working

## Production Monitoring

### Health Checks
- **URL**: `/health`
- **Expected Response**: `{"status": "healthy"}`
- **Monitor**: Database, memory, disk, models

### Key Metrics to Monitor
- Response times
- Error rates
- Memory usage
- Database connections
- Queue sizes

### Log Monitoring
- Application logs
- Error tracking
- Performance metrics
- Security events

## Troubleshooting Common Issues

### Issue: "Working outside of application context"
**Solution**: 
- Use `wsgi_production.py` instead of `wsgi.py`
- Ensure proper Flask context handling
- Check eventlet compatibility

### Issue: Model loading fails
**Solution**:
- Check database connection
- Verify model imports
- Check app context availability

### Issue: Database connection timeout
**Solution**:
- Verify DATABASE_URL
- Check Railway database status
- Adjust connection timeout settings

### Issue: Memory issues
**Solution**:
- Reduce MAX_CONCURRENT_AGENTS
- Enable file cleanup
- Monitor memory usage

## Rollback Procedure

### In case of deployment failure:
1. Check Railway deployment logs
2. Identify the issue
3. If critical, rollback to previous deployment
4. Fix the issue in a new branch
5. Re-deploy after testing

### Emergency Rollback:
```bash
# In Railway dashboard:
1. Go to Deployments tab
2. Find previous working deployment
3. Click "Redeploy"
```

## Performance Optimization

### Production Settings Applied:
- Gunicorn with sync workers (stable)
- Connection pooling optimized for Railway
- File cleanup enabled
- Caching configured
- Security headers enabled
- Error tracking enabled

### Resource Limits:
- Memory: Monitor and optimize
- CPU: 2 workers for Railway starter plan
- Storage: Enable file cleanup
- Database: Connection pooling enabled

## Security Considerations

### Implemented:
- ✅ Security headers
- ✅ CORS configuration
- ✅ Rate limiting
- ✅ File upload validation
- ✅ SQL injection protection
- ✅ XSS protection

### Regular Security Tasks:
- [ ] Update dependencies regularly
- [ ] Monitor security alerts
- [ ] Review access logs
- [ ] Backup data regularly

## Maintenance Tasks

### Weekly:
- [ ] Check application logs
- [ ] Monitor performance metrics
- [ ] Review error rates
- [ ] Check disk usage

### Monthly:
- [ ] Update dependencies
- [ ] Review security settings
- [ ] Backup database
- [ ] Performance optimization review

### Quarterly:
- [ ] Security audit
- [ ] Performance tuning
- [ ] Documentation update
- [ ] Disaster recovery testing
