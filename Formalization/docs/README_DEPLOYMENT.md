# 🚀 Resume Screening App - Unified Deployment Guide

This guide covers the unified deployment system that supports development, beta, and production environments with a single set of scripts.

## 🎯 Quick Start

### Option 1: Interactive Deployment
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows
deploy.bat
```

### Option 2: Command Line Deployment
```bash
# Development (default)
./deploy.sh --env development

# Beta deployment
./deploy.sh --env beta

# Production deployment  
./deploy.sh --env production
```

## 📋 Prerequisites

- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- **Linux/Windows Server** with at least 4GB RAM (for beta/production)

### Installing Docker:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Windows: Download Docker Desktop from docker.com
```

## 🌍 Environment Configurations

### 1. **Development** (`--env development`)
- **Purpose**: Local development and testing
- **Features**: Hot reload, debug logging, exposed ports
- **Compose File**: `docker-compose.yml`
- **Environment**: `.env.development`
- **Security**: Minimal (development credentials)
- **Access**: `http://localhost:3000` (frontend), `http://localhost:8000` (API)

### 2. **Beta** (`--env beta`)
- **Purpose**: Beta testing and staging
- **Features**: Production build, relaxed security, monitoring
- **Compose File**: `docker-compose.production.yml`
- **Environment**: `.env.beta`
- **Security**: Basic (auto-generated secure passwords)
- **Access**: `http://your-domain.com` (via nginx reverse proxy)

### 3. **Production** (`--env production`)
- **Purpose**: Full production deployment
- **Features**: Enterprise security, hardening, monitoring, secrets management
- **Compose File**: `docker-compose.production.yml`
- **Environment**: `.env.production`
- **Security**: Maximum (hardened containers, secrets, resource limits)
- **Access**: `https://your-domain.com` (SSL required)

## 🛠️ Available Commands

### Deployment Commands
```bash
# Deploy environment
./deploy.sh --env <environment> --action deploy

# Deploy without rebuilding containers
./deploy.sh --env <environment> --action deploy --skip-build
```

### Management Commands
```bash
# Start services
./deploy.sh --env <environment> --action start

# Stop services
./deploy.sh --env <environment> --action stop

# Restart services
./deploy.sh --env <environment> --action restart

# View status
./deploy.sh --env <environment> --action status

# View logs
./deploy.sh --env <environment> --action logs

# Backup database
./deploy.sh --env <environment> --action backup
```

### Quick Aliases
```bash
# Use the management script (forwards to deploy.sh)
./manage.sh --env production --action status
./manage.sh --env beta --action logs
```

## 📁 File Structure After Cleanup

```
your-app/
├── deploy.sh                      # 🔥 Unified deployment script (Linux/Mac)
├── deploy.bat                     # 🔥 Unified deployment script (Windows)  
├── manage.sh                      # Quick alias to deploy.sh
├── docker-compose.yml             # Development configuration
├── docker-compose.production.yml  # Beta + Production configuration
├── .env.development              # Development environment
├── .env.beta.example            # Beta environment template
├── .env.production.example      # Production environment template
├── frontend/
│   ├── Dockerfile               # Development build
│   └── Dockerfile.prod         # Production build
├── backend/
├── nginx/
│   └── nginx.conf              # Production nginx config
└── README_DEPLOYMENT.md        # This file
```

### 🗑️ Removed Redundant Files:
- ❌ `docker-compose.beta.yml` → Use production with beta env
- ❌ `deploy-beta.sh` → Use unified `deploy.sh --env beta`
- ❌ `deploy-beta.bat` → Use unified `deploy.bat --env beta`
- ❌ `manage-beta.sh` → Use `deploy.sh --action <action>`
- ❌ `quick-start.sh/.bat` → Use `deploy.sh --env development`
- ❌ `start.bat` → Use `deploy.sh --env development`
- ❌ `README_BETA_DEPLOYMENT.md` → Consolidated into this file

## 🔧 Environment Setup

### Development (Auto-configured)
```bash
./deploy.sh --env development
# Uses default development credentials
```

### Beta/Production (First Time)
```bash
# 1. Deploy with auto-generated secrets
./deploy.sh --env beta

# 2. Edit environment file if needed
nano .env.beta

# 3. Redeploy if changes made
./deploy.sh --env beta --action restart
```

### Manual Environment Setup
```bash
# Copy template
cp .env.beta.example .env.beta

# Edit configuration
nano .env.beta

# Deploy
./deploy.sh --env beta
```

## 🌐 Hosting & Deployment

### 1. **Development (Local)**
```bash
./deploy.sh --env development
# Access: http://localhost:3000
```

### 2. **Beta/Production (Cloud)**

#### Digital Ocean Droplet:
```bash
# 1. Create Ubuntu 20.04+ droplet
# 2. SSH to server
ssh root@your-server-ip

# 3. Clone repository
git clone your-repo
cd your-repo

# 4. Deploy
./deploy.sh --env beta
# or
./deploy.sh --env production
```

#### AWS EC2:
```bash
# 1. Launch Ubuntu instance (t3.medium+)
# 2. SSH to instance
ssh -i your-key.pem ubuntu@ec2-instance

# 3. Install git and clone
sudo apt update && sudo apt install -y git
git clone your-repo
cd your-repo

# 4. Deploy
./deploy.sh --env production
```

## 🔐 Security Features by Environment

| Feature | Development | Beta | Production |
|---------|-------------|------|------------|
| Container Hardening | ❌ | ⚠️ Basic | ✅ Full |
| Secrets Management | ❌ | ⚠️ Basic | ✅ Docker Secrets |
| Resource Limits | ❌ | ❌ | ✅ CPU/Memory |
| Network Segmentation | ❌ | ❌ | ✅ Isolated |
| SSL/TLS | ❌ | Optional | ✅ Required |
| Security Monitoring | ❌ | ⚠️ Basic | ✅ Full |
| Rate Limiting | ❌ | ✅ | ✅ |
| Input Validation | ✅ | ✅ | ✅ |

## 📊 Monitoring & Health Checks

### Built-in Health Checks
```bash
# Check all services
./deploy.sh --env production --action status

# View logs
./deploy.sh --env production --action logs

# Health check endpoints
curl http://localhost/health          # Frontend health
curl http://localhost/api/health      # Backend health
```

### Service Status
- **Postgres**: Database connectivity
- **Redis**: Cache connectivity  
- **Backend**: API responsiveness
- **Frontend**: Web application availability
- **Nginx**: Reverse proxy status

## 🔧 Troubleshooting

### Common Issues

#### Services won't start:
```bash
# Check logs
./deploy.sh --env <env> --action logs

# Check status
./deploy.sh --env <env> --action status

# Restart services
./deploy.sh --env <env> --action restart
```

#### Environment file errors:
```bash
# Regenerate from template
cp .env.<env>.example .env.<env>
./deploy.sh --env <env> --skip-secrets
```

#### Port conflicts:
```bash
# Stop all containers
docker stop $(docker ps -q)

# Remove containers
docker container prune -f

# Redeploy
./deploy.sh --env <env>
```

#### Database issues:
```bash
# Reset database
docker volume rm formalization_postgres_data
./deploy.sh --env <env>
```

## 💾 Backup & Recovery

### Automated Backups
```bash
# Create backup
./deploy.sh --env production --action backup

# Schedule daily backups (Linux)
echo "0 2 * * * /path/to/deploy.sh --env production --action backup" | crontab -
```

### Manual Recovery
```bash
# Restore from backup
docker-compose -f docker-compose.production.yml exec -T postgres psql -U app_user -d resume_screening < backup_file.sql
```

## 🎉 Success!

Your unified deployment system provides:

✅ **Single deployment script** for all environments  
✅ **Consistent configuration** across dev/beta/production  
✅ **Automatic secret generation** for security  
✅ **Environment-specific optimizations**  
✅ **Easy management commands**  
✅ **Reduced code duplication**  
✅ **Clear environment separation**

### Next Steps:
1. 🔧 **Deploy development**: `./deploy.sh --env development`
2. 🧪 **Test beta deployment**: `./deploy.sh --env beta`
3. 🚀 **Deploy production**: `./deploy.sh --env production`
4. 📊 **Monitor services**: `./deploy.sh --env <env> --action status`
5. 💾 **Setup backups**: `./deploy.sh --env production --action backup`

**Your deployment system is now clean, unified, and production-ready!** 🚀
