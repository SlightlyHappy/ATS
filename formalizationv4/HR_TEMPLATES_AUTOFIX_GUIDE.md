# HR Templates Auto-Fix System

This system automatically detects and fixes common issues with HR templates during application startup and provides admin endpoints for manual intervention.

## Features

### 1. Automatic Issue Detection
The system can detect the following issues:
- **user_id constraint**: When the `user_id` column doesn't allow NULL values (preventing system templates)
- **missing_system_templates**: When no default system templates exist
- **table_missing**: When the hr_templates table doesn't exist
- **foreign_key_issues**: When foreign key constraints are broken

### 2. Automatic Startup Fix
During application initialization (`app/__init__.py`), the system:
1. Checks for HR templates issues
2. Automatically attempts to fix detected problems
3. Logs results and provides manual fix instructions if needed
4. Continues startup even if auto-fix fails

### 3. Database Initialization Fix
In the Railway deployment script (`scripts/railway_db_init.py`):
1. Attempts to create system templates
2. If it fails due to user_id constraint, automatically fixes the schema
3. Retries template creation after schema fix
4. Provides clear error messages and recovery instructions

### 4. Admin API Endpoints

#### Diagnose Issues
```http
GET /api/v1/admin/hr-templates/diagnose
```
Returns detected issues and recommendations for fixing them.

**Response:**
```json
{
  "issues_detected": {
    "user_id_constraint": true,
    "missing_system_templates": true,
    "table_missing": false,
    "foreign_key_issues": false
  },
  "has_issues": true,
  "recommendations": [
    {
      "issue": "user_id column does not allow NULL values",
      "fix": "Use auto-fix endpoint to update schema",
      "api": "POST /api/v1/admin/hr-templates/auto-fix"
    }
  ]
}
```

#### Auto-Fix All Issues
```http
POST /api/v1/admin/hr-templates/auto-fix
```
Automatically fixes all detected issues.

**Response:**
```json
{
  "success": true,
  "message": "Fixed 2/2 issues",
  "results": {
    "issues_detected": {...},
    "fixes_attempted": {
      "user_id_constraint": {
        "success": true,
        "message": "user_id constraint fixed successfully"
      },
      "system_templates": {
        "success": true,
        "message": "Created 3 system templates successfully"
      }
    },
    "overall_success": true
  }
}
```

### 5. Health Check Integration
The health check endpoint (`/api/health`) now includes HR templates status:

```json
{
  "status": "healthy",
  "services": {
    "hr_templates": {
      "status": "healthy",
      "message": "HR templates system operational",
      "system_templates": 3
    }
  }
}
```

If issues are detected:
```json
{
  "hr_templates": {
    "status": "degraded",
    "message": "HR templates have configuration issues",
    "issues": {
      "user_id_constraint": true
    },
    "system_templates": 0,
    "auto_fix_available": true
  }
}
```

## Manual Fix Options

### Option 1: Use Admin API (Recommended)
```bash
# Diagnose issues
curl -X GET /api/v1/admin/hr-templates/diagnose \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Auto-fix issues
curl -X POST /api/v1/admin/hr-templates/auto-fix \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Option 2: Run Standalone Script
```bash
python scripts/fix_hr_templates_user_id.py
```

### Option 3: Manual Database Commands
```sql
-- Fix user_id constraint
ALTER TABLE hr_templates DROP CONSTRAINT IF EXISTS hr_templates_user_id_fkey;
ALTER TABLE hr_templates ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE hr_templates ADD CONSTRAINT hr_templates_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id);
```

## Error Scenarios and Recovery

### Scenario 1: Deployment Fails with user_id Constraint
**Error:** `null value in column "user_id" violates not-null constraint`

**Automatic Recovery:**
1. Railway script detects the specific error
2. Runs auto-fix to update schema
3. Retries template creation
4. Logs success or failure

**Manual Recovery (if automatic fails):**
```bash
# Check diagnosis
curl -X GET /api/v1/admin/hr-templates/diagnose

# Apply fix
curl -X POST /api/v1/admin/hr-templates/auto-fix
```

### Scenario 2: Missing System Templates
**Symptoms:** HR templates functionality not working, no default templates

**Recovery:**
1. Auto-fix runs during startup and creates templates
2. If that fails, use admin API to create templates
3. Health check will show the issue and auto-fix availability

### Scenario 3: Schema Migration Issues
**Symptoms:** Table doesn't exist or has wrong structure

**Recovery:**
1. Run database migrations: `flask db upgrade`
2. Use auto-fix to create missing templates
3. Restart application to trigger startup auto-fix

## Logging and Monitoring

The system provides comprehensive logging:

```
2025-08-05 11:12:13 INFO [app]: Checking HR Templates system...
2025-08-05 11:12:13 INFO [app]: HR Templates issues detected, attempting auto-fix...
2025-08-05 11:12:13 INFO [app.services.hr_templates_autofix]: Fixing HR templates user_id constraint...
2025-08-05 11:12:13 INFO [app.services.hr_templates_autofix]: Creating system templates...
2025-08-05 11:12:13 INFO [app]: ✓ HR Templates auto-fix completed successfully
```

## Benefits

1. **Zero Downtime**: Issues are fixed automatically without manual intervention
2. **Graceful Degradation**: Application continues to work even if HR templates fail
3. **Admin Visibility**: Clear diagnostics and fix options for administrators
4. **Audit Trail**: All fixes are logged and tracked via admin actions
5. **Prevention**: Startup checks prevent issues from accumulating
6. **Recovery**: Multiple recovery options for different scenarios

## Configuration

No additional configuration required. The auto-fix system:
- Uses existing database connections
- Respects admin permissions
- Follows the same error handling patterns
- Integrates with existing logging and monitoring
