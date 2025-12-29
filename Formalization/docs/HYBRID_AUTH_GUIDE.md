# Hybrid Authentication System Guide

## Overview

This application now supports **both** Supabase authentication and custom backend authentication, with intelligent fallback mechanisms.

## How It Works

### Authentication Priority
1. **Supabase First**: If Supabase credentials are configured, try Supabase auth first
2. **Custom Backend Fallback**: If Supabase fails or isn't configured, use custom backend
3. **Admin Always Custom**: Admin logins always use custom backend

### Authentication Flow

```javascript
// Regular user login - tries Supabase first, falls back to custom
const result = await login('user@example.com', 'password')

// Admin login - always uses custom backend
const result = await login('admin@company.com', 'password', true)
```

## Configuration Options

### Option 1: Supabase + Custom Backend (Recommended)
```env
REACT_APP_SUPABASE_URL=your-project-url.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
REACT_APP_API_URL=http://localhost:8000
```

### Option 2: Custom Backend Only
```env
# Leave Supabase vars empty or undefined
REACT_APP_API_URL=http://localhost:8000
```

### Option 3: Supabase Only
```env
REACT_APP_SUPABASE_URL=your-project-url.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
# Custom backend will be used for fallback
```

## User Types Supported

### Supabase Users
- **Trial Users**: `access_type: 'trial'` in user_profiles table
- **Full Users**: `access_type: 'full'` 
- **Enterprise Users**: `access_type: 'enterprise'`
- **Admins**: `is_admin: true` (can also login via custom backend)

### Custom Backend Users
- All existing user types from your current system
- Admins with special privileges

## Features Available

### All Users
- ✅ Login/Logout
- ✅ Session management
- ✅ Profile updates
- ✅ Trial usage tracking
- ✅ Access level checks

### Supabase Users Additional Features
- ✅ Email confirmation
- ✅ Password reset via email
- ✅ Real-time auth state changes
- ✅ Row Level Security
- ✅ Automatic profile creation

### Custom Backend Users
- ✅ Existing custom features
- ✅ Admin panel access
- ✅ Legacy system compatibility

## AuthContext API

### Properties
```javascript
const {
  // Core state
  user,              // Current user object
  loading,           // Auth loading state
  isAuthenticated,   // Boolean auth status
  
  // Methods
  login,             // (email, password, isAdmin?) => Promise
  logout,            // () => Promise
  createUser,        // (userData) => Promise
  updateProfile,     // (updates) => Promise
  
  // User type helpers
  isTrialUser,       // () => Boolean
  isFullUser,        // () => Boolean  
  isEnterpriseUser,  // () => Boolean
  isAdmin,           // () => Boolean
  
  // Trial management
  canUploadMore,     // () => Boolean
  getRemainingTrialUses, // () => Number|null
  
  // System info
  useSupabase,       // Boolean - currently using Supabase
  supabaseAvailable, // Boolean - Supabase is configured
  
  // Direct access (advanced)
  supabase,          // Supabase client (if using)
  axios              // Axios instance
} = useAuth()
```

## Migration Strategy

### Phase 1: Hybrid Setup (Current)
- Keep existing custom backend
- Add Supabase as primary auth
- Users can login with either system

### Phase 2: Gradual Migration
- New users automatically use Supabase
- Existing users continue with custom backend
- Provide migration tool for users to switch

### Phase 3: Full Supabase (Optional)
- Migrate all users to Supabase
- Keep custom backend for admin functions only

## Database Schema

Your existing Supabase schema (`supabase_schema_complete_v3.sql`) already supports this hybrid approach with:

- `auth.users` - Supabase managed users
- `user_profiles` - Extended user information
- Row Level Security policies
- Trial management
- Activity tracking

## Benefits of This Approach

1. **Flexibility**: Choose authentication method based on needs
2. **Gradual Migration**: No big-bang migration required  
3. **Redundancy**: Fallback if one system fails
4. **User Choice**: Different user types can use appropriate auth
5. **Admin Control**: Admins can use custom backend with full control
6. **Modern Features**: Supabase users get modern auth features

## Testing

Test both authentication paths:

```javascript
// Test Supabase auth
await login('supabase-user@example.com', 'password')

// Test custom backend auth  
await login('custom-user@example.com', 'password')

// Test admin auth (always custom)
await login('admin@company.com', 'password', true)
```

## Monitoring

The system logs which authentication method is being used:

```javascript
console.log('Using Supabase authentication')
console.log('Using custom backend authentication') 
console.log('Supabase login failed, falling back to custom auth')
```

This hybrid approach gives you the best of both worlds while maintaining complete backwards compatibility!
