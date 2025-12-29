"""
Refactoring Validation Script
Tests that the refactored modular architecture works correctly
"""

import sys
import os
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all refactored components can be imported"""
    results = {}
    
    # Test core components
    try:
        from app_factory import create_app
        results['app_factory'] = '✅ Success'
        logger.info("✅ App factory imported successfully")
    except Exception as e:
        results['app_factory'] = f'❌ Failed: {e}'
        logger.error(f"❌ App factory import failed: {e}")
    
    try:
        from core.initializers import ComponentInitializer, MiddlewareInitializer, RoutesInitializer
        results['core_initializers'] = '✅ Success'
        logger.info("✅ Core initializers imported successfully")
    except Exception as e:
        results['core_initializers'] = f'❌ Failed: {e}'
        logger.error(f"❌ Core initializers import failed: {e}")
    
    try:
        from core.health_manager import HealthManager
        results['health_manager'] = '✅ Success'
        logger.info("✅ Health manager imported successfully")
    except Exception as e:
        results['health_manager'] = f'❌ Failed: {e}'
        logger.error(f"❌ Health manager import failed: {e}")
    
    try:
        from services.business_logic import ResumeProcessingService, LegalQueryService, AdminService
        results['business_logic'] = '✅ Success'
        logger.info("✅ Business logic services imported successfully")
    except Exception as e:
        results['business_logic'] = f'❌ Failed: {e}'
        logger.error(f"❌ Business logic import failed: {e}")
    
    try:
        from services.cache_manager import CacheManager
        results['cache_manager'] = '✅ Success'
        logger.info("✅ Cache manager imported successfully")
    except Exception as e:
        results['cache_manager'] = f'❌ Failed: {e}'
        logger.error(f"❌ Cache manager import failed: {e}")
    
    return results

def test_route_imports():
    """Test that route modules can be imported"""
    route_modules = [
        'routes.auth',
        'routes.admin', 
        'routes.user',
        'routes.hr_legal',
        'routes.monitoring',
        'routes.credits',
        'routes.payments',
        'routes.analytics_routes',
        'routes.backup_management',
        'routes.websocket',
        'routes.bulk',
        'routes.search',
        'routes.performance',
        'routes.ollama_test',
        'routes.health_routes'
    ]
    
    results = {}
    
    for module in route_modules:
        try:
            __import__(module)
            results[module] = '✅ Success'
            logger.info(f"✅ {module} imported successfully")
        except Exception as e:
            results[module] = f'❌ Failed: {e}'
            logger.error(f"❌ {module} import failed: {e}")
    
    return results

def test_app_creation():
    """Test that the refactored app can be created"""
    try:
        from app_factory import create_app
        
        # Try to create the app in test mode
        app = create_app()
        
        if app:
            logger.info("✅ Application created successfully")
            
            # Test that routes are registered
            rules = [str(rule) for rule in app.url_map.iter_rules()]
            
            logger.info(f"📊 Total routes registered: {len(rules)}")
            
            # Check for key routes
            key_routes = ['/api/health', '/api/auth/', '/api/admin/', '/api/user/']
            found_routes = []
            
            for route in key_routes:
                if any(route in rule for rule in rules):
                    found_routes.append(route)
            
            logger.info(f"✅ Key routes found: {found_routes}")
            
            return {
                'app_creation': '✅ Success',
                'total_routes': len(rules),
                'key_routes_found': len(found_routes),
                'app_object': app
            }
        else:
            return {'app_creation': '❌ Failed: No app returned'}
            
    except Exception as e:
        logger.error(f"❌ App creation failed: {e}")
        return {'app_creation': f'❌ Failed: {e}'}

def main():
    """Run all validation tests"""
    logger.info("🚀 Starting Refactoring Validation")
    logger.info("=" * 60)
    
    # Test imports
    logger.info("📦 Testing Core Component Imports...")
    import_results = test_imports()
    
    logger.info("📦 Testing Route Module Imports...")
    route_results = test_route_imports()
    
    # Test app creation
    logger.info("🏗️ Testing Application Creation...")
    app_results = test_app_creation()
    
    # Summary
    logger.info("=" * 60)
    logger.info("📋 VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    print("\n🏗️ CORE COMPONENTS:")
    for component, result in import_results.items():
        print(f"  {component}: {result}")
    
    print("\n🛣️ ROUTE MODULES:")
    successful_routes = 0
    total_routes = len(route_results)
    
    for route, result in route_results.items():
        print(f"  {route}: {result}")
        if '✅' in result:
            successful_routes += 1
    
    print(f"\n📊 ROUTE IMPORT SUCCESS RATE: {successful_routes}/{total_routes} ({successful_routes/total_routes*100:.1f}%)")
    
    print("\n🏭 APPLICATION CREATION:")
    for test, result in app_results.items():
        if test != 'app_object':
            print(f"  {test}: {result}")
    
    # Calculate overall success
    core_success = sum(1 for r in import_results.values() if '✅' in r)
    total_core = len(import_results)
    
    overall_success_rate = (core_success + successful_routes) / (total_core + total_routes) * 100
    
    print(f"\n🎉 OVERALL SUCCESS RATE: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 80:
        print("✅ REFACTORING VALIDATION: PASSED")
        logger.info("✅ Refactoring validation completed successfully!")
    else:
        print("❌ REFACTORING VALIDATION: NEEDS WORK")
        logger.warning("❌ Refactoring validation shows issues that need to be addressed")
    
    return overall_success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
