# Complete Production Deployment Guide
# Resume Screening Application with Enhanced Security

## Overview

This guide provides comprehensive instructions for deploying the Resume Screening Application in a production environment with enterprise-grade security, monitoring, and backup capabilities.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04 LTS or CentOS 8+ (recommended)
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **Storage**: Minimum 50GB SSD (100GB+ recommended)
- **CPU**: 2+ cores (4+ cores recommended)
- **Network**: Static IP address with domain name

### Software Dependencies
- Docker Engine 20.10+
- Docker Compose 2.0+
- OpenSSL
- curl
- jq
- Git

## Security Architecture

### 1. Network Security
- **Multi-layer network isolation** with separate backend, frontend, and monitoring networks
- **Rate limiting** with different limits for users, admins, and endpoints
- **SSL/TLS termination** with modern cipher suites
- **DDoS protection** through NGINX rate limiting and connection limits

### 2. Application Security
- **Role-based access control** (Trial, Full, Admin users)
- **JWT-based authentication** with secure session management
- **Input validation and sanitization** on all endpoints
- **SQL injection protection** through parameterized queries
- **File upload restrictions** with type and size validation
- **Audit logging** for all security-relevant events

### 3. Infrastructure Security
- **Container security** with non-root users and read-only file systems
- **Secret management** using Docker secrets
- **Resource limiting** to prevent DoS attacks
- **Security monitoring** with Falco
- **Automated backups** with retention policies

## Deployment Process

### Step 1: Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd resume-screening-app
   ```

2. **Make deployment script executable**:
   ```bash
   chmod +x deploy-production.sh
   ```

3. **Run initial setup**:
   ```bash
   ./deploy-production.sh setup yourdomain.com admin@yourdomain.com
   ```

### Step 2: SSL Certificate Configuration

For production deployment, you need valid SSL certificates:

1. **Using Let's Encrypt (Recommended)**:
   ```bash
   # Install Certbot
   sudo apt-get update
   sudo apt-get install certbot python3-certbot-nginx
   
   # Obtain certificate
   sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
   
   # Copy certificates to nginx directory
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/certificate.crt
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/private.key
   ```

2. **Using custom certificates**:
   - Place your certificate in `nginx/ssl/certificate.crt`
   - Place your private key in `nginx/ssl/private.key`

3. **Generate DH parameters**:
   ```bash
   openssl dhparam -out nginx/ssl/dhparam.pem 2048
   ```

### Step 3: Environment Configuration

1. **Edit `.env.production`** with your specific settings:
   ```bash
   nano .env.production
   ```

2. **Key configuration items**:
   - `APP_DOMAIN`: Your domain name
   - `ADMIN_EMAIL`: Admin user email
   - `POSTGRES_DB`: Database name
   - Rate limiting settings
   - Backup retention settings

### Step 4: Build and Deploy

1. **Build the application**:
   ```bash
   ./deploy-production.sh build
   ```

2. **Deploy the application**:
   ```bash
   ./deploy-production.sh deploy
   ```

3. **Check deployment status**:
   ```bash
   ./deploy-production.sh status
   ```

## Configuration Files

### Docker Compose Configuration
The `docker-compose.production-secure.yml` includes:

- **PostgreSQL** with security hardening
- **Redis** for caching and rate limiting
- **Application container** with security restrictions
- **NGINX** reverse proxy with SSL
- **Security monitoring** with Falco
- **Log management** with Promtail
- **Automated backups**
- **Health checks** for all services

### NGINX Configuration
The enhanced `nginx/nginx.conf` provides:

- **SSL/TLS termination** with modern security
- **Rate limiting** by endpoint type
- **Security headers** (HSTS, CSP, etc.)
- **Attack pattern blocking**
- **Admin path protection**
- **Static file optimization**

### Security Middleware
The application includes comprehensive security middleware:

- **Rate limiting** (60 req/min for users, 120 req/min for admins)
- **Trial validation** to prevent system bypass
- **Admin security checks** for sensitive operations
- **Audit logging** for security events
- **Input sanitization** and validation

## Monitoring and Maintenance

### Health Checks
The application provides multiple health check endpoints:

- **Application health**: `https://yourdomain.com/health`
- **NGINX health**: Internal monitoring
- **Database health**: Automatic container health checks
- **Redis health**: Connection and authentication checks

### Backup Strategy

1. **Automated daily backups** of the database
2. **File system backups** of uploads and processed files
3. **Configuration backups** of environment settings
4. **30-day retention policy** with automatic cleanup

### Log Management

Logs are collected and stored in:
- Application logs: `/var/log/resume-app/`
- NGINX logs: `nginx/logs/`
- Security logs: `logs/falco/`
- Audit logs: Application-generated security events

### Monitoring Commands

```bash
# Check application status
./deploy-production.sh status

# View application logs
./deploy-production.sh logs

# Create backup
./deploy-production.sh backup

# Restart services
./deploy-production.sh restart

# Stop application
./deploy-production.sh stop
```

## Security Best Practices

### 1. Regular Updates
- **Monthly security patches** for the operating system
- **Quarterly application updates** with security reviews
- **Certificate renewal** (automated with Let's Encrypt)

### 2. Access Control
- **Strong admin passwords** with regular rotation
- **Limited SSH access** with key-based authentication
- **Firewall configuration** allowing only necessary ports
- **VPN access** for administrative tasks

### 3. Monitoring
- **Daily log reviews** for security events
- **Weekly backup verification**
- **Monthly security scans**
- **Quarterly penetration testing**

### 4. Incident Response
- **Documented procedures** for security incidents
- **Contact information** for security team
- **Backup recovery procedures**
- **Emergency shutdown procedures**

## Troubleshooting

### Common Issues

1. **SSL Certificate Problems**:
   - Verify certificate files exist and have correct permissions
   - Check certificate validity with `openssl x509 -in certificate.crt -text -noout`
   - Ensure DH parameters are generated

2. **Database Connection Issues**:
   - Check PostgreSQL container logs
   - Verify database credentials in secrets
   - Ensure network connectivity between containers

3. **High Resource Usage**:
   - Monitor container resource consumption
   - Check for memory leaks in application logs
   - Verify rate limiting is working correctly

4. **Authentication Failures**:
   - Check JWT secret configuration
   - Verify user database integrity
   - Review authentication middleware logs

### Emergency Procedures

1. **Immediate shutdown**:
   ```bash
   ./deploy-production.sh stop
   ```

2. **Emergency backup**:
   ```bash
   ./deploy-production.sh backup
   ```

3. **Restore from backup**:
   ```bash
   # Restore database
   docker-compose -f docker-compose.production-secure.yml exec postgres \
     psql -U app_user -d resume_screening < backup_file.sql
   ```

## Cost Optimization

### Cloud Provider Recommendations

1. **AWS**: Use t3.medium instances with EBS storage
2. **Google Cloud**: Use e2-medium instances with persistent disks
3. **DigitalOcean**: Use 4GB droplets with block storage
4. **Azure**: Use B2s instances with managed disks

### Cost-Saving Tips

- **Use spot instances** for development environments
- **Implement auto-scaling** based on usage patterns
- **Optimize Docker images** to reduce bandwidth costs
- **Use CDN** for static assets in high-traffic scenarios

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Review security logs
   - Check backup integrity
   - Monitor resource usage

2. **Monthly**:
   - Update system packages
   - Review user access logs
   - Performance optimization

3. **Quarterly**:
   - Security assessment
   - Backup restoration test
   - Disaster recovery drill

### Contact Information

For technical support and security incidents:
- **Email**: support@yourdomain.com
- **Emergency**: +1-XXX-XXX-XXXX
- **Documentation**: https://docs.yourdomain.com

---

This deployment guide provides enterprise-grade security and monitoring for your Resume Screening Application. Follow all security recommendations for production use.
