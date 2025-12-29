from datetime import datetime
from typing import Dict, Any, Optional
import logging
from app import db
from app.models import Resume, Analysis
from app.services.ollama_service import OllamaService
from app.services.resume_parsing_service import ResumeParsingService
from app.agents import AgentOrchestrator
import asyncio

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for managing resume analysis workflow."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.parsing_service = ResumeParsingService(
            upload_folder=self.config.get('upload_folder', 'uploads')
        )
    
    async def analyze_resume_async(self, resume_id: str, user_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Async wrapper for resume analysis - returns dict for queue processing.
        
        Args:
            resume_id: UUID of the resume to analyze
            user_id: UUID of the user requesting analysis
            context: Additional context for analysis
            
        Returns:
            Dict with analysis results and metadata
        """
        try:
            analysis = await self.analyze_resume(resume_id, context)
            
            return {
                'id': str(analysis.id),
                'status': analysis.status,
                'overall_score': analysis.overall_score,
                'scores_breakdown': analysis.scores_breakdown,
                'processing_time': analysis.processing_time,
                'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None
            }
            
        except Exception as e:
            logger.error(f"Async analysis failed for resume {resume_id}: {str(e)}")
            return {
                'id': None,
                'status': 'failed',
                'error': str(e),
                'overall_score': None,
                'scores_breakdown': None,
                'processing_time': None,
                'completed_at': datetime.utcnow().isoformat()
            }

    async def analyze_resume(self, resume_id: str, context: Dict[str, Any] = None) -> Analysis:
        """
        Perform comprehensive resume analysis using multiple agents.
        
        Args:
            resume_id: UUID of the resume to analyze
            context: Additional context for analysis (job requirements, etc.)
            
        Returns:
            Analysis object with results
        """
        # Get resume from database
        resume = Resume.query.get(resume_id)
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")
        
        # Create analysis record
        analysis = Analysis(
            resume_id=resume.id,
            analysis_type='full',
            status='processing',
            started_at=datetime.utcnow(),
            model_used=self.config.get('model', 'qwen2.5:7b')
        )
        db.session.add(analysis)
        db.session.commit()
        
        try:
            # Extract text if not already done
            if not resume.raw_text:
                resume.raw_text = self.parsing_service.extract_text(resume.file_path)
                resume.structured_data = self.parsing_service.parse_resume_structure(resume.raw_text)
                db.session.commit()
            
            # Initialize Ollama service and orchestrator
            async with OllamaService() as ollama_service:
                orchestrator = AgentOrchestrator(ollama_service, self.config)
                
                # Run analysis
                results = await orchestrator.analyze_resume(resume.raw_text, context)
                
                # Update analysis with results
                analysis.status = results.get('status', 'completed')
                analysis.overall_score = results.get('overall_score')
                analysis.scores_breakdown = results.get('agent_scores')
                
                # Store individual agent results
                detailed_results = results.get('detailed_results', {})
                analysis.technical_skills_result = detailed_results.get('technical_skills', {}).get('analysis')
                analysis.experience_result = detailed_results.get('experience', {}).get('analysis')
                analysis.education_result = detailed_results.get('education', {}).get('analysis')
                analysis.soft_skills_result = detailed_results.get('soft_skills', {}).get('analysis')
                
                # Store summary
                summary = results.get('summary', {})
                analysis.strengths = summary.get('strengths', [])
                analysis.weaknesses = summary.get('weaknesses', [])
                analysis.recommendations = summary.get('recommendations', [])
                
                # Processing metadata
                analysis.processing_time = results.get('processing_time')
                analysis.completed_at = datetime.utcnow()
                
                # Update resume status
                resume.processing_status = 'completed'
                resume.processed_at = datetime.utcnow()
                
                db.session.commit()
                
                logger.info(f"Analysis completed for resume {resume_id}: score {analysis.overall_score}")
                return analysis
                
        except Exception as e:
            # Handle analysis failure
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.completed_at = datetime.utcnow()
            
            resume.processing_status = 'failed'
            resume.error_message = str(e)
            
            db.session.commit()
            
            logger.error(f"Analysis failed for resume {resume_id}: {str(e)}")
            raise
    
    async def reanalyze_resume(self, resume_id: str, agent_types: list = None, context: Dict[str, Any] = None) -> Analysis:
        """
        Re-run analysis for specific agents or all agents.
        
        Args:
            resume_id: UUID of the resume to re-analyze
            agent_types: List of agent types to run (optional, defaults to all)
            context: Additional context for analysis
            
        Returns:
            New analysis object with results
        """
        resume = Resume.query.get(resume_id)
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")
        
        if not resume.raw_text:
            raise ValueError("Resume text not available for analysis")
        
        # Create new analysis record
        analysis = Analysis(
            resume_id=resume.id,
            analysis_type='partial' if agent_types else 'full',
            status='processing',
            started_at=datetime.utcnow(),
            model_used=self.config.get('model', 'qwen2.5:7b')
        )
        db.session.add(analysis)
        db.session.commit()
        
        try:
            async with OllamaService() as ollama_service:
                if agent_types:
                    # Run specific agents only
                    orchestrator = AgentOrchestrator(ollama_service, self.config)
                    # Filter agents based on agent_types
                    # This would require modification to orchestrator to support partial runs
                    results = await orchestrator.analyze_resume(resume.raw_text, context)
                else:
                    # Run all agents
                    orchestrator = AgentOrchestrator(ollama_service, self.config)
                    results = await orchestrator.analyze_resume(resume.raw_text, context)
                
                # Update analysis with results (same as above)
                analysis.status = results.get('status', 'completed')
                analysis.overall_score = results.get('overall_score')
                analysis.scores_breakdown = results.get('agent_scores')
                
                detailed_results = results.get('detailed_results', {})
                analysis.technical_skills_result = detailed_results.get('technical_skills', {}).get('analysis')
                analysis.experience_result = detailed_results.get('experience', {}).get('analysis')
                analysis.education_result = detailed_results.get('education', {}).get('analysis')
                analysis.soft_skills_result = detailed_results.get('soft_skills', {}).get('analysis')
                
                summary = results.get('summary', {})
                analysis.strengths = summary.get('strengths', [])
                analysis.weaknesses = summary.get('weaknesses', [])
                analysis.recommendations = summary.get('recommendations', [])
                
                analysis.processing_time = results.get('processing_time')
                analysis.completed_at = datetime.utcnow()
                
                db.session.commit()
                
                logger.info(f"Re-analysis completed for resume {resume_id}")
                return analysis
                
        except Exception as e:
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.error(f"Re-analysis failed for resume {resume_id}: {str(e)}")
            raise
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID."""
        return Analysis.query.get(analysis_id)
    
    def get_latest_analysis(self, resume_id: str) -> Optional[Analysis]:
        """Get latest analysis for a resume."""
        return Analysis.query.filter_by(resume_id=resume_id)\
                            .order_by(Analysis.created_at.desc())\
                            .first()
    
    def get_analysis_history(self, resume_id: str) -> list:
        """Get all analyses for a resume."""
        return Analysis.query.filter_by(resume_id=resume_id)\
                            .order_by(Analysis.created_at.desc())\
                            .all()
    
    def compare_analyses(self, analysis_id1: str, analysis_id2: str) -> Dict[str, Any]:
        """
        Compare two analyses and highlight differences.
        
        Args:
            analysis_id1: First analysis ID
            analysis_id2: Second analysis ID
            
        Returns:
            Comparison results
        """
        analysis1 = Analysis.query.get(analysis_id1)
        analysis2 = Analysis.query.get(analysis_id2)
        
        if not analysis1 or not analysis2:
            raise ValueError("One or both analyses not found")
        
        comparison = {
            'analysis1': {
                'id': str(analysis1.id),
                'created_at': analysis1.created_at.isoformat(),
                'overall_score': analysis1.overall_score,
                'scores_breakdown': analysis1.scores_breakdown
            },
            'analysis2': {
                'id': str(analysis2.id),
                'created_at': analysis2.created_at.isoformat(),
                'overall_score': analysis2.overall_score,
                'scores_breakdown': analysis2.scores_breakdown
            },
            'differences': {
                'score_change': analysis2.overall_score - analysis1.overall_score if analysis1.overall_score and analysis2.overall_score else None,
                'improved_areas': [],
                'declined_areas': [],
                'new_strengths': [],
                'new_weaknesses': []
            }
        }
        
        # Calculate agent score differences
        if analysis1.scores_breakdown and analysis2.scores_breakdown:
            for agent_name in analysis1.scores_breakdown:
                if agent_name in analysis2.scores_breakdown:
                    score1 = analysis1.scores_breakdown[agent_name].get('score', 0)
                    score2 = analysis2.scores_breakdown[agent_name].get('score', 0)
                    diff = score2 - score1
                    
                    if diff > 5:  # Significant improvement
                        comparison['differences']['improved_areas'].append({
                            'agent': agent_name,
                            'improvement': diff
                        })
                    elif diff < -5:  # Significant decline
                        comparison['differences']['declined_areas'].append({
                            'agent': agent_name,
                            'decline': abs(diff)
                        })
        
        return comparison
