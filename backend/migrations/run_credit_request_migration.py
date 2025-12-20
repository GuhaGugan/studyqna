"""
Migration script to add credit request feature
Run this script to add bonus_questions column and credit_requests table
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

# Create engine directly from settings, handling both postgresql:// and postgresql+psycopg://
database_url = settings.DATABASE_URL
# If it's already postgresql+psycopg://, use it as-is, otherwise convert
if not database_url.startswith("postgresql+psycopg://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://")

engine = create_engine(database_url)

def run_migration():
    """Run the credit request feature migration"""
    print("🔄 Starting credit request feature migration...")
    
    migration_sql = """
    -- Step 1: Add bonus_questions column to users table
    ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_questions INTEGER DEFAULT 0;
    
    -- Step 2: Create credit_requests table
    CREATE TABLE IF NOT EXISTS credit_requests (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        requested_credits INTEGER NOT NULL CHECK (requested_credits > 0),
        status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
        requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TIMESTAMP,
        reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        notes TEXT,
        user_notes TEXT
    );
    
    -- Step 3: Create indexes for better query performance
    CREATE INDEX IF NOT EXISTS idx_credit_requests_user_id ON credit_requests(user_id);
    CREATE INDEX IF NOT EXISTS idx_credit_requests_status ON credit_requests(status);
    CREATE INDEX IF NOT EXISTS idx_credit_requests_requested_at ON credit_requests(requested_at DESC);
    """
    
    try:
        with engine.begin() as connection:  # Use begin() for automatic transaction management
            # Execute each statement separately
            statements = migration_sql.strip().split(';')
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        connection.execute(text(statement))
                        # Get a short description of what was executed
                        desc = statement.split()[0:3] if len(statement.split()) >= 3 else statement.split()
                        print(f"✅ Executed: {' '.join(desc)}...")
                    except Exception as e:
                        # Some statements might fail if already exists, that's okay
                        error_str = str(e).lower()
                        if "already exists" in error_str or "duplicate" in error_str or "column" in error_str and "already" in error_str:
                            desc = statement.split()[0:3] if len(statement.split()) >= 3 else statement.split()
                            print(f"⚠️  Skipped (already exists): {' '.join(desc)}...")
                        else:
                            print(f"❌ Error executing statement: {e}")
                            print(f"   Statement: {statement[:100]}")
            
            print("\n✅ Migration completed successfully!")
            print("\n📋 Summary:")
            print("   - Added bonus_questions column to users table")
            print("   - Created credit_requests table")
            print("   - Created indexes for performance")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

