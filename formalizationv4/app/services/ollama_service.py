import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional
from app.config import Config

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with Ollama API."""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self.model = model or Config.OLLAMA_MODEL
        self.timeout = Config.OLLAMA_TIMEOUT
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        # If AI_TIMEOUT (Config.OLLAMA_TIMEOUT) <= 0, disable aiohttp total timeout
        total_timeout = None if not self.timeout or self.timeout <= 0 else self.timeout
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=total_timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def generate(self, 
                      prompt: str, 
                      model: str = None,
                      temperature: float = 0.3,
                      max_tokens: int = 2000,
                      system_prompt: str = None) -> str:
        """
        Generate text using Ollama API.
        
        Args:
            prompt: The input prompt
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            Generated text response
        """
        if not self.session:
            raise RuntimeError("OllamaService must be used as async context manager")
        
        model = model or self.model
        
        # Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
                
                result = await response.json()
                return result.get("response", "")
                
        except asyncio.TimeoutError:
            logger.error(f"Ollama request timed out after {self.timeout} seconds")
            raise Exception("Request timed out")
        except Exception as e:
            logger.error(f"Ollama API call failed: {str(e)}")
            raise
    
    async def chat(self, 
                   messages: list,
                   model: str = None,
                   temperature: float = 0.3,
                   max_tokens: int = 2000) -> str:
        """
        Chat completion using Ollama API.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Assistant's response content
        """
        if not self.session:
            raise RuntimeError("OllamaService must be used as async context manager")
        
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama chat API error {response.status}: {error_text}")
                
                result = await response.json()
                return result.get("message", {}).get("content", "")
                
        except asyncio.TimeoutError:
            logger.error(f"Ollama chat request timed out after {self.timeout} seconds")
            raise Exception("Chat request timed out")
        except Exception as e:
            logger.error(f"Ollama chat API call failed: {str(e)}")
            raise
    
    async def list_models(self) -> list:
        """
        List available models in Ollama.
        
        Returns:
            List of available model names
        """
        if not self.session:
            raise RuntimeError("OllamaService must be used as async context manager")
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to list models {response.status}: {error_text}")
                
                result = await response.json()
                return [model["name"] for model in result.get("models", [])]
                
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {str(e)}")
            raise
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        if not self.session:
            raise RuntimeError("OllamaService must be used as async context manager")
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception:
            return False
