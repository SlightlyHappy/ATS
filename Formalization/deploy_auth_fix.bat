@echo off
echo 🚀 Deploying Authentication Fixes
echo =================================

echo 📦 Building frontend...
cd frontend
call npm run build
cd ..

echo.
echo 🔧 Environment variables to set in Vercel:
echo REACT_APP_API_URL=https://backend-production-7fe0.up.railway.app
echo REACT_APP_SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
echo REACT_APP_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ

echo.
echo ✅ Changes made:
echo 1. Created apiClient.js for centralized auth handling
echo 2. Fixed FileUpload.js to include Authorization header
echo 3. Fixed FullApp.js API calls to include Authorization header
echo 4. Improved backend token type detection
echo 5. Added logging for authentication debugging
echo 6. Updated frontend .env.production with Supabase config

echo.
echo 📋 Next steps:
echo 1. Deploy to Vercel with the new environment variables
echo 2. Check Railway logs for authentication debugging
echo 3. Test file upload functionality

echo.
echo 🔧 Test the authentication with: python test_auth.py
pause
