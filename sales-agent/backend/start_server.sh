#!/bin/bash

echo "========================================"
echo "Starting Backend Server with VENV"
echo "========================================"

# Activate virtual environment
source venv/Scripts/activate

echo ""
echo "✅ Virtual environment activated"
echo "Python:"
python --version
echo ""

# Check LangGraph
echo "Checking LangGraph installation..."
python -c "from langgraph.graph import StateGraph; print('✅ LangGraph: OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  LangGraph not found, installing..."
    pip install langgraph langchain langchain-google-genai langchain-community
fi

echo ""
echo "Starting uvicorn server..."
echo "========================================"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
