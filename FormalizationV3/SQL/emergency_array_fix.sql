-- Emergency Array Fix for Railway PostgreSQL Console
-- This can be run directly in Railway's PostgreSQL console if needed

-- Check current data type of skills column
SELECT 
    table_name, 
    column_name, 
    data_type, 
    udt_name,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'resumes' AND column_name = 'skills';

-- Fix skills column if it's an array
DO $$ 
DECLARE
    current_type TEXT;
    current_udt_name TEXT;
    record_count INT;
BEGIN
    -- Get current type info
    SELECT data_type, udt_name INTO current_type, current_udt_name
    FROM information_schema.columns 
    WHERE table_name = 'resumes' AND column_name = 'skills';
    
    -- Check if we have data
    SELECT COUNT(*) INTO record_count FROM resumes;
    
    RAISE NOTICE 'Found % records in resumes table', record_count;
    RAISE NOTICE 'Skills column type: % (udt: %)', current_type, current_udt_name;
    
    -- Handle array conversion
    IF current_type = 'ARRAY' OR current_udt_name = '_text' THEN
        RAISE NOTICE 'Converting PostgreSQL text[] array to JSONB...';
        
        -- First, convert array values to JSON text
        UPDATE resumes 
        SET skills = CASE 
            WHEN skills IS NULL THEN '[]'::text
            WHEN array_length(skills, 1) IS NULL THEN '[]'::text
            ELSE array_to_json(skills)::text
        END
        WHERE skills IS NOT NULL;
        
        -- Change column type step by step for safety
        ALTER TABLE resumes ALTER COLUMN skills TYPE TEXT USING skills::text;
        ALTER TABLE resumes ALTER COLUMN skills TYPE JSONB USING skills::jsonb;
        
        RAISE NOTICE '✅ Successfully converted skills column from array to JSONB';
        
    ELSIF current_type = 'text' OR current_type = 'character varying' THEN
        RAISE NOTICE 'Converting text skills to JSONB...';
        
        -- Handle text values
        UPDATE resumes 
        SET skills = CASE 
            WHEN skills IS NULL OR trim(skills) = '' THEN '[]'::text
            WHEN skills LIKE '[%]' OR skills LIKE '{%}' THEN skills
            ELSE ('["' || replace(trim(skills), ',', '","') || '"]')::text
        END;
        
        ALTER TABLE resumes ALTER COLUMN skills TYPE JSONB USING skills::jsonb;
        
        RAISE NOTICE '✅ Successfully converted skills column from text to JSONB';
        
    ELSIF current_type = 'jsonb' THEN
        RAISE NOTICE 'Skills column is already JSONB, just updating NULL values...';
        UPDATE resumes SET skills = '[]'::jsonb WHERE skills IS NULL;
        
    ELSE
        RAISE NOTICE 'Adding skills column as JSONB...';
        ALTER TABLE resumes ADD COLUMN skills JSONB DEFAULT '[]';
    END IF;
    
    -- Verify the fix
    SELECT COUNT(*) INTO record_count FROM resumes WHERE skills IS NOT NULL;
    RAISE NOTICE 'Fixed % records with non-null skills', record_count;
    
END $$;

-- Verify the result
SELECT 
    table_name, 
    column_name, 
    data_type, 
    udt_name,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'resumes' AND column_name = 'skills';

-- Show sample data (first 3 records)
SELECT id, filename, skills FROM resumes WHERE skills IS NOT NULL LIMIT 3;
