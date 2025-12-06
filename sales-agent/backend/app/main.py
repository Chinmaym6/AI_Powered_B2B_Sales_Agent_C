import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import settings
from .api.routes import campaigns, auth, email_monitor
from .models import database, tables
from .jobs.scheduler import start_scheduler, stop_scheduler

# Fix for Windows Playwright compatibility
# Windows doesn't support subprocess creation with the default event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Create database tables
tables.Base.metadata.create_all(bind=database.engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application"""
    # Startup
    print("🚀 Starting up AI Sales Agent API...")
    
    # Display LangGraph mode status
    print("=" * 60)
    if settings.USE_LANGGRAPH:
        print("🌐 LANGGRAPH MODE: ENABLED")
        print("   ✅ Stateful workflow active")
        print("   ✅ State persistence enabled")
        print("   ✅ Parallel execution available")
    else:
        print("📊 STANDARD MODE: ENABLED (default)")
        print("   ℹ️  Using traditional linear agent")
        print("   💡 To enable LangGraph: Set USE_LANGGRAPH=true in .env")
    print("=" * 60)
    
    await start_scheduler()
    yield
    # Shutdown
    print("🛑 Shutting down AI Sales Agent API...")
    await stop_scheduler()

app = FastAPI(
    title="AI Sales Agent API",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(email_monitor.router, prefix="/api/email-monitor", tags=["email-monitor"])

@app.get("/")
async def root():
    return {"message": "Sales Agent API is running"}
