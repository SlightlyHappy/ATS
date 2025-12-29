-- ==========================================================================
-- FIX RLS INFINITE RECURSION ISSUE
-- ==========================================================================
-- This script fixes the infinite recursion issue in user_profiles RLS policies
-- The problem was admin policies querying the same table they're protecting

-- Step 1: Drop ALL existing policies to avoid conflicts
DROP POLICY IF EXISTS "users_own_data" ON user_profiles;
DROP POLICY IF EXISTS "admins_can_view_all" ON user_profiles;
DROP POLICY IF EXISTS "service_role_full_access" ON user_profiles;

DROP POLICY IF EXISTS "users_own_resumes" ON resumes;
DROP POLICY IF EXISTS "admins_can_view_all_resumes" ON resumes;
DROP POLICY IF EXISTS "service_role_resumes_access" ON resumes;

DROP POLICY IF EXISTS "users_own_activity" ON user_activity;
DROP POLICY IF EXISTS "admins_can_view_all_activity" ON user_activity;
DROP POLICY IF EXISTS "service_role_activity_access" ON user_activity;

DROP POLICY IF EXISTS "users_own_legal_queries" ON hr_legal_queries;
DROP POLICY IF EXISTS "service_role_legal_access" ON hr_legal_queries;

DROP POLICY IF EXISTS "public_access_system_config" ON system_config;
DROP POLICY IF EXISTS "authenticated_access_system_config" ON system_config;
DROP POLICY IF EXISTS "admin_manage_system_config" ON system_config;
DROP POLICY IF EXISTS "service_role_system_config" ON system_config;

-- Step 2: Create a function to check admin status using service role
CREATE OR REPLACE FUNCTION is_admin_user(user_id UUID)
RETURNS BOOLEAN
LANGUAGE SQL
SECURITY DEFINER
AS $$
    SELECT EXISTS (
        SELECT 1 FROM auth.users 
        WHERE id = user_id 
        AND raw_app_meta_data->>'role' = 'admin'
    );
$$;

-- Alternative approach: Use user metadata instead of user_profiles table
-- Step 3: Create all policies fresh (after dropping existing ones)

-- User profiles policies
CREATE POLICY "users_own_data" ON user_profiles
    FOR ALL
    USING (auth.uid() = id);

-- Admin policy using service role instead of user_profiles query
CREATE POLICY "service_role_full_access" ON user_profiles
    FOR ALL
    USING (auth.role() = 'service_role');

-- For resumes
CREATE POLICY "users_own_resumes" ON resumes
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_resumes_access" ON resumes
    FOR ALL
    USING (auth.role() = 'service_role');

-- For user_activity
CREATE POLICY "users_own_activity" ON user_activity
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_activity_access" ON user_activity
    FOR ALL
    USING (auth.role() = 'service_role');

-- For hr_legal_queries
CREATE POLICY "users_own_legal_queries" ON hr_legal_queries
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_legal_access" ON hr_legal_queries
    FOR ALL
    USING (auth.role() = 'service_role');

-- For system_config - simplified policies
CREATE POLICY "public_access_system_config" ON system_config
    FOR SELECT
    USING (is_public = true);

CREATE POLICY "authenticated_access_system_config" ON system_config
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_system_config" ON system_config
    FOR ALL
    USING (auth.role() = 'service_role');

-- Step 4: Create a safer admin check function that doesn't cause recursion
CREATE OR REPLACE FUNCTION get_user_access_level(user_id UUID)
RETURNS TEXT
LANGUAGE SQL
SECURITY DEFINER
AS $$
    SELECT COALESCE(
        (auth.users.raw_app_meta_data->>'access_level')::TEXT,
        'user'
    )
    FROM auth.users 
    WHERE id = user_id;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION is_admin_user(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_access_level(UUID) TO authenticated;
