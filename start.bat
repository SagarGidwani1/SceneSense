@echo off
echo ============================================
echo   SceneSense AI - Production Startup
echo ============================================
echo.

REM Start Backend
echo [1/2] Starting Backend (FastAPI on port 8000)...
cd /d "%~dp0backend"
start "SceneSense Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start Frontend
echo [2/2] Starting Frontend (Next.js on port 3000)...
cd /d "%~dp0frontend"
start "SceneSense Frontend" cmd /k "npm run dev"

echo.
echo ============================================
echo   Both services started!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
pause
