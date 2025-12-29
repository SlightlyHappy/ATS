"""
Enhanced Multi-provider AI processing system for resume analysis.
Supports Ollama, OpenAI, Google Gemini, Anthropic, and Together AI with robust error handling.
"""

import json
import logging
import os
import requests
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import asyncio
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AIProviderConfig:
    """Configuration for AI providers."""
    provider_type: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 600  # Increased from 120 to 300 seconds for limited hardware
    retry_attempts: int = 3
    retry_delay: float = 1.0

class AIProviderError(Exception):
    """Custom exception for AI provider errors."""
    pass

class AIProvider(ABC):
    """Enhanced abstract base class for AI providers."""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "last_error": None,
            "consecutive_failures": 0,
            "last_success_time": None
        }
        self.is_healthy = True
        self._initialize_provider()
    
    @abstractmethod
    def _initialize_provider(self):
        """Initialize provider-specific settings."""
        pass
    
    @abstractmethod
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make the actual request to the AI provider."""
        pass
    
    def generate_response(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Generate AI response with retry logic and error handling."""
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()
                result = self._make_request(prompt, format_json)
                response_time = time.time() - start_time
                
                self._update_stats(True, response_time)
                self.is_healthy = True
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                self._update_stats(False, response_time, str(e))
                
                if attempt < self.config.retry_attempts - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed for {self.config.provider_type}, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    self.is_healthy = False
                    logger.error(f"All attempts failed for {self.config.provider_type}: {str(e)}")
                    raise AIProviderError(f"Provider {self.config.provider_type} failed after {self.config.retry_attempts} attempts: {str(e)}")
    
    def _update_stats(self, success: bool, response_time: float, error: str = None):
        """Update provider statistics."""
        self.stats["total_requests"] += 1
        
        if success:
            self.stats["successful_requests"] += 1
            self.stats["consecutive_failures"] = 0
            self.stats["last_success_time"] = time.time()
        else:
            self.stats["failed_requests"] += 1
            self.stats["consecutive_failures"] += 1
            self.stats["last_error"] = error
        
        # Update average response time
        total_time = self.stats["average_response_time"] * (self.stats["total_requests"] - 1)
        self.stats["average_response_time"] = (total_time + response_time) / self.stats["total_requests"]
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the provider."""
        try:
            test_result = self.generate_response("Hello, respond with just: OK", format_json=False)
            return {
                "healthy": True,
                "provider": self.config.provider_type,
                "model": self.config.model,
                "stats": self.stats,
                "test_response": test_result
            }
        except Exception as e:
            return {
                "healthy": False,
                "provider": self.config.provider_type,
                "model": self.config.model,
                "error": str(e),
                "stats": self.stats
            }

class OllamaProvider(AIProvider):
    """Enhanced Ollama local AI provider with robust connection handling."""
    
    def _initialize_provider(self):
        """Initialize Ollama provider."""
        self.base_url = self.config.base_url or os.getenv('OLLAMA_URL', 'http://localhost:11434')
        # Ensure Ollama is available
        self._verify_ollama_connection()
    
    def _verify_ollama_connection(self):
        """Verify Ollama server is accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=300)  # Increased from 10 to 30 seconds
            response.raise_for_status()
            logger.info(f"Ollama connection verified at {self.base_url}")
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            # Don't raise error here, let the actual request handle it
    
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to Ollama with enhanced error handling."""
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": 0.9,
                "num_ctx": 8192,
                "repeat_penalty": 1.1,
                "num_predict": self.config.max_tokens
            }
        }
        
        if format_json:
            payload["format"] = "json"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise AIProviderError(f"Ollama returned error: {result['error']}")
            
            response_text = result.get("response", "")
            
            if format_json:
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from Ollama: {e}")
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            pass
                    # Fallback to structured response
                    return {"response": response_text, "raw_response": True}
            else:
                return {"response": response_text}
                
        except requests.exceptions.ConnectionError:
            raise AIProviderError(f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama is running.")
        except requests.exceptions.Timeout:
            raise AIProviderError(f"Ollama request timed out after {self.config.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise AIProviderError(f"Ollama request failed: {str(e)}")

class OpenAIProvider(AIProvider):
    """Enhanced OpenAI API provider with robust error handling."""
    
    def _initialize_provider(self):
        """Initialize OpenAI provider."""
        if not self.config.api_key:
            raise AIProviderError("OpenAI API key is required")
        
        try:
            import openai
            self.openai = openai
            # Set up client with proper error handling
            self.client = openai.OpenAI(api_key=self.config.api_key)
        except ImportError:
            raise AIProviderError("OpenAI library not installed. Run: pip install openai>=1.0.0")
    
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to OpenAI with enhanced error handling."""
        messages = [{"role": "user", "content": prompt}]
        
        if format_json:
            messages.insert(0, {
                "role": "system", 
                "content": "You are a helpful assistant that always responds with valid JSON format."
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=0.9,
                timeout=self.config.timeout
            )
            
            content = response.choices[0].message.content
            
            if format_json:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from OpenAI: {e}")
                    return {"response": content, "raw_response": True}
            else:
                return {"response": content}
                
        except self.openai.AuthenticationError:
            raise AIProviderError("OpenAI authentication failed. Check your API key.")
        except self.openai.RateLimitError:
            raise AIProviderError("OpenAI rate limit exceeded. Please try again later.")
        except self.openai.APIError as e:
            raise AIProviderError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise AIProviderError(f"OpenAI request failed: {str(e)}")

class GeminiProvider(AIProvider):
    """Enhanced Google Gemini API provider with robust error handling."""
    
    def _initialize_provider(self):
        """Initialize Gemini provider."""
        if not self.config.api_key:
            raise AIProviderError("Google API key is required")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            self.genai = genai
            
            # Initialize model with safety settings
            generation_config = {
                "temperature": self.config.temperature,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": self.config.max_tokens,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            self.model_instance = genai.GenerativeModel(
                model_name=self.config.model,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
        except ImportError:
            raise AIProviderError("Google Generative AI library not installed. Run: pip install google-generativeai")
    
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to Gemini with enhanced error handling."""
        if format_json:
            prompt += "\n\nIMPORTANT: Respond with valid JSON format only."
        
        try:
            response = self.model_instance.generate_content(prompt)
            
            # Check if response was blocked
            if response.prompt_feedback.block_reason:
                raise AIProviderError(f"Gemini blocked the request: {response.prompt_feedback.block_reason}")
            
            if not response.parts:
                raise AIProviderError("Gemini returned empty response")
            
            content = response.text
            
            if format_json:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from Gemini: {e}")
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            pass
                    return {"response": content, "raw_response": True}
            else:
                return {"response": content}
                
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg:
                raise AIProviderError("Invalid Google API key")
            elif "quota" in error_msg.lower():
                raise AIProviderError("Google API quota exceeded")
            else:
                raise AIProviderError(f"Gemini request failed: {error_msg}")

class AnthropicProvider(AIProvider):
    """Enhanced Anthropic Claude API provider with robust error handling."""
    
    def _initialize_provider(self):
        """Initialize Anthropic provider."""
        if not self.config.api_key:
            raise AIProviderError("Anthropic API key is required")
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.config.api_key)
        except ImportError:
            raise AIProviderError("Anthropic library not installed. Run: pip install anthropic")
    
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to Claude with enhanced error handling."""
        if format_json:
            prompt += "\n\nIMPORTANT: Respond with valid JSON format only."
        
        try:
            message = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = message.content[0].text
            
            if format_json:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from Claude: {e}")
                    return {"response": content, "raw_response": True}
            else:
                return {"response": content}
                
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower():
                raise AIProviderError("Invalid Anthropic API key")
            elif "rate_limit" in error_msg.lower():
                raise AIProviderError("Anthropic rate limit exceeded")
            else:
                raise AIProviderError(f"Anthropic request failed: {error_msg}")

class TogetherAIProvider(AIProvider):
    """Enhanced Together AI provider for fast open-source models."""
    
    def _initialize_provider(self):
        """Initialize Together AI provider."""
        if not self.config.api_key:
            raise AIProviderError("Together AI API key is required")
        
        self.base_url = "https://api.together.xyz/v1"
    
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to Together AI with enhanced error handling."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "user", "content": prompt}]
        if format_json:
            messages.insert(0, {
                "role": "system", 
                "content": "You are a helpful assistant that always responds with valid JSON format."
            })
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise AIProviderError(f"Together AI returned error: {result['error']}")
            
            content = result["choices"][0]["message"]["content"]
            
            if format_json:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from Together AI: {e}")
                    return {"response": content, "raw_response": True}
            else:
                return {"response": content}
                
        except requests.exceptions.RequestException as e:
            if "401" in str(e):
                raise AIProviderError("Invalid Together AI API key")
            elif "429" in str(e):
                raise AIProviderError("Together AI rate limit exceeded")
            else:
                raise AIProviderError(f"Together AI request failed: {str(e)}")

class EnhancedMultiProviderAI:
    """Enhanced AI processor with intelligent provider management and failover."""
    
    def __init__(self):
        self.providers = {}
        self.primary_provider = None
        self.failover_providers = []
        self.response_cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        
        # Provider priority order (fallback chain)
        self.provider_priority = [
            'ollama',      # Primary: Free, fast, local
            'gemini',      # Secondary: Free tier available
            'openai',      # Tertiary: Paid but reliable
            'anthropic',   # Quaternary: High quality
            'together'     # Quinary: Fast inference
        ]
        
        # Model recommendations by provider
        self.recommended_models = {
            'ollama': ['qwen2.5:7b', 'qwen2.5:3b', 'llama3.2:3b', 'phi3.5:3.8b'],
            'openai': ['gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4o'],
            'gemini': ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro'],
            'anthropic': ['claude-3-haiku-20240307', 'claude-3-5-sonnet-20241022'],
            'together': ['meta-llama/Llama-2-7b-chat-hf', 'mistralai/Mixtral-8x7B-Instruct-v0.1']
        }
    
    def add_provider(self, provider_type: str, model: str, api_key: str = None, **kwargs) -> bool:
        """Add an AI provider with enhanced configuration."""
        try:
            config = AIProviderConfig(
                provider_type=provider_type,
                model=model,
                api_key=api_key,
                base_url=kwargs.get('base_url'),
                max_tokens=kwargs.get('max_tokens', 2000),
                temperature=kwargs.get('temperature', 0.1),
                timeout=kwargs.get('timeout', 700),  # Increased from 120 to 300 seconds
                retry_attempts=kwargs.get('retry_attempts', 3)
            )
            
            if provider_type == 'ollama':
                provider = OllamaProvider(config)
            elif provider_type == 'openai':
                provider = OpenAIProvider(config)
            elif provider_type == 'gemini':
                provider = GeminiProvider(config)
            elif provider_type == 'anthropic':
                provider = AnthropicProvider(config)
            elif provider_type == 'together':
                provider = TogetherAIProvider(config)
            else:
                raise AIProviderError(f"Unsupported provider type: {provider_type}")
            
            provider_key = f"{provider_type}_{model}"
            self.providers[provider_key] = provider
            
            # Set as primary if it's the first or highest priority provider
            if not self.primary_provider or self._get_provider_priority(provider_type) < self._get_provider_priority(self.primary_provider.config.provider_type):
                self.primary_provider = provider
                logger.info(f"Set primary AI provider: {provider_type} - {model}")
            
            # Add to failover list
            if provider not in self.failover_providers:
                self.failover_providers.append(provider)
                self.failover_providers.sort(key=lambda p: self._get_provider_priority(p.config.provider_type))
            
            logger.info(f"Added AI provider: {provider_type} - {model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add provider {provider_type}: {e}")
            return False
    
    def _get_provider_priority(self, provider_type: str) -> int:
        """Get priority index for provider type."""
        try:
            return self.provider_priority.index(provider_type)
        except ValueError:
            return 999  # Low priority for unknown providers
    
    def generate_response(self, prompt: str, format_json: bool = True, use_cache: bool = True) -> Dict[str, Any]:
        """Generate response with intelligent provider selection and failover."""
        # Check cache first
        if use_cache:
            cache_key = f"{hash(prompt)}_{format_json}"
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                logger.debug("Using cached AI response")
                return cached_response
        
        # Try primary provider first
        if self.primary_provider and self.primary_provider.is_healthy:
            try:
                response = self.primary_provider.generate_response(prompt, format_json)
                if use_cache:
                    self._cache_response(cache_key, response)
                return response
            except Exception as e:
                logger.warning(f"Primary provider {self.primary_provider.config.provider_type} failed: {e}")
        
        # Try failover providers
        for provider in self.failover_providers:
            if provider == self.primary_provider:
                continue  # Already tried
            
            if not provider.is_healthy:
                continue  # Skip unhealthy providers
            
            try:
                response = provider.generate_response(prompt, format_json)
                logger.info(f"Failover successful using {provider.config.provider_type}")
                if use_cache:
                    self._cache_response(cache_key, response)
                return response
            except Exception as e:
                logger.warning(f"Failover provider {provider.config.provider_type} failed: {e}")
                continue
        
        # If all providers failed, raise error
        raise AIProviderError("All AI providers failed. Please check your configuration and network connectivity.")
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if still valid."""
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['response']
            else:
                del self.response_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache response with timestamp."""
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            'providers': {},
            'primary_provider': None,
            'failover_providers': [],
            'cache_size': len(self.response_cache),
            'recommendations': {}
        }
        
        # Get provider health status
        for key, provider in self.providers.items():
            health = provider.health_check()
            status['providers'][key] = health
        
        # Primary provider info
        if self.primary_provider:
            status['primary_provider'] = {
                'provider': self.primary_provider.config.provider_type,
                'model': self.primary_provider.config.model,
                'healthy': self.primary_provider.is_healthy
            }
        
        # Failover providers info
        status['failover_providers'] = [
            {
                'provider': p.config.provider_type,
                'model': p.config.model,
                'healthy': p.is_healthy
            }
            for p in self.failover_providers
        ]
        
        # Recommendations for setup
        status['recommendations'] = self._get_setup_recommendations()
        
        return status
    
    def set_provider(self, provider_type: str, model: str, api_key: str = None, **kwargs) -> bool:
        """Set AI provider (compatibility method for existing code)."""
        return self.add_provider(provider_type, model, api_key, **kwargs)
    
    def set_multiple_providers(self, provider_configs: list) -> bool:
        """Set multiple AI providers from config list."""
        success_count = 0
        for config in provider_configs:
            if self.add_provider(
                config.get('provider_type'),
                config.get('model'),
                config.get('api_key'),
                **config.get('kwargs', {})
            ):
                success_count += 1
        return success_count > 0
    
    def analyze_query_complexity(self, query: str) -> dict:
        """Analyze query complexity (simplified implementation)."""
        return {
            'complexity': 'medium',
            'estimated_tokens': len(query.split()) * 1.3,
            'recommended_provider': 'ollama'
        }
    
    def get_best_provider(self, complexity: dict, priority: str = 'speed') -> str:
        """Get best provider based on complexity and priority."""
        if not self.providers:
            return None
        # Return the first available provider (simplified)
        return list(self.providers.keys())[0]
    
    def get_provider_stats(self) -> dict:
        """Get provider statistics."""
        return {
            'total_providers': len(self.providers),
            'active_providers': len([p for p in self.providers.values() if p.is_healthy]),
            'primary_provider': self.primary_provider.config.provider_type if self.primary_provider else None
        }
    
    def generate_with_fallback(self, prompt: str, format_json: bool = True, **kwargs) -> dict:
        """Generate response with fallback (alias for generate_response)."""
        return self.generate_response(prompt, format_json)
    
    def clear_cache(self):
        """Clear response cache."""
        self.response_cache.clear()
        logger.info("AI response cache cleared")
    
    @property
    def current_provider(self):
        """Get current provider (alias for primary_provider)."""
        return self.primary_provider
    
    @current_provider.setter
    def current_provider(self, provider):
        """Set current provider."""
        self.primary_provider = provider
    
    def _get_setup_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for optimal setup."""
        recommendations = {
            'missing_providers': [],
            'suggested_models': {},
            'configuration_tips': []
        }
        
        # Check for missing high-priority providers
        current_types = set(p.config.provider_type for p in self.providers.values())
        
        if 'ollama' not in current_types:
            recommendations['missing_providers'].append({
                'provider': 'ollama',
                'reason': 'Free, fast, local processing - ideal for privacy',
                'setup': 'Install Ollama and pull a model like qwen2.5:7b'
            })
        
        if 'gemini' not in current_types:
            recommendations['missing_providers'].append({
                'provider': 'gemini',
                'reason': 'Free tier available, good performance',
                'setup': 'Get API key from Google AI Studio'
            })
        
        # Suggest optimal models for each provider
        for provider_type, models in self.recommended_models.items():
            if provider_type in current_types:
                recommendations['suggested_models'][provider_type] = models[0]  # Best model
        
        # Configuration tips
        if len(self.providers) == 1:
            recommendations['configuration_tips'].append("Consider adding a backup AI provider for reliability")
        
        if not any(p.config.provider_type == 'ollama' for p in self.providers.values()):
            recommendations['configuration_tips'].append("Ollama provides free local processing - great for development")
        
        return recommendations

# Global instance
multi_provider_ai = EnhancedMultiProviderAI()

# Compatibility functions for existing code
def set_provider(provider_type: str, model: str, api_key: str = None, **kwargs):
    """Set AI provider (compatibility function)."""
    return multi_provider_ai.add_provider(provider_type, model, api_key, **kwargs)

def generate_response(prompt: str, format_json: bool = True) -> Dict[str, Any]:
    """Generate AI response (compatibility function)."""
    return multi_provider_ai.generate_response(prompt, format_json)

def get_system_status() -> Dict[str, Any]:
    """Get system status (compatibility function)."""
    return multi_provider_ai.get_system_status()
