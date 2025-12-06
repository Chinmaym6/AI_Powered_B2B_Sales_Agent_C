"""
Test script to verify LangGraph integration
Run this to check if ENV flag control is working correctly
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

print("=" * 50)
print("LangGraph Integration - Configuration Test")
print("=" * 50)

print(f"\n✅ Config module loaded successfully")
print(f"📋 USE_LANGGRAPH setting: {settings.USE_LANGGRAPH}")
print(f"🎯 Type: {type(settings.USE_LANGGRAPH)}")

if settings.USE_LANGGRAPH:
    print("\n🌐 LangGraph Mode: ENABLED")
    print("   - Campaigns will use stateful workflow")
    print("   - State persistence enabled")
    print("   - Parallel execution enabled")
    
    # Test LangGraph imports
    try:
        from langgraph.graph import StateGraph, END
        from langgraph.checkpoint.memory import MemorySaver
        print("\n✅ LangGraph packages installed correctly")
    except ImportError as e:
        print(f"\n❌ LangGraph import failed: {e}")
        print("   Run: pip install langgraph langchain")
    
    # Test LangGraph agent
    try:
        from app.core.langgraph_agent import LangGraphAgent, LANGGRAPH_AVAILABLE
        if LANGGRAPH_AVAILABLE:
            print("✅ LangGraphAgent module loaded successfully")
        else:
            print("⚠️  LangGraphAgent module exists but LangGraph not available")
    except ImportError as e:
        print(f"❌ LangGraphAgent import failed: {e}")
else:
    print("\n📊 Standard Mode: ENABLED  (default)")
    print("   - Campaigns will use existing linear agent")
    print("   - No changes to current behavior")
    print("\n💡 To enable LangGraph:")
    print("   1. Set USE_LANGGRAPH=true in .env")
    print("   2. Restart backend server")

print("\n" + "=" * 50)
print("Test Complete")
print("=" * 50)
