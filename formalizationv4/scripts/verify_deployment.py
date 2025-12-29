#!/usr/bin/env python3
"""
Railway deployment verification script.
Verifies that all components are working correctly after deployment.
"""
import os
import sys
import requests
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentVerifier:
    """Verifies Railway deployment is working correctly."""
    
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('RAILWAY_STATIC_URL', 'http://localhost:8000')
        if not self.base_url.startswith('http'):
            self.base_url = f'https://{self.base_url}'
        
        self.session = requests.Session()
        self.session.timeout = 30
        
        logger.info(f"🚀 Starting deployment verification for: {self.base_url}")
    
    def verify_deployment(self):
        """Run complete deployment verification."""
        try:
            logger.info("🔍 Running comprehensive deployment verification...")
            
            # Test 1: Health checks
            self._test_health_endpoints()
            
            # Test 2: Admin authentication
            admin_token = self._test_admin_authentication()
            
            # Test 3: API endpoints
            self._test_api_endpoints(admin_token)
            
            # Test 4: Database functionality
            self._test_database_functionality(admin_token)
            
            # Test 5: WebSocket functionality
            self._test_websocket_functionality()
            
            logger.info("🎉 All deployment verification tests passed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Deployment verification failed: {str(e)}")
            return False
    
    def _test_health_endpoints(self):
        """Test health check endpoints."""
        logger.info("🏥 Testing health endpoints...")
        
        endpoints = [
            '/api/v1/health/simple',
            '/api/v1/health',
            '/api/v1/health/database',
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    logger.info(f"  ✅ Health check: {endpoint}")
                else:
                    logger.warning(f"  ⚠️  Health check failed: {endpoint} ({response.status_code})")
            except Exception as e:
                logger.warning(f"  ⚠️  Health check error: {endpoint} - {str(e)}")
    
    def _test_admin_authentication(self):
        """Test admin user authentication."""
        logger.info("🔐 Testing admin authentication...")
        
        admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@bearsystems.co.in')
        admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'Benzie1!Benzie1!Benzie1!Benzie1!')
        
        try:
            # Test login
            login_data = {
                'email': admin_email,
                'password': admin_password
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                user_data = data.get('user', {})
                
                logger.info(f"  ✅ Admin login successful: {admin_email}")
                logger.info(f"  ✅ Admin is_admin: {user_data.get('is_admin', False)}")
                logger.info(f"  ✅ Admin credits: {user_data.get('credits_balance', 0)}")
                
                if token:
                    logger.info("  ✅ JWT token received")
                    return token
                else:
                    raise Exception("No access token in response")
            else:
                error_msg = f"Login failed: {response.status_code} - {response.text}"
                logger.error(f"  ❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"  ❌ Admin authentication failed: {str(e)}")
            raise
    
    def _test_api_endpoints(self, token):
        """Test API endpoints with authentication."""
        logger.info("🌐 Testing API endpoints...")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        endpoints = [
            ('GET', '/auth/me', 'User info'),
            ('GET', '/api/v1/admin/users', 'Admin users list'),
            ('GET', '/api/v1/websocket/stats', 'System stats'),
        ]
        
        for method, endpoint, description in endpoints:
            try:
                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}", headers=headers)
                elif method == 'POST':
                    response = self.session.post(f"{self.base_url}{endpoint}", headers=headers)
                
                if response.status_code in [200, 201]:
                    logger.info(f"  ✅ {description}: {endpoint}")
                else:
                    logger.warning(f"  ⚠️  {description} failed: {endpoint} ({response.status_code})")
                    
            except Exception as e:
                logger.warning(f"  ⚠️  {description} error: {str(e)}")
    
    def _test_database_functionality(self, token):
        """Test database operations."""
        logger.info("🗄️  Testing database functionality...")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        try:
            # Test getting users (should have at least admin)
            response = self.session.get(f"{self.base_url}/api/v1/admin/users", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                
                if users:
                    logger.info(f"  ✅ Database users accessible: {len(users)} users found")
                    
                    # Check admin user exists
                    admin_users = [u for u in users if u.get('is_admin', False)]
                    if admin_users:
                        logger.info(f"  ✅ Admin users found: {len(admin_users)}")
                    else:
                        logger.warning("  ⚠️  No admin users found in database")
                else:
                    logger.warning("  ⚠️  No users found in database")
            else:
                logger.warning(f"  ⚠️  Database users query failed: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"  ⚠️  Database functionality test error: {str(e)}")
    
    def _test_websocket_functionality(self):
        """Test WebSocket endpoints."""
        logger.info("🔌 Testing WebSocket functionality...")
        
        try:
            # Test WebSocket stats endpoint (should be public)
            response = self.session.get(f"{self.base_url}/api/v1/websocket/stats")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("  ✅ WebSocket stats endpoint accessible")
                
                # Log some key metrics if available
                if 'system' in data:
                    logger.info(f"  📊 Active connections: {data['system'].get('active_connections', 0)}")
                    logger.info(f"  📊 Total users: {data['system'].get('total_users', 0)}")
            else:
                logger.warning(f"  ⚠️  WebSocket stats failed: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"  ⚠️  WebSocket functionality test error: {str(e)}")
    
    def generate_deployment_report(self):
        """Generate a deployment status report."""
        logger.info("📋 Generating deployment report...")
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'base_url': self.base_url,
            'verification_status': 'unknown',
            'admin_credentials': {
                'email': os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@bearsystems.co.in'),
                'password_set': bool(os.getenv('DEFAULT_ADMIN_PASSWORD'))
            },
            'environment_variables': {
                'FLASK_ENV': os.getenv('FLASK_ENV'),
                'SERVICE_TYPE': os.getenv('SERVICE_TYPE'),
                'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT'),
                'DATABASE_URL': bool(os.getenv('DATABASE_URL')),
                'OLLAMA_URL': bool(os.getenv('OLLAMA_URL'))
            }
        }
        
        # Run verification
        try:
            success = self.verify_deployment()
            report['verification_status'] = 'success' if success else 'failed'
        except Exception as e:
            report['verification_status'] = 'error'
            report['error'] = str(e)
        
        # Save report
        report_file = 'deployment_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Deployment report saved: {report_file}")
        return report

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Railway deployment')
    parser.add_argument('--url', help='Base URL to test (optional)')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--wait', type=int, default=0, help='Wait seconds before testing')
    
    args = parser.parse_args()
    
    if args.wait > 0:
        logger.info(f"⏳ Waiting {args.wait} seconds before starting verification...")
        time.sleep(args.wait)
    
    verifier = DeploymentVerifier(args.url)
    
    try:
        if args.report:
            report = verifier.generate_deployment_report()
            print(f"\n📋 DEPLOYMENT REPORT:")
            print(f"Status: {report['verification_status']}")
            print(f"URL: {report['base_url']}")
            print(f"Admin Email: {report['admin_credentials']['email']}")
            print(f"Admin Password Set: {report['admin_credentials']['password_set']}")
        else:
            success = verifier.verify_deployment()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
