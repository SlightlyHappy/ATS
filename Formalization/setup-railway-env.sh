#!/bin/bash

# Railway Environment Variables Setup Script
echo "🚀 Setting up Railway Environment Variables"

# Backend Environment Variables
echo "Setting backend environment variables..."

# You need to run these commands in your Railway project dashboard or via Railway CLI
echo "
Run these commands in your Railway CLI or set in the dashboard:

# Backend Service Environment Variables
railway variables set SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
railway variables set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ
railway variables set SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTEyNjY5MSwiZXhwIjoyMDY0NzAyNjkxfQ.id-q8WoSmAAsdX5frY-egbY4PorDyxumPdeSQFuEDdc
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Frontend Service Environment Variables (switch to frontend service first)
railway variables set REACT_APP_API_URL=https://backend-production-7fe0.up.railway.app
railway variables set REACT_APP_ENVIRONMENT=production
railway variables set REACT_APP_SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
railway variables set REACT_APP_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4bmJueHZ2aWpvY2tma3pzeWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjY2OTEsImV4cCI6MjA2NDcwMjY5MX0.1X8lYG2yUuWNx4KvpHk1WOXd_Vrtj-hA-iIG3EyKGKQ
"

echo "✅ Copy and run the commands above in your Railway CLI"
echo "📝 Or set them manually in the Railway dashboard under each service's Variables tab"
