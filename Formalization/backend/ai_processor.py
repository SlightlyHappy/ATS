"""
High-performance AI processing module optimized for bulk resume analysis.
Implements connection pooling, batch processing, and adaptive model selection.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading
from queue import Queue, Empty
import requests

# Import multi-provider AI system
from multi_provider_ai import multi_provider_ai
from agentic_resume_analyzer import AgenticResumeAnalyzer, MarketContext

logger = logging.getLogger(__name__)

class AIProcessingPool:
    """Connection pool manager for Ollama API calls."""
    
    def __init__(self, config, ollama_url: str):
        self.config = config
        self.ollama_url = ollama_url
        self.session_pool = Queue(maxsize=config.AI_CONNECTION_POOL_SIZE)
        self.lock = threading.Lock()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "cache_hits": 0
        }
        self.response_cache = {}  # Simple cache for identical prompts
        
        # Initialize connection pool
        for _ in range(config.AI_CONNECTION_POOL_SIZE):
            session = requests.Session()
            session.headers.update({
                'Content-Type': 'application/json',
                'Connection': 'keep-alive'
            })
            self.session_pool.put(session)
    
    def get_session(self) -> requests.Session:
        """Get a session from the pool."""
        try:
            return self.session_pool.get(timeout=5)
        except Empty:
            # Create new session if pool is empty
            session = requests.Session()
            session.headers.update({
                'Content-Type': 'application/json',
                'Connection': 'keep-alive'
            })
            return session
    
    def return_session(self, session: requests.Session):
        """Return session to pool."""
        try:
            self.session_pool.put(session, timeout=1)
        except:
            # Pool is full, session will be garbage collected
            pass
    
    def make_request(self, model: str, prompt: str, use_cache: bool = True) -> Dict[str, Any]:
        """Make AI request with connection pooling and caching."""
        start_time = time.time()
        
        # Check cache first
        if use_cache and self.config.ENABLE_AI_RESPONSE_CACHING:
            cache_key = f"{model}:{hash(prompt)}"
            if cache_key in self.response_cache:
                self.stats["cache_hits"] += 1
                logger.debug("Cache hit for AI request")
                return self.response_cache[cache_key]
        
        session = self.get_session()
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_ctx": 8192,  # Reduced context for faster processing
                    "repeat_penalty": 1.1
                }
            }
            
            response = session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.config.AI_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Cache successful responses
                if use_cache and self.config.ENABLE_AI_RESPONSE_CACHING:
                    cache_key = f"{model}:{hash(prompt)}"
                    self.response_cache[cache_key] = result
                    
                    # Limit cache size
                    if len(self.response_cache) > 100:
                        # Remove oldest 20% of cache entries
                        keys_to_remove = list(self.response_cache.keys())[:20]
                        for key in keys_to_remove:
                            del self.response_cache[key]
                
                self.stats["successful_requests"] += 1
                response_time = time.time() - start_time
                self._update_average_response_time(response_time)
                
                return result
            else:
                raise Exception(f"AI API error: {response.status_code}")
                
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"AI request failed: {e}")
            raise
        finally:
            self.return_session(session)
            self.stats["total_requests"] += 1
    
    def _update_average_response_time(self, response_time: float):
        """Update running average of response times."""
        with self.lock:
            if self.stats["successful_requests"] == 1:
                self.stats["average_response_time"] = response_time
            else:
                # Running average
                count = self.stats["successful_requests"]
                current_avg = self.stats["average_response_time"]
                self.stats["average_response_time"] = ((current_avg * (count - 1)) + response_time) / count

class OptimizedAIProcessor:
    """Optimized AI processor for high-volume resume analysis with agentic capabilities."""
    
    def __init__(self, config, ollama_url: str, ollama_model: str):
        self.config = config
        self.base_model = ollama_model
        self.ai_pool = AIProcessingPool(config, ollama_url)
        self.executor = ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_PROCESSING)
        self.current_ai_settings = None
        
        # Initialize agentic analyzer with AI provider
        try:
            from multi_provider_ai import EnhancedMultiProviderAI
            ai_provider = EnhancedMultiProviderAI()
            self.agentic_analyzer = AgenticResumeAnalyzer(ai_provider)
            self.agentic_available = True
        except Exception as e:
            logger.warning(f"Agentic analyzer initialization failed: {e}")
            self.agentic_analyzer = None
            self.agentic_available = False
    
    def update_ai_settings(self, ai_settings: Dict[str, Any]):
        """Update AI provider settings."""
        try:
            provider = ai_settings.get('provider')
            model = ai_settings.get('model')
            api_key = ai_settings.get('apiKey', '')
            
            if provider == 'ollama':
                multi_provider_ai.set_provider('ollama', model, base_url=self.ai_pool.ollama_url)
            elif provider == 'openai':
                multi_provider_ai.set_provider('openai', model, api_key=api_key)
            elif provider == 'gemini':
                multi_provider_ai.set_provider('gemini', model, api_key=api_key)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            self.current_ai_settings = ai_settings
            logger.info(f"AI settings updated: {provider} - {model}")
            
        except Exception as e:
            logger.error(f"Failed to update AI settings: {e}")
            raise
    
    def analyze_resume(self, markdown_content: str, role_requirements: str = "", filename: str = "") -> Dict[str, Any]:
        """Alias for process_single_resume to maintain backward compatibility."""
        return self.process_single_resume(markdown_content, filename, role_requirements)
    
    def process_single_resume(self, markdown_content: str, filename: str, 
                            role_requirements: str = "") -> Dict[str, Any]:
        """Process a single resume with enhanced agentic AI analysis."""
        logger.info(f"Starting agentic AI analysis for: {filename}")
        
        try:
            # Extract basic resume data first
            basic_data = self._extract_basic_resume_data(markdown_content, filename)
            
            # Use agentic analyzer for comprehensive analysis
            agentic_result = self.agentic_analyzer.analyze_resume(
                basic_data, role_requirements
            )
            
            # Convert agentic result to expected format
            result = self._convert_agentic_to_standard_format(agentic_result, basic_data, markdown_content)
            
            if not self._validate_ai_response(result):
                logger.warning(f"Agentic analysis validation failed for {filename}, falling back to standard analysis")
                # Fallback to original analysis if validation fails
                return self._perform_fallback_analysis(markdown_content, filename, role_requirements)
            
            logger.info(f"Agentic AI analysis completed for: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Agentic AI analysis failed for {filename}: {e}")
            logger.info(f"Falling back to standard analysis for: {filename}")
            # Fallback to original analysis
            try:
                return self._perform_fallback_analysis(markdown_content, filename, role_requirements)
            except Exception as fallback_error:
                logger.error(f"Fallback analysis also failed for {filename}: {fallback_error}")
                return self._create_minimal_response(filename, str(e))
    
    def process_batch_resumes(self, resume_data_list: List[Dict[str, Any]], 
                            role_requirements: str = "") -> List[Dict[str, Any]]:
        """Process multiple resumes with enhanced agentic analysis and comparative ranking."""
        logger.info(f"Starting agentic batch processing of {len(resume_data_list)} resumes")
        
        try:
            # Extract basic data for all resumes
            basic_data_list = []
            for resume_data in resume_data_list:
                try:
                    basic_data = self._extract_basic_resume_data(
                        resume_data['markdown_content'], 
                        resume_data['filename']
                    )
                    basic_data_list.append(basic_data)
                except Exception as e:
                    logger.error(f"Failed to extract basic data for {resume_data['filename']}: {e}")
                    # Add empty data to maintain list alignment
                    basic_data_list.append({
                        'filename': resume_data['filename'],
                        'skills': [], 'experience': [], 'education': []
                    })
            
            # Use agentic batch analysis with comparative ranking
            agentic_results = self.agentic_analyzer.analyze_batch(basic_data_list, role_requirements)
            
            # Convert results to expected format
            all_results = []
            for i, agentic_result in enumerate(agentic_results):
                try:
                    resume_data = resume_data_list[i]
                    basic_data = basic_data_list[i]
                    
                    result = self._convert_agentic_to_standard_format(
                        agentic_result, basic_data, resume_data['markdown_content']
                    )
                    all_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed to convert agentic result for {resume_data_list[i]['filename']}: {e}")
                    # Create minimal response for failed conversions
                    all_results.append(self._create_minimal_response(
                        resume_data_list[i]['filename'], str(e)
                    ))
            
            logger.info(f"Agentic batch processing completed: {len(all_results)} results")
            return all_results
            
        except Exception as e:
            logger.error(f"Agentic batch processing failed: {e}")
            logger.info("Falling back to sequential standard analysis")
            
            # Fallback to original batch processing
            return self._fallback_batch_processing(resume_data_list, role_requirements)
    
    def _select_optimal_model(self, resume_count: int) -> str:
        """Select the best model based on processing volume and system resources."""
        return self.config.get_model_for_volume(resume_count)
    
    def _process_concurrent_batch(self, batch: List[Dict[str, Any]], 
                                role_requirements: str, model: str) -> List[Dict[str, Any]]:
        """Process a batch of resumes concurrently."""
        concurrent_limit = self.config.get_concurrent_limit(len(batch))
        
        with ThreadPoolExecutor(max_workers=concurrent_limit) as executor:
            # Submit all tasks
            future_to_resume = {
                executor.submit(
                    self._perform_unified_analysis,
                    resume_data['markdown_content'],
                    resume_data['filename'],
                    role_requirements,
                    model
                ): resume_data for resume_data in batch
            }
            
            results = []
            
            # Collect results as they complete
            for future in as_completed(future_to_resume, timeout=1200):  # Increased to 20 minutes per batch for limited hardware
                resume_data = future_to_resume[future]
                
                try:
                    result = future.result()
                    if self._validate_ai_response(result):
                        results.append(result)
                    else:
                        # Create minimal response for validation failures
                        results.append(self._create_minimal_response(
                            resume_data['filename'], "Validation failed"
                        ))
                except Exception as e:
                    logger.error(f"Batch processing error for {resume_data['filename']}: {e}")
                    results.append(self._create_minimal_response(
                        resume_data['filename'], str(e)
                    ))
            
            return results
    
    def _perform_unified_analysis(self, markdown_content: str, filename: str, 
                                role_requirements: str, model: str) -> Dict[str, Any]:
        """Perform unified AI analysis in a single call for efficiency."""
        
        # Include role requirements context
        role_context = ""
        if role_requirements:
            role_context = f"""
            
JOB REQUIREMENTS CONTEXT:
{role_requirements}

ANALYSIS INSTRUCTIONS:
- Compare candidate against these specific job requirements
- Focus on role-specific scoring and fit assessment
- Provide evidence-based analysis with specific examples
            """
        
        prompt = f"""
        You are an expert resume analyzer. Analyze this resume and return comprehensive structured data in the EXACT JSON format below.

        CRITICAL REQUIREMENTS:
        1. Extract ALL information accurately
        2. Provide realistic scores (1-100)
        3. Return ONLY valid JSON
        4. Be specific and evidence-based in analysis

        Return this EXACT JSON structure:

        {{
            "basic_info": {{
                "name": "full name or null",
                "email": "email address or null",
                "phone": "phone number or null",
                "linkedin": "LinkedIn URL or null",
                "github": "GitHub URL or null",
                "location": {{"city": "city", "state": "state", "country": "country"}}
            }},
            "summary": "professional summary text or null",
            "skills": ["list of all skills mentioned"],
            "experience": [{{
                "job_title": "title",
                "company": "company name",
                "start_date": "YYYY-MM or null",
                "end_date": "YYYY-MM or null",
                "currently_working": true/false,
                "responsibilities": ["key responsibilities"]
            }}],
            "education": [{{
                "degree": "degree type and name",
                "university": "institution name",
                "graduation_year": "YYYY or null"
            }}],
            "certifications": [{{
                "certification_name": "name",
                "issuer": "organization",
                "issue_date": "YYYY-MM or null"
            }}],
            "projects": [{{
                "project_name": "name",
                "description": "brief description",
                "technologies_used": ["tech list"]
            }}],
            "keywords": ["important keywords from resume"],
            "scores": {{
                "overall_score": <1-100>,
                "technical_skills_score": <1-100>,
                "experience_score": <1-100>,
                "education_score": <1-100>,
                "communication_score": <1-100>,
                "leadership_score": <1-100>,
                "role_fit_score": <1-100>,
                "confidence_level": <1-100>
            }},
            "analysis": {{
                "experience_level": "Junior/Mid/Senior/Expert",
                "specialization_focus": "primary expertise area",
                "strengths": ["key strengths with evidence"],
                "weaknesses": ["areas for improvement"],
                "career_trajectory": "assessment of career progression"
            }},
            "role_match": {{
                "requirements_match_percentage": <0-100>,
                "critical_requirements_met": ["satisfied requirements"],
                "missing_requirements": ["unmet requirements"],
                "role_fit_rationale": "explanation of fit"
            }},
            "recommendations": {{
                "hiring_decision": "Strong Hire/Hire/Maybe/Pass",
                "decision_confidence": "High/Medium/Low",
                "key_decision_factors": ["top 3 factors"],
                "interview_focus_areas": ["areas to probe"]
            }},
            "executive_summary": "2-3 sentence summary for hiring manager",
            "raw_text": "complete resume text for reference"
        }}

        {role_context}

        RESUME TO ANALYZE:
        {markdown_content}

        Return ONLY the JSON structure above with ALL fields populated.
        """
        
        try:
            # Use multi-provider AI system if available, otherwise fallback to Ollama
            if self.current_ai_settings:
                response = multi_provider_ai.generate_response(prompt, format_json=True)
                result = response if isinstance(response, dict) else json.loads(response['response'])
            else:
                # Fallback to original Ollama system
                response = self.ai_pool.make_request(model, prompt, use_cache=True)
                result = json.loads(response['response'])
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}")
            raise ValueError(f"AI returned invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"AI analysis request failed: {e}")
            raise
    
    def _validate_ai_response(self, ai_response: Dict[str, Any]) -> bool:
        """Validate AI response structure and content."""
        required_fields = [
            "basic_info", "skills", "experience", "education", 
            "scores", "analysis", "role_match", "recommendations"
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in ai_response:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate scores are numeric and in range
        scores = ai_response.get("scores", {})
        for score_name, score_value in scores.items():
            if not isinstance(score_value, (int, float)) or not (0 <= score_value <= 100):
                logger.error(f"Invalid score {score_name}: {score_value}")
                return False
        
        # Check for placeholder responses
        invalid_indicators = ["unknown", "not found", "placeholder", "ai unavailable"]
        
        def contains_placeholder(obj):
            if isinstance(obj, str):
                return any(indicator in obj.lower() for indicator in invalid_indicators)
            elif isinstance(obj, dict):
                return any(contains_placeholder(v) for v in obj.values())
            elif isinstance(obj, list):
                return any(contains_placeholder(item) for item in obj)
            return False
        
        if contains_placeholder(ai_response):
            logger.error("AI response contains placeholder values")
            return False
        
        return True
    
    def _create_minimal_response(self, filename: str, error_message: str) -> Dict[str, Any]:
        """Create minimal response structure for failed processing."""
        return {
            "basic_info": {
                "name": f"Error processing {filename}",
                "email": None,
                "phone": None,
                "linkedin": None,
                "github": None,
                "location": {"city": None, "state": None, "country": None}
            },
            "summary": f"Processing failed: {error_message}",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "projects": [],
            "keywords": [],
            "scores": {
                "overall_score": 0,
                "technical_skills_score": 0,
                "experience_score": 0,
                "education_score": 0,
                "communication_score": 0,
                "leadership_score": 0,
                "role_fit_score": 0,
                "confidence_level": 0
            },
            "analysis": {
                "experience_level": "Unknown",
                "specialization_focus": "Error in processing",
                "strengths": ["Manual review required"],
                "weaknesses": ["Processing failed"],
                "career_trajectory": "Unable to analyze"
            },
            "role_match": {
                "requirements_match_percentage": 0,
                "critical_requirements_met": [],
                "missing_requirements": ["Manual review required"],
                "role_fit_rationale": "Analysis failed - manual review needed"
            },
            "recommendations": {
                "hiring_decision": "Manual Review Required",
                "decision_confidence": "Low",
                "key_decision_factors": ["Processing error occurred"],
                "interview_focus_areas": ["Verify resume content manually"]
            },
            "executive_summary": f"Resume processing failed for {filename}. Manual review required.",
            "raw_text": f"Error: {error_message}",
            "processing_error": True,
            "error_message": error_message
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "ai_pool_stats": self.ai_pool.stats,
            "cache_size": len(self.ai_pool.response_cache),
            "active_threads": self.executor._threads and len(self.executor._threads) or 0
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.executor.shutdown(wait=True)
        # Clear cache
        self.ai_pool.response_cache.clear()
    
    # === AGENTIC ANALYSIS HELPER METHODS ===
    
    def _extract_basic_resume_data(self, markdown_content: str, filename: str) -> Dict[str, Any]:
        """Extract basic resume data for agentic analysis."""
        
        # Use a lightweight AI call to extract structured data
        prompt = f"""
        Extract basic structured data from this resume for further analysis:
        
        {markdown_content}
        
        Return ONLY valid JSON in this exact format:
        {{
            "filename": "{filename}",
            "basic_info": {{
                "name": "full name or null",
                "email": "email or null",
                "phone": "phone or null",
                "linkedin": "LinkedIn URL or null", 
                "github": "GitHub URL or null",
                "location": {{"city": "city", "state": "state", "country": "country"}}
            }},
            "skills": ["list of all skills"],
            "experience": [{{
                "job_title": "title",
                "company": "company",
                "start_date": "YYYY-MM or null",
                "end_date": "YYYY-MM or null",
                "currently_working": true/false,
                "responsibilities": ["key responsibilities"]
            }}],
            "education": [{{
                "degree": "degree",
                "university": "university", 
                "graduation_year": "YYYY or null"
            }}],
            "certifications": [{{
                "certification_name": "name",
                "issuer": "issuer",
                "issue_date": "YYYY-MM or null"
            }}],
            "projects": [{{
                "project_name": "name",
                "description": "description",
                "technologies_used": ["tech list"]
            }}]
        }}
        """
        
        try:
            response = multi_provider_ai.generate_response(prompt, format_json=True)
            return response
        except Exception as e:
            logger.error(f"Failed to extract basic resume data: {e}")
            # Return minimal structure
            return {
                "filename": filename,
                "basic_info": {"name": None, "email": None, "phone": None, 
                             "linkedin": None, "github": None, 
                             "location": {"city": None, "state": None, "country": None}},
                "skills": [],
                "experience": [],
                "education": [],
                "certifications": [],
                "projects": []
            }
    
    def _convert_agentic_to_standard_format(self, agentic_result: Dict, 
                                           basic_data: Dict, markdown_content: str) -> Dict[str, Any]:
        """Convert agentic analysis result to standard format expected by the application."""
        
        scores = agentic_result.get('scores', {})
        analysis_data = agentic_result.get('analysis', {})
        
        # Extract agent results for detailed analysis
        agent_results = analysis_data.get('agent_results', [])
        
        # Build comprehensive analysis from agent results
        detailed_analysis = {}
        role_match = {}
        recommendations = {}
        
        for agent_result in agent_results:
            agent_name = agent_result.get('agent', '')
            agent_analysis = agent_result.get('analysis', {})
            
            if 'Skills Validator' in agent_name:
                detailed_analysis.update({
                    'specialization_focus': self._extract_specialization(basic_data.get('skills', [])),
                    'strengths': agent_analysis.get('strengths', []),
                    'weaknesses': agent_analysis.get('questionable_skills', [])
                })
                
            elif 'Experience Assessor' in agent_name:
                detailed_analysis.update({
                    'experience_level': agent_analysis.get('experience_level_assessment', 'Unknown'),
                    'career_trajectory': agent_analysis.get('career_progression_analysis', {}).get('progression_pattern', 'Unknown')
                })
                
            elif 'Role Fit Analyzer' in agent_name:
                role_match.update({
                    'requirements_match_percentage': agent_analysis.get('requirements_match_percentage', 0),
                    'critical_requirements_met': agent_analysis.get('must_have_requirements', {}).get('met', []),
                    'missing_requirements': agent_analysis.get('must_have_requirements', {}).get('missing', []),
                    'role_fit_rationale': agent_analysis.get('adaptation_potential', 'Analysis pending')
                })
                
                recommendations.update({
                    'interview_focus_areas': agent_analysis.get('interview_focus_areas', [])
                })
        
        # Generate hiring decision based on overall score
        overall_score = scores.get('overall_score', 0)
        if overall_score >= 75:
            hiring_decision = "Strong Hire"
            decision_confidence = "High"
        elif overall_score >= 60:
            hiring_decision = "Hire"
            decision_confidence = "Medium"
        elif overall_score >= 45:
            hiring_decision = "Conditional"
            decision_confidence = "Medium"
        else:
            hiring_decision = "No Hire"
            decision_confidence = "High"
        
        recommendations.update({
            'hiring_decision': hiring_decision,
            'decision_confidence': decision_confidence,
            'key_decision_factors': agentic_result.get('strengths', [])[:3]
        })
        
        # Build the standard format expected by the application
        return {
            "basic_info": basic_data.get('basic_info', {}),
            "summary": self._generate_summary_from_analysis(agentic_result, basic_data),
            "skills": basic_data.get('skills', []),
            "experience": basic_data.get('experience', []),
            "education": basic_data.get('education', []),
            "certifications": basic_data.get('certifications', []),
            "projects": basic_data.get('projects', []),
            "keywords": self._extract_keywords(basic_data),
            "scores": {
                "overall_score": scores.get('overall_score', 0),
                "technical_skills_score": scores.get('technical_skills', 0),
                "experience_score": scores.get('experience', 0),
                "education_score": self._calculate_education_score(basic_data.get('education', [])),
                "communication_score": self._calculate_communication_score(basic_data),
                "leadership_score": self._calculate_leadership_score(basic_data),
                "role_fit_score": scores.get('role_fit', 0),
                "confidence_level": scores.get('confidence_level', 70)
            },
            "analysis": {
                "experience_level": detailed_analysis.get('experience_level', 'Unknown'),
                "specialization_focus": detailed_analysis.get('specialization_focus', 'General'),
                "strengths": agentic_result.get('strengths', []),
                "weaknesses": detailed_analysis.get('weaknesses', []),
                "career_trajectory": detailed_analysis.get('career_trajectory', 'Unknown')
            },
            "role_match": role_match,
            "recommendations": recommendations,
            "executive_summary": agentic_result.get('executive_summary', 'Analysis completed.'),
            "raw_text": markdown_content,
            "processing_error": False,
            "market_percentile": scores.get('market_percentile', 50),
            "agentic_analysis": True  # Flag to indicate enhanced analysis
        }
    
    def _perform_fallback_analysis(self, markdown_content: str, filename: str, role_requirements: str) -> Dict[str, Any]:
        """Perform fallback analysis using the original method."""
        model = self._select_optimal_model(1)
        return self._perform_unified_analysis(markdown_content, filename, role_requirements, model)
    
    def _fallback_batch_processing(self, resume_data_list: List[Dict[str, Any]], role_requirements: str) -> List[Dict[str, Any]]:
        """Fallback batch processing using original method."""
        model = self._select_optimal_model(len(resume_data_list))
        batch_size = self.config.CHUNK_SIZE
        all_results = []
        
        for i in range(0, len(resume_data_list), batch_size):
            batch = resume_data_list[i:i + batch_size]
            batch_results = self._process_concurrent_batch(batch, role_requirements, model)
            all_results.extend(batch_results)
            
            if i + batch_size < len(resume_data_list):
                time.sleep(1)
        
        return all_results
    
    def _extract_specialization(self, skills: List[str]) -> str:
        """Extract specialization focus from skills."""
        if not skills:
            return "General"
        
        skill_categories = {
            "frontend": ["react", "vue", "angular", "javascript", "html", "css"],
            "backend": ["python", "java", "node.js", "express", "django", "spring"],
            "data": ["sql", "python", "r", "tableau", "analytics", "machine learning"],
            "cloud": ["aws", "azure", "gcp", "docker", "kubernetes"],
            "mobile": ["ios", "android", "react native", "flutter"]
        }
        
        skill_scores = {category: 0 for category in skill_categories}
        
        for skill in skills:
            skill_lower = skill.lower()
            for category, category_skills in skill_categories.items():
                if any(cat_skill in skill_lower for cat_skill in category_skills):
                    skill_scores[category] += 1
        
        if max(skill_scores.values()) > 0:
            return max(skill_scores, key=skill_scores.get).title()
        return "General"
    
    def _generate_summary_from_analysis(self, agentic_result: Dict, basic_data: Dict) -> str:
        """Generate professional summary from agentic analysis."""
        experience = basic_data.get('experience', [])
        skills = basic_data.get('skills', [])
        strengths = agentic_result.get('strengths', [])
        
        if not experience and not skills:
            return "Professional summary unavailable due to limited resume data."
        
        summary_parts = []
        
        if experience:
            years_exp = len(experience) * 2  # Rough estimate
            if experience[0].get('job_title'):
                summary_parts.append(f"Experienced {experience[0]['job_title']} with {years_exp}+ years")
        
        if skills:
            top_skills = skills[:5]
            summary_parts.append(f"skilled in {', '.join(top_skills)}")
        
        if strengths:
            summary_parts.append(f"Strong background in {', '.join(strengths[:2])}")
        
        return ". ".join(summary_parts) + "." if summary_parts else "Professional with diverse experience."
    
    def _extract_keywords(self, basic_data: Dict) -> List[str]:
        """Extract important keywords from resume data."""
        keywords = set()
        
        # Add skills as keywords
        keywords.update(basic_data.get('skills', []))
        
        # Add job titles
        for exp in basic_data.get('experience', []):
            if exp.get('job_title'):
                keywords.add(exp['job_title'])
        
        # Add companies (top-tier companies are valuable keywords)
        notable_companies = {'google', 'microsoft', 'amazon', 'apple', 'meta', 'netflix'}
        for exp in basic_data.get('experience', []):
            company = exp.get('company', '').lower()
            if any(notable in company for notable in notable_companies):
                keywords.add(exp.get('company', ''))
        
        return list(keywords)[:20]  # Limit to top 20 keywords
    
    def _calculate_education_score(self, education: List[Dict]) -> float:
        """Calculate education score based on degrees."""
        if not education:
            return 40
        
        degree_scores = {
            'phd': 95, 'doctorate': 95, 'md': 90,
            'master': 80, 'mba': 85, 'ms': 80, 'ma': 75,
            'bachelor': 70, 'bs': 70, 'ba': 70,
            'associate': 60, 'diploma': 50
        }
        
        max_score = 40
        for edu in education:
            degree = edu.get('degree', '').lower()
            for degree_type, score in degree_scores.items():
                if degree_type in degree:
                    max_score = max(max_score, score)
                    break
        
        return min(max_score, 85)  # Cap at 85 to maintain realistic distribution
    
    def _calculate_communication_score(self, basic_data: Dict) -> float:
        """Calculate communication score based on resume quality and content."""
        score = 50  # Base score
        
        # Check for clear, well-structured experience descriptions
        experience = basic_data.get('experience', [])
        if experience:
            for exp in experience:
                responsibilities = exp.get('responsibilities', [])
                if responsibilities and len(responsibilities) > 2:
                    score += 5
                    if any(len(resp) > 50 for resp in responsibilities):  # Detailed descriptions
                        score += 5
        
        # Check for projects with clear descriptions
        projects = basic_data.get('projects', [])
        if projects:
            for project in projects:
                if project.get('description') and len(project['description']) > 30:
                    score += 3
        
        return min(score, 80)  # Cap communication score
    
    def _calculate_leadership_score(self, basic_data: Dict) -> float:
        """Calculate leadership score based on experience and responsibilities."""
        score = 30  # Base score
        
        leadership_keywords = ['lead', 'manage', 'director', 'senior', 'principal', 'architect', 'head of']
        
        experience = basic_data.get('experience', [])
        for exp in experience:
            job_title = exp.get('job_title', '').lower()
            if any(keyword in job_title for keyword in leadership_keywords):
                score += 15
            
            responsibilities = exp.get('responsibilities', [])
            for resp in responsibilities:
                resp_lower = resp.lower()
                if any(keyword in resp_lower for keyword in ['manage', 'lead', 'mentor', 'coordinate']):
                    score += 5
        
        return min(score, 85)  # Cap leadership score
