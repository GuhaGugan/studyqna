# Database Migration: Add Subject Column

## Error
```
sqlalchemy.exc.ProgrammingError: column uploads.subject does not exist
```

## Solution: Run Database Migration

The `subject` column needs to be added to the `uploads` table. Choose one of the following methods:

### Method 1: Using Python Script (Recommended)

**Step 1:** Activate your virtual environment:
```bash
cd backend
.\venv\Scripts\activate  # Windows PowerShell
# OR
venv\Scripts\activate.bat  # Windows CMD
```

**Step 2:** Run the migration:
```bash
python migrations/add_subject_column.py
```

### Method 2: Using Batch Script (Windows)

Simply double-click or run:
```bash
backend\migrations\run_subject_migration.bat
```

### Method 3: Direct SQL (If Python script fails)

Connect to your PostgreSQL database and run:

```sql
-- Check if column exists, then add it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'uploads' AND column_name = 'subject'
    ) THEN
        ALTER TABLE uploads 
        ADD COLUMN subject VARCHAR(50) DEFAULT 'general';
        
        RAISE NOTICE '✅ Successfully added subject column';
    ELSE
        RAISE NOTICE '✅ Subject column already exists';
    END IF;
END $$;
```

Or simply:
```sql
ALTER TABLE uploads 
ADD COLUMN IF NOT EXISTS subject VARCHAR(50) DEFAULT 'general';
```

### Method 4: Using psql Command Line

```bash
psql -U your_username -d your_database_name -f backend/migrations/add_subject_column.sql
```

## Verification

After running the migration, verify it worked:

```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'uploads' AND column_name = 'subject';
```

You should see:
- column_name: `subject`
- data_type: `character varying` (or `varchar`)
- column_default: `'general'`

## After Migration

1. Restart your backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. The application should now work correctly with subject selection.

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pydantic_settings'"
- **Solution:** Activate your virtual environment first, then run the migration

### Error: "Permission denied"
- **Solution:** Make sure your database user has ALTER TABLE permissions

### Error: "Column already exists"
- **Solution:** The migration already ran successfully. You can proceed.

### Still getting errors?
- Check your database connection settings in `.env`
- Verify the table name is `uploads` (not `upload`)
- Check PostgreSQL logs for detailed error messages
