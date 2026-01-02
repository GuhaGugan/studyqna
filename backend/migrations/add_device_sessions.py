"""
Migration script to add device_sessions table for 30-day 'remember me' functionality
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
    
    print("[INFO] Starting device_sessions table migration...")
    
    with engine.begin() as conn:
        # Check if table already exists
        check_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'device_sessions'
        """)
        result = conn.execute(check_query).fetchone()
        
        if result:
            print("[OK] device_sessions table already exists")
        else:
            print("[INFO] Creating device_sessions table...")
            create_table_query = text("""
                CREATE TABLE device_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    device_fingerprint VARCHAR NOT NULL,
                    device_token VARCHAR UNIQUE NOT NULL,
                    ip_address VARCHAR,
                    user_agent VARCHAR,
                    device_type VARCHAR,
                    last_used_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
                )
            """)
            conn.execute(create_table_query)
            
            # Create indexes
            print("[INFO] Creating indexes...")
            conn.execute(text("CREATE INDEX idx_device_sessions_user_id ON device_sessions(user_id)"))
            conn.execute(text("CREATE INDEX idx_device_sessions_fingerprint ON device_sessions(device_fingerprint)"))
            conn.execute(text("CREATE INDEX idx_device_sessions_token ON device_sessions(device_token)"))
            conn.execute(text("CREATE INDEX idx_device_sessions_expires ON device_sessions(expires_at)"))
            
            print("[OK] Successfully created device_sessions table with indexes")
    
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



