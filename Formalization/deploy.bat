@echo off
setlocal enabledelayedexpansion

REM 🚀 Unified Deployment Script for Resume Screening App (Windows)
REM Supports development, beta, and production deployments

echo 🚀 Resume Screening App - Unified Deployment

REM Default values
set "ENVIRONMENT=development"
set "ACTION=deploy"
set "SKIP_BUILD=false"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :done_parsing
if "%~1"=="-e" (
    set "ENVIRONMENT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--env" (
    set "ENVIRONMENT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-a" (
    set "ACTION=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--action" (
    set "ACTION=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-h" goto :show_usage
if "%~1"=="--help" goto :show_usage
if "%~1"=="-s" (
    set "SKIP_BUILD=true"
    shift
    goto :parse_args
)
if "%~1"=="--skip-build" (
    set "SKIP_BUILD=true"
    shift
    goto :parse_args
)
echo ❌ Unknown option: %~1
goto :show_usage

:done_parsing

REM Validate environment
if "%ENVIRONMENT%"=="development" goto :valid_env
if "%ENVIRONMENT%"=="beta" goto :valid_env
if "%ENVIRONMENT%"=="production" goto :valid_env
echo ❌ Invalid environment: %ENVIRONMENT%
echo Valid environments: development, beta, production
exit /b 1

:valid_env

REM Set environment-specific variables
if "%ENVIRONMENT%"=="development" (
    set "COMPOSE_FILE=docker-compose.yml"
    set "ENV_FILE=.env.development"
) else (
    set "COMPOSE_FILE=docker-compose.production.yml"
    set "ENV_FILE=.env.%ENVIRONMENT%"
)

echo Environment: %ENVIRONMENT%
echo Action: %ACTION%
echo Compose file: %COMPOSE_FILE%
echo Environment file: %ENV_FILE%
echo.

REM Check prerequisites
echo 📋 Checking prerequisites...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed
    exit /b 1
)

if not exist "%COMPOSE_FILE%" (
    echo ❌ Compose file not found: %COMPOSE_FILE%
    exit /b 1
)

echo ✅ Prerequisites OK

REM Setup environment file
if not exist "%ENV_FILE%" (
    if exist "%ENV_FILE%.example" (
        echo ⚠️ Environment file not found. Creating from template...
        copy "%ENV_FILE%.example" "%ENV_FILE%"
        
        if not "%ENVIRONMENT%"=="development" (
            call :generate_secrets
        )
        
        echo ⚠️ Please edit %ENV_FILE% with your configuration
    ) else (
        echo ❌ Environment file not found: %ENV_FILE%
        exit /b 1
    )
)

REM Execute action
if "%ACTION%"=="deploy" goto :deploy
if "%ACTION%"=="start" goto :start
if "%ACTION%"=="stop" goto :stop
if "%ACTION%"=="restart" goto :restart
if "%ACTION%"=="status" goto :status
if "%ACTION%"=="logs" goto :logs
if "%ACTION%"=="backup" goto :backup
echo ❌ Invalid action: %ACTION%
goto :show_usage

:deploy
echo 🚀 Deploying %ENVIRONMENT% environment...

REM Create directories
echo 📁 Creating directories...
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "processed" mkdir processed
if not exist "nginx\ssl" mkdir nginx\ssl

REM Check existing containers and what needs rebuilding
call :check_containers_and_changes

REM Stop existing containers if needed
if "%NEED_RESTART%"=="true" (
    echo 🛑 Stopping existing containers...
    docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" down --remove-orphans 2>nul
)

REM Selective build and start
call :selective_build_and_start

REM Wait for services
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

call :health_check
call :show_access_info

echo ✅ Deployment completed successfully!
goto :end

:start
echo 🚀 Starting services...
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" up -d
echo ✅ Services started
goto :end

:stop
echo 🛑 Stopping services...
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" down
echo ✅ Services stopped
goto :end

:restart
echo 🔄 Restarting services...
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" restart
echo ✅ Services restarted
goto :end

:status
echo 📊 Service Status:
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" ps
echo.
echo 💾 Resource Usage:
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>nul
goto :end

:logs
echo 📋 Showing logs (Press Ctrl+C to exit)...
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" logs -f
goto :end

:backup
set "BACKUP_FILE=backup_%ENVIRONMENT%_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql"
set "BACKUP_FILE=%BACKUP_FILE: =0%"
echo 💾 Creating database backup: %BACKUP_FILE%
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" exec -T postgres pg_dump -U app_user resume_screening > "%BACKUP_FILE%"
if %errorlevel%==0 (
    echo ✅ Backup created: %BACKUP_FILE%
) else (
    echo ❌ Backup failed!
)
goto :end

:health_check
echo 🔍 Health Check:
REM Basic health check (simplified for Windows)
curl -f "http://localhost:8000/health" >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Backend: Healthy
) else (
    echo ⚠️ Backend: Not ready yet
)

if "%ENVIRONMENT%"=="development" (
    curl -f "http://localhost:3000/" >nul 2>&1
    if %errorlevel%==0 (
        echo ✅ Frontend: Accessible
    ) else (
        echo ⚠️ Frontend: Not ready yet
    )
) else (
    curl -f "http://localhost/" >nul 2>&1
    if %errorlevel%==0 (
        echo ✅ Frontend: Accessible via nginx
    ) else (
        echo ⚠️ Frontend: Not ready yet
    )
)
goto :eof

:show_access_info
echo.
echo 🌐 Access Information:
if "%ENVIRONMENT%"=="development" (
    echo Frontend: http://localhost:3000
    echo Backend: http://localhost:8000
    echo API: http://localhost:8000/api
) else (
    echo Application: http://localhost
    echo API: http://localhost/api
)
echo.
echo Admin Email: admin@localhost
echo Admin Password: admin123
goto :eof

:generate_secrets
echo 🔐 Generating secure passwords...
REM Generate simple passwords for Windows (use better method in production)
set "DB_PASSWORD=SecurePass%RANDOM%"
set "REDIS_PASSWORD=RedisPass%RANDOM%"
set "ADMIN_PASSWORD=Admin%RANDOM%"

REM Update environment file using PowerShell
powershell -Command "(Get-Content '%ENV_FILE%') -replace 'CHANGE_ME_.*_PASSWORD', '%DB_PASSWORD%' -replace 'CHANGE_ME_.*_REDIS_PASSWORD', '%REDIS_PASSWORD%' -replace 'CHANGE_ME_.*_ADMIN_PASSWORD', '%ADMIN_PASSWORD%' | Set-Content '%ENV_FILE%'"

echo Generated credentials:
echo   Database Password: %DB_PASSWORD%
echo   Redis Password: %REDIS_PASSWORD%
echo   Admin Password: %ADMIN_PASSWORD%
echo.
echo ⚠️ SAVE THESE CREDENTIALS!
goto :eof

:check_containers_and_changes
echo 🔍 Checking existing containers and file changes...

REM Initialize flags
set "NEED_RESTART=false"
set "REBUILD_FRONTEND=false"
set "REBUILD_BACKEND=false"
set "REBUILD_NGINX=false"

REM Check if containers exist and are running
for /f %%i in ('docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" ps -q 2^>nul ^| find /c /v ""') do set RUNNING_CONTAINERS=%%i

if %RUNNING_CONTAINERS%==0 (
    echo 📦 No containers running - full deployment needed
    set "NEED_RESTART=true"
    set "REBUILD_FRONTEND=true"
    set "REBUILD_BACKEND=true"
    set "REBUILD_NGINX=true"
    goto :eof
)

REM Check file changes since last build
call :check_file_changes

REM Check if images exist
docker images | findstr "formalization.*frontend" >nul 2>&1
if %errorlevel% neq 0 (
    echo 🏗️ Frontend image not found - rebuild needed
    set "REBUILD_FRONTEND=true"
    set "NEED_RESTART=true"
)

docker images | findstr "formalization.*backend" >nul 2>&1
if %errorlevel% neq 0 (
    echo 🏗️ Backend image not found - rebuild needed
    set "REBUILD_BACKEND=true"
    set "NEED_RESTART=true"
)

REM Check container health
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" ps | findstr "Up" >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔄 Some containers unhealthy - restart needed
    set "NEED_RESTART=true"
)

echo 🎯 Build strategy:
if "%REBUILD_FRONTEND%"=="true" echo   - Frontend: REBUILD
if "%REBUILD_BACKEND%"=="true" echo   - Backend: REBUILD
if "%REBUILD_NGINX%"=="true" echo   - Nginx: REBUILD
if "%NEED_RESTART%"=="false" echo   - No changes detected, containers will be reused
goto :eof

:check_file_changes
echo 📝 Checking for file changes...

REM Check if build tracking file exists
if not exist ".last_build_hash" (
    echo 🆕 No previous build detected - full rebuild needed
    set "REBUILD_FRONTEND=true"
    set "REBUILD_BACKEND=true"
    set "REBUILD_NGINX=true"
    set "NEED_RESTART=true"
    goto :eof
)

REM Create current hash of key files
set "HASH_FILE=.current_build_hash"
if exist "%HASH_FILE%" del "%HASH_FILE%"

REM Hash frontend files
if exist "frontend\package.json" (
    for /f %%a in ('powershell -command "Get-FileHash 'frontend\package.json' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo frontend_package: %%a >> "%HASH_FILE%"
)
if exist "frontend\Dockerfile" (
    for /f %%a in ('powershell -command "Get-FileHash 'frontend\Dockerfile' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo frontend_docker: %%a >> "%HASH_FILE%"
)

REM Hash backend files
if exist "backend\requirements.txt" (
    for /f %%a in ('powershell -command "Get-FileHash 'backend\requirements.txt' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo backend_requirements: %%a >> "%HASH_FILE%"
)
if exist "backend\Dockerfile" (
    for /f %%a in ('powershell -command "Get-FileHash 'backend\Dockerfile' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo backend_docker: %%a >> "%HASH_FILE%"
)

REM Hash docker-compose file
if exist "%COMPOSE_FILE%" (
    for /f %%a in ('powershell -command "Get-FileHash '%COMPOSE_FILE%' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo compose: %%a >> "%HASH_FILE%"
)

REM Compare with previous build
fc /b "%HASH_FILE%" ".last_build_hash" >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔄 Changes detected in build files
    
    REM Check specific components for changes
    findstr "frontend_" "%HASH_FILE%" > .temp_frontend_hash
    findstr "frontend_" ".last_build_hash" > .temp_frontend_old 2>nul
    fc /b .temp_frontend_hash .temp_frontend_old >nul 2>&1
    if %errorlevel% neq 0 (
        echo   - Frontend changes detected
        set "REBUILD_FRONTEND=true"
        set "NEED_RESTART=true"
    )
    
    findstr "backend_" "%HASH_FILE%" > .temp_backend_hash
    findstr "backend_" ".last_build_hash" > .temp_backend_old 2>nul
    fc /b .temp_backend_hash .temp_backend_old >nul 2>&1
    if %errorlevel% neq 0 (
        echo   - Backend changes detected
        set "REBUILD_BACKEND=true"
        set "NEED_RESTART=true"
    )
    
    findstr "compose" "%HASH_FILE%" > .temp_compose_hash
    findstr "compose" ".last_build_hash" > .temp_compose_old 2>nul
    fc /b .temp_compose_hash .temp_compose_old >nul 2>&1
    if %errorlevel% neq 0 (
        echo   - Docker compose changes detected
        set "REBUILD_FRONTEND=true"
        set "REBUILD_BACKEND=true"
        set "REBUILD_NGINX=true"
        set "NEED_RESTART=true"
    )
    
    REM Clean up temp files
    if exist ".temp_*" del .temp_*
) else (
    echo ✅ No changes detected in build files
)

REM Clean up
if exist "%HASH_FILE%" del "%HASH_FILE%"
goto :eof

:selective_build_and_start
if "%NEED_RESTART%"=="false" (
    echo ✅ All containers are up and running - no action needed
    goto :eof
)

echo 🏗️ Starting selective build and deployment...

REM Build only what's needed
set "BUILD_SERVICES="
if "%REBUILD_FRONTEND%"=="true" set "BUILD_SERVICES=%BUILD_SERVICES% frontend"
if "%REBUILD_BACKEND%"=="true" set "BUILD_SERVICES=%BUILD_SERVICES% backend"
if "%REBUILD_NGINX%"=="true" set "BUILD_SERVICES=%BUILD_SERVICES% nginx"

if not "%BUILD_SERVICES%"=="" (
    echo 🔨 Building services:%BUILD_SERVICES%
    docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" build%BUILD_SERVICES%
    if %errorlevel% neq 0 (
        echo ❌ Build failed!
        exit /b 1
    )
)

echo 🚀 Starting all services...
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" up -d

REM Update build hash for next run
call :update_build_hash

goto :eof

:update_build_hash
echo 💾 Updating build tracking...
set "HASH_FILE=.current_build_hash"
if exist "%HASH_FILE%" del "%HASH_FILE%"

REM Recreate hash file
if exist "frontend\package.json" (
    for /f %%a in ('powershell -command "Get-FileHash 'frontend\package.json' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo frontend_package: %%a >> "%HASH_FILE%"
)
if exist "frontend\Dockerfile" (
    for /f %%a in ('powershell -command "Get-FileHash 'frontend\Dockerfile' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo frontend_docker: %%a >> "%HASH_FILE%"
)
if exist "backend\requirements.txt" (
    for /f %%a in ('powershell -command "Get-FileHash 'backend\requirements.txt' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo backend_requirements: %%a >> "%HASH_FILE%"
)
if exist "backend\Dockerfile" (
    for /f %%a in ('powershell -command "Get-FileHash 'backend\Dockerfile' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo backend_docker: %%a >> "%HASH_FILE%"
)
if exist "%COMPOSE_FILE%" (
    for /f %%a in ('powershell -command "Get-FileHash '%COMPOSE_FILE%' -Algorithm MD5 | Select-Object -ExpandProperty Hash"') do echo compose: %%a >> "%HASH_FILE%"
)

REM Save as last build hash
if exist "%HASH_FILE%" (
    copy "%HASH_FILE%" ".last_build_hash" >nul
    del "%HASH_FILE%"
)
goto :eof

:show_usage
echo.
echo Resume Screening App - Unified Deployment Script (Windows)
echo ========================================================
echo.
echo Usage: %0 [OPTIONS]
echo.
echo OPTIONS:
echo     -e, --env ENV          Environment: development, beta, production (default: development)
echo     -a, --action ACTION    Action: deploy, start, stop, restart, status, logs, backup (default: deploy)
echo     -s, --skip-build       Skip building containers
echo     -h, --help             Show this help message
echo.
echo EXAMPLES:
echo     %0 --env development                    # Deploy for local development
echo     %0 --env beta --action deploy          # Deploy beta environment
echo     %0 --env production --action deploy    # Deploy production
echo     %0 --env beta --action logs            # View beta logs
echo     %0 --env production --action backup    # Backup production database
echo.
echo ENVIRONMENTS:
echo     development - Local development with hot reload
echo     beta        - Beta testing with production build
echo     production  - Full production deployment with security
echo.
goto :end

:end
pause
