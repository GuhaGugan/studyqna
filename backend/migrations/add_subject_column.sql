-- Migration: Add subject column to uploads table
-- Run this SQL directly in your PostgreSQL database

-- Check if column already exists (optional - will error if exists, but that's okay)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'uploads' AND column_name = 'subject'
    ) THEN
        ALTER TABLE uploads 
        ADD COLUMN subject VARCHAR(50) DEFAULT 'general';
        
        RAISE NOTICE '✅ Successfully added subject column to uploads table';
        RAISE NOTICE '   Default value: general';
        RAISE NOTICE '   Valid values: mathematics, english, tamil, science, social_science, general';
    ELSE
        RAISE NOTICE '✅ Subject column already exists in uploads table';
    END IF;
END $$;


