"""
Check database connection and help fix DATABASE_URL
"""
import os
import sys

# Check if .env file exists
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

print("🔍 Checking database configuration...\n")

if not os.path.exists(env_path):
    print("❌ ERROR: .env file not found!")
    print(f"   Expected location: {env_path}")
    print("\n📝 Solution:")
    print("   1. Copy ENV_TEMPLATE.txt to .env:")
    print("      cp backend/ENV_TEMPLATE.txt backend/.env")
    print("   2. Edit backend/.env and set your DATABASE_URL")
    print("   3. Format: postgresql://username:password@host:port/database")
    sys.exit(1)

print(f"✅ Found .env file at: {env_path}\n")

# Try to read DATABASE_URL
try:
    from dotenv import load_dotenv
    load_dotenv(env_path)
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in .env file!")
        print("\n📝 Solution:")
        print("   Add this line to your .env file:")
        print("   DATABASE_URL=postgresql://username:password@localhost:5432/database_name")
        sys.exit(1)
    
    print(f"✅ Found DATABASE_URL: {database_url[:50]}...")
    
    # Parse DATABASE_URL
    if database_url.startswith("postgresql://"):
        parts = database_url.replace("postgresql://", "").split("@")
        if len(parts) == 2:
            user_pass = parts[0].split(":")
            host_db = parts[1].split("/")
            
            if len(user_pass) >= 2 and len(host_db) >= 2:
                username = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ""
                host_port = host_db[0].split(":")
                host = host_port[0]
                port = host_port[1] if len(host_port) > 1 else "5432"
                database = host_db[1].split("?")[0]  # Remove query params
                
                print(f"\n📋 Parsed Database Configuration:")
                print(f"   Username: {username}")
                print(f"   Password: {'*' * len(password) if password else 'NOT SET'}")
                print(f"   Host: {host}")
                print(f"   Port: {port}")
                print(f"   Database: {database}")
                
                if username == "user" or not password:
                    print("\n⚠️  WARNING: DATABASE_URL appears to be using default/placeholder values!")
                    print("\n📝 Solution:")
                    print("   1. Edit backend/.env file")
                    print("   2. Update DATABASE_URL with your actual database credentials")
                    print("   3. Format: postgresql://your_username:your_password@localhost:5432/your_database")
                    print("\n   Example:")
                    print("   DATABASE_URL=postgresql://studyqna_user:mypassword123@localhost:5432/studyqna_db")
                    sys.exit(1)
                
                # Try to test connection
                print("\n🔄 Testing database connection...")
                try:
                    from app.database import engine
                    with engine.connect() as conn:
                        result = conn.execute("SELECT 1")
                        print("✅ Database connection successful!")
                        print("\n✅ You can now run the migration:")
                        print("   python backend/migrations/run_credit_request_migration.py")
                except Exception as e:
                    print(f"\n❌ Database connection failed: {e}")
                    print("\n📝 Troubleshooting:")
                    print("   1. Verify PostgreSQL is running")
                    print("   2. Check username and password are correct")
                    print("   3. Verify database exists")
                    print("   4. Check if PostgreSQL is listening on the correct port")
                    sys.exit(1)
            else:
                print("❌ ERROR: DATABASE_URL format is incorrect!")
                print("   Expected format: postgresql://username:password@host:port/database")
        else:
            print("❌ ERROR: DATABASE_URL format is incorrect!")
            print("   Expected format: postgresql://username:password@host:port/database")
    else:
        print("❌ ERROR: DATABASE_URL must start with 'postgresql://'")
        
except ImportError:
    print("⚠️  python-dotenv not installed. Trying to read .env manually...")
    # Try manual parsing
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                database_url = line.split("=", 1)[1].strip()
                print(f"✅ Found DATABASE_URL: {database_url[:50]}...")
                if "user:password" in database_url or database_url.endswith("user"):
                    print("\n⚠️  WARNING: DATABASE_URL appears to be using placeholder values!")
                    print("   Please update it with your actual database credentials.")
                break
except Exception as e:
    print(f"❌ Error reading .env file: {e}")
    sys.exit(1)

