# Supabase Setup Instructions

## 1. Create the Database Schema

Go to your Supabase Dashboard → SQL Editor and run the contents of `supabase_schema.sql`:

```sql
-- Copy and paste the entire contents of supabase_schema.sql
-- This will create the resumes table with all necessary indexes and constraints
```

## 2. Verify the Setup

After running the schema, you should see:
- A `resumes` table in your database
- Several indexes for performance
- A `resume_stats` view for analytics
- A test record inserted

## 3. Test the Integration

Run the test script to verify everything is working:

```bash
cd backend
python test_supabase_integration.py
```

## 4. Environment Variables

Make sure these are set in your `.env` file:
```
ENABLE_PERSISTENT_STORAGE=True
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 5. New API Endpoints Available

Once setup is complete, you'll have these new endpoints:

### Supabase Storage
- `GET /api/supabase/status` - Check Supabase connection
- `GET /api/supabase/resumes` - Get all resumes from Supabase
- `POST /api/supabase/search` - Search resumes in Supabase
- `POST /api/supabase/sync/<id>` - Sync specific resume to Supabase
- `POST /api/supabase/sync-all` - Sync all local resumes to Supabase

### Combined Storage
- `GET /api/storage/combined` - Get resumes from both local and Supabase

## 6. How It Works

1. **Local First**: Resumes are still stored locally for fast access
2. **Auto-Sync**: New resumes are automatically synced to Supabase in the background
3. **Shared Pool**: All resumes (from free and paid users) go into the same Supabase database
4. **Deduplication**: Duplicate resumes are detected by file hash
5. **Compression**: All resume data is compressed (typically 80-90% reduction)

## 7. Testing the Full Flow

1. Clear local storage (already done)
2. Upload a resume through the web interface
3. Check that it appears in both local storage and Supabase
4. Use the `/api/storage/combined` endpoint to see all resumes

## 8. Troubleshooting

If you encounter issues:
1. Check the backend logs for Supabase connection errors
2. Verify your environment variables are correct
3. Test the connection with: `GET /api/supabase/status`
4. Run the test script: `python test_supabase_integration.py`
