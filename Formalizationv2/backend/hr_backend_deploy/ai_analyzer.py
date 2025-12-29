"""
Enhanced AI Integration System
Handles resume analysis using multi-provider AI with market-based scoring
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
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
    {
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Start-End dates",
      "description": "Brief description of role and responsibilities"
    }
  ],
  "education": [
    {
      "degree": "Degree/Certification",
      "institution": "Institution name",
      "year": "Graduation year or duration"
    }
  ],
  "certifications": ["certification1", "certification2"],
  "projects": [
    {
      "name": "Project Name",
      "description": "Project description",
      "technologies": ["tech1", "tech2"]
    }
  ],
  "scores": {
    "overall_score": 85,
    "technical_score": 90,
    "experience_score": 80,
    "education_score": 85,
    "skills_match": 75
  },
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "analysis": {
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2"],
    "recommendations": ["recommendation1", "recommendation2"]
  },
  "role_match": {
    "fit_percentage": 85,
    "matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "experience_relevance": "High/Medium/Low"
  }
}

Provide only the JSON response, no additional text.
"""
    
    async def analyze_resume(self, resume_text: str, job_description: str = "") -> Dict[str, Any]:
        """Analyze resume text and return structured analysis"""
        try:
            # For now, return a mock analysis since Ollama isn't deployed yet
            # TODO: Replace with actual Ollama integration when deployed
            
            analysis = await self._generate_mock_analysis(resume_text)
            
            # If Ollama becomes available, use this:
            # analysis = await self._analyze_with_ollama(resume_text, job_description)
            
            return {
                'success': True,
                'analysis': analysis,
                'processing_time': 2.5,  # Mock processing time
                'model_used': self.ollama_model,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Resume analysis error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _analyze_with_ollama(self, resume_text: str, job_description: str = "") -> Dict[str, Any]:
        """Analyze resume using Ollama (for future integration)"""
        try:
            # Prepare prompt
            prompt = self.analysis_prompt.format(resume_text=resume_text)
            
            # Add job description context if provided
            if job_description:
                prompt += f"\n\nJob Description for Matching:\n{job_description}"
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_ctx": 8192
                    }
                },
                timeout=self.ai_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '')
                
                # Parse JSON response
                try:
                    analysis = json.loads(analysis_text)
                    return analysis
                except json.JSONDecodeError:
                    # If JSON parsing fails, return error
                    return self._generate_fallback_analysis(resume_text)
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._generate_fallback_analysis(resume_text)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama connection error: {str(e)}")
            return self._generate_fallback_analysis(resume_text)
        except Exception as e:
            logger.error(f"Ollama analysis error: {str(e)}")
            return self._generate_fallback_analysis(resume_text)
    
    async def _generate_mock_analysis(self, resume_text: str) -> Dict[str, Any]:
        """Generate mock analysis for testing (temporary)"""
        # Extract basic info using simple parsing
        lines = resume_text.split('\n')
        text_lower = resume_text.lower()
        
        # Try to extract name (first meaningful line)
        name = "Unknown"
        for line in lines[:5]:
            line = line.strip()
            if line and len(line.split()) <= 4 and not any(char.isdigit() for char in line):
                name = line
                break
        
        # Try to extract email
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, resume_text)
        email = email_match.group() if email_match else ""
        
        # Try to extract phone
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        phone_match = re.search(phone_pattern, resume_text)
        phone = phone_match.group() if phone_match else ""
        
        # Generate skills based on common keywords
        all_skills = [
            'Python', 'JavaScript', 'Java', 'C++', 'React', 'Node.js', 'SQL', 'MongoDB',
            'AWS', 'Docker', 'Kubernetes', 'Git', 'Linux', 'HTML', 'CSS', 'Angular',
            'Vue.js', 'TypeScript', 'Go', 'Rust', 'Swift', 'Kotlin', 'Flutter',
            'Machine Learning', 'Data Science', 'AI', 'Deep Learning', 'TensorFlow',
            'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn', 'Project Management',
            'Agile', 'Scrum', 'DevOps', 'CI/CD', 'Microservices', 'REST API',
            'GraphQL', 'Redis', 'PostgreSQL', 'MySQL', 'Firebase', 'Azure', 'GCP'
        ]
        
        found_skills = [skill for skill in all_skills if skill.lower() in text_lower][:10]
        
        return {
            "basic_info": {
                "name": name,
                "email": email,
                "phone": phone,
                "location": ""
            },
            "summary": f"Professional candidate with experience in {', '.join(found_skills[:3]) if found_skills else 'various technologies'}. Demonstrates strong technical skills and professional background.",
            "skills": found_skills[:8] if found_skills else ["Communication", "Teamwork", "Problem Solving"],
            "experience": [
                {
                    "title": "Software Developer",
                    "company": "Technology Company",
                    "duration": "2020-Present",
                    "description": "Developed and maintained software applications using modern technologies"
                }
            ],
            "education": [
                {
                    "degree": "Bachelor's Degree",
                    "institution": "University",
                    "year": "2020"
                }
            ],
            "certifications": [],
            "projects": [],
            "scores": {
                "overall_score": min(85, 60 + len(found_skills) * 3),
                "technical_score": min(90, 70 + len(found_skills) * 2),
                "experience_score": 80,
                "education_score": 75,
                "skills_match": min(85, 50 + len(found_skills) * 4)
            },
            "keywords": found_skills[:5] if found_skills else ["professional", "experience", "skills"],
            "analysis": {
                "strengths": [
                    f"Strong technical skills in {', '.join(found_skills[:2])}" if found_skills else "Professional background",
                    "Well-structured resume",
                    "Clear presentation of information"
                ],
                "weaknesses": [
                    "Could benefit from more specific achievements",
                    "Consider adding quantifiable results"
                ],
                "recommendations": [
                    "Add specific metrics and achievements",
                    "Include relevant certifications",
                    "Highlight leadership experience"
                ]
            },
            "role_match": {
                "fit_percentage": min(85, 60 + len(found_skills) * 3),
                "matching_skills": found_skills[:4] if found_skills else [],
                "missing_skills": ["Cloud Architecture", "System Design"] if found_skills else ["Technical Skills"],
                "experience_relevance": "High" if len(found_skills) > 5 else "Medium"
            }
        }
    
    def _generate_fallback_analysis(self, resume_text: str) -> Dict[str, Any]:
        """Generate basic fallback analysis when AI fails"""
        return {
            "basic_info": {
                "name": "Unable to extract",
                "email": "",
                "phone": "",
                "location": ""
            },
            "summary": "Resume analysis unavailable due to AI service error. Please try again later.",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "projects": [],
            "scores": {
                "overall_score": 0,
                "technical_score": 0,
                "experience_score": 0,
                "education_score": 0,
                "skills_match": 0
            },
            "keywords": [],
            "analysis": {
                "strengths": ["Analysis unavailable"],
                "weaknesses": ["Analysis unavailable"],
                "recommendations": ["Please try again later"]
            },
            "role_match": {
                "fit_percentage": 0,
                "matching_skills": [],
                "missing_skills": [],
                "experience_relevance": "Unknown"
            }
        }
    
    async def check_ai_service_health(self) -> Dict[str, Any]:
        """Check if AI service is available"""
        try:
            # For now, return mock health status
            # TODO: Replace with actual Ollama health check when deployed
            
            return {
                'status': 'mock_mode',
                'service': 'available',
                'model': self.ollama_model,
                'url': self.ollama_url,
                'note': 'Currently using mock analysis. Ollama integration ready for deployment.'
            }
            
            # When Ollama is available, use this:
            # response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            # if response.status_code == 200:
            #     return {
            #         'status': 'healthy',
            #         'service': 'available',
            #         'model': self.ollama_model,
            #         'models': response.json().get('models', [])
            #     }
            # else:
            #     return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
            
        except Exception as e:
            logger.error(f"AI service health check error: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'service': 'unavailable'
            }

# Singleton instance
ai_analyzer = AIAnalyzer()
