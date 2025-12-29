@echo off
echo 🔧 QUICK FIX: Updating Vercel Environment Variables
echo ===============================================

echo 📁 Switching to frontend directory...
cd frontend

echo.
echo 🌐 Setting production environment variables...

echo REACT_APP_API_URL=https://backend-production-7fe0.up.railway.app
call npx vercel env add REACT_APP_API_URL production --force <nul
echo.

echo REACT_APP_SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
call npx vercel env add REACT_APP_SUPABASE_URL production --force <nul
echo.

echo NODE_ENV=production
call npx vercel env add NODE_ENV production --force <nul
echo.

echo.
echo 🚀 Triggering new deployment...
call npx vercel --prod

echo.
echo ✅ DEPLOYMENT COMPLETE!
echo 🌐 Your frontend should now connect to the Railway backend
echo 📋 Backend URL: https://backend-production-7fe0.up.railway.app
echo.
echo 🔍 If you still see connection issues:
echo   1. Wait 2-3 minutes for Vercel deployment to complete
echo   2. Clear your browser cache
echo   3. Try accessing in an incognito window
echo.
pause
