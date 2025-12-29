@echo off
echo ================================================================
echo    Starting Agentic HR System for Local Development
echo ================================================================
echo.

REM Check if we're in the correct directory
if not exist "frontend" (
    echo Error: frontend folder not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

if not exist "backend" (
    echo Error: backend folder not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo [1/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo [2/4] Installing backend dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo Warning: Some backend dependencies might not have installed correctly
)
cd ..

echo [3/4] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo Error: Failed to install frontend dependencies
    echo Please make sure Node.js and npm are installed
    pause
    exit /b 1
)
cd ..

echo [4/4] Starting servers...
echo.
echo Starting Backend Server (Port 8000)...
echo Starting Frontend Server (Port 3000)...
echo.
echo ================================================================
echo Your app will be available at:
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo ================================================================
echo.
echo Press Ctrl+C in either window to stop the servers
echo.

REM Start backend server in a new window
start "Backend Server" cmd /k "cd backend && python app.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server in a new window
start "Frontend Server" cmd /k "cd frontend && npm start"

echo Both servers are starting in separate windows...
echo Close this window or press any key to exit the launcher.
pause >nul
