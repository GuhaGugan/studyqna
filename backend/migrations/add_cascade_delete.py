"""
Database migration script to add ON DELETE CASCADE to all foreign key constraints
This ensures that when a user or upload is deleted, all related records are automatically deleted.

Usage:
    cd backend
    python -m migrations.add_cascade_delete
    OR
    python migrations/add_cascade_delete.py
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
    """Add ON DELETE CASCADE to all foreign key constraints"""
    print("🔄 Starting CASCADE DELETE migration...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        with engine.begin() as conn:
            # List of foreign key constraints to update
            # Format: (table_name, column_name, referenced_table, constraint_name_pattern)
            fk_constraints = [
                # Foreign keys referencing users.id
                ("uploads", "user_id", "users", "uploads_user_id_fkey"),
                ("qna_sets", "user_id", "users", "qna_sets_user_id_fkey"),
                ("premium_requests", "user_id", "users", "premium_requests_user_id_fkey"),
                ("premium_requests", "reviewed_by", "users", "premium_requests_reviewed_by_fkey"),
                ("usage_logs", "user_id", "users", "usage_logs_user_id_fkey"),
                ("audit_logs", "admin_id", "users", "audit_logs_admin_id_fkey"),
                ("audit_logs", "target_user_id", "users", "audit_logs_target_user_id_fkey"),
                ("reviews", "user_id", "users", "reviews_user_id_fkey"),
                ("ai_usage_logs", "user_id", "users", "ai_usage_logs_user_id_fkey"),
                ("login_logs", "user_id", "users", "login_logs_user_id_fkey"),
                ("pdf_split_parts", "user_id", "users", "pdf_split_parts_user_id_fkey"),
                
                # Foreign keys referencing uploads.id
                ("qna_sets", "upload_id", "uploads", "qna_sets_upload_id_fkey"),
                ("usage_logs", "upload_id", "uploads", "usage_logs_upload_id_fkey"),
                ("pdf_split_parts", "parent_upload_id", "uploads", "pdf_split_parts_parent_upload_id_fkey"),
                
                # Foreign keys referencing qna_sets.id
                ("ai_usage_logs", "qna_set_id", "qna_sets", "ai_usage_logs_qna_set_id_fkey"),
            ]
            
            # First, get all existing foreign key constraints dynamically
            print("\n📋 Finding all foreign key constraints...")
            fk_query = text("""
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                ORDER BY tc.table_name, kcu.column_name;
            """)
            
            existing_fks = conn.execute(fk_query).fetchall()
            print(f"   Found {len(existing_fks)} foreign key constraints")
            
            # Process each foreign key constraint
            for table_name, column_name, referenced_table, constraint_name in fk_constraints:
                try:
                    # Find the actual constraint name from existing constraints
                    actual_constraint = None
                    for fk in existing_fks:
                        if (fk[0] == table_name and 
                            fk[1] == column_name and 
                            fk[2] == referenced_table):
                            actual_constraint = fk[3]
                            break
                    
                    if actual_constraint:
                        print(f"\n📋 Processing: {table_name}.{column_name} → {referenced_table}.id")
                        print(f"   Constraint: {actual_constraint}")
                        
                        # Drop the existing constraint
                        drop_sql = text(f"""
                            ALTER TABLE {table_name}
                            DROP CONSTRAINT IF EXISTS {actual_constraint};
                        """)
                        conn.execute(drop_sql)
                        print(f"   ✅ Dropped constraint")
                        
                        # Recreate with ON DELETE CASCADE
                        create_sql = text(f"""
                            ALTER TABLE {table_name}
                            ADD CONSTRAINT {actual_constraint}
                            FOREIGN KEY ({column_name})
                            REFERENCES {referenced_table}(id)
                            ON DELETE CASCADE;
                        """)
                        conn.execute(create_sql)
                        print(f"   ✅ Recreated with ON DELETE CASCADE")
                    else:
                        # Constraint not found - might not exist yet or column is nullable
                        print(f"\n⚠️  Constraint not found for {table_name}.{column_name} → {referenced_table}")
                        print(f"   Skipping (may be nullable or already handled)")
                            
                except Exception as e:
                    print(f"\n❌ Error processing {table_name}.{column_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print("\n✅ Migration completed successfully!")
            print("📝 All foreign key constraints now have ON DELETE CASCADE")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_migration()

