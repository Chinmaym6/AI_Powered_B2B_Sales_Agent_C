import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.models.database import engine, Base
from app.models.tables import Campaign, Lead, Email, MLModel, LeadOutcome, ModelFeedback
from sqlalchemy import text

def init_db():
    print("🔄 Initializing database...")
    
    try:
        # Create pgvector extension
        with engine.connect() as conn:
            # conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # conn.commit()
            print("⚠️ pgvector extension skipped (using ARRAY fallback)")
            
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
