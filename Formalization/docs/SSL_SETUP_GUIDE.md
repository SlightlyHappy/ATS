# SSL Certificate Setup Guide for Windows
# Resume Screening Application - Production Deployment

## Overview
This guide will help you set up proper SSL certificates for your Resume Screening Application MVP demonstration using Let's Encrypt (free, trusted SSL certificates).

## Prerequisites

### 1. Domain Setup
- **Purchase a domain** (e.g., from Namecheap, GoDaddy, Cloudflare)
- **Configure DNS** to point to your server's public IP:
  ```
  A Record: yourdomain.com → YOUR_SERVER_IP
  A Record: www.yourdomain.com → YOUR_SERVER_IP
  ```

### 2. Server Requirements
- **Public IP address** (VPS, cloud server, or dedicated server)
- **Port 80 and 443 open** in firewall
- **Docker and Docker Compose** installed

## Method 1: Using Cloud Provider SSL (Recommended for MVP)

### Option A: Cloudflare (Free SSL + CDN)
1. **Sign up for Cloudflare** (free plan)
2. **Add your domain** to Cloudflare
3. **Update nameservers** at your domain registrar
4. **Enable SSL** in Cloudflare dashboard:
   - SSL/TLS → Overview → Full (strict)
   - SSL/TLS → Edge Certificates → Always Use HTTPS: ON

### Option B: AWS Certificate Manager (if using AWS)
1. **Request certificate** in AWS Certificate Manager
2. **Validate domain** via DNS or email
3. **Attach to Application Load Balancer**

### Option C: DigitalOcean Managed Certificates (if using DO)
1. **Create certificate** in DigitalOcean control panel
2. **Attach to Load Balancer**

## Method 2: Let's Encrypt with Docker (Self-managed)

### Step 1: Prepare Environment
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Create environment file
echo "DOMAIN=yourdomain.com" > .env.ssl
echo "EMAIL=admin@yourdomain.com" >> .env.ssl
```

### Step 2: Get SSL Certificate
```bash
# Stop any running services on port 80
docker-compose down

# Get certificate using Certbot Docker container
docker run -it --rm --name certbot \
  -v ${PWD}/nginx/ssl:/etc/letsencrypt \
  -v ${PWD}/nginx/ssl:/var/lib/letsencrypt \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email \
  -d yourdomain.com \
  -d www.yourdomain.com
```

### Step 3: Copy Certificates
```bash
# Copy certificates to nginx directory
cp nginx/ssl/live/yourdomain.com/fullchain.pem nginx/ssl/certificate.crt
cp nginx/ssl/live/yourdomain.com/privkey.pem nginx/ssl/private.key

# Generate DH parameters for security
openssl dhparam -out nginx/ssl/dhparam.pem 2048
```

## Method 3: Development/Testing SSL (Self-signed)

### Only for testing - browsers will show warnings
```bash
# Generate self-signed certificate (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/private.key \
  -out nginx/ssl/certificate.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"

# Generate DH parameters
openssl dhparam -out nginx/ssl/dhparam.pem 2048
```

## Cloud Hosting Options for MVP

### 1. DigitalOcean App Platform (Recommended for MVP)
**Cost**: ~$12/month
**Benefits**: Managed SSL, auto-deployment, scaling

```yaml
# .do/app.yaml
name: resume-screening-app
services:
- name: web
  source_dir: /
  github:
    repo: your-username/resume-screening-app
    branch: main
  run_command: docker-compose up
  environment_slug: docker
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  envs:
  - key: APP_DOMAIN
    value: your-app.ondigitalocean.app
```

### 2. Railway (Easy Docker Deployment)
**Cost**: ~$5-10/month
**Benefits**: GitHub integration, automatic SSL

1. **Connect GitHub repo** to Railway
2. **Add environment variables**
3. **Deploy with one click**

### 3. Render (Free tier available)
**Cost**: Free tier, then $7/month
**Benefits**: Free SSL, easy deployment

```yaml
# render.yaml
services:
  - type: web
    name: resume-screening
    env: docker
    repo: https://github.com/your-username/resume-screening-app
    dockerfilePath: ./Dockerfile.production
    envVars:
      - key: APP_DOMAIN
        value: your-app.onrender.com
```

### 4. Heroku (Simple deployment)
**Cost**: ~$7/month per dyno
**Benefits**: Easy deployment, managed SSL

```bash
# Deploy to Heroku
heroku create your-resume-app
heroku addons:create heroku-postgresql
heroku addons:create heroku-redis
git push heroku main
```

### 5. AWS ECS with Application Load Balancer
**Cost**: ~$15-25/month
**Benefits**: Enterprise-grade, scalable

### 6. Google Cloud Run
**Cost**: Pay-per-use, ~$5-15/month
**Benefits**: Serverless, auto-scaling

## Quick MVP Deployment (Recommended Path)

### Option 1: DigitalOcean Droplet + Docker
```bash
# 1. Create $12/month droplet
# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Clone your repo
git clone your-repo-url
cd resume-screening-app

# 4. Setup SSL (using Cloudflare proxy)
# - Add domain to Cloudflare
# - Set SSL mode to "Full"
# - Use Cloudflare nameservers

# 5. Deploy
./deploy-production.sh full yourdomain.com
```

### Option 2: Railway (Simplest)
```bash
# 1. Push code to GitHub
# 2. Connect Railway to GitHub
# 3. Add environment variables
# 4. Deploy with one click
# 5. Get free .railway.app subdomain with SSL
```

## SSL Certificate Renewal

### Automatic Renewal Script
```bash
#!/bin/bash
# File: scripts/renew-ssl.sh

DOMAIN="yourdomain.com"

# Stop services
docker-compose down

# Renew certificate
docker run --rm --name certbot \
  -v ${PWD}/nginx/ssl:/etc/letsencrypt \
  -v ${PWD}/nginx/ssl:/var/lib/letsencrypt \
  -p 80:80 \
  certbot/certbot renew --standalone

# Copy renewed certificates
cp nginx/ssl/live/$DOMAIN/fullchain.pem nginx/ssl/certificate.crt
cp nginx/ssl/live/$DOMAIN/privkey.pem nginx/ssl/private.key

# Restart services
docker-compose up -d

echo "SSL renewal completed"
```

### Schedule Renewal (Linux/Mac)
```bash
# Add to crontab (runs monthly)
crontab -e

# Add this line:
0 2 1 * * /path/to/your/app/scripts/renew-ssl.sh
```

## Verification

### Check SSL Certificate
```bash
# Verify certificate
openssl x509 -in nginx/ssl/certificate.crt -text -noout

# Test SSL connection
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### Online SSL Checkers
- https://www.ssllabs.com/ssltest/
- https://www.sslchecker.com/
- https://gf.dev/ssl-checker

## Security Best Practices

1. **Use Strong Ciphers**: Already configured in nginx.conf
2. **Enable HSTS**: Already configured
3. **Regular Updates**: Keep certificates renewed
4. **Monitor Expiry**: Set up alerts 30 days before expiry
5. **Backup Certificates**: Store securely

## Troubleshooting

### Common Issues

1. **Port 80 blocked**: Check firewall settings
2. **DNS not propagated**: Wait 24-48 hours
3. **Certificate chain issues**: Use fullchain.pem
4. **Mixed content warnings**: Ensure all resources use HTTPS

### Quick Fixes
```bash
# Check port 80 accessibility
curl -I http://yourdomain.com

# Verify DNS propagation
nslookup yourdomain.com

# Test certificate
curl -I https://yourdomain.com
```

## Recommended MVP Setup

For quickest MVP deployment with proper SSL:

1. **Domain**: Register with Cloudflare Registrar ($8-12/year)
2. **Hosting**: DigitalOcean Droplet ($12/month) 
3. **SSL**: Cloudflare proxy (Free)
4. **Deployment**: Docker Compose

**Total cost**: ~$12-15/month for production-ready MVP

This gives you:
- ✅ Proper SSL certificates
- ✅ CDN and DDoS protection
- ✅ Professional domain
- ✅ Scalable infrastructure
- ✅ SSL certificate management
- ✅ 99.9% uptime
