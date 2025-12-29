-- ==========================================================================
-- STEP 3: TEST THE FIX (Run this after Step 2)
-- ==========================================================================

-- Test 1: Check if we can query user_profiles without infinite recursion
SELECT COUNT(*) as user_count FROM user_profiles;

-- Test 2: Check system_config access
SELECT COUNT(*) as config_count FROM system_config;

-- Test 3: List all policies to verify they're correct
SELECT schemaname, tablename, policyname, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('user_profiles', 'resumes', 'user_activity', 'hr_legal_queries', 'system_config')
ORDER BY tablename, policyname;
