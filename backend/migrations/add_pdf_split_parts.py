"""
Database migration script to add PDF split parts table
Run this script to create the pdf_split_parts table

Usage:
    cd backend
    python -m migrations.add_pdf_split_parts
    OR
    python migrations/add_pdf_split_parts.py
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
    """Create pdf_split_parts table"""
    print("🔄 Starting PDF split parts migration...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        with engine.begin() as conn:
            # Add is_split column to uploads table if it doesn't exist
            try:
            conn.execute(text("""
                ALTER TABLE uploads 
                ADD COLUMN IF NOT EXISTS is_split BOOLEAN DEFAULT FALSE;
            """))
            print("✅ Added is_split column to uploads table")
        except Exception as e:
            print(f"⚠️  is_split column may already exist: {e}")
        
        # Create pdf_split_parts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pdf_split_parts (
                id SERIAL PRIMARY KEY,
                parent_upload_id INTEGER NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                part_number INTEGER NOT NULL,
                custom_name VARCHAR(200),
                file_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size INTEGER NOT NULL,
                start_page INTEGER NOT NULL,
                end_page INTEGER NOT NULL,
                total_pages INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(parent_upload_id, part_number)
            );
        """))
        print("✅ Created pdf_split_parts table")
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pdf_split_parts_parent_upload 
            ON pdf_split_parts(parent_upload_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pdf_split_parts_user 
            ON pdf_split_parts(user_id);
        """))
        print("✅ Created indexes")
        
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_migration()

