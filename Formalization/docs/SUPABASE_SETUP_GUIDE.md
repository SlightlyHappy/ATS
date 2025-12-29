# Complete Supabase Setup Guide for Resume Screening App

## 🚀 Quick Start Setup

### 1. Create Supabase Project
1. Go to [https://supabase.com](https://supabase.com)
2. Create a new account or sign in
3. Click "New Project" and fill in:
   - **Project Name**: `resume-screening-app`
   - **Database Password**: Generate a strong password
   - **Region**: Select closest to your users
4. Wait for project initialization (2-3 minutes)

### 2. Run Database Schema
1. Go to your Supabase Dashboard → **SQL Editor**
2. Copy the entire content of `backend/supabase_schema_complete_v3.sql`
3. Paste it in the SQL Editor and click **Run**
4. Verify you see success messages at the bottom

### 3. Configure Environment Variables
1. In Supabase Dashboard → **Settings** → **API**
2. Copy these values to your `.env` file:

```env
# From Supabase Dashboard → Settings → API
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# From Settings → API → JWT Settings
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

### 4. Enable Authentication
1. Go to **Authentication** → **Settings**
2. Enable **Email** provider
3. Configure email templates if needed
4. Set site URL to: `http://localhost:3000`

### 5. Test the Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Test Supabase connection
python supabase_manager.py

# Start the backend
python app.py
```

## 📊 Database Schema Overview

### Core Tables Created:

#### 1. `user_profiles`
- Extends Supabase auth.users
- Manages trial limits, subscriptions, preferences
- Tracks user activity and login history

#### 2. `resumes`  
- Stores resume files and analysis results
- Links to user_profiles via user_id
- Includes AI scores, extracted data, full-text search

#### 3. `user_activity`
- Comprehensive activity tracking
- Logs uploads, logins, analyses, exports
- Performance metrics and error tracking

#### 4. `hr_legal_queries`
- Stores HR legal questions and AI responses
- Categorized queries with confidence scores
- User feedback and rating system

#### 5. `system_config`
- Application settings and feature flags
- Trial limits, AI model configs
- Email templates and legal sources

### Analytics Views:
- `user_analytics` - User statistics and trial data
- `resume_stats` - Resume processing analytics  
- `system_analytics` - Overall system metrics

## 🔐 Security Features

### Row Level Security (RLS)
- Users can only access their own data
- Admins have elevated permissions
- Public access to system config where appropriate

### Authentication Flow
1. User signs up via Supabase Auth
2. Automatic profile creation via database trigger
3. JWT token validation for API requests
4. Activity logging for all actions

### Trial Management
- Automatic trial usage tracking
- Database triggers prevent limit exceeded
- Upgrade prompts and restrictions

## 🛠️ Backend Integration

### Key Classes and Functions:

#### `SupabaseManager`
```python
# Initialize
manager = SupabaseManager()

# User authentication
result = await manager.authenticate_user(email, password)

# Store resume
resume_id = await manager.store_resume(user_id, resume_data)

# Track activity  
await manager.log_user_activity(user_id, 'upload_resume', 'Uploaded CV')
```

#### Authentication Helpers
```python
# Validate request
is_valid, user = await authenticate_request(access_token)

# Require auth (raises exception if invalid)
user = await require_auth(access_token)
```

## 📈 Usage Examples

### 1. User Registration
```python
result = await supabase_manager.create_user(
    email="john@example.com",
    password="secure123",
    full_name="John Doe"
)
```

### 2. Resume Upload & Analysis
```python
# Store resume
resume_result = await supabase_manager.store_resume(user_id, {
    'filename': 'john_doe_cv.pdf',
    'compressed_content': compressed_data,
    'file_size': 1024000,
    'parsed_info': {
        'name': 'John Doe',
        'email': 'john@example.com',
        'skills': ['Python', 'React', 'SQL']
    }
})

# Update with AI analysis
await supabase_manager.update_resume_analysis(resume_id, {
    'overall_score': 85,
    'technical_score': 90,
    'ai_feedback': 'Strong technical background...'
})
```

### 3. HR Legal Query
```python
query_id = await supabase_manager.store_hr_legal_query(
    user_id, 
    "What are the legal requirements for background checks?",
    "compliance"
)

await supabase_manager.update_hr_legal_response(query_id, {
    'response': 'Background checks must comply with...',
    'confidence': 0.92,
    'sources': ['Employment Law 2024', 'Privacy Act']
})
```

## 🔧 Frontend Integration

### Update React App to use Supabase:

#### 1. Install Supabase Client
```bash
cd frontend
npm install @supabase/supabase-js
```

#### 2. Create Supabase Client
```javascript
// src/lib/supabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

#### 3. Update Auth Context
```javascript
// src/contexts/AuthContext.js
import { supabase } from '../lib/supabase'

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password
})

// Sign out
await supabase.auth.signOut()

// Check session
const { data: { session } } = await supabase.auth.getSession()
```

## 🎯 Next Steps

### 1. Create Admin User
After first user signup, run:
```sql
SELECT setup_admin_user('your-admin-email@domain.com');
```

### 2. Configure Email Templates
- Update system_config for custom email templates
- Set up SMTP for trial expiration notifications

### 3. Add More Features
- Real-time notifications via Supabase Realtime
- File storage via Supabase Storage
- Advanced analytics dashboards

### 4. Production Deployment
- Enable database backups
- Configure custom domain
- Set up monitoring and alerts
- Review RLS policies for security

## 🐛 Troubleshooting

### Common Issues:

#### 1. "Invalid JWT" Error
- Check SUPABASE_JWT_SECRET is correct
- Verify token expiration
- Ensure user is properly authenticated

#### 2. "Row Level Security" Error  
- User may not have permission to access data
- Check if user profile exists
- Verify admin status for admin operations

#### 3. "Trial Limit Reached" Error
- User has exceeded trial limits
- Check trial_usage vs trial_limit
- Update access_type to 'full' for unlimited access

#### 4. Database Connection Issues
- Verify SUPABASE_URL and keys are correct
- Check project is not paused
- Ensure network connectivity

### Getting Help
- Check Supabase Dashboard → Logs for errors
- Use browser dev tools to inspect network requests
- Enable debug logging in backend
- Review database activity in SQL Editor

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Realtime Subscriptions](https://supabase.com/docs/guides/realtime)
- [Storage Documentation](https://supabase.com/docs/guides/storage)

---

✅ Your Resume Screening App is now ready with full user management, authentication, activity tracking, and analytics!
