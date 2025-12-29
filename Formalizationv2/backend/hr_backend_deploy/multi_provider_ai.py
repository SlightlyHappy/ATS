"""
Enhanced Multi-Provider AI Integration System
Supports multiple AI providers with automatic fallback and load balancing
"""

import json
import logging
import os
import requests
import time
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from config import config, AIProviderConfig, AIProvider

logger = logging.getLogger(__name__)

class AIProviderError(Exception):
    """Custom exception for AI provider errors"""
    pass

class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""
    
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
        """Initialize provider-specific settings"""
        pass
    
    @abstractmethod
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make the actual request to the AI provider"""
        pass
    
    def generate_response(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Generate AI response with retry logic and error handling"""
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
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {self.config.provider_type}, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    self.is_healthy = False
                    logger.error(f"All attempts failed for {self.config.provider_type}: {str(e)}")
                    raise AIProviderError(f"Provider {self.config.provider_type} failed after {self.config.retry_attempts} attempts: {str(e)}")
    
    def _update_stats(self, success: bool, response_time: float, error: str = None):
        """Update provider statistics"""
        self.stats["total_requests"] += 1
        
        if success:
            self.stats["successful_requests"] += 1
            self.stats["consecutive_failures"] = 0
            self.stats["last_success_time"] = time.time()
            
            # Update average response time
            total_successful = self.stats["successful_requests"]
            current_avg = self.stats["average_response_time"]
            self.stats["average_response_time"] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        else:
            self.stats["failed_requests"] += 1
            self.stats["consecutive_failures"] += 1
            self.stats["last_error"] = error

class OllamaProvider(BaseAIProvider):
    """Ollama AI provider implementation"""
    
    def _initialize_provider(self):
        """Initialize Ollama provider"""
        self.base_url = self.config.base_url or "http://localhost:11434"
        
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to Ollama API"""
        try:
            url = f"{self.base_url}/api/generate"
            
            data = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }
            
            if format_json:
                data["format"] = "json"
            
            response = requests.post(
                url, 
                json=data, 
                timeout=self.config.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise AIProviderError(f"Ollama API returned status {response.status_code}: {response.text}")
            
            result = response.json()
            response_text = result.get('response', '')
            
            if format_json:
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    raise AIProviderError("Failed to parse JSON response from Ollama")
            
            return {"response": response_text}
            
        except requests.exceptions.Timeout:
            raise AIProviderError("Ollama request timed out")
        except requests.exceptions.ConnectionError:
            raise AIProviderError("Failed to connect to Ollama server")
        except Exception as e:
            raise AIProviderError(f"Ollama provider error: {str(e)}")

class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider implementation"""
    
    def _initialize_provider(self):
        """Initialize OpenAI provider"""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required")
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to OpenAI API"""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            
            messages = [{"role": "user", "content": prompt}]
            
            data = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
            
            if format_json:
                data["response_format"] = {"type": "json_object"}
            
            response = requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=self.config.timeout
            )
            
            if response.status_code != 200:
                raise AIProviderError(f"OpenAI API returned status {response.status_code}: {response.text}")
            
            result = response.json()
            response_text = result["choices"][0]["message"]["content"]
            
            if format_json:
                return json.loads(response_text)
            
            return {"response": response_text}
            
        except requests.exceptions.Timeout:
            raise AIProviderError("OpenAI request timed out")
        except Exception as e:
            raise AIProviderError(f"OpenAI provider error: {str(e)}")

class GeminiProvider(BaseAIProvider):
    """Google Gemini API provider implementation"""
    
    def _initialize_provider(self):
        """Initialize Gemini provider"""
        if not self.config.api_key:
            raise ValueError("Gemini API key is required")
    
    def _make_request(self, prompt: str, format_json: bool = True) -> Dict[str, Any]:
        """Make request to Gemini API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:generateContent?key={self.config.api_key}"
            
            if format_json:
                prompt += "\n\nPlease respond with valid JSON only."
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": self.config.temperature,
                    "maxOutputTokens": self.config.max_tokens
                }
            }
            
            response = requests.post(
                url,
                json=data,
                timeout=self.config.timeout
            )
            
            if response.status_code != 200:
                raise AIProviderError(f"Gemini API returned status {response.status_code}: {response.text}")
            
            result = response.json()
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
            
            if format_json:
                return json.loads(response_text)
            
            return {"response": response_text}
            
        except requests.exceptions.Timeout:
            raise AIProviderError("Gemini request timed out")
        except Exception as e:
            raise AIProviderError(f"Gemini provider error: {str(e)}")

class MultiProviderAI:
    """Multi-provider AI system with automatic fallback"""
    
    def __init__(self):
        """Initialize multi-provider AI system"""
        self.providers = {}
        self.fallback_order = config.get_fallback_providers()
        self._initialize_providers()
        
        logger.info(f"Multi-provider AI initialized with providers: {list(self.providers.keys())}")
    
    def _initialize_providers(self):
        """Initialize all available AI providers"""
        for provider_name, provider_config in config.AI_PROVIDERS.items():
            try:
                if provider_name == 'ollama':
                    self.providers[provider_name] = OllamaProvider(provider_config)
                elif provider_name == 'openai' and provider_config.api_key:
                    self.providers[provider_name] = OpenAIProvider(provider_config)
                elif provider_name == 'gemini' and provider_config.api_key:
                    self.providers[provider_name] = GeminiProvider(provider_config)
                # Add other providers as needed
                
                logger.info(f"Initialized {provider_name} provider")
                
            except Exception as e:
                logger.warning(f"Failed to initialize {provider_name} provider: {str(e)}")
    
    async def analyze_resume(self, resume_content: str, preferred_provider: str = None) -> Dict[str, Any]:
        """Analyze resume using multi-provider AI with fallback"""
        analysis_prompt = self._create_analysis_prompt(resume_content)
        
        # Determine provider order
        providers_to_try = [preferred_provider] if preferred_provider and preferred_provider in self.providers else []
        providers_to_try.extend([p for p in self.fallback_order if p not in providers_to_try and p in self.providers])
        
        last_error = None
        
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name)
            if not provider or not provider.is_healthy:
                continue
            
            try:
                logger.info(f"Attempting analysis with {provider_name}")
                result = provider.generate_response(analysis_prompt, format_json=True)
                
                # Validate and enhance the result
                enhanced_result = self._enhance_analysis_result(result, provider_name)
                
                return {
                    'success': True,
                    'analysis': enhanced_result,
                    'provider_used': provider_name,
                    'processing_time': provider.stats.get('average_response_time', 0)
                }
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Analysis failed with {provider_name}: {str(e)}")
                continue
        
        # All providers failed
        return {
            'success': False,
            'error': f'All AI providers failed. Last error: {last_error}',
            'analysis': None
        }
    
    def _create_analysis_prompt(self, resume_content: str) -> str:
        """Create comprehensive resume analysis prompt"""
        return f"""
You are an expert HR professional and resume analyst. Analyze the following resume text and provide a comprehensive JSON analysis.

Resume Text:
{resume_content}

Please provide a detailed analysis in the following JSON format:

{{
  "basic_info": {{
    "name": "Full name extracted from resume",
    "email": "Email address if found",
    "phone": "Phone number if found",
    "location": "Location/address if found"
  }},
  "summary": "2-3 sentence executive summary of the candidate",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "duration": "Duration (e.g., Jan 2020 - Present)",
      "description": "Brief description of responsibilities and achievements"
    }}
  ],
  "education": [
    {{
      "degree": "Degree type and field",
      "institution": "Institution name",
      "year": "Graduation year or duration"
    }}
  ],
  "certifications": ["cert1", "cert2"],
  "projects": [
    {{
      "name": "Project name",
      "description": "Project description",
      "technologies": ["tech1", "tech2"]
    }}
  ],
  "scores": {{
    "overall_score": 75,
    "technical_score": 80,
    "experience_score": 70,
    "education_score": 85,
    "skills_match": 75
  }},
  "analysis": {{
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "recommendations": ["recommendation1", "recommendation2"]
  }}
}}

Ensure all scores are integers between 0-100. Focus on extracting accurate information and providing realistic scoring.
"""
    
    def _enhance_analysis_result(self, result: Dict[str, Any], provider_name: str) -> Dict[str, Any]:
        """Enhance and validate the analysis result"""
        # Ensure required fields exist
        required_fields = ['basic_info', 'summary', 'skills', 'experience', 'education', 'scores', 'analysis']
        for field in required_fields:
            if field not in result:
                result[field] = self._get_default_field_value(field)
        
        # Ensure scores are within valid range
        if 'scores' in result:
            for score_key, score_value in result['scores'].items():
                if isinstance(score_value, (int, float)):
                    result['scores'][score_key] = max(0, min(100, int(score_value)))
        
        # Add metadata
        result['_meta'] = {
            'provider_used': provider_name,
            'analysis_timestamp': time.time(),
            'version': '2.0'
        }
        
        return result
    
    def _get_default_field_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            'basic_info': {'name': '', 'email': '', 'phone': '', 'location': ''},
            'summary': 'No summary available',
            'skills': [],
            'experience': [],
            'education': [],
            'certifications': [],
            'projects': [],
            'scores': {
                'overall_score': 50,
                'technical_score': 50,
                'experience_score': 50,
                'education_score': 50,
                'skills_match': 50
            },
            'analysis': {
                'strengths': [],
                'weaknesses': [],
                'recommendations': []
            }
        }
        return defaults.get(field, {})
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers"""
        stats = {}
        for name, provider in self.providers.items():
            stats[name] = {
                'is_healthy': provider.is_healthy,
                'stats': provider.stats
            }
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        results = {}
        for name, provider in self.providers.items():
            try:
                # Simple test request
                test_result = provider.generate_response("Say 'OK' in JSON format", format_json=True)
                results[name] = {
                    'healthy': True,
                    'response_time': provider.stats.get('average_response_time', 0)
                }
            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'error': str(e)
                }
        
        return results

# Global multi-provider AI instance
multi_provider_ai = MultiProviderAI()
