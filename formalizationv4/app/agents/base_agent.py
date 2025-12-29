from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentResult:
    """Standard result format for all agents."""
    agent_name: str
    score: float  # 0-100
    confidence: float  # 0-1
    analysis: Dict[str, Any]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    processing_time: float
    raw_output: str

class BaseAgent(ABC):
    """Abstract base class for all resume analysis agents."""
    
    def __init__(self, name: str, model_service, config: Dict[str, Any] = None):
        self.name = name
        self.model_service = model_service
        self.config = config or {}
        self.version = "1.0"
    
    @abstractmethod
    async def analyze(self, resume_text: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        Analyze the resume and return structured results.
        
        Args:
            resume_text: The extracted text from the resume
            context: Additional context like job requirements, preferences
            
        Returns:
            AgentResult with analysis findings
        """
        pass
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """Return the prompt template for this agent."""
        pass
    
    def _build_prompt(self, resume_text: str, context: Dict[str, Any] = None) -> str:
        """Build the complete prompt for analysis."""
        template = self.get_prompt_template()
        context = context or {}
        
        return template.format(
            resume_text=resume_text,
            agent_name=self.name,
            **context
        )
    
    async def _call_model(self, prompt: str) -> str:
        """Call the language model with the prepared prompt."""
        try:
            response = await self.model_service.generate(
                prompt=prompt,
                model=self.config.get('model', 'qwen2.5:7b'),
                temperature=self.config.get('temperature', 0.3),
                max_tokens=self.config.get('max_tokens', 2000)
            )
            return response
        except Exception as e:
            logger.error(f"Model call failed for agent {self.name}: {str(e)}")
            raise
    
    def _parse_model_response(self, response: str) -> Dict[str, Any]:
        """Parse the model response into structured data."""
        # This should be implemented by each agent based on their expected output format
        # For now, return a basic structure
        return {
            "raw_analysis": response,
            "parsed": True
        }
    
    def _calculate_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate a numerical score from the analysis."""
        # Default implementation - should be overridden by specific agents
        return 75.0
    
    def _extract_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract strengths from the analysis."""
        # Default implementation - should be overridden
        return []
    
    def _extract_weaknesses(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract weaknesses from the analysis."""
        # Default implementation - should be overridden
        return []
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations."""
        # Default implementation - should be overridden
        return []
