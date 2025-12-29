from typing import Dict, Any, List
import asyncio
import logging
from .base_agent import BaseAgent, AgentResult
from .technical_skills_agent import TechnicalSkillsAgent
from .experience_agent import ExperienceAgent
from .education_agent import EducationAgent
from .soft_skills_agent import SoftSkillsAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates multiple agents to analyze resumes comprehensively."""
    
    def __init__(self, model_service, config: Dict[str, Any] = None):
        self.model_service = model_service
        self.config = config or {}
        
        # Initialize all agents
        self.agents = {
            'technical_skills': TechnicalSkillsAgent(model_service, config),
            'experience': ExperienceAgent(model_service, config),
            'education': EducationAgent(model_service, config),
            'soft_skills': SoftSkillsAgent(model_service, config)
        }
        
        # Configuration
        self.max_concurrent = config.get('max_concurrent_agents', 4)
        self.timeout = config.get('agent_timeout', 60)
    
    async def analyze_resume(self, resume_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run all agents to analyze a resume comprehensively.
        
        Args:
            resume_text: The extracted text from the resume
            context: Additional context like job requirements
            
        Returns:
            Comprehensive analysis results from all agents
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Run all agents concurrently
            tasks = []
            for agent_name, agent in self.agents.items():
                task = asyncio.create_task(
                    self._run_agent_with_timeout(agent, resume_text, context)
                )
                tasks.append((agent_name, task))
            
            # Wait for all agents to complete
            results = {}
            for agent_name, task in tasks:
                try:
                    result = await task
                    results[agent_name] = result
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {str(e)}")
                    results[agent_name] = self._create_error_result(agent_name, str(e))
            
            # Calculate overall metrics
            overall_analysis = self._consolidate_results(results)
            overall_analysis['processing_time'] = asyncio.get_event_loop().time() - start_time
            
            return overall_analysis
            
        except Exception as e:
            logger.error(f"Resume analysis orchestration failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'processing_time': asyncio.get_event_loop().time() - start_time
            }
    
    async def _run_agent_with_timeout(self, agent: BaseAgent, resume_text: str, context: Dict[str, Any]) -> AgentResult:
        """Run a single agent with optional timeout protection.
        Set agent_timeout <= 0 in config to disable timeouts entirely.
        """
        try:
            # Disable timeout when configured <= 0
            if not self.timeout or self.timeout <= 0:
                return await agent.analyze(resume_text, context)
            return await asyncio.wait_for(
                agent.analyze(resume_text, context),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Agent {agent.name} timed out after {self.timeout} seconds")
            return self._create_timeout_result(agent.name)
    
    def _create_error_result(self, agent_name: str, error_message: str) -> AgentResult:
        """Create an error result for a failed agent."""
        return AgentResult(
            agent_name=agent_name,
            score=0,
            confidence=0,
            analysis={"error": error_message},
            strengths=[],
            weaknesses=[f"{agent_name} analysis failed"],
            recommendations=[f"Retry {agent_name} analysis"],
            processing_time=0,
            raw_output=f"Error: {error_message}"
        )
    
    def _create_timeout_result(self, agent_name: str) -> AgentResult:
        """Create a timeout result for an agent that timed out."""
        return AgentResult(
            agent_name=agent_name,
            score=0,
            confidence=0,
            analysis={"timeout": True},
            strengths=[],
            weaknesses=[f"{agent_name} analysis timed out"],
            recommendations=[f"Retry {agent_name} analysis with shorter timeout"],
            processing_time=self.timeout,
            raw_output="Timeout error"
        )
    
    def _consolidate_results(self, agent_results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """Consolidate results from all agents into a comprehensive analysis."""
        
        # Extract individual scores
        scores = {}
        total_score = 0
        valid_scores = 0
        
        for agent_name, result in agent_results.items():
            scores[agent_name] = {
                'score': result.score,
                'confidence': result.confidence,
                'processing_time': result.processing_time
            }
            
            if result.score > 0:  # Only count valid scores
                total_score += result.score
                valid_scores += 1
        
        # Calculate overall score
        overall_score = total_score / valid_scores if valid_scores > 0 else 0
        
        # Consolidate strengths, weaknesses, and recommendations
        all_strengths = []
        all_weaknesses = []
        all_recommendations = []
        
        for result in agent_results.values():
            all_strengths.extend(result.strengths)
            all_weaknesses.extend(result.weaknesses)
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates while preserving order
        unique_strengths = list(dict.fromkeys(all_strengths))
        unique_weaknesses = list(dict.fromkeys(all_weaknesses))
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        # Build consolidated analysis
        consolidated = {
            'status': 'completed',
            'overall_score': round(overall_score, 2),
            'agent_scores': scores,
            'summary': {
                'strengths': unique_strengths,
                'weaknesses': unique_weaknesses,
                'recommendations': unique_recommendations
            },
            'detailed_results': {
                agent_name: {
                    'score': result.score,
                    'confidence': result.confidence,
                    'analysis': result.analysis,
                    'strengths': result.strengths,
                    'weaknesses': result.weaknesses,
                    'recommendations': result.recommendations,
                    'processing_time': result.processing_time
                }
                for agent_name, result in agent_results.items()
            },
            'metadata': {
                'agents_used': list(agent_results.keys()),
                'successful_agents': len([r for r in agent_results.values() if r.score > 0]),
                'failed_agents': len([r for r in agent_results.values() if r.score == 0]),
                'average_confidence': sum(r.confidence for r in agent_results.values()) / len(agent_results),
                'total_processing_time': sum(r.processing_time for r in agent_results.values())
            }
        }
        
        return consolidated
