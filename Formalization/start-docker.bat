@echo off
echo 🚀 Starting n8n and WAHA Automation Services...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Clean up any existing containers
echo 🧹 Cleaning up existing containers...
docker-compose -f docker-compose-new.yml down

REM Remove old images
echo 🗑️ Removing old images...
docker image prune -f

REM Build and start services
echo 🔨 Building and starting services...
docker-compose -f docker-compose-new.yml up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Check service status
echo 📊 Checking service status...
docker-compose -f docker-compose-new.yml ps

echo.
echo ✅ Automation services should be ready!
echo 🤖 n8n Workflow Automation: http://localhost:5678
echo � WAHA WhatsApp API: http://localhost:3001
echo.
echo 📝 To view logs: docker-compose -f docker-compose-new.yml logs -f
echo 🛑 To stop: docker-compose -f docker-compose-new.yml down
pause
