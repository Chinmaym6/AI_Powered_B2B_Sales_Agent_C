from app.models.database import engine
from sqlalchemy import text

def update_schema():
    with engine.connect() as conn:
        print("🔄 Updating database schema...")
        
        # 1. Fix Users table
        # We attempt to add columns. If they exist, it's fine (IF NOT EXISTS is used).
        # If the table doesn't exist, this might fail, but the error confirms it exists.
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"))
            print("✅ Updated 'users' table columns.")
        except Exception as e:
            print(f"⚠️ Error updating 'users' table: {e}")

        # 2. Fix Campaigns table
        try:
            conn.execute(text("ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS user_id UUID"))
            print("✅ Updated 'campaigns' table columns.")
        except Exception as e:
            print(f"⚠️ Error updating 'campaigns' table: {e}")
            
        conn.commit()
        print("🎉 Schema update complete!")

if __name__ == "__main__":
    update_schema()
