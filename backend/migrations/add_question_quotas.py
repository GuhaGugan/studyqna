"""
Database migration script to add question-based quota columns
This adds:
- questions_used and questions_limit to users table
- questions_count to daily_generation_usage table

Usage:
    cd backend
    python migrations/add_question_quotas.py
    OR
    python -m migrations.add_question_quotas
"""
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database import engine

def run_migration():
    """Add question-based quota columns"""
    print("Starting question quota migration...")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        with engine.begin() as conn:
            # Add questions_used column to users table
            print("\nAdding questions_used column to users table...")
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS questions_used INTEGER DEFAULT 0;
                """))
                print("   OK: Added questions_used column")
            except Exception as e:
                print(f"   WARNING: questions_used column may already exist: {e}")
            
            # Add questions_limit column to users table
            print("\nAdding questions_limit column to users table...")
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS questions_limit INTEGER DEFAULT 700;
                """))
                print("   OK: Added questions_limit column")
            except Exception as e:
                print(f"   WARNING: questions_limit column may already exist: {e}")
            
            # Update existing premium users to have 700 questions limit
            print("\nUpdating existing premium users...")
            try:
                conn.execute(text("""
                    UPDATE users 
                    SET questions_limit = 700, questions_used = 0
                    WHERE premium_status::text = 'approved' 
                    AND (questions_limit IS NULL OR questions_limit = 0);
                """))
                print("   OK: Updated existing premium users")
            except Exception as e:
                print(f"   WARNING: Error updating premium users: {e}")
            
            # Add questions_count column to daily_generation_usage table
            print("\nAdding questions_count column to daily_generation_usage table...")
            try:
                conn.execute(text("""
                    ALTER TABLE daily_generation_usage 
                    ADD COLUMN IF NOT EXISTS questions_count INTEGER DEFAULT 0;
                """))
                print("   OK: Added questions_count column")
            except Exception as e:
                print(f"   WARNING: questions_count column may already exist: {e}")
            
            # Initialize questions_count for existing records
            print("\nInitializing questions_count for existing records...")
            try:
                conn.execute(text("""
                    UPDATE daily_generation_usage 
                    SET questions_count = 0
                    WHERE questions_count IS NULL;
                """))
                print("   OK: Initialized questions_count")
            except Exception as e:
                print(f"   WARNING: Error initializing questions_count: {e}")
            
            print("\nMigration completed successfully!")
            print("Question-based quota columns added:")
            print("   - users.questions_used (default: 0)")
            print("   - users.questions_limit (default: 700)")
            print("   - daily_generation_usage.questions_count (default: 0)")
            
    except Exception as e:
        print(f"\nERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_migration()

