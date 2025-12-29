-- ==========================================================================
-- STEP-BY-STEP RLS FIX FOR INFINITE RECURSION
-- ==========================================================================
-- Run each section separately to avoid conflicts

-- ==========================================================================
-- STEP 1: DROP ALL EXISTING POLICIES (Run this first)
-- ==========================================================================

-- Drop user_profiles policies
DROP POLICY IF EXISTS "users_own_data" ON user_profiles;
DROP POLICY IF EXISTS "admins_can_view_all" ON user_profiles;
DROP POLICY IF EXISTS "service_role_full_access" ON user_profiles;

-- Drop resumes policies  
DROP POLICY IF EXISTS "users_own_resumes" ON resumes;
DROP POLICY IF EXISTS "admins_can_view_all_resumes" ON resumes;
DROP POLICY IF EXISTS "service_role_resumes_access" ON resumes;

-- Drop user_activity policies
DROP POLICY IF EXISTS "users_own_activity" ON user_activity;
DROP POLICY IF EXISTS "admins_can_view_all_activity" ON user_activity;
DROP POLICY IF EXISTS "service_role_activity_access" ON user_activity;

-- Drop hr_legal_queries policies
DROP POLICY IF EXISTS "users_own_legal_queries" ON hr_legal_queries;
DROP POLICY IF EXISTS "service_role_legal_access" ON hr_legal_queries;

-- Drop system_config policies
DROP POLICY IF EXISTS "public_access_system_config" ON system_config;
DROP POLICY IF EXISTS "authenticated_access_system_config" ON system_config;
DROP POLICY IF EXISTS "admin_manage_system_config" ON system_config;
DROP POLICY IF EXISTS "service_role_system_config" ON system_config;
