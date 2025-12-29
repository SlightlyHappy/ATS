#!/usr/bin/env bash

# Railway MinIO Setup Script
# This script helps set up MinIO service on Railway

echo "🚂 Railway MinIO Setup Helper"
echo "=============================="

echo "
To properly set up S3/MinIO storage for your Railway worker service, you need to:

1️⃣  **Deploy MinIO Service:**
   railway service create --name minio
   railway service update --service minio --image minio/minio:latest
   railway service update --service minio --command 'server --console-address \":9001\" /data'

2️⃣  **Set MinIO Environment Variables:**
   railway variables set MINIO_ROOT_USER=tdo1jZDlVtVlDmSfRkYlqWmAK3NzIRO5 --service minio
   railway variables set MINIO_ROOT_PASSWORD=QAe1hzWQ2x1ajBVMpez3GD1yBoEmQfNX3lrFvZa5oSUCfEa7 --service minio
   railway variables set MINIO_DOMAIN=bucket.railway.internal --service minio

3️⃣  **Create Railway Internal Network:**
   # MinIO should be accessible at bucket.railway.internal:9000
   # This requires Railway private networking setup

4️⃣  **Deploy MinIO Bucket Setup Service:**
   railway service create --name minio-setup
   railway service update --service minio-setup --image minio/mc:latest
   railway service update --service minio-setup --command 'mc alias set local http://bucket.railway.internal:9000 tdo1jZDlVtVlDmSfRkYlqWmAK3NzIRO5 QAe1hzWQ2x1ajBVMpez3GD1yBoEmQfNX3lrFvZa5oSUCfEa7 && mc mb -p local/resumes || true && mc mb -p local/tmp-uploads || true'

5️⃣  **Update Worker Service Configuration:**
   # Your worker service should already have the correct S3 environment variables:
   # S3_ENDPOINT=http://bucket.railway.internal:9000
   # S3_ACCESS_KEY=tdo1jZDlVtVlDmSfRkYlqWmAK3NzIRO5
   # S3_SECRET_KEY=QAe1hzWQ2x1ajBVMpez3GD1yBoEmQfNX3lrFvZa5oSUCfEa7
   # S3_BUCKET=resumes
   # S3_BUCKET_TMP=tmp-uploads
   # S3_PATH_STYLE=true

📋 **Alternative: Use External S3-Compatible Service**

If Railway private networking is complex, consider using:
- AWS S3 (with proper IAM credentials)
- DigitalOcean Spaces
- Cloudflare R2
- Any S3-compatible service

Update these environment variables in your worker service:
- S3_ENDPOINT (e.g., https://nyc3.digitaloceanspaces.com)
- S3_ACCESS_KEY (your service access key)
- S3_SECRET_KEY (your service secret key)
- S3_REGION (appropriate region)

🔧 **Testing S3 Connection:**

After setup, test your S3 connection:
railway run --service worker python check_s3_health.py

✅ **Troubleshooting:**

1. Check service logs: railway logs --service minio
2. Verify internal networking: railway service info
3. Test MinIO console: Access via Railway public domain
4. Check bucket creation: Use mc client to verify buckets exist

💡 **Development Environment:**

For local development that matches Railway:
docker-compose -f docker-compose.railway.yml up

This uses the same credentials and bucket names as Railway.
"

echo "Would you like to run the Railway CLI commands automatically? (y/N)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🚀 Running Railway setup commands..."
    
    # Check if railway CLI is installed
    if ! command -v railway &> /dev/null; then
        echo "❌ Railway CLI not found. Please install it first:"
        echo "npm install -g @railway/cli"
        exit 1
    fi
    
    echo "Creating MinIO service..."
    railway service create --name minio || echo "⚠️  Service might already exist"
    
    echo "Configuring MinIO..."
    railway variables set MINIO_ROOT_USER=tdo1jZDlVtVlDmSfRkYlqWmAK3NzIRO5 --service minio
    railway variables set MINIO_ROOT_PASSWORD=QAe1hzWQ2x1ajBVMpez3GD1yBoEmQfNX3lrFvZa5oSUCfEa7 --service minio
    
    echo "✅ Setup commands completed!"
    echo "📋 Next steps:"
    echo "1. Deploy MinIO: railway deploy --service minio"
    echo "2. Check logs: railway logs --service minio"
    echo "3. Test connection: railway run --service worker python check_s3_health.py"
else
    echo "ℹ️  Manual setup required. Follow the instructions above."
fi
