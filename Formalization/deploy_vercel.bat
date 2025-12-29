@echo off
echo 🚀 Deploying Frontend to Vercel
echo ================================

echo 📁 Switching to frontend directory...
cd frontend

echo.
echo 🔧 Setting Vercel environment variables...

echo Setting REACT_APP_API_URL...
echo "https://backend-production-7fe0.up.railway.app" | npx vercel env add REACT_APP_API_URL production --force

echo Setting REACT_APP_SUPABASE_URL...
echo "https://uxnbnxvvijockfkzsyck.supabase.co" | npx vercel env add REACT_APP_SUPABASE_URL production --force

echo Setting REACT_APP_SUPABASE_ANON_KEY...
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ" | npx vercel env add REACT_APP_SUPABASE_ANON_KEY production --force

echo.
echo 📦 Building and deploying to Vercel...
npx vercel --prod

echo.
echo ✅ Deployment complete!
echo 🌐 Your app should be available at your Vercel domain
echo.
echo 📋 Environment variables set:
echo - REACT_APP_API_URL=https://backend-production-7fe0.up.railway.app
echo - REACT_APP_SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
echo - REACT_APP_SUPABASE_ANON_KEY=[Hidden for security]
echo.
pause
