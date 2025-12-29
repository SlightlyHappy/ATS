# HR Templates Database Fix

## Issue
The deployment failed because the HR templates table has a NOT NULL constraint on the `user_id` column, but the system tries to create system templates with `user_id = NULL`.

## Root Cause
- The `HRTemplate` model in `app/models/communication.py` had `user_id` as `nullable=False`
- System templates should be able to have `user_id = NULL` to indicate they're global templates
- The initialization script tries to create templates with `user_id=None`

## Fix Applied
1. **Updated Model**: Changed `user_id` column in `HRTemplate` model to `nullable=True`
2. **Updated to_dict method**: Handle None values for `user_id` in serialization
3. **Created migration script**: `scripts/fix_hr_templates_user_id.py` to update existing database

## Next Steps for Deployment

### Option 1: Run Migration Script (Recommended)
```bash
# In your Railway environment
python scripts/fix_hr_templates_user_id.py
```

### Option 2: Manual Database Fix
```sql
-- Connect to your PostgreSQL database
ALTER TABLE hr_templates DROP CONSTRAINT IF EXISTS hr_templates_user_id_fkey;
ALTER TABLE hr_templates ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE hr_templates ADD CONSTRAINT hr_templates_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id);
```

### Option 3: Drop and Recreate Tables (Nuclear Option)
```bash
# If the above doesn't work, you can reset the HR templates table
python -c "
from app import create_app, db
from app.models.communication import HRTemplate
app = create_app()
with app.app_context():
    db.session.execute('DROP TABLE IF EXISTS hr_templates CASCADE')
    db.session.commit()
    db.create_all()
"
```

## Verification
After applying the fix, the system should be able to:
1. Create system templates with `user_id = NULL`
2. Successfully initialize default HR templates
3. Complete the deployment process

## Legal RAG Status
✅ The legal RAG system is working correctly - the logs show successful model downloads and initialization.
