"""
Migration script to add logout_at column to login_logs table
Run this script to add the logout_at column without losing existing data
"""
from sqlalchemy import text
from app.database import engine

def add_logout_column():
    """Add logout_at column to login_logs table"""
    try:
        with engine.begin() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='login_logs' AND column_name='logout_at'
            """))
            
            if result.fetchone():
                print("✅ Column 'logout_at' already exists in login_logs table")
                return
            
            # Add the column
            conn.execute(text("ALTER TABLE login_logs ADD COLUMN logout_at TIMESTAMP NULL"))
            print("✅ Successfully added 'logout_at' column to login_logs table")
            
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        raise

if __name__ == "__main__":
    print("🔄 Adding logout_at column to login_logs table...")
    add_logout_column()
    print("✅ Migration complete!")


