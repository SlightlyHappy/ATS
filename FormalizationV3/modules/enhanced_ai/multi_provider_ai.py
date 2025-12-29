"""
Enhanced Multi-provider AI processing system for resume analysis.
Supports Ollama, OpenAI, Anthropic with intelligent routing, realistic scoring, and Railway optimization.
Integration from Salvage backend with enhanced capabilities.
"""

import json
import logging
import os
import requests
import time
import asyncio
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import aiohttp
import statistics
from datetime import datetime, timedelta

from config import Config

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
    timeout: int = 300
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
    async def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make the actual request to the AI provider."""
        pass
    
    async def generate_response(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Generate AI response with retry logic and error handling."""
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()
                result = await self._make_request(prompt, format_json)
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
                    await asyncio.sleep(wait_time)
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
        if self.stats["successful_requests"] > 0:
            self.stats["average_response_time"] = (
                self.stats["average_response_time"] * (self.stats["successful_requests"] - 1) + response_time
            ) / self.stats["successful_requests"]

class OllamaProvider(AIProvider):
    """Ollama AI provider implementation."""
    
    def _initialize_provider(self):
        """Initialize Ollama-specific settings."""
        if not self.config.base_url:
            self.config.base_url = "http://localhost:11434"
    
    async def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to Ollama API."""
        
        # Add JSON formatting instruction if requested
        if format_json:
            prompt += "\n\nPlease provide your response in valid JSON format only, without any additional text or explanation."
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
            async with session.post(f"{self.config.base_url}/api/generate", json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                result = await response.json()
                response_text = result.get("response", "")
                
                if format_json:
                    try:
                        # Try to parse as JSON
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        # Fallback: try to extract JSON from text
                        return self._extract_json_from_text(response_text)
                else:
                    return {"response": response_text}
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        try:
            # Find JSON-like content between braces
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: return error structure
        return {
            "error": "Failed to parse JSON response",
            "raw_response": text,
            "technical_skills_score": 50,
            "confidence_level": 30
        }

class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation."""
    
    def _initialize_provider(self):
        """Initialize OpenAI-specific settings."""
        if not self.config.api_key:
            self.config.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.config.api_key:
            raise ValueError("OpenAI API key not provided")
    
    async def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to OpenAI API."""
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": "You are an expert HR analyst. Provide detailed, accurate analysis."},
            {"role": "user", "content": prompt}
        ]
        
        if format_json:
            messages[0]["content"] += " Always respond with valid JSON format only."
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"} if format_json else None
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
            async with session.post("https://api.openai.com/v1/chat/completions", 
                                   headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                
                if format_json:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return self._extract_json_from_text(content)
                else:
                    return {"response": content}
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        try:
            # Find JSON-like content between braces
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: return error structure
        return {
            "error": "Failed to parse JSON response",
            "raw_response": text,
            "technical_skills_score": 50,
            "confidence_level": 30
        }

class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider implementation."""
    
    def _initialize_provider(self):
        """Initialize Anthropic-specific settings."""
        if not self.config.api_key:
            self.config.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.config.api_key:
            raise ValueError("Anthropic API key not provided")
    
    async def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to Anthropic API."""
        
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        if format_json:
            prompt += "\n\nPlease provide your response in valid JSON format only."
        
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
            async with session.post("https://api.anthropic.com/v1/messages",
                                   headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error: {response.status} - {error_text}")
                
                result = await response.json()
                content = result["content"][0]["text"]
                
                if format_json:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return self._extract_json_from_text(content)
                else:
                    return {"response": content}
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        try:
            # Find JSON-like content between braces
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: return error structure
        return {
            "error": "Failed to parse JSON response",
            "raw_response": text,
            "technical_skills_score": 50,
            "confidence_level": 30
        }

class MultiProviderAI:
    """Enhanced multi-provider AI system with intelligent routing and context optimization."""
    
    def __init__(self, config: Config):
        self.config = config
        self.providers = {}
        self.provider_priority = config.AI_PROVIDER_PRIORITY
        self.current_provider_index = 0
        self.performance_history = {}
        self.context_cache = {}
        self.routing_rules = {
            "technical_analysis": ["ollama", "openai"],
            "legal_compliance": ["openai", "anthropic"],
            "cultural_fit": ["anthropic", "openai"],
            "experience_evaluation": ["ollama", "openai"]
        }
        
        self._initialize_providers()
        self._setup_intelligent_routing()
    
    def _initialize_providers(self):
        """Initialize all available AI providers."""
        
        # Initialize Ollama (primary)
        if 'ollama' in self.provider_priority:
            try:
                ollama_config = AIProviderConfig(
                    provider_type="ollama",
                    model=self.config.OLLAMA_MODEL,
                    base_url=self.config.OLLAMA_URL,
                    timeout=self.config.AI_TIMEOUT,
                    retry_attempts=self.config.AI_MAX_RETRIES,
                    max_tokens=3000,
                    temperature=0.1
                )
                self.providers['ollama'] = OllamaProvider(ollama_config)
                logger.info("Ollama provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama provider: {e}")
        
        # Initialize OpenAI (fallback)
        if 'openai' in self.provider_priority and self.config.OPENAI_API_KEY:
            try:
                openai_config = AIProviderConfig(
                    provider_type="openai",
                    model=self.config.OPENAI_MODEL,
                    api_key=self.config.OPENAI_API_KEY,
                    timeout=self.config.AI_TIMEOUT,
                    retry_attempts=self.config.AI_MAX_RETRIES,
                    max_tokens=2500,
                    temperature=0.1
                )
                self.providers['openai'] = OpenAIProvider(openai_config)
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        # Initialize Anthropic (fallback)
        if 'anthropic' in self.provider_priority and self.config.ANTHROPIC_API_KEY:
            try:
                anthropic_config = AIProviderConfig(
                    provider_type="anthropic",
                    model=self.config.ANTHROPIC_MODEL,
                    api_key=self.config.ANTHROPIC_API_KEY,
                    timeout=self.config.AI_TIMEOUT,
                    retry_attempts=self.config.AI_MAX_RETRIES,
                    max_tokens=2000,
                    temperature=0.1
                )
                self.providers['anthropic'] = AnthropicProvider(anthropic_config)
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic provider: {e}")
        
        # Validate at least one provider is available
        if not self.providers:
            raise Exception("No AI providers available")
        
        logger.info(f"Initialized {len(self.providers)} AI providers: {list(self.providers.keys())}")
    
    def _setup_intelligent_routing(self):
        """Setup intelligent routing based on task type and provider performance."""
        # Initialize performance tracking
        for provider_name in self.providers.keys():
            self.performance_history[provider_name] = {
                "response_times": [],
                "success_rates": [],
                "quality_scores": [],
                "task_specializations": {}
            }
    
    def _select_optimal_provider(self, task_type: str = "general", context_complexity: str = "medium") -> str:
        """Select optimal provider based on task type, performance, and availability."""
        
        # Get preferred providers for this task type
        preferred_providers = self.routing_rules.get(task_type, self.provider_priority)
        
        # Filter to available providers
        available_providers = [p for p in preferred_providers if p in self.providers and self.providers[p].is_healthy]
        
        if not available_providers:
            # Fall back to any healthy provider
            available_providers = [p for p in self.providers.keys() if self.providers[p].is_healthy]
        
        if not available_providers:
            # Last resort: try any provider
            available_providers = list(self.providers.keys())
        
        if not available_providers:
            raise AIProviderError("No AI providers available")
        
        # Select based on recent performance for complex tasks
        if context_complexity == "high" and len(available_providers) > 1:
            return self._select_best_performing_provider(available_providers, task_type)
        
        return available_providers[0]
    
    def _select_best_performing_provider(self, candidates: List[str], task_type: str) -> str:
        """Select best performing provider from candidates."""
        
        best_provider = candidates[0]
        best_score = 0
        
        for provider_name in candidates:
            if provider_name not in self.performance_history:
                continue
            
            history = self.performance_history[provider_name]
            
            # Calculate composite score
            avg_response_time = statistics.mean(history["response_times"][-10:]) if history["response_times"] else 30
            avg_success_rate = statistics.mean(history["success_rates"][-10:]) if history["success_rates"] else 0.8
            
            # Prefer faster providers with high success rates
            composite_score = avg_success_rate * 100 - (avg_response_time / 10)
            
            # Bonus for task specialization
            if task_type in history["task_specializations"]:
                composite_score += history["task_specializations"][task_type] * 10
            
            if composite_score > best_score:
                best_score = composite_score
                best_provider = provider_name
        
        return best_provider
    
    async def generate_response(self, prompt: str, format_json: bool = True, task_type: str = "general", 
                              context_complexity: str = "medium") -> Dict[str, Any]:
        """Generate response using intelligent provider selection and context optimization."""
        
        # Optimize prompt based on context
        optimized_prompt = self._optimize_prompt_for_context(prompt, task_type, context_complexity)
        
        # Select optimal provider
        selected_provider_name = self._select_optimal_provider(task_type, context_complexity)
        
        # Try primary provider
        try:
            start_time = time.time()
            provider = self.providers[selected_provider_name]
            
            logger.info(f"Using {selected_provider_name} provider for {task_type} task")
            result = await provider.generate_response(optimized_prompt, format_json)
            
            response_time = time.time() - start_time
            self._update_performance_history(selected_provider_name, response_time, True, task_type)
            
            # Validate and enhance response
            enhanced_result = self._enhance_response_quality(result, task_type)
            
            return enhanced_result
            
        except Exception as e:
            logger.warning(f"Primary provider {selected_provider_name} failed: {e}")
            response_time = time.time() - start_time
            self._update_performance_history(selected_provider_name, response_time, False, task_type)
            
            # Try fallback providers
            return await self._try_fallback_providers(optimized_prompt, format_json, task_type, selected_provider_name)
    
    def _optimize_prompt_for_context(self, prompt: str, task_type: str, complexity: str) -> str:
        """Optimize prompt based on task type and complexity."""
        
        # Add task-specific instructions
        if task_type == "technical_analysis":
            prompt = f"""You are a technical skills analyst with expertise in various programming languages and technologies.
Focus on: skill verification, proficiency assessment, technology stack evaluation.

{prompt}

Provide detailed technical assessment including:
- Skill authenticity verification
- Technology proficiency levels
- Missing critical skills
- Recommendations for skill development"""
        
        elif task_type == "legal_compliance":
            prompt = f"""You are an HR legal compliance expert with deep knowledge of employment law.
Focus on: bias detection, legal compliance, discrimination risks.

{prompt}

Ensure assessment covers:
- Bias detection in evaluation
- Legal compliance considerations
- Risk assessment for hiring decisions
- Recommendations for compliant evaluation"""
        
        elif task_type == "cultural_fit":
            prompt = f"""You are a cultural fit and soft skills assessment expert.
Focus on: team compatibility, communication skills, cultural alignment.

{prompt}

Evaluate for:
- Team collaboration potential
- Communication effectiveness
- Cultural alignment indicators
- Soft skills assessment"""
        
        elif task_type == "experience_evaluation":
            prompt = f"""You are an experience evaluation specialist focusing on career progression and role fit.
Focus on: career trajectory, role suitability, growth potential.

{prompt}

Analyze:
- Career progression patterns
- Role-specific experience relevance
- Leadership and growth indicators
- Future potential assessment"""
        
        # Add complexity-based instructions
        if complexity == "high":
            prompt += "\n\nProvide comprehensive analysis with detailed reasoning and multiple perspectives."
        elif complexity == "low":
            prompt += "\n\nProvide concise analysis focusing on key points."
        
        return prompt
    
    async def _try_fallback_providers(self, prompt: str, format_json: bool, task_type: str, 
                                    failed_provider: str) -> Dict[str, Any]:
        """Try fallback providers when primary fails."""
        
        fallback_providers = [p for p in self.provider_priority if p != failed_provider and p in self.providers]
        
        for provider_name in fallback_providers:
            if not self.providers[provider_name].is_healthy:
                continue
            
            try:
                start_time = time.time()
                logger.info(f"Trying fallback provider: {provider_name}")
                
                result = await self.providers[provider_name].generate_response(prompt, format_json)
                
                response_time = time.time() - start_time
                self._update_performance_history(provider_name, response_time, True, task_type)
                
                return self._enhance_response_quality(result, task_type)
                
            except Exception as e:
                response_time = time.time() - start_time
                self._update_performance_history(provider_name, response_time, False, task_type)
                logger.warning(f"Fallback provider {provider_name} failed: {e}")
                continue
        
        raise AIProviderError("All AI providers failed")
    
    def _enhance_response_quality(self, result: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Enhance response quality based on task type."""
        
        # Add metadata
        result["processing_metadata"] = {
            "task_type": task_type,
            "enhancement_applied": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Ensure required fields exist with defaults
        if task_type == "technical_analysis":
            result.setdefault("technical_skills_score", 50)
            result.setdefault("skill_verification", {})
            result.setdefault("missing_skills", [])
        
        elif task_type == "experience_evaluation":
            result.setdefault("experience_score", 50)
            result.setdefault("career_progression", "Not assessed")
            result.setdefault("role_fit", 50)
        
        elif task_type == "cultural_fit":
            result.setdefault("cultural_fit_score", 50)
            result.setdefault("soft_skills", [])
            result.setdefault("team_compatibility", 50)
        
        elif task_type == "legal_compliance":
            result.setdefault("compliance_score", 80)
            result.setdefault("bias_flags", [])
            result.setdefault("legal_risks", [])
        
        # Validate score ranges
        for key, value in result.items():
            if key.endswith("_score") and isinstance(value, (int, float)):
                result[key] = max(0, min(100, value))
        
        return result
    
    def _update_performance_history(self, provider_name: str, response_time: float, 
                                  success: bool, task_type: str):
        """Update performance history for provider selection optimization."""
        
        if provider_name not in self.performance_history:
            return
        
        history = self.performance_history[provider_name]
        
        # Update response times (keep last 20 records)
        history["response_times"].append(response_time)
        if len(history["response_times"]) > 20:
            history["response_times"] = history["response_times"][-20:]
        
        # Update success rates
        history["success_rates"].append(1.0 if success else 0.0)
        if len(history["success_rates"]) > 20:
            history["success_rates"] = history["success_rates"][-20:]
        
        # Update task specialization scores
        if task_type not in history["task_specializations"]:
            history["task_specializations"][task_type] = 0.5
        
        # Adjust specialization score based on success
        current_score = history["task_specializations"][task_type]
        if success:
            history["task_specializations"][task_type] = min(1.0, current_score + 0.05)
        else:
            history["task_specializations"][task_type] = max(0.0, current_score - 0.1)
    
    def get_provider_stats(self) -> Dict[str, Dict]:
        """Get statistics for all providers."""
        return {name: provider.stats for name, provider in self.providers.items()}
    
    def get_healthy_providers(self) -> List[str]:
        """Get list of healthy providers."""
        return [name for name, provider in self.providers.items() if provider.is_healthy]
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all providers."""
        health_status = {}
        
        test_prompt = "Test connection. Respond with: {\"status\": \"ok\"}"
        
        for name, provider in self.providers.items():
            try:
                await provider.generate_response(test_prompt, format_json=True)
                health_status[name] = True
                provider.is_healthy = True
            except Exception as e:
                logger.warning(f"Health check failed for {name}: {e}")
                health_status[name] = False
                provider.is_healthy = False
        
        return health_status
