"""
Migration script to add total_questions_reset_at column to users table
"""
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] Loaded environment from {env_path}")
    else:
        print(f"[WARN] .env file not found at {env_path}")
        print("   Using environment variables from system")
except ImportError:
    print("[WARN] python-dotenv not installed, using system environment variables")

# Get database URL from environment
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("[ERROR] DATABASE_URL not found in environment variables!")
    print("   Please set DATABASE_URL in your .env file or environment")
    sys.exit(1)

# Replace postgresql:// with postgresql+psycopg:// for psycopg3
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

print(f"[INFO] Connecting to database...")
db_display = database_url.split('@')[1] if '@' in database_url else 'hidden'
print(f"   URL: {db_display}")

try:
    from sqlalchemy import create_engine, text
    
    # Create engine
    engine = create_engine(database_url)
    
    print("[INFO] Starting total questions reset timestamp migration...")
    
    with engine.begin() as conn:
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name = 'total_questions_reset_at'
        """)
        result = conn.execute(check_query).fetchone()
        
        if result:
            print("[OK] total_questions_reset_at column already exists")
        else:
            print("[INFO] Adding total_questions_reset_at column to users table...")
            alter_query = text("""
                ALTER TABLE users 
                ADD COLUMN total_questions_reset_at TIMESTAMP NULL
            """)
            conn.execute(alter_query)
            print("[OK] Successfully added total_questions_reset_at column")
    
    print("\n[OK] Migration completed successfully!")
    print("   You can now restart your backend server")
    
except ImportError as e:
    print(f"[ERROR] Missing required package: {e}")
    print("   Please install: pip install sqlalchemy psycopg[binary] python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

