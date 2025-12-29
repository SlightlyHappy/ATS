# Archived Files Summary

This directory contains files that were moved from the main project structure as they were identified as unused in the current deployment on Vercel.

## Archived on: August 20, 2025

## Categories of Archived Files:

### 1. Unused Page Variants (`unused-pages/`)
- `page_old.tsx` - Old version of main landing page
- `page_enhanced.tsx` - Enhanced version of landing page
- `page_apple.tsx` - Apple-style landing page variant
- `page_optimized.tsx` - Optimized version of landing page
- `page.tsx.backup` - Backup of main page file

**Note**: The current active page is `src/app/page.tsx` (main landing page)

### 2. Unused Admin Components (`unused-admin-components/`)
- `dashboard-overview-fixed.tsx` - Fixed version of dashboard overview
- `database-view-old.tsx` - Old version of database view component
- `users-management-new.tsx` - New version of users management (not in use)
- `users-management-old.tsx` - Old version of users management

**Note**: The current active admin components are:
- `dashboard-overview.tsx`
- `database-view.tsx` 
- `users-management.tsx`

### 3. Development Scripts (`dev-scripts/`)
- `performance-report.js` - Performance testing script
- `test-optimizations.js` - Optimization testing script

**Note**: These scripts were not referenced in package.json or build process

### 4. Development Documentation (`dev-docs/`)
- `BACKEND_CHECKLIST.md` - Backend development checklist
- `BACKEND_REQUIREMENTS.md` - Backend requirements documentation
- `CANDIDATE_IMPLEMENTATION.md` - Candidate feature implementation notes

**Note**: These are development/planning documents not needed for production

## How Files Were Identified as Unused:

1. **Build Analysis**: Ran `npm run build` to see which files are actually compiled
2. **Import Tracing**: Searched for imports and usage of each file variant
3. **Active Component Verification**: Checked which components are imported in active dashboard pages

## Current Active File Structure:

### Main Pages:
- `/` → `src/app/page.tsx`
- `/admin/dashboard` → `src/app/admin/dashboard/page.tsx`
- `/admin/login` → `src/app/admin/login/page.tsx`
- `/candidates/*` → Various candidate pages
- `/user/dashboard` → `src/app/user/dashboard/page.tsx`

### Active Admin Components:
- `business-analytics.tsx`
- `candidate-oversight.tsx`
- `dashboard-overview.tsx` ✓
- `database-view.tsx` ✓
- `health-reports.tsx`
- `recruiter-accounts.tsx`
- `system-admin.tsx`
- `system-logs.tsx`
- `users-management.tsx` ✓

### Active User Components:
- `candidate-finder-chat.tsx`
- `resume-upload.tsx`
- `uploaded-resume-dashboard.tsx`

## Restoration Instructions:

If any of these files need to be restored:

1. Copy the file from the appropriate archived subdirectory
2. Move it back to its original location in the `src/` directory
3. Update any import statements if necessary
4. Run `npm run build` to verify everything compiles correctly

## Production Safety:

✅ All archived files were verified as unused in the current production build
✅ No active imports or dependencies were found for these files
✅ Build process completed successfully after archiving
✅ All active pages and components remain functional
