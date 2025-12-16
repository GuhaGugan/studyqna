"""
Database migration script to add subject column to uploads table
Run this script to add the subject field to the uploads table.

Usage:
    cd backend
    python -m migrations.add_subject_column
    OR
    python migrations/add_subject_column.py
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
    """Add subject column to uploads table"""
    print("🔄 Starting subject column migration...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        with engine.begin() as conn:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='uploads' AND column_name='subject'
            """)
            result = conn.execute(check_query).fetchone()
            
            if result:
                print("✅ Subject column already exists in uploads table")
                return
            
            # Add subject column
            alter_query = text("""
                ALTER TABLE uploads 
                ADD COLUMN subject VARCHAR(50) DEFAULT 'general'
            """)
            conn.execute(alter_query)
            print("✅ Successfully added subject column to uploads table")
            print("   Default value: 'general'")
            print("   Valid values: 'mathematics', 'english', 'tamil', 'science', 'social_science', 'general'")
            
            print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_migration()

