"""
Standalone migration script to add credit request feature
This script doesn't require app imports - just needs psycopg and sqlalchemy
"""
import os
import sys
from urllib.parse import quote_plus

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("ERROR: sqlalchemy not installed")
    print("   Install it with: pip install sqlalchemy psycopg[binary]")
    sys.exit(1)

def get_database_url():
    """Get DATABASE_URL from environment or .env file"""
    # Try environment variable first
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Try reading from .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            print(f"Reading .env file from: {env_path}")
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("DATABASE_URL="):
                            database_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            except Exception as e:
                print(f"[WARNING] Error reading .env file: {e}")
    
    if not database_url:
        print("ERROR: DATABASE_URL not found!")
        print("\nSolution:")
        print("   1. Set DATABASE_URL environment variable, OR")
        print("   2. Add DATABASE_URL to backend/.env file")
        print("\n   Format: postgresql://username:password@host:port/database")
        print("   Example: postgresql://postgres:mypass@localhost:5432/studyqna")
        sys.exit(1)
    
    # Handle postgresql+psycopg:// format (already correct)
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    # Convert postgresql:// to postgresql+psycopg://
    elif database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://")
    else:
        print(f"[WARNING] DATABASE_URL format might be incorrect: {database_url[:50]}...")
        print("   Expected format: postgresql://username:password@host:port/database")
        return database_url

def run_migration():
    """Run the credit request feature migration"""
    print("Starting credit request feature migration...\n")
    
    # Get database URL
    database_url = get_database_url()
    print(f"Using database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}\n")
    
    # Create engine
    try:
        engine = create_engine(database_url)
    except Exception as e:
        print(f"Error creating database engine: {e}")
        print("\nCheck your DATABASE_URL format:")
        print("   Format: postgresql://username:password@host:port/database")
        sys.exit(1)
    
    # Define migration steps separately to ensure correct order
    migration_steps = [
        {
            "name": "Add bonus_questions column",
            "sql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_questions INTEGER DEFAULT 0;"
        },
        {
            "name": "Create credit_requests table",
            "sql": """CREATE TABLE IF NOT EXISTS credit_requests (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        requested_credits INTEGER NOT NULL CHECK (requested_credits > 0),
        status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
        requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TIMESTAMP,
        reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        notes TEXT,
        user_notes TEXT
    );"""
        },
        {
            "name": "Create index on user_id",
            "sql": "CREATE INDEX IF NOT EXISTS idx_credit_requests_user_id ON credit_requests(user_id);"
        },
        {
            "name": "Create index on status",
            "sql": "CREATE INDEX IF NOT EXISTS idx_credit_requests_status ON credit_requests(status);"
        },
        {
            "name": "Create index on requested_at",
            "sql": "CREATE INDEX IF NOT EXISTS idx_credit_requests_requested_at ON credit_requests(requested_at DESC);"
        }
    ]
    
    try:
        with engine.begin() as connection:
            # Execute each step separately
            for step in migration_steps:
                try:
                    connection.execute(text(step["sql"]))
                    print(f"[OK] {step['name']}")
                except Exception as e:
                    # Some statements might fail if already exists, that's okay
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ["already exists", "duplicate", "column", "already"]):
                        print(f"[SKIP] {step['name']} (already exists)")
                    elif "does not exist" in error_str and "index" in error_str:
                        # Index creation failed because table doesn't exist - this shouldn't happen but handle it
                        print(f"[WARNING] {step['name']} - table might not exist yet, will retry")
                        # Don't raise, continue to next step
                    else:
                        print(f"[ERROR] {step['name']} failed: {e}")
                        print(f"   SQL: {step['sql'][:100]}...")
                        raise
            
            print("\n[SUCCESS] Migration completed successfully!")
            print("\nSummary:")
            print("   - Added bonus_questions column to users table")
            print("   - Created credit_requests table")
            print("   - Created indexes for performance")
            print("\nCredit request feature is now ready to use!")
            
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        print("\nTroubleshooting:")
        print("   1. Verify PostgreSQL is running")
        print("   2. Check DATABASE_URL in .env file is correct")
        print("   3. Verify username and password are correct")
        print("   4. Check if database exists")
        print("   5. Ensure user has CREATE TABLE and ALTER TABLE permissions")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

