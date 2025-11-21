@echo off
echo.
echo ========================================
echo  AI-Powered B2B Sales Agent
echo  Starting Development Servers...
echo ========================================
echo.

REM Start Backend
echo [1/2] Starting Backend (FastAPI)...
start "Sales Agent - Backend" cmd /k "cd backend && .\venv\Scripts\activate && echo Backend Starting... && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to initialize
echo [*] Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start Frontend
echo [2/2] Starting Frontend (React + Vite)...
start "Sales Agent - Frontend" cmd /k "cd frontend && echo Frontend Starting... && npm run dev"

echo.
echo ========================================
echo  ✅ Both servers started successfully!
echo ========================================
echo.
echo  Backend API:  http://localhost:8000
echo  API Docs:     http://localhost:8000/docs
echo  Frontend UI:  http://localhost:5173
echo.
echo  Press Ctrl+C in each window to stop.
echo ========================================
echo.
pause
