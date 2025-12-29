"""
Service Implementations for Startup Package
Individual service handlers for different components
"""

import os
import sys
import time
import logging
import asyncio
import subprocess
import requests
import psycopg2
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor, as_completed

if TYPE_CHECKING:
    from .config import ServiceConfig

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """Base class for all startup services"""
    
    def __init__(self, name: str, config: 'ServiceConfig'):
        self.name = name
        self.config = config
        self.is_running = False
        self.health_status = False
        self.start_time: Optional[float] = None
        self.error_message: Optional[str] = None
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the service"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the service"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'name': self.name,
            'is_running': self.is_running,
            'health_status': self.health_status,
            'start_time': self.start_time,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'error_message': self.error_message
        }

class DatabaseService(BaseService):
    """Database initialization and migration service"""
    
    def __init__(self, config: 'ServiceConfig'):
        super().__init__('database', config)
        self.database_url = os.getenv('DATABASE_URL')
        self.migration_status = {}
    
    async def start(self) -> bool:
        """Initialize database and run migrations"""
        try:
            self.start_time = time.time()
            logger.info("🗄️ Starting database service...")
            
            if not self.database_url:
                raise ValueError("DATABASE_URL not found")
            
            # Run enhanced schema migration
            success = await self._run_enhanced_migration()
            
            if success:
                # Initialize Supabase if available
                await self._initialize_supabase()
                
                self.is_running = True
                self.health_status = True
                logger.info("✅ Database service started successfully")
                return True
            else:
                raise Exception("Database migration failed")
                
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"❌ Database service failed to start: {e}")
            return False
    
    async def _run_enhanced_migration(self) -> bool:
        """Run database schema validation and basic setup"""
        try:
            # Use existing railway_database for basic connectivity test
            from railway_database import RailwayPostgreSQL
            
            # Test database connection and basic setup
            railway_db = RailwayPostgreSQL(self.database_url)
            
            # Test connection
            with railway_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            
            logger.info("✅ Database connection successful")
            self.migration_status = {'success': True, 'method': 'connection_test'}
            return True
            
        except Exception as e:
            logger.warning(f"Database connection test failed: {e}")
            # Try fallback migration
            return await self._run_fallback_migration()
    
    async def _run_fallback_migration(self) -> bool:
        """Run basic database setup using app's database initialization"""
        try:
            # Use app's existing database initialization
            from app import initialize_database
            
            success = initialize_database()
            self.migration_status = {'fallback': True, 'success': success, 'method': 'app_init'}
            return success
            
        except Exception as e:
            logger.error(f"Fallback migration failed: {e}")
            return False
    
    async def _initialize_supabase(self):
        """Initialize Supabase synchronization if available"""
        try:
            if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_KEY'):
                from utils.supabase_initializer import SupabaseInitializer
                
                supabase_init = SupabaseInitializer()
                results = supabase_init.run_comprehensive_initialization()
                
                logger.info(f"Supabase sync: {'✅' if results.get('success') else '⚠️'}")
                
        except Exception as e:
            logger.warning(f"Supabase initialization failed: {e}")
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            self.health_status = True
            return True
            
        except Exception as e:
            self.health_status = False
            self.error_message = f"Health check failed: {e}"
            return False
    
    async def stop(self) -> bool:
        """Stop database service"""
        self.is_running = False
        self.health_status = False
        return True

class OllamaService(BaseService):
    """Ollama AI service manager"""
    
    def __init__(self, config: 'ServiceConfig'):
        super().__init__('ollama', config)
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.preferred_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
        self.fallback_model = os.getenv('OLLAMA_FALLBACK_MODEL', 'qwen2.5:3b')
        self.process = None
    
    async def start(self) -> bool:
        """Start Ollama service and ensure models are available"""
        try:
            self.start_time = time.time()
            logger.info("🤖 Starting Ollama service...")
            
            # Check if Ollama is already running
            if await self._check_ollama_running():
                logger.info("✅ Ollama already running")
                self.is_running = True
                await self._ensure_models()
                return True
            
            # Start Ollama server
            success = await self._start_ollama_server()
            if success:
                # Ensure models are available
                await self._ensure_models()
                self.is_running = True
                self.health_status = True
                logger.info("✅ Ollama service started successfully")
                return True
            else:
                raise Exception("Failed to start Ollama server")
                
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"❌ Ollama service failed to start: {e}")
            # Set environment variable to indicate Ollama is unavailable
            os.environ['OLLAMA_AVAILABLE'] = 'false'
            return False
    
    async def _check_ollama_running(self) -> bool:
        """Check if Ollama is already running"""
        try:
            response = requests.get(f'{self.ollama_url}/api/version', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def _start_ollama_server(self) -> bool:
        """Start Ollama server process"""
        try:
            self.process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Wait for server to start
            for attempt in range(30):
                await asyncio.sleep(2)
                if await self._check_ollama_running():
                    logger.info("✅ Ollama server started and responding")
                    return True
            
            logger.error("❌ Ollama server failed to respond after 60 seconds")
            return False
            
        except FileNotFoundError:
            logger.error("❌ Ollama not found in PATH")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to start Ollama server: {e}")
            return False
    
    async def _ensure_models(self):
        """Ensure required models are available"""
        try:
            # Check existing models
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if self.preferred_model in result.stdout:
                logger.info(f"✅ {self.preferred_model} already available")
                os.environ['OLLAMA_MODEL'] = self.preferred_model
                return
            elif self.fallback_model in result.stdout:
                logger.info(f"✅ {self.fallback_model} already available")
                os.environ['OLLAMA_MODEL'] = self.fallback_model
                return
            
            # Pull preferred model in background
            logger.info(f"📥 Pulling {self.preferred_model} in background...")
            subprocess.Popen(
                ['ollama', 'pull', self.preferred_model],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Set environment variable
            os.environ['OLLAMA_MODEL'] = self.preferred_model
            os.environ['OLLAMA_AVAILABLE'] = 'true'
            
        except Exception as e:
            logger.warning(f"Model setup failed: {e}")
    
    async def health_check(self) -> bool:
        """Check Ollama service health"""
        try:
            response = requests.get(f'{self.ollama_url}/api/version', timeout=10)
            self.health_status = response.status_code == 200
            return self.health_status
        except Exception as e:
            self.health_status = False
            self.error_message = f"Health check failed: {e}"
            return False
    
    async def stop(self) -> bool:
        """Stop Ollama service"""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)
            
            self.is_running = False
            self.health_status = False
            return True
            
        except Exception as e:
            logger.error(f"Error stopping Ollama: {e}")
            return False

class AIProcessorService(BaseService):
    """AI response processing service"""
    
    def __init__(self, config: 'ServiceConfig'):
        super().__init__('ai_processor', config)
    
    async def start(self) -> bool:
        """Initialize AI response processor"""
        try:
            self.start_time = time.time()
            logger.info("🧠 Starting AI processor service...")
            
            from utils.ai_response_processor import response_processor
            
            # Test processor initialization
            test_result = response_processor.validate_processed_data({
                'id': 'test',
                'user_id': 'test',
                'overall_score': 75,
                'skills': '[]',
                'analysis_results': '{}'
            })
            
            if test_result:
                self.is_running = True
                self.health_status = True
                logger.info("✅ AI processor service started successfully")
                return True
            else:
                raise Exception("AI processor validation failed")
                
        except Exception as e:
            self.error_message = str(e)
            logger.warning(f"⚠️ AI processor service failed to start: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check AI processor health"""
        try:
            # Simple health check
            self.health_status = self.is_running
            return self.health_status
        except Exception as e:
            self.health_status = False
            self.error_message = f"Health check failed: {e}"
            return False
    
    async def stop(self) -> bool:
        """Stop AI processor service"""
        self.is_running = False
        self.health_status = False
        return True

class HealthCheckService(BaseService):
    """System health monitoring service"""
    
    def __init__(self, config: 'ServiceConfig'):
        super().__init__('health_monitor', config)
        self.monitored_services = []
    
    def set_monitored_services(self, services: List[BaseService]):
        """Set services to monitor"""
        self.monitored_services = services
    
    async def start(self) -> bool:
        """Start health monitoring service"""
        try:
            self.start_time = time.time()
            logger.info("💚 Starting health monitoring service...")
            
            self.is_running = True
            self.health_status = True
            logger.info("✅ Health monitoring service started successfully")
            return True
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"❌ Health monitoring service failed to start: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check overall system health"""
        try:
            healthy_services = 0
            total_services = len(self.monitored_services)
            
            for service in self.monitored_services:
                if await service.health_check():
                    healthy_services += 1
            
            # System is healthy if at least critical services are running
            self.health_status = healthy_services >= (total_services * 0.7)  # 70% threshold
            return self.health_status
            
        except Exception as e:
            self.health_status = False
            self.error_message = f"Health check failed: {e}"
            return False
    
    async def stop(self) -> bool:
        """Stop health monitoring service"""
        self.is_running = False
        self.health_status = False
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        service_statuses = [service.get_status() for service in self.monitored_services]
        
        return {
            'overall_health': self.health_status,
            'services': service_statuses,
            'monitoring_since': self.start_time,
            'last_check': time.time()
        }
