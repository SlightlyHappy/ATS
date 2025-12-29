# 🔧 Railway Environment Variables Setup

## Copy these to Railway Dashboard > Your Service > Variables tab:

```bash
# Required - Database
SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTEyNjY5MSwiZXhwIjoyMDY0NzAyNjkxfQ.id-q8WoSmAAsdX5frY-egbY4PorDyxumPdeSQFuEDdc

# Required - Security
SECRET_KEY=hr-resume-screening-flask-secret-key-2025-temp
SUPABASE_JWT_SECRET=hr-resume-jwt-secret-key-2025-temp

# Required - Frontend
FRONTEND_URL=https://hrtool-sable.vercel.app

# Required - Server
PORT=8000
FLASK_ENV=production

# AI Provider (add at least one)
# OPENAI_API_KEY=your_openai_key_here
# GEMINI_API_KEY=your_gemini_key_here

# Optional - System Configuration
HR_LEGAL_ENABLED=true
DEFAULT_AI_PROVIDER=openai
MAX_CONCURRENT_PROCESSING=2
```

## Alternative: Via Railway CLI

If you prefer CLI, run these commands:

```bash
# Navigate to your project
npx @railway/cli link -p 48e4ee33-bf22-497a-99e6-6e8774ca1dec

# Add GitHub service (you'll need to do this via dashboard first)
# Then set variables:
npx @railway/cli variables --set "SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co"
npx @railway/cli variables --set "SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ"
npx @railway/cli variables --set "SECRET_KEY=hr-resume-screening-flask-secret-key-2025-temp"
npx @railway/cli variables --set "FRONTEND_URL=https://hrtool-sable.vercel.app"
npx @railway/cli variables --set "PORT=8000"
npx @railway/cli variables --set "FLASK_ENV=production"
```

## 🎯 Next Steps After Connection:

1. **Verify Deployment**: Railway will automatically build and deploy
2. **Check Logs**: Monitor the deployment logs for any issues
3. **Test Endpoints**: Visit your Railway domain + `/api/health`
4. **Add AI Provider Keys**: Add OpenAI or other AI provider keys

## 📊 What You'll Get:

✅ **Automatic Deployments**: Any push to master branch will auto-deploy
✅ **Environment Variables**: Secure storage of your secrets
✅ **Health Checks**: Built-in monitoring at `/api/health`
✅ **Fallback Mode**: HR Legal system will work without HRlaw folder
✅ **All Enterprise Features**: Admin dashboard, email templates, multi-AI

---

Your enhanced HR backend is now ready for production deployment! 🎉
