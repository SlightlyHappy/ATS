# Deploy Frontend to Vercel with Environment Variables
Write-Host "🚀 Deploying Frontend to Vercel" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Switch to frontend directory
Write-Host "`n📁 Switching to frontend directory..." -ForegroundColor Yellow
Set-Location frontend

# Set environment variables
Write-Host "`n🔧 Setting Vercel environment variables..." -ForegroundColor Yellow

$env_vars = @{
    "REACT_APP_API_URL" = "https://backend-production-7fe0.up.railway.app"
    "REACT_APP_SUPABASE_URL" = "https://uxnbnxvvijockfkzsyck.supabase.co"
    "REACT_APP_SUPABASE_ANON_KEY" = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ"
}

foreach ($key in $env_vars.Keys) {
    Write-Host "Setting $key..." -ForegroundColor Cyan
    $value = $env_vars[$key]
    # Use echo to pipe the value to vercel env add
    echo $value | npx vercel env add $key production
}

Write-Host "`n📦 Building and deploying to Vercel..." -ForegroundColor Yellow
npx vercel --prod

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Your app should be available at your Vercel domain" -ForegroundColor Cyan

Write-Host "`n📋 Environment variables set:" -ForegroundColor Yellow
Write-Host "- REACT_APP_API_URL=https://backend-production-7fe0.up.railway.app" -ForegroundColor Gray
Write-Host "- REACT_APP_SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co" -ForegroundColor Gray
Write-Host "- REACT_APP_SUPABASE_ANON_KEY=[Hidden for security]" -ForegroundColor Gray

# Go back to root directory
Set-Location ..

Read-Host "`nPress Enter to continue..."
