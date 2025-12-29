#!/usr/bin/env pwsh
Write-Host "🔧 QUICK FIX: Updating Vercel Environment Variables" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

Write-Host "📁 Switching to frontend directory..." -ForegroundColor Yellow
Set-Location "frontend"

Write-Host ""
Write-Host "🌐 Setting production environment variables..." -ForegroundColor Yellow

# Set environment variables using echo to pipe values
Write-Host "Setting REACT_APP_API_URL..." -ForegroundColor Cyan
"https://backend-production-7fe0.up.railway.app" | npx vercel env add REACT_APP_API_URL production --force

Write-Host "Setting REACT_APP_SUPABASE_URL..." -ForegroundColor Cyan  
"https://uxnbnxvvijockfkzsyck.supabase.co" | npx vercel env add REACT_APP_SUPABASE_URL production --force

Write-Host "Setting REACT_APP_SUPABASE_ANON_KEY..." -ForegroundColor Cyan
"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ" | npx vercel env add REACT_APP_SUPABASE_ANON_KEY production --force

Write-Host "Setting NODE_ENV..." -ForegroundColor Cyan
"production" | npx vercel env add NODE_ENV production --force

Write-Host ""
Write-Host "🚀 Triggering new deployment..." -ForegroundColor Yellow
npx vercel --prod

Write-Host ""
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "🌐 Your frontend should now connect to the Railway backend" -ForegroundColor Green
Write-Host "📋 Backend URL: https://backend-production-7fe0.up.railway.app" -ForegroundColor Blue

Write-Host ""
Write-Host "🔍 If you still see connection issues:" -ForegroundColor Yellow
Write-Host "   1. Wait 2-3 minutes for Vercel deployment to complete" -ForegroundColor White
Write-Host "   2. Clear your browser cache" -ForegroundColor White
Write-Host "   3. Try accessing in an incognito window" -ForegroundColor White
Write-Host "   4. Check browser developer console for errors" -ForegroundColor White

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
