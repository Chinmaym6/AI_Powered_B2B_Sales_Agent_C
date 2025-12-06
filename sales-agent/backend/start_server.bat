@echo off
REM Activate venv and start uvic

orn with correct environment

echo ========================================
echo Starting Backend Server with VENV
echo ========================================

REM Activate the virtual environment
call venv\Scripts\activate.bat

echo.
echo ✅ Virtual environment activated
echo Python: 
python --version
echo.

REM Install/check dependencies
echo Checking LangGraph installation...
python -c "from langgraph.graph import StateGraph; print('✅ LangGraph: OK')" 2>nul
if errorlevel 1 (
    echo ⚠️  LangGraph not found, installing...
    pip install langgraph langchain langchain-google-genai langchain-community
)

echo.
echo Starting uvicorn server...
echo ========================================
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
