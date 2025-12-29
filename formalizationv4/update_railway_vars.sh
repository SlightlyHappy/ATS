#!/bin/bash
# Railway Environment Variable Updates
# Run these commands to fix the database connection issues

echo "🔧 Updating Railway environment variables..."

# Fix database pool settings
npx @railway/cli variables set DATABASE_POOL_SIZE=5
npx @railway/cli variables set DATABASE_MAX_CONNECTIONS=8
npx @railway/cli variables set DATABASE_MIN_CONNECTIONS=2
npx @railway/cli variables set DATABASE_CONNECTION_TIMEOUT=30

# Fix worker/thread configuration
npx @railway/cli variables set GUNICORN_WORKERS=1
npx @railway/cli variables set GUNICORN_THREADS=4

# Fix admin credentials (make sure they match)
npx @railway/cli variables set DEFAULT_ADMIN_EMAIL=admin@bearsystems.co.in
npx @railway/cli variables set DEFAULT_ADMIN_PASSWORD="Benzie1!Benzie1!Benzie1!Benzie1!"

# Update CORS configuration for new frontend
npx @railway/cli variables set FRONTEND_URL="https://hrt-bearsystems.vercel.app"
npx @railway/cli variables set ADDITIONAL_CORS_ORIGINS="https://hrtool-sable.vercel.app"

echo "✅ Railway variables updated!"
echo ""
echo "🚀 The changes will take effect on next deployment."
echo "   The database connection threading issues should be resolved."
