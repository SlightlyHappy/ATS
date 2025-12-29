-- ==========================================================================
-- STEP 2: CREATE SAFE RLS POLICIES (Run this after Step 1)
-- ==========================================================================

-- User profiles policies (NO CIRCULAR REFERENCES)
CREATE POLICY "users_own_data" ON user_profiles
    FOR ALL
    USING (auth.uid() = id);

CREATE POLICY "service_role_full_access" ON user_profiles
    FOR ALL
    USING (auth.role() = 'service_role');

-- Resumes policies
CREATE POLICY "users_own_resumes" ON resumes
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_resumes_access" ON resumes
    FOR ALL
    USING (auth.role() = 'service_role');

-- User activity policies
CREATE POLICY "users_own_activity" ON user_activity
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_activity_access" ON user_activity
    FOR ALL
    USING (auth.role() = 'service_role');

-- HR legal queries policies
CREATE POLICY "users_own_legal_queries" ON hr_legal_queries
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_legal_access" ON hr_legal_queries
    FOR ALL
    USING (auth.role() = 'service_role');

-- System config policies
CREATE POLICY "public_access_system_config" ON system_config
    FOR SELECT
    USING (is_public = true);

CREATE POLICY "authenticated_access_system_config" ON system_config
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_system_config" ON system_config
    FOR ALL
    USING (auth.role() = 'service_role');
