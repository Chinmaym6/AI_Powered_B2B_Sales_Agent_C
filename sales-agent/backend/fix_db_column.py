from app.models.database import engine
from sqlalchemy import text

def fix_schema():
    with engine.connect() as conn:
        print("🔄 Fixing database schema...")
        
        # 1. Check if password_hash exists and rename it to hashed_password if needed
        # OR drop password_hash and ensure hashed_password exists
        
        try:
            # Check columns in users table
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
            columns = [row[0] for row in result]
            print(f"Current columns: {columns}")
            
            if 'password_hash' in columns and 'hashed_password' not in columns:
                print("Renaming password_hash to hashed_password...")
                conn.execute(text("ALTER TABLE users RENAME COLUMN password_hash TO hashed_password"))
            elif 'hashed_password' not in columns:
                print("Adding hashed_password column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR"))
                
            # If both exist, we might want to drop one, but let's just ensure hashed_password is populated if needed
            # For now, just ensuring the column expected by the code (hashed_password) exists is enough.
            
            print("✅ Schema fix complete.")
        except Exception as e:
            print(f"⚠️ Error fixing schema: {e}")
            
        conn.commit()

if __name__ == "__main__":
    fix_schema()
