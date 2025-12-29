"""
Enhanced AI Integration System
Handles resume analysis using multi-provider AI with market-based scoring
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import enhanced systems
from multi_provider_ai import multi_provider_ai
from market_scoring import market_scoring
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAIAnalyzer:
    """Enhanced AI-powered resume analysis with multi-provider support"""
    
    def __init__(self):
        """Initialize enhanced AI analyzer"""
        self.multi_ai = multi_provider_ai
        self.market_scorer = market_scoring
        self.enable_market_scoring = config.ENABLE_MARKET_SCORING
        self.enable_agentic_analysis = config.ENABLE_AGENTIC_ANALYSIS
        
        logger.info("Enhanced AI Analyzer initialized with multi-provider support")
    
    async def analyze_resume(self, resume_content: str, job_context: str = None, 
                           preferred_provider: str = None) -> Dict[str, Any]:
        """Analyze resume with enhanced AI and market-based scoring"""
        try:
            # Use multi-provider AI for analysis
            ai_result = await self.multi_ai.analyze_resume(
                resume_content, 
                preferred_provider=preferred_provider
            )
            
            if not ai_result['success']:
                return ai_result
            
            analysis = ai_result['analysis']
            
            # Apply market-based scoring if enabled
            if self.enable_market_scoring:
                analysis = self.market_scorer.calculate_realistic_score(
                    analysis, 
                    role_context=job_context
                )
            
            # Enhanced analysis metadata
            analysis['_meta'] = {
                'provider_used': ai_result.get('provider_used'),
                'processing_time': ai_result.get('processing_time', 0),
                'analysis_timestamp': datetime.now().isoformat(),
                'market_scoring_enabled': self.enable_market_scoring,
                'agentic_analysis_enabled': self.enable_agentic_analysis,
                'version': '2.0'
            }
            
            return {
                'success': True,
                'analysis': analysis,
                'provider_used': ai_result.get('provider_used'),
                'processing_time': ai_result.get('processing_time', 0)
            }
            
        except Exception as e:
            logger.error(f"Enhanced analysis error: {str(e)}")
            return {
                'success': False,
                'error': f"Analysis failed: {str(e)}",
                'analysis': None
            }
    
    async def batch_analyze_resumes(self, resume_data_list: List[Dict[str, Any]], 
                                  job_context: str = None) -> List[Dict[str, Any]]:
        """Analyze multiple resumes with batch optimization"""
        try:
            results = []
            
            # Process resumes based on batch configuration
            if config.ENABLE_BATCH_PROCESSING and len(resume_data_list) >= config.BATCH_ANALYSIS_THRESHOLD:
                logger.info(f"Processing {len(resume_data_list)} resumes in batch mode")
                
                # Batch processing with optimal provider selection
                provider = config.get_model_for_volume(len(resume_data_list))
                
                for resume_data in resume_data_list:
                    result = await self.analyze_resume(
                        resume_data['content'],
                        job_context=job_context,
                        preferred_provider='ollama'  # Use Ollama for batch processing
                    )
                    result['filename'] = resume_data.get('filename', 'unknown')
                    results.append(result)
            else:
                # Individual processing
                for resume_data in resume_data_list:
                    result = await self.analyze_resume(
                        resume_data['content'],
                        job_context=job_context
                    )
                    result['filename'] = resume_data.get('filename', 'unknown')
                    results.append(result)
            
            # Apply comparative ranking if market scoring is enabled
            if self.enable_market_scoring and len(results) > 1:
                successful_results = [r for r in results if r['success']]
                if successful_results:
                    analyses = [r['analysis'] for r in successful_results]
                    ranked_analyses = self.market_scorer.rank_candidates(analyses)
                    
                    # Update results with ranking
                    for i, result in enumerate(successful_results):
                        if i < len(ranked_analyses):
                            result['analysis'] = ranked_analyses[i]
            
            return results
            
        except Exception as e:
            logger.error(f"Batch analysis error: {str(e)}")
            return [{'success': False, 'error': str(e), 'analysis': None} for _ in resume_data_list]
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all AI providers"""
        return self.multi_ai.get_provider_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on AI systems"""
        try:
            # Check multi-provider AI health
            provider_health = self.multi_ai.health_check()
            
            # Check market scoring system
            market_scoring_healthy = True
            try:
                # Test market scoring with dummy data
                test_analysis = {
                    'basic_info': {'name': 'Test'},
                    'skills': ['python', 'javascript'],
                    'experience': [{'title': 'Developer', 'company': 'Test Co'}],
                    'scores': {'overall_score': 75}
                }
                self.market_scorer.calculate_realistic_score(test_analysis)
            except Exception as e:
                market_scoring_healthy = False
                logger.error(f"Market scoring health check failed: {str(e)}")
            
            return {
                'overall_healthy': any(p['healthy'] for p in provider_health.values()),
                'providers': provider_health,
                'market_scoring_healthy': market_scoring_healthy,
                'features': {
                    'multi_provider_ai': True,
                    'market_based_scoring': self.enable_market_scoring,
                    'agentic_analysis': self.enable_agentic_analysis,
                    'batch_processing': config.ENABLE_BATCH_PROCESSING
                }
            }
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return {
                'overall_healthy': False,
                'error': str(e)
            }

# Global enhanced AI analyzer instance
ai_analyzer = EnhancedAIAnalyzer()
