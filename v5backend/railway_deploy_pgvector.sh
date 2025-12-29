#!/bin/bash
# Railway deployment helper script for pgvector migration
# This script helps with the Railway deployment process

set -e

echo "🚂 Railway pgvector Migration Helper"
echo "======================================"

# Check if Railway CLI is available
if ! command -v npx &> /dev/null; then
    echo "❌ npx not found. Please install Node.js and Railway CLI"
    exit 1
fi

# Function to update environment variables for a service
update_service_vars() {
    local service_name="$1"
    echo ""
    echo "🔧 Updating $service_name service..."
    
    # Select the service
    echo "Selecting service: $service_name"
    npx @railway/cli service "$service_name" || {
        echo "❌ Failed to select service $service_name"
        echo "Available services:"
        npx @railway/cli service
        exit 1
    }
    
    # Update database variables
    echo "📊 Updating database configuration..."
    npx @railway/cli variables set DATABASE_URL="postgresql://postgres:v2T.XhpyDFev5G4jzyM705tJzpLnDav5@centerbeam.proxy.rlwy.net:25894/railway?application_name=ats_${service_name}&connect_timeout=30&sslmode=prefer"
    npx @railway/cli variables set DATABASE_INTERNAL_URL="postgresql://postgres:v2T.XhpyDFev5G4jzyM705tJzpLnDav5@pgvector.railway.internal:5432/railway?application_name=ats_${service_name}&connect_timeout=30&sslmode=prefer"
    npx @railway/cli variables set DATABASE_PUBLIC_URL="postgresql://postgres:v2T.XhpyDFev5G4jzyM705tJzpLnDav5@centerbeam.proxy.rlwy.net:25894/railway?application_name=ats_${service_name}&connect_timeout=30&sslmode=prefer"
    npx @railway/cli variables set PGHOST="pgvector.railway.internal"
    npx @railway/cli variables set PGPORT="5432"
    npx @railway/cli variables set PGUSER="postgres"
    npx @railway/cli variables set PGPASSWORD="v2T.XhpyDFev5G4jzyM705tJzpLnDav5"
    npx @railway/cli variables set PGDATABASE="railway"
    
    # Update vector configuration
    echo "🔍 Updating vector search configuration..."
    npx @railway/cli variables set ENABLE_VECTOR_SEARCH="true"
    npx @railway/cli variables set PGVECTOR_RETRY_COUNT="3"
    npx @railway/cli variables set PGVECTOR_RETRY_DELAY="5"
    npx @railway/cli variables set SKIP_PGVECTOR_ON_FAILURE="false"
    npx @railway/cli variables set FORCE_PGVECTOR_CREATION="true"
    
    # Update Railway metadata
    echo "🚂 Updating Railway metadata..."
    npx @railway/cli variables set RAILWAY_TCP_PROXY_DOMAIN="centerbeam.proxy.rlwy.net"
    npx @railway/cli variables set RAILWAY_TCP_PROXY_PORT="25894"
    
    echo "✅ $service_name configuration updated"
}

# Function to remove old HA cluster variables
remove_old_vars() {
    local service_name="$1"
    echo ""
    echo "🧹 Removing old HA cluster variables from $service_name..."
    
    # Select the service
    npx @railway/cli service "$service_name"
    
    # Remove old variables (this might fail if they don't exist, which is fine)
    variables_to_remove=(
        "PGPOOL_ADMIN_USERNAME"
        "PGPOOL_ADMIN_PASSWORD"
        "PGPOOL_POSTGRES_USERNAME"
        "PGPOOL_POSTGRES_PASSWORD"
        "PGPOOL_SR_CHECK_USER"
        "PGPOOL_SR_CHECK_PASSWORD"
        "PGPOOL_BACKEND_NODES"
        "PGPOOL_ENABLE_LDAP"
        "PGPOOL_HEALTH_CHECK_MAX_RETRIES"
        "PGPOOL_HEALTH_CHECK_RETRY_DELAY"
        "REPMGR_PRIMARY_HOST"
        "REPMGR_PASSWORD"
        "REPMGR_USERNAME"
        "REPMGR_PARTNER_NODES"
    )
    
    for var in "${variables_to_remove[@]}"; do
        echo "Removing $var..."
        npx @railway/cli variables delete "$var" 2>/dev/null || echo "  (variable not found, skipping)"
    done
    
    echo "✅ Old variables cleaned up"
}

# Function to verify deployment
verify_deployment() {
    local service_name="$1"
    echo ""
    echo "🔍 Verifying $service_name deployment..."
    
    # Select the service
    npx @railway/cli service "$service_name"
    
    echo "📋 Current environment variables:"
    npx @railway/cli variables | grep -E "(DATABASE|PGVECTOR|ENABLE_VECTOR)" || echo "No relevant variables found"
    
    echo ""
    echo "📊 Recent deployment logs:"
    npx @railway/cli logs --lines 20
}

# Main execution
case "${1:-help}" in
    "api")
        echo "🌐 Updating API service (adventurous-quietude)..."
        update_service_vars "adventurous-quietude"
        remove_old_vars "adventurous-quietude"
        verify_deployment "adventurous-quietude"
        ;;
    "worker")
        echo "👷 Updating Worker service..."
        # You'll need to replace this with your actual worker service name
        read -p "Enter worker service name: " worker_service
        update_service_vars "$worker_service"
        remove_old_vars "$worker_service"
        verify_deployment "$worker_service"
        ;;
    "both")
        echo "🔄 Updating both API and Worker services..."
        update_service_vars "adventurous-quietude"
        remove_old_vars "adventurous-quietude"
        
        read -p "Enter worker service name: " worker_service
        update_service_vars "$worker_service"
        remove_old_vars "$worker_service"
        
        verify_deployment "adventurous-quietude"
        verify_deployment "$worker_service"
        ;;
    "verify")
        echo "🔍 Verifying current configuration..."
        echo ""
        echo "Available services:"
        npx @railway/cli service
        echo ""
        read -p "Enter service name to verify: " service_name
        verify_deployment "$service_name"
        ;;
    "test-db")
        echo "🧪 Testing pgvector database connection..."
        python verify_pgvector_db.py
        ;;
    "help"|*)
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  api      - Update API service (adventurous-quietude) configuration"
        echo "  worker   - Update Worker service configuration"
        echo "  both     - Update both API and Worker services"
        echo "  verify   - Verify current service configuration"
        echo "  test-db  - Test pgvector database connection"
        echo "  help     - Show this help message"
        echo ""
        echo "This script will:"
        echo "  1. Update database connection to pgvector service"
        echo "  2. Enable vector search functionality"
        echo "  3. Remove old HA cluster variables"
        echo "  4. Verify the deployment"
        echo ""
        echo "Make sure you have Railway CLI installed and authenticated:"
        echo "  npm install -g @railway/cli"
        echo "  npx @railway/cli login"
        echo ""
        ;;
esac

echo ""
echo "🎉 Railway migration helper completed!"
echo "Check the deployment logs to ensure everything is working correctly."
