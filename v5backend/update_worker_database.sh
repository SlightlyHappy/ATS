# Railway Worker Service Database Update Commands
# Run these commands to align worker with the PostgreSQL HA cluster

# 1. Switch to worker service (if not already selected)
npx @railway/cli service worker

# 2. Update database URLs to match HA cluster
npx @railway/cli variables set DATABASE_URL="postgresql://postgres:Aed0bbEDa6B5a4e9A225D101Cc43D23F@pgpool.railway.internal:5432/?application_name=ats_worker&connect_timeout=30&sslmode=prefer"

npx @railway/cli variables set DATABASE_PUBLIC_URL="postgresql://postgres:Aed0bbEDa6B5a4e9A225D101Cc43D23F@crossover.proxy.rlwy.net:24303/railway?application_name=ats_worker&connect_timeout=30&sslmode=prefer"

# 3. Update individual PostgreSQL connection parameters
npx @railway/cli variables set PGHOST="pgpool.railway.internal"
npx @railway/cli variables set PGPORT="5432"
npx @railway/cli variables set PGUSER="postgres"
npx @railway/cli variables set PGPASSWORD="Aed0bbEDa6B5a4e9A225D101Cc43D23F"
npx @railway/cli variables set PGDATABASE="railway"

# 4. Add missing database URLs for consistency
npx @railway/cli variables set DATABASE_INTERNAL_URL="postgresql://postgres:Aed0bbEDa6B5a4e9A225D101Cc43D23F@pgpool.railway.internal:5432/?application_name=ats_worker&connect_timeout=30&sslmode=prefer"

npx @railway/cli variables set DATABASE_PRIMARY_NODE="postgresql://postgres:Aed0bbEDa6B5a4e9A225D101Cc43D23F@pg-0.railway.internal:5432/?application_name=ats_worker&connect_timeout=30&sslmode=prefer"

npx @railway/cli variables set DATABASE_REPLICA_1="postgresql://postgres:Aed0bbEDa6B5a4e9A225D101Cc43D23F@pg-1.railway.internal:5432/?application_name=ats_worker&connect_timeout=30&sslmode=prefer"

npx @railway/cli variables set DATABASE_REPLICA_2="postgresql://postgres:Aed0bbEDa6B5a4e9A225D101Cc43D23F@pg-2.railway.internal:5432/?application_name=ats_worker&connect_timeout=30&sslmode=prefer"

# 5. Add HA cluster configuration variables
npx @railway/cli variables set PGPOOL_ADMIN_USERNAME="admin"
npx @railway/cli variables set PGPOOL_ADMIN_PASSWORD="Aed0bbEDa6B5a4e9A225D101Cc43D23F"
npx @railway/cli variables set PGPOOL_POSTGRES_USERNAME="postgres"
npx @railway/cli variables set PGPOOL_POSTGRES_PASSWORD="Aed0bbEDa6B5a4e9A225D101Cc43D23F"
npx @railway/cli variables set PGPOOL_SR_CHECK_USER="postgres"
npx @railway/cli variables set PGPOOL_SR_CHECK_PASSWORD="Aed0bbEDa6B5a4e9A225D101Cc43D23F"
npx @railway/cli variables set PGPOOL_BACKEND_NODES="0:pg-0.railway.internal:5432,1:pg-1.railway.internal:5432,2:pg-2.railway.internal:5432"
npx @railway/cli variables set PGPOOL_ENABLE_LDAP="no"
npx @railway/cli variables set PGPOOL_HEALTH_CHECK_MAX_RETRIES="10"
npx @railway/cli variables set PGPOOL_HEALTH_CHECK_RETRY_DELAY="30"

# 6. Add repmgr configuration
npx @railway/cli variables set REPMGR_PRIMARY_HOST="pg-0.railway.internal"
npx @railway/cli variables set REPMGR_PASSWORD="0ba1B8DCcaf51Dba665dAAD8DdFF6aBd"
npx @railway/cli variables set REPMGR_USERNAME="repmgr"
npx @railway/cli variables set REPMGR_PARTNER_NODES="pg-0,pg-1,pg-2"

# 7. Update database pool settings for consistency
npx @railway/cli variables set DATABASE_POOL_SIZE="10"
npx @railway/cli variables set DATABASE_MAX_OVERFLOW="15"

# 8. Add auto-migration flag
npx @railway/cli variables set AUTO_MIGRATE_ON_STARTUP="true"

echo "✅ Worker database configuration updated to use PostgreSQL HA cluster"
echo "🔄 Redeploy the worker service to apply changes"
