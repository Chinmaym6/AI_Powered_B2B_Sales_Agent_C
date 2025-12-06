@echo off
cd /d "%~dp0"
echo Starting Backend Server...
"c:\Users\91767\Desktop\AI_Powered_B2B_Sales_Agent_C\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
