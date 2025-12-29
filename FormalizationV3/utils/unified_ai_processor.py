#!/usr/bin/env python3
"""
Unified AI Processing System with Admin-Configurable Models
Supports OpenAI, Anthropic, and Ollama with per-user configuration
"""

import logging
import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import os

# AI Provider imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import requests
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Supported AI providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

@dataclass
class AIProviderConfig:
    """Configuration for AI providers"""
    provider: AIProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 120
    enabled: bool = True

@dataclass
class AIProcessingResult:
    """Result from AI processing"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider_used: Optional[AIProvider] = None
    model_used: Optional[str] = None
    processing_time: float = 0.0
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None

class UnifiedAIProcessor:
    """
    Unified AI processing system with admin-configurable per-user models
    Supports intelligent fallback chains and provider health monitoring
    """
    
    def __init__(self, railway_db=None, cache_manager=None):
        self.railway_db = railway_db
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        
        # Provider configurations
        self.providers = {}
        self.user_provider_cache = {}
        self.provider_health = {}
        
        # Initialize providers
        self._initialize_providers()
        
        # Health check intervals
        self.last_health_check = {}
        self.health_check_interval = 300  # 5 minutes
        
        self.logger.info("✅ Unified AI Processor initialized with admin-configurable models")
    
    def _initialize_providers(self):
        """Initialize all available AI providers with Ollama as guaranteed fallback"""
        
        # OpenAI (highest priority if available)
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            self.providers[AIProvider.OPENAI] = AIProviderConfig(
                provider=AIProvider.OPENAI,
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                api_key=os.getenv('OPENAI_API_KEY'),
                max_tokens=4000,
                temperature=0.7
            )
            self.logger.info("✅ OpenAI provider initialized (Priority 1)")
        
        # Anthropic (second priority if available)
        if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY'):
            self.providers[AIProvider.ANTHROPIC] = AIProviderConfig(
                provider=AIProvider.ANTHROPIC,
                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                max_tokens=4000,
                temperature=0.7
            )
            self.logger.info("✅ Anthropic provider initialized (Priority 2)")
        
        # Ollama (REQUIRED - guaranteed fallback for 32GB/32CPU setup)
        ollama_available = self._check_ollama_availability()
        if ollama_available:
            # Use qwen2.5:7b for better performance and reduced memory usage
            ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
            self.providers[AIProvider.OLLAMA] = AIProviderConfig(
                provider=AIProvider.OLLAMA,
                model=ollama_model,
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                timeout=180,  # Longer timeout for larger models
                max_tokens=8192  # Larger context for qwen2.5
            )
            self.logger.info(f"✅ Ollama provider initialized with {ollama_model} (Required Fallback)")
        else:
            self.logger.error("❌ CRITICAL: Ollama is required but not available!")
            # Try to start Ollama automatically
            if self._attempt_ollama_startup():
                ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
                self.providers[AIProvider.OLLAMA] = AIProviderConfig(
                    provider=AIProvider.OLLAMA,
                    model=ollama_model,
                    base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                    timeout=180,
                    max_tokens=8192
                )
                self.logger.info(f"✅ Ollama started automatically with {ollama_model}")
            else:
                self.logger.error("❌ FAILED to start Ollama - system will have limited AI capability")
        
        if not self.providers:
            self.logger.error("❌ CRITICAL: No AI providers available!")
            raise Exception("No AI providers configured - system cannot function")
        
        # Log provider priority order
        provider_names = [p.value for p in self.providers.keys()]
        self.logger.info(f"AI Provider priority order: {provider_names}")
        self.logger.info(f"Total providers initialized: {len(self.providers)}")
    
    def _attempt_ollama_startup(self) -> bool:
        """Attempt to start Ollama service automatically"""
        try:
            import subprocess
            import time
            
            self.logger.info("🚀 Attempting to start Ollama service...")
            
            # Start Ollama server
            process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Wait for startup
            time.sleep(5)
            
            # Check if responding
            for attempt in range(15):  # Try for 15 seconds
                if self._check_ollama_availability():
                    self.logger.info("✅ Ollama started successfully")
                    
                    # Ensure required model is available
                    self._ensure_ollama_model()
                    return True
                time.sleep(1)
                
            self.logger.error("❌ Ollama started but not responding")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Ollama: {e}")
            return False
    
    def _ensure_ollama_model(self):
        """Ensure the required Ollama model is available"""
        try:
            # Use qwen2.5:7b as default for better performance
            preferred_model = "qwen2.5:7b"
            fallback_model = "qwen2.5:3b"
            
            self.logger.info(f"🧠 Ensuring Ollama model {preferred_model} is available...")
            
            # Check if model exists using official client
            try:
                if OLLAMA_AVAILABLE:
                    # Use official Ollama client
                    models = ollama.list()
                    available_models = [model['name'] for model in models['models']]
                    
                    if preferred_model in available_models:
                        self.logger.info(f"✅ Model {preferred_model} already available")
                        os.environ['OLLAMA_MODEL'] = preferred_model
                        return
                    elif fallback_model in available_models:
                        self.logger.info(f"✅ Using fallback model {fallback_model}")
                        os.environ['OLLAMA_MODEL'] = fallback_model
                        return
                else:
                    # Fallback to subprocess
                    import subprocess
                    result = subprocess.run(
                        ['ollama', 'list'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if preferred_model in result.stdout:
                        self.logger.info(f"✅ Model {preferred_model} already available")
                        os.environ['OLLAMA_MODEL'] = preferred_model
                        return
                    elif fallback_model in result.stdout:
                        self.logger.info(f"✅ Using fallback model {fallback_model}")
                        os.environ['OLLAMA_MODEL'] = fallback_model
                        return
                    
            except Exception as list_error:
                self.logger.warning(f"Could not list Ollama models: {list_error}")
            
            # Pull preferred model
            try:
                self.logger.info(f"📥 Pulling {preferred_model} (this may take a few minutes)...")
                
                if OLLAMA_AVAILABLE:
                    # Use official client
                    ollama.pull(preferred_model)
                    self.logger.info(f"✅ Successfully pulled {preferred_model}")
                    os.environ['OLLAMA_MODEL'] = preferred_model
                    return
                else:
                    # Fallback to subprocess
                    import subprocess
                    result = subprocess.run(
                        ['ollama', 'pull', preferred_model],
                        capture_output=True,
                        text=True,
                        timeout=900  # 15 minutes timeout for model download
                    )
                    
                    if result.returncode == 0:
                        self.logger.info(f"✅ Successfully pulled {preferred_model}")
                        os.environ['OLLAMA_MODEL'] = preferred_model
                        return
                    else:
                        self.logger.warning(f"Failed to pull {preferred_model}, trying {fallback_model}")
                        
            except Exception as pull_error:
                self.logger.warning(f"Error pulling {preferred_model}: {pull_error}, trying {fallback_model}")
            
            # Try fallback model
            try:
                self.logger.info(f"📥 Pulling fallback model {fallback_model}...")
                
                if OLLAMA_AVAILABLE:
                    ollama.pull(fallback_model)
                    self.logger.info(f"✅ Successfully pulled fallback {fallback_model}")
                    os.environ['OLLAMA_MODEL'] = fallback_model
                else:
                    import subprocess
                    result = subprocess.run(
                        ['ollama', 'pull', fallback_model],
                        capture_output=True,
                        text=True,
                        timeout=600  # 10 minutes for smaller model
                    )
                    
                    if result.returncode == 0:
                        self.logger.info(f"✅ Successfully pulled fallback {fallback_model}")
                        os.environ['OLLAMA_MODEL'] = fallback_model
                    else:
                        self.logger.error(f"❌ Failed to pull any qwen2.5 models")
                        
            except Exception as fallback_error:
                self.logger.error(f"❌ Error pulling fallback model: {fallback_error}")
                
        except Exception as e:
            self.logger.error(f"❌ Error ensuring Ollama model: {e}")
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama service is available"""
        try:
            # Check environment variable first
            if os.getenv('OLLAMA_AVAILABLE', '').lower() == 'false':
                return False
                
            # Use official Ollama client for better reliability
            if OLLAMA_AVAILABLE:
                try:
                    # Try to list models to verify Ollama is working
                    ollama.list()
                    return True
                except Exception as ollama_error:
                    self.logger.warning(f"Ollama client failed: {ollama_error}")
                    
            # Fallback to HTTP check
            import requests
            response = requests.get('http://localhost:11434/api/version', timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_user_ai_provider(self, user_id: str) -> AIProvider:
        """Get the AI provider configured for a specific user"""
        try:
            # Check cache first
            if user_id in self.user_provider_cache:
                cached_entry = self.user_provider_cache[user_id]
                if cached_entry['expires'] > datetime.utcnow():
                    return cached_entry['provider']
            
            # Query database for user's AI provider setting
            if self.railway_db:
                user_settings = self.railway_db.execute_read("""
                    SELECT ai_provider, ai_model, updated_at 
                    FROM user_ai_settings 
                    WHERE user_id = %s AND enabled = true
                    ORDER BY updated_at DESC LIMIT 1
                """, (user_id,))
                
                if user_settings:
                    provider_name = user_settings[0]['ai_provider']
                    try:
                        provider = AIProvider(provider_name)
                        
                        # Cache the result for 1 hour
                        self.user_provider_cache[user_id] = {
                            'provider': provider,
                            'expires': datetime.utcnow() + timedelta(hours=1)
                        }
                        
                        self.logger.info(f"User {user_id} configured to use {provider.value}")
                        return provider
                        
                    except ValueError:
                        self.logger.warning(f"Invalid AI provider '{provider_name}' for user {user_id}")
            
            # Default provider priority: OpenAI → Anthropic → Ollama
            if AIProvider.OPENAI in self.providers:
                default_provider = AIProvider.OPENAI
                self.logger.info(f"Using OpenAI as default provider for user {user_id}")
            elif AIProvider.ANTHROPIC in self.providers:
                default_provider = AIProvider.ANTHROPIC
                self.logger.info(f"Using Anthropic as default provider for user {user_id}")
            elif AIProvider.OLLAMA in self.providers:
                default_provider = AIProvider.OLLAMA
                self.logger.info(f"Using Ollama as default provider for user {user_id}")
            else:
                self.logger.error("No AI providers available!")
                raise Exception("No AI providers configured")
            
            return default_provider
            
        except Exception as e:
            self.logger.error(f"Error getting AI provider for user {user_id}: {e}")
            # Return provider in priority order as fallback
            if AIProvider.OPENAI in self.providers:
                fallback_provider = AIProvider.OPENAI
            elif AIProvider.ANTHROPIC in self.providers:
                fallback_provider = AIProvider.ANTHROPIC
            elif AIProvider.OLLAMA in self.providers:
                fallback_provider = AIProvider.OLLAMA
            else:
                raise Exception("No AI providers available - system misconfigured")
            
            self.logger.info(f"Using fallback provider {fallback_provider.value}")
            return fallback_provider
    
    def set_user_ai_provider(self, user_id: str, provider: AIProvider, model: str = None, admin_user_id: str = None) -> bool:
        """Set AI provider for a user (admin only)"""
        try:
            if not self.railway_db:
                return False
            
            # Validate provider is available
            if provider not in self.providers:
                self.logger.error(f"Provider {provider.value} not available")
                return False
            
            # Use default model if not specified
            if not model:
                model = self.providers[provider].model
            
            # Insert/update user AI settings
            self.railway_db.execute_write("""
                INSERT INTO user_ai_settings (user_id, ai_provider, ai_model, set_by_admin, admin_user_id, created_at, updated_at, enabled)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), true)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    ai_provider = EXCLUDED.ai_provider,
                    ai_model = EXCLUDED.ai_model,
                    set_by_admin = EXCLUDED.set_by_admin,
                    admin_user_id = EXCLUDED.admin_user_id,
                    updated_at = NOW(),
                    enabled = true
            """, (user_id, provider.value, model, True, admin_user_id))
            
            # Clear cache for this user
            if user_id in self.user_provider_cache:
                del self.user_provider_cache[user_id]
            
            # Log the change
            self.logger.info(f"Admin {admin_user_id} set user {user_id} to use {provider.value} model {model}")
            
            # Record activity log
            if self.railway_db:
                self.railway_db.execute_write("""
                    INSERT INTO activity_logs (user_id, action, details, metadata, created_at)
                    VALUES (%s, 'ai_provider_changed', %s, %s, NOW())
                """, (
                    user_id,
                    json.dumps({
                        'new_provider': provider.value,
                        'new_model': model,
                        'changed_by_admin': admin_user_id
                    }),
                    json.dumps({'admin_action': True, 'ai_configuration': True})
                ))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting AI provider for user {user_id}: {e}")
            return False
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available AI providers and their status"""
        providers_info = {}
        
        for provider_enum, config in self.providers.items():
            provider_name = provider_enum.value
            
            # Check provider health
            is_healthy = self._check_provider_health(provider_enum)
            
            providers_info[provider_name] = {
                'name': provider_name,
                'model': config.model,
                'enabled': config.enabled,
                'healthy': is_healthy,
                'description': self._get_provider_description(provider_enum)
            }
        
        return providers_info
    
    def _get_provider_description(self, provider: AIProvider) -> str:
        """Get human-readable description of provider"""
        descriptions = {
            AIProvider.OLLAMA: "Open-source local model (free)",
            AIProvider.OPENAI: "OpenAI GPT models (paid)",
            AIProvider.ANTHROPIC: "Anthropic Claude models (paid)"
        }
        return descriptions.get(provider, "Unknown provider")
    
    async def process_resume(self, resume_text: str, user_id: str, analysis_type: str = "comprehensive", progress_callback=None) -> AIProcessingResult:
        """
        Process resume using the user's configured AI provider
        Falls back to alternative providers if primary fails
        """
        start_time = time.time()
        
        # Initialize progress tracking
        if progress_callback:
            progress_callback("Starting AI processing", 10)
        
        # Get user's preferred provider
        primary_provider = self.get_user_ai_provider(user_id)
        
        # Create fallback chain with proper priority: OpenAI → Anthropic → Ollama
        fallback_chain = [primary_provider]
        
        # Add providers in priority order (excluding primary if already included)
        priority_order = [AIProvider.OPENAI, AIProvider.ANTHROPIC, AIProvider.OLLAMA]
        
        for provider in priority_order:
            if provider in self.providers and provider not in fallback_chain:
                fallback_chain.append(provider)
        
        self.logger.info(f"Fallback chain for user {user_id}: {[p.value for p in fallback_chain]}")
        
        last_error = None
        
        for i, provider in enumerate(fallback_chain):
            if provider not in self.providers:
                continue
                
            try:
                # Update progress based on current provider attempt
                base_progress = 20 + (i * 20)  # Start at 20%, increment by 20% per provider
                if progress_callback:
                    progress_callback(f"Attempting {provider.value} processing", base_progress)
                
                self.logger.info(f"Processing resume for user {user_id} using {provider.value}")
                
                result = await self._process_with_provider(
                    provider, 
                    resume_text, 
                    user_id, 
                    analysis_type,
                    progress_callback
                )
                
                if result.success:
                    if progress_callback:
                        progress_callback("Processing complete", 100)
                    result.processing_time = time.time() - start_time
                    self.logger.info(f"✅ Resume processed successfully using {provider.value} in {result.processing_time:.2f}s")
                    return result
                else:
                    last_error = result.error
                    self.logger.warning(f"Provider {provider.value} failed: {result.error}")
                    
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Error with provider {provider.value}: {e}")
        
        # All providers failed
        if progress_callback:
            progress_callback("Processing failed", 0)
        processing_time = time.time() - start_time
        return AIProcessingResult(
            success=False,
            error=f"All AI providers failed. Last error: {last_error}",
            processing_time=processing_time
        )
    
    async def _process_with_provider(self, provider: AIProvider, resume_text: str, user_id: str, analysis_type: str, progress_callback=None) -> AIProcessingResult:
        """Process resume with specific provider"""
        config = self.providers[provider]
        
        if provider == AIProvider.OLLAMA:
            return await self._process_with_ollama(config, resume_text, user_id, analysis_type, progress_callback)
        elif provider == AIProvider.OPENAI:
            return await self._process_with_openai(config, resume_text, user_id, analysis_type, progress_callback)
        elif provider == AIProvider.ANTHROPIC:
            return await self._process_with_anthropic(config, resume_text, user_id, analysis_type, progress_callback)
        else:
            return AIProcessingResult(success=False, error=f"Unknown provider: {provider}")
    
    async def _process_with_ollama(self, config: AIProviderConfig, resume_text: str, user_id: str, analysis_type: str, progress_callback=None) -> AIProcessingResult:
        """Process with Ollama with enhanced timeout and error handling"""
        try:
            if progress_callback:
                progress_callback("Preparing Ollama request", 30)
                
            prompt = self._build_analysis_prompt(resume_text, analysis_type)
            
            if OLLAMA_AVAILABLE:
                # Use official Ollama client (preferred) with thread-safe timeout
                try:
                    import concurrent.futures
                    
                    if progress_callback:
                        progress_callback("Sending request to Ollama", 40)
                    
                    # Use ThreadPoolExecutor with timeout (thread-safe)
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            ollama.generate,
                            model=config.model,
                            prompt=prompt,
                            options={
                                'temperature': config.temperature,
                                'num_predict': min(config.max_tokens, 1000),  # Limit tokens for speed
                                'top_k': 20,  # Reduce for faster generation
                                'top_p': 0.8,  # Reduce randomness for efficiency
                                'repeat_penalty': 1.1,  # Prevent repetition
                                'num_thread': 4,  # Limit CPU usage
                                'num_ctx': 2048  # Reduce context window for speed
                            }
                        )
                        
                        if progress_callback:
                            progress_callback("Ollama processing (this may take several minutes)", 50)
                        
                        # Increased timeout for Railway Pro: 15 minutes instead of 2 minutes
                        response = future.result(timeout=900)  # 15 minute timeout for Railway Pro
                    
                    if progress_callback:
                        progress_callback("Processing Ollama response", 80)
                    
                    analysis = self._parse_ai_response(response['response'])
                    
                    return AIProcessingResult(
                        success=True,
                        data=analysis,
                        provider_used=AIProvider.OLLAMA,
                        model_used=config.model
                    )
                    
                except (TimeoutError, concurrent.futures.TimeoutError) as timeout_error:
                    self.logger.warning(f"Ollama client timed out: {timeout_error}, falling back to HTTP")
                except Exception as client_error:
                    self.logger.warning(f"Ollama client failed: {client_error}, falling back to HTTP")
            
            # Fallback to HTTP API with enhanced timeout handling
            payload = {
                "model": config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": min(config.max_tokens, 800),  # Limit for faster response
                    "top_k": 20,
                    "top_p": 0.8,
                    "num_thread": 4,
                    "num_ctx": 2048
                }
            }
            
            if progress_callback:
                progress_callback("Using HTTP fallback for Ollama", 45)
            
            # Make request to Ollama with Railway Pro timeout - 15 minutes
            import aiohttp
            timeout = aiohttp.ClientTimeout(
                total=900,  # 15 minute total timeout for Railway Pro
                connect=30,  # 30 second connect timeout
                sock_read=120  # 2 minute read timeout
            )
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    if progress_callback:
                        progress_callback("Connecting to Ollama server", 50)
                        
                    async with session.post(f"{config.base_url}/api/generate", json=payload) as response:
                        if progress_callback:
                            progress_callback("Receiving Ollama response", 70)
                            
                        if response.status == 200:
                            result = await response.json()
                            
                            if progress_callback:
                                progress_callback("Parsing AI response", 85)
                                
                            analysis = self._parse_ai_response(result.get('response', ''))
                            
                            return AIProcessingResult(
                                success=True,
                                data=analysis,
                                provider_used=AIProvider.OLLAMA,
                                model_used=config.model
                            )
                        else:
                            error_text = await response.text()
                            return AIProcessingResult(
                                success=False,
                                error=f"Ollama API error {response.status}: {error_text}",
                                provider_used=AIProvider.OLLAMA
                            )
                except asyncio.TimeoutError:
                    return AIProcessingResult(
                        success=False,
                        error="Ollama request timed out after 15 minutes (Railway Pro timeout)",
                        provider_used=AIProvider.OLLAMA
                    )
                except aiohttp.ClientError as client_error:
                    return AIProcessingResult(
                        success=False,
                        error=f"Ollama connection error: {str(client_error)}",
                        provider_used=AIProvider.OLLAMA
                    )
                        
        except Exception as e:
            return AIProcessingResult(
                success=False,
                error=f"Ollama processing error: {str(e)}",
                provider_used=AIProvider.OLLAMA
            )
    
    async def _process_with_openai(self, config: AIProviderConfig, resume_text: str, user_id: str, analysis_type: str, progress_callback=None) -> AIProcessingResult:
        """Process with OpenAI"""
        try:
            if progress_callback:
                progress_callback("Connecting to OpenAI", 30)
                
            client = openai.AsyncOpenAI(api_key=config.api_key)
            prompt = self._build_analysis_prompt(resume_text, analysis_type)
            
            if progress_callback:
                progress_callback("Sending request to OpenAI", 50)
            
            response = await client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": "You are an expert HR professional analyzing resumes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            if progress_callback:
                progress_callback("Processing OpenAI response", 80)
            
            analysis = self._parse_ai_response(response.choices[0].message.content)
            
            return AIProcessingResult(
                success=True,
                data=analysis,
                provider_used=AIProvider.OPENAI,
                model_used=config.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                cost_estimate=self._estimate_openai_cost(response.usage.total_tokens if response.usage else 0, config.model)
            )
            
        except Exception as e:
            return AIProcessingResult(
                success=False,
                error=f"OpenAI processing error: {str(e)}",
                provider_used=AIProvider.OPENAI
            )
    
    async def _process_with_anthropic(self, config: AIProviderConfig, resume_text: str, user_id: str, analysis_type: str, progress_callback=None) -> AIProcessingResult:
        """Process with Anthropic Claude"""
        try:
            if progress_callback:
                progress_callback("Connecting to Anthropic", 30)
                
            client = anthropic.AsyncAnthropic(api_key=config.api_key)
            prompt = self._build_analysis_prompt(resume_text, analysis_type)
            
            if progress_callback:
                progress_callback("Sending request to Anthropic", 50)
            
            response = await client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if progress_callback:
                progress_callback("Processing Anthropic response", 80)
            
            analysis = self._parse_ai_response(response.content[0].text)
            
            return AIProcessingResult(
                success=True,
                data=analysis,
                provider_used=AIProvider.ANTHROPIC,
                model_used=config.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else None,
                cost_estimate=self._estimate_anthropic_cost(response.usage.input_tokens if response.usage else 0, response.usage.output_tokens if response.usage else 0, config.model)
            )
            
        except Exception as e:
            return AIProcessingResult(
                success=False,
                error=f"Anthropic processing error: {str(e)}",
                provider_used=AIProvider.ANTHROPIC
            )
    
    def _build_analysis_prompt(self, resume_text: str, analysis_type: str) -> str:
        """Build enhanced agentic analysis prompt with market-aware scoring"""
        if analysis_type == "comprehensive":
            return f"""
You are an expert HR professional with 15+ years of experience in talent acquisition. Analyze this resume using a realistic, market-aware approach and provide a detailed JSON response.

CRITICAL: Use realistic scoring (most candidates score 45-75, exceptional candidates 80-90, avoid score inflation).

Required JSON structure:
{{
    "candidate_info": {{
        "name": "extracted full name",
        "email": "extracted email",
        "phone": "extracted phone number",
        "location": "extracted location/city"
    }},
    "scores": {{
        "overall_score": 75,
        "experience_score": 80,
        "skills_score": 70,
        "education_score": 75,
        "technical_score": 65,
        "role_fit_score": 72,
        "ats_compatibility": 85
    }},
    "analysis": {{
        "summary": "Brief 2-3 sentence professional summary",
        "experience_years": 5,
        "seniority_level": "mid-level",
        "industry_fit": "Technology",
        "salary_estimate": {{"min": 70000, "max": 90000, "currency": "USD"}}
    }},
    "skills": {{
        "key_skills": ["primary skill", "secondary skill", "tertiary skill"],
        "technical_skills": ["programming language", "framework", "tool"],
        "soft_skills": ["communication", "leadership", "problem-solving"],
        "certifications": ["certification 1", "certification 2"]
    }},
    "experience": {{
        "job_titles": ["Current/Recent Title", "Previous Title"],
        "companies": ["Company 1", "Company 2"],
        "key_achievements": ["achievement 1", "achievement 2"],
        "career_progression": "steady growth/lateral moves/rapid advancement"
    }},
    "education": [
        {{
            "degree": "Bachelor's/Master's/PhD",
            "field": "Computer Science",
            "institution": "University Name",
            "year": "2020",
            "gpa": "3.8"
        }}
    ],
    "assessment": {{
        "strengths": ["key strength 1", "key strength 2", "key strength 3"],
        "improvement_areas": ["area for improvement 1", "area 2"],
        "red_flags": ["concern 1 if any", "concern 2 if any"],
        "unique_value_proposition": "What makes this candidate stand out"
    }},
    "recommendations": {{
        "recommended_roles": ["Software Engineer", "Senior Developer"],
        "keywords_missing": ["keyword1", "keyword2"],
        "suggestions": "Specific actionable advice for improvement",
        "interview_focus": ["technical depth", "leadership experience"],
        "cultural_fit_indicators": ["team collaboration", "innovation mindset"]
    }},
    "market_analysis": {{
        "competitiveness": "high/medium/low in current market",
        "demand_level": "high demand for these skills",
        "market_positioning": "top 25% of candidates in this field"
    }},
    "metadata": {{
        "analysis_type": "comprehensive",
        "confidence_score": 0.85,
        "processing_notes": "Any special observations"
    }}
}}

IMPORTANT SCORING GUIDELINES:
- Overall Score: 40-54 (average), 55-69 (good), 70-84 (strong), 85+ (exceptional)
- Be realistic - most candidates are in the 45-75 range
- Only give 80+ scores to truly outstanding candidates
- Consider market standards and role requirements

Resume text to analyze:
{resume_text}
"""
        else:
            return f"""Analyze this resume and extract key information in JSON format with realistic scoring:

Resume text:
{resume_text}"""
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data with agentic format support"""
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                
                # Transform to expected frontend format if agentic structure detected
                if 'scores' in parsed_data and 'analysis' in parsed_data:
                    return self._transform_agentic_to_unified_format(parsed_data)
                
                # If already in unified format, ensure all required fields exist
                return self._ensure_unified_format_completeness(parsed_data)
            
            # Fallback: create basic structure
            return {
                "candidate_info": {"name": "Unknown", "email": "", "phone": "", "location": ""},
                "scores": {
                    "overall_score": 70,
                    "experience_score": 65,
                    "skills_score": 70,
                    "education_score": 65,
                    "technical_score": 60,
                    "role_fit_score": 70,
                    "ats_compatibility": 75
                },
                "analysis": {
                    "summary": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                    "experience_years": 0,
                    "seniority_level": "entry-level",
                    "industry_fit": "General"
                },
                "skills": {
                    "key_skills": [],
                    "technical_skills": [],
                    "soft_skills": [],
                    "certifications": []
                },
                "assessment": {
                    "strengths": ["Experience in relevant field"],
                    "improvement_areas": ["More specific achievements needed"],
                    "red_flags": []
                },
                "recommendations": {
                    "recommended_roles": ["Entry Level Position"],
                    "keywords_missing": [],
                    "suggestions": "Consider adding more quantifiable achievements"
                },
                "metadata": {
                    "analysis_complete": True,
                    "confidence_score": 0.6,
                    "raw_response": response_text
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return {
                "candidate_info": {"name": "Unknown", "email": "", "phone": "", "location": ""},
                "scores": {
                    "overall_score": 60,
                    "experience_score": 60,
                    "skills_score": 60,
                    "education_score": 60,
                    "technical_score": 55,
                    "role_fit_score": 60,
                    "ats_compatibility": 70
                },
                "analysis": {
                    "summary": "Analysis completed with limited parsing",
                    "experience_years": 0,
                    "seniority_level": "unknown"
                },
                "skills": {"key_skills": [], "technical_skills": [], "soft_skills": [], "certifications": []},
                "assessment": {
                    "strengths": ["Resume submitted for analysis"],
                    "improvement_areas": ["Unable to parse resume content effectively"],
                    "red_flags": ["Parsing error occurred"]
                },
                "recommendations": {
                    "recommended_roles": ["General Position"],
                    "suggestions": "Please ensure resume is in a clear, readable format"
                },
                "metadata": {
                    "analysis_complete": True,
                    "confidence_score": 0.3,
                    "error": str(e),
                    "raw_response": response_text
                }
            }
    
    def _transform_agentic_to_unified_format(self, agentic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic analysis format to unified frontend-expected format"""
        try:
            # Extract data from agentic structure
            candidate_info = agentic_data.get('candidate_info', {})
            scores = agentic_data.get('scores', {})
            analysis = agentic_data.get('analysis', {})
            skills = agentic_data.get('skills', {})
            assessment = agentic_data.get('assessment', {})
            recommendations = agentic_data.get('recommendations', {})
            
            # Transform to unified format
            return {
                "candidate_info": candidate_info,
                "scores": scores,
                "analysis": analysis,
                "skills": skills,
                "experience": agentic_data.get('experience', {}),
                "education": agentic_data.get('education', []),
                "assessment": assessment,
                "recommendations": recommendations,
                "market_analysis": agentic_data.get('market_analysis', {}),
                "metadata": agentic_data.get('metadata', {
                    "analysis_complete": True,
                    "confidence_score": 0.8
                }),
                # Legacy fields for backward compatibility
                "overall_score": scores.get('overall_score', 70),
                "experience_score": scores.get('experience_score', 70),
                "skills_score": scores.get('skills_score', 70),
                "education_score": scores.get('education_score', 70),
                "summary": analysis.get('summary', ''),
                "key_skills": skills.get('key_skills', []),
                "experience_years": analysis.get('experience_years', 0),
                "strengths": assessment.get('strengths', []),
                "improvement_areas": assessment.get('improvement_areas', []),
                "recommended_roles": recommendations.get('recommended_roles', []),
                "industry_fit": analysis.get('industry_fit', ''),
                "salary_estimate": analysis.get('salary_estimate', {}),
                "ats_compatibility": scores.get('ats_compatibility', 75),
                "keywords_missing": recommendations.get('keywords_missing', [])
            }
        except Exception as e:
            self.logger.error(f"Error transforming agentic data: {e}")
            return agentic_data  # Return original if transformation fails
    
    def _ensure_unified_format_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure unified format has all required fields"""
        # Default structure
        complete_data = {
            "candidate_info": data.get('candidate_info', {"name": "Unknown", "email": "", "phone": "", "location": ""}),
            "scores": {
                "overall_score": data.get('overall_score', 70),
                "experience_score": data.get('experience_score', 70),
                "skills_score": data.get('skills_score', 70),
                "education_score": data.get('education_score', 70),
                "technical_score": data.get('technical_score', 65),
                "role_fit_score": data.get('role_fit_score', 70),
                "ats_compatibility": data.get('ats_compatibility', 75)
            },
            "analysis": {
                "summary": data.get('summary', ''),
                "experience_years": data.get('experience_years', 0),
                "seniority_level": data.get('seniority_level', 'entry-level'),
                "industry_fit": data.get('industry_fit', ''),
                "salary_estimate": data.get('salary_estimate', {})
            },
            "skills": {
                "key_skills": data.get('key_skills', []),
                "technical_skills": data.get('technical_skills', []),
                "soft_skills": data.get('soft_skills', []),
                "certifications": data.get('certifications', [])
            },
            "assessment": {
                "strengths": data.get('strengths', []),
                "improvement_areas": data.get('improvement_areas', []),
                "red_flags": data.get('red_flags', [])
            },
            "recommendations": {
                "recommended_roles": data.get('recommended_roles', []),
                "keywords_missing": data.get('keywords_missing', []),
                "suggestions": data.get('recommendations', '')
            },
            "metadata": {
                "analysis_complete": True,
                "confidence_score": 0.8
            }
        }
        
        # Merge with provided data
        complete_data.update(data)
        return complete_data
    
    def _check_provider_health(self, provider: AIProvider) -> bool:
        """Check if provider is healthy and available"""
        try:
            # Check if we've checked recently
            if provider in self.last_health_check:
                if time.time() - self.last_health_check[provider] < self.health_check_interval:
                    return self.provider_health.get(provider, False)
            
            config = self.providers.get(provider)
            if not config or not config.enabled:
                return False
            
            # Quick health check based on provider
            if provider == AIProvider.OLLAMA:
                try:
                    if OLLAMA_AVAILABLE:
                        # Use official client
                        ollama.list()
                        healthy = True
                    else:
                        # Fallback to HTTP
                        import requests
                        response = requests.get(f"{config.base_url}/api/tags", timeout=5)
                        healthy = response.status_code == 200
                except:
                    healthy = False
            
            elif provider == AIProvider.OPENAI:
                healthy = bool(config.api_key and OPENAI_AVAILABLE)
            
            elif provider == AIProvider.ANTHROPIC:
                healthy = bool(config.api_key and ANTHROPIC_AVAILABLE)
            
            else:
                healthy = False
            
            # Cache the result
            self.provider_health[provider] = healthy
            self.last_health_check[provider] = time.time()
            
            return healthy
            
        except Exception as e:
            self.logger.error(f"Error checking health for {provider}: {e}")
            return False
    
    def _estimate_openai_cost(self, tokens: int, model: str) -> float:
        """Estimate OpenAI API cost"""
        # Rough cost estimates (as of 2024)
        cost_per_1k_tokens = {
            'gpt-4o': 0.005,
            'gpt-4o-mini': 0.0015,
            'gpt-4': 0.03,
            'gpt-3.5-turbo': 0.002
        }
        
        rate = cost_per_1k_tokens.get(model, 0.002)
        return (tokens / 1000) * rate
    
    def _estimate_anthropic_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate Anthropic API cost"""
        # Rough cost estimates (as of 2024)
        if 'haiku' in model:
            input_rate = 0.00025
            output_rate = 0.00125
        elif 'sonnet' in model:
            input_rate = 0.003
            output_rate = 0.015
        else:
            input_rate = 0.015
            output_rate = 0.075
        
        return (input_tokens / 1000) * input_rate + (output_tokens / 1000) * output_rate

# Global instance for easy access
unified_processor = None

def get_unified_processor(railway_db=None, cache_manager=None) -> UnifiedAIProcessor:
    """Get or create the global unified processor instance"""
    global unified_processor
    if unified_processor is None:
        unified_processor = UnifiedAIProcessor(railway_db, cache_manager)
    return unified_processor

def initialize_unified_processor(railway_db=None, cache_manager=None):
    """Initialize the global unified processor"""
    global unified_processor
    unified_processor = UnifiedAIProcessor(railway_db, cache_manager)
    return unified_processor
