# 🚨 URGENT: Fix RLS Infinite Recursion Issue

## Problem
Your Railway deployment is failing because of infinite recursion in Supabase RLS policies on the `user_profiles` table.

**Error:** `infinite recursion detected in policy for relation "user_profiles"`

## Root Cause
The admin policies are querying the same `user_profiles` table they're trying to protect, creating infinite recursion:

```sql
-- This causes infinite recursion ❌
CREATE POLICY "admins_can_view_all" ON user_profiles
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles  -- ← Queries same table!
            WHERE id = auth.uid() AND is_admin = true
        )
    );
```

## 🔧 IMMEDIATE FIX (Manual)

### Step 1: Access Your Supabase Dashboard
1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**

### Step 2: Drop Problematic Policies
Copy and paste this SQL to remove the circular policies:

```sql
-- Drop problematic admin policies
DROP POLICY IF EXISTS "admins_can_view_all" ON user_profiles;
DROP POLICY IF EXISTS "admins_can_view_all_resumes" ON resumes;
DROP POLICY IF EXISTS "admins_can_view_all_activity" ON user_activity;
DROP POLICY IF EXISTS "admin_manage_system_config" ON system_config;
```

### Step 3: Create Safe Policies
Replace with these service-role based policies:

```sql
-- Safe user policies
CREATE POLICY "users_own_data" ON user_profiles
    FOR ALL
    USING (auth.uid() = id);

CREATE POLICY "service_role_full_access" ON user_profiles
    FOR ALL
    USING (auth.role() = 'service_role');

-- Safe resume policies  
CREATE POLICY "users_own_resumes" ON resumes
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_resumes_access" ON resumes
    FOR ALL
    USING (auth.role() = 'service_role');

-- Safe activity policies
CREATE POLICY "users_own_activity" ON user_activity
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_activity_access" ON user_activity
    FOR ALL
    USING (auth.role() = 'service_role');

-- Safe system config policies
CREATE POLICY "public_access_system_config" ON system_config
    FOR SELECT
    USING (is_public = true);

CREATE POLICY "authenticated_access_system_config" ON system_config
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_system_config" ON system_config
    FOR ALL
    USING (auth.role() = 'service_role');
```

### Step 4: Verify Fix
Run this test query to ensure no recursion:

```sql
SELECT COUNT(*) FROM user_profiles LIMIT 1;
```

## 🚀 After Database Fix

1. **Redeploy on Railway**: Your deployment should now work
2. **Test Health Check**: The application will use service role for health checks
3. **Admin Access**: Use your service role key for admin operations

## 🔒 Security Notes

- Service role policies maintain security while avoiding recursion
- Users can only access their own data
- Admin operations use service role authentication
- Public system config remains properly protected

## 📱 Alternative Quick Fix (If SQL Editor Unavailable)

If you can't access SQL Editor, temporarily disable RLS:

```sql
-- TEMPORARY - Only for emergency deployment
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
```

**⚠️ Important:** Re-enable RLS and apply proper policies ASAP:

```sql
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
-- Then apply the safe policies above
```

---

**🎯 Result:** Your Railway deployment will work, and the RLS infinite recursion will be resolved!
