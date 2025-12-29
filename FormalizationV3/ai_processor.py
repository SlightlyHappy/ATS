"""
AI Processor Module
Enhanced with agentic resume analysis capabilities, premium routing, and backward compatibility
Phase 2: Premium AI routing for paid users
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import uuid

# Import configuration
from config import Config

# Safe imports with fallback handling
try:
    import requests
except ImportError:
    requests = None

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from modules.agentic_ai.enhanced_agentic_processor import EnhancedAgenticResumeProcessor
except ImportError:
    EnhancedAgenticResumeProcessor = None

try:
    from modules.agentic_ai.agentic_resume_analyzer import AgenticResumeAnalyzer
except ImportError:
    AgenticResumeAnalyzer = None

try:
    from modules.enhanced_ai.multi_provider_ai import MultiProviderAI
except ImportError:
    MultiProviderAI = None

try:
    from modules.enhanced_ai.market_config import MarketDataProvider
except ImportError:
    MarketDataProvider = None

try:
    from modules.hr_legal_rag.hr_legal_rag import get_rag_system, query_hr_legal
except ImportError:
    get_rag_system = None
    query_hr_legal = None

# CPU optimization for Railway Pro
try:
    from cpu_optimizer import cache_response, get_cached_response, cpu_optimizer
except ImportError:
    # Fallback functions if cpu_optimizer not available
    def cache_response(key, response): pass
    def get_cached_response(key): return None
    cpu_optimizer = None

logger = logging.getLogger(__name__)

class PremiumAIRouter:
    """Premium AI routing for paid users - Phase 2 Implementation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize premium AI providers
        self._initialize_premium_providers()
    
    def _initialize_premium_providers(self):
        """Initialize premium AI providers (OpenAI, Anthropic)"""
        try:
            # Initialize OpenAI
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key != 'your-openai-api-key-here' and openai:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized for premium users")
            
            # Initialize Anthropic
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_key and anthropic_key != 'your-anthropic-api-key-here' and anthropic:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized for premium users")
                
        except Exception as e:
            logger.error(f"Failed to initialize premium AI providers: {e}")
    
    async def route_premium_resume_analysis(self, resume_text: str, job_requirements: Dict[str, Any], 
                                          processing_tier: str = "free_trial") -> Dict[str, Any]:
        """Route resume analysis to appropriate AI provider based on user tier"""
        try:
            if processing_tier in ["premium_instant", "queue_skip", "enterprise"]:
                # Use premium AI providers for paid users
                if self.openai_client:
                    return await self._openai_resume_analysis(resume_text, job_requirements)
                elif self.anthropic_client:
                    return await self._anthropic_resume_analysis(resume_text, job_requirements)
                else:
                    logger.warning("Premium AI providers not available, falling back to Ollama")
                    return await self._ollama_resume_analysis(resume_text, job_requirements)
            else:
                # Use free Ollama for trial users
                return await self._ollama_resume_analysis(resume_text, job_requirements)
                
        except Exception as e:
            logger.error(f"Premium routing failed: {e}")
            # Fallback to Ollama
            return await self._ollama_resume_analysis(resume_text, job_requirements)
    
    async def _openai_resume_analysis(self, resume_text: str, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Premium resume analysis using OpenAI GPT-4"""
        try:
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            
            prompt = self._create_premium_resume_prompt(resume_text, job_requirements)
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert HR professional with 15+ years of experience in talent acquisition and resume analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            result['ai_provider'] = 'openai'
            result['model_used'] = model
            result['processing_tier'] = 'premium'
            
            logger.info("Premium OpenAI resume analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            # Fallback to Ollama
            return await self._ollama_resume_analysis(resume_text, job_requirements)
    
    async def _anthropic_resume_analysis(self, resume_text: str, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Premium resume analysis using Anthropic Claude"""
        try:
            model = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
            
            prompt = self._create_premium_resume_prompt(resume_text, job_requirements)
            
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text)
            result['ai_provider'] = 'anthropic'
            result['model_used'] = model
            result['processing_tier'] = 'premium'
            
            logger.info("Premium Anthropic resume analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Anthropic analysis failed: {e}")
            # Fallback to Ollama
            return await self._ollama_resume_analysis(resume_text, job_requirements)
    
    async def _ollama_resume_analysis(self, resume_text: str, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Free resume analysis using Ollama"""
        try:
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
            
            prompt = self._create_standard_resume_prompt(resume_text, job_requirements)
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            # Make async request to Ollama
            response = await asyncio.to_thread(
                requests.post,
                f"{ollama_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = json.loads(response.json()['response'])
                result['ai_provider'] = 'ollama'
                result['model_used'] = model
                result['processing_tier'] = 'free_trial'
                return result
            else:
                raise Exception(f"Ollama request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return self._fallback_analysis(resume_text, job_requirements)
    
    def _create_premium_resume_prompt(self, resume_text: str, job_requirements: Dict[str, Any]) -> str:
        """Create enhanced prompt for premium AI providers"""
        return f"""
As a senior HR executive, provide a comprehensive analysis of this resume for the given job requirements.

RESUME:
{resume_text}

JOB REQUIREMENTS:
Position: {job_requirements.get('title', 'Not specified')}
Required Skills: {', '.join(job_requirements.get('required_skills', []))}
Experience Level: {job_requirements.get('experience_level', 'Not specified')}
Department: {job_requirements.get('department', 'Not specified')}

Provide analysis in this JSON format:
{{
    "overall_score": <0-100>,
    "skill_match_percentage": <0-100>,
    "experience_relevance": <0-100>,
    "cultural_fit_indicators": [<list of indicators>],
    "strengths": [<list of key strengths>],
    "improvement_areas": [<list of areas needing improvement>],
    "missing_skills": [<list of skills not found>],
    "recommended_next_steps": [<list of recommendations>],
    "detailed_assessment": {{
        "technical_skills": {{
            "score": <0-100>,
            "analysis": "<detailed analysis>"
        }},
        "professional_experience": {{
            "score": <0-100>,
            "analysis": "<detailed analysis>"
        }},
        "education_background": {{
            "score": <0-100>,
            "analysis": "<detailed analysis>"
        }},
        "achievements_impact": {{
            "score": <0-100>,
            "analysis": "<detailed analysis>"
        }}
    }},
    "hiring_recommendation": "<strong_hire|hire|maybe|no_hire>",
    "salary_range_suggestion": {{
        "min": <amount>,
        "max": <amount>,
        "currency": "INR"
    }},
    "interview_focus_areas": [<list of areas to focus on during interview>]
}}
"""
    
    def _create_standard_resume_prompt(self, resume_text: str, job_requirements: Dict[str, Any]) -> str:
        """Create standard prompt for free tier (Ollama)"""
        return f"""
Analyze this resume for the job requirements and provide a JSON response.

RESUME:
{resume_text}

JOB: {job_requirements.get('title', 'Position')}
SKILLS NEEDED: {', '.join(job_requirements.get('required_skills', []))}

Return JSON format:
{{
    "overall_score": <0-100>,
    "skill_match_percentage": <0-100>,
    "strengths": [<list>],
    "missing_skills": [<list>],
    "hiring_recommendation": "<hire|maybe|no_hire>"
}}
"""
    
    def _fallback_analysis(self, resume_text: str, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when all AI providers fail"""
        return {
            "overall_score": 50,
            "skill_match_percentage": 30,
            "strengths": ["Resume submitted for analysis"],
            "missing_skills": ["Unable to analyze due to system limitations"],
            "hiring_recommendation": "maybe",
            "ai_provider": "fallback",
            "processing_tier": "fallback",
            "error": "AI analysis unavailable, using fallback scoring"
        }

    async def route_premium_legal_query(self, query: str, processing_tier: str = "free_trial") -> Dict[str, Any]:
        """Route legal query to appropriate AI provider based on user tier"""
        try:
            if processing_tier in ["premium_instant", "queue_skip", "enterprise"]:
                # Use premium AI for legal queries
                if self.openai_client:
                    return await self._openai_legal_analysis(query)
                elif self.anthropic_client:
                    return await self._anthropic_legal_analysis(query)
                else:
                    return await self._ollama_legal_analysis(query)
            else:
                # Use free Ollama for trial users
                return await self._ollama_legal_analysis(query)
                
        except Exception as e:
            logger.error(f"Premium legal routing failed: {e}")
            return await self._ollama_legal_analysis(query)
        
    async def _openai_legal_analysis(self, query: str) -> Dict[str, Any]:
        """Premium legal analysis using OpenAI"""
        try:
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            
            prompt = f"""
As an expert in Indian HR and Labour Laws, provide a comprehensive answer to this query:

QUERY: {query}

Provide detailed analysis covering:
1. Relevant laws and sections
2. Practical implications
3. Compliance requirements
4. Best practices
5. Potential risks

Format as JSON:
{{
    "answer": "<detailed answer>",
    "relevant_laws": [<list of applicable laws>],
    "compliance_steps": [<list of action items>],
    "risk_level": "<low|medium|high>",
    "additional_resources": [<list of resources>]
}}
"""
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert in Indian HR and Labour Laws with 20+ years of experience."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            result['ai_provider'] = 'openai'
            result['processing_tier'] = 'premium'
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI legal analysis failed: {e}")
            return await self._ollama_legal_analysis(query)
    
    async def _anthropic_legal_analysis(self, query: str) -> Dict[str, Any]:
        """Premium legal analysis using Anthropic"""
        try:
            model = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
            
            prompt = f"""
As an Indian HR and Labour Law expert, answer this query comprehensively:

{query}

Provide JSON response with legal analysis, compliance requirements, and recommendations.
"""
            
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text)
            result['ai_provider'] = 'anthropic'
            result['processing_tier'] = 'premium'
            
            return result
            
        except Exception as e:
            logger.error(f"Anthropic legal analysis failed: {e}")
            return await self._ollama_legal_analysis(query)
    
    async def _ollama_legal_analysis(self, query: str) -> Dict[str, Any]:
        """Free legal analysis using Ollama"""
        try:
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
            
            # Use existing HR legal RAG if available
            if query_hr_legal:
                rag_result = query_hr_legal(query)
                if rag_result:
                    return {
                        "answer": rag_result,
                        "ai_provider": "ollama_rag",
                        "processing_tier": "free_trial"
                    }
            
            # Fallback to direct Ollama query
            prompt = f"Answer this HR/Labour law query for India: {query}"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            }
            
            response = await asyncio.to_thread(
                requests.post,
                f"{ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return {
                    "answer": response.json()['response'],
                    "ai_provider": "ollama",
                    "processing_tier": "free_trial"
                }
            else:
                raise Exception(f"Ollama request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama legal analysis failed: {e}")
            return {
                "answer": "Unable to process legal query at this time. Please try again later.",
                "ai_provider": "fallback",
                "processing_tier": "fallback",
                "error": str(e)
            }

class AgenticResumeProcessor:
    """Enhanced AI processor with agentic capabilities, premium routing, and backward compatibility"""
    
    def __init__(self, credit_manager=None):
        """Initialize with agentic AI system and premium routing"""
        self.fallback_mode = False
        self._temp_resume_storage = {}  # Temporary storage for analysis
        self.credit_manager = credit_manager
        
        # Initialize configuration
        self.config = Config()
        
        # Initialize premium AI router for Phase 2
        self.premium_router = PremiumAIRouter(self.config)
        
        # Try to initialize enhanced agentic analyzer first
        if EnhancedAgenticResumeProcessor:
            try:
                self.multi_ai = MultiProviderAI(self.config) if MultiProviderAI else None
                self.enhanced_agentic_processor = EnhancedAgenticResumeProcessor(self.multi_ai)
                self.market_provider = MarketDataProvider(self.config) if MarketDataProvider else None
                self.rag_system = get_rag_system() if get_rag_system else None
                logger.info("Enhanced Agentic AI system initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize enhanced agentic system: {e}")
                self._try_fallback_agentic()
        elif AgenticResumeAnalyzer:
            self._try_fallback_agentic()
        else:
            self._initialize_builtin_system()
    
    def _try_fallback_agentic(self):
        """Try to initialize fallback agentic system"""
        try:
            self.agentic_analyzer = AgenticResumeAnalyzer(self.config)
            self.multi_ai = MultiProviderAI(self.config) if MultiProviderAI else None
            self.market_provider = MarketDataProvider(self.config) if MarketDataProvider else None
            self.rag_system = get_rag_system() if get_rag_system else None
            logger.info("Fallback Agentic AI system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize fallback agentic system: {e}")
            logger.warning("Agentic AI modules not available, using built-in system")
            self._initialize_builtin_system()
            
    def _initialize_builtin_system(self):
        """Initialize built-in agentic system"""
        try:
            # Use built-in classes if modules not available
            self.agentic_analyzer = BuiltInAgenticResumeAnalyzer()
            self.multi_ai = None
            self.market_provider = None
            self.rag_system = None
            logger.info("Built-in agentic system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize built-in system: {e}")
            self.fallback_mode = True
            
    async def analyze_resume(self, resume_text: str, job_requirements: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """Analyze resume with premium routing and enhanced agentic AI + CPU optimization"""
        try:
            # CPU OPTIMIZATION: Check cache first (use memory instead of CPU)
            cache_key = f"resume_analysis_{hash(resume_text)}_{hash(str(job_requirements))}"
            cached_result = get_cached_response(cache_key)
            if cached_result:
                logger.info(f"🚀 Using cached analysis result for user {user_id}")
                return cached_result
            
            # Start CPU optimization monitoring (if available)
            optimization_start = None
            if cpu_optimizer and hasattr(cpu_optimizer, 'monitor_ai_processing_start'):
                optimization_start = cpu_optimizer.monitor_ai_processing_start("resume_analysis", user_id)
            
            # Determine processing tier based on user credits/payment status
            processing_tier = "free_trial"  # Default
            
            if self.credit_manager and user_id:
                try:
                    user_id_int = int(user_id) if isinstance(user_id, str) else user_id
                    credit_status = self.credit_manager.get_credit_status(user_id_int)
                    processing_tier = credit_status.processing_tier.value
                    
                    logger.info(f"User {user_id} processing tier: {processing_tier}")
                except Exception as e:
                    logger.warning(f"Failed to get credit status for user {user_id}: {e}")
            
            # Route to premium AI if user has paid
            if processing_tier in ["premium_instant", "queue_skip", "enterprise"]:
                logger.info(f"Routing user {user_id} to premium AI processing")
                result = await self.premium_router.route_premium_resume_analysis(
                    resume_text, job_requirements, processing_tier
                )
                
                # Add premium processing indicators
                result['is_premium'] = True
                result['processing_tier'] = processing_tier
                
            # Use enhanced agentic analysis for free tier
            elif not self.fallback_mode and hasattr(self, 'enhanced_agentic_processor'):
                # Use enhanced multi-agent analysis
                result = await self._enhanced_agentic_analysis(resume_text, job_requirements, user_id)
                result['is_premium'] = False
                result['processing_tier'] = processing_tier
            elif not self.fallback_mode and hasattr(self, 'agentic_analyzer'):
                # Use standard agentic analysis
                result = await self._agentic_analysis(resume_text, job_requirements, user_id)
                result['is_premium'] = False
                result['processing_tier'] = processing_tier
            else:
                # Use simple fallback analysis
                result = await self._simple_analysis(resume_text, job_requirements)
                result['is_premium'] = False
                result['processing_tier'] = processing_tier
            
            # CPU OPTIMIZATION: Cache result to avoid re-processing
            cache_response(cache_key, result, ttl_minutes=120)  # Cache for 2 hours
            
            # End CPU optimization monitoring (if available and started)
            if cpu_optimizer and hasattr(cpu_optimizer, 'monitor_ai_processing_end') and optimization_start is not None:
                cpu_optimizer.monitor_ai_processing_end(optimization_start)
            
            return result
                
        except Exception as e:
            logger.error(f"Resume analysis error: {e}")
            return self._get_error_response(str(e))
    
    async def _enhanced_agentic_analysis(self, resume_text: str, job_requirements: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Perform enhanced multi-agent analysis with realistic scoring"""
        try:
            # Parse resume text into structured data
            resume_data = self._parse_resume_text(resume_text)
            
            # Create job description from requirements
            job_description = self._create_job_description(job_requirements)
            
            # Run enhanced multi-agent analysis
            result = self.enhanced_agentic_processor.analyze_resume(resume_data, job_description)
            
            # Add market context if available
            if self.market_provider:
                try:
                    market_context = self.market_provider.get_market_context(job_requirements.get('title', ''))
                    result['market_context'] = market_context
                except Exception as e:
                    logger.warning(f"Market context retrieval failed: {e}")
            
            # Add HR Legal context if available
            if self.rag_system:
                try:
                    legal_context = await self._get_hr_legal_context(resume_data, job_requirements)
                    result['hr_legal_context'] = legal_context
                except Exception as e:
                    logger.warning(f"HR Legal context retrieval failed: {e}")
            
            # Clean up temporary storage
            if hasattr(self, '_temp_resume_storage'):
                temp_keys = [k for k in self._temp_resume_storage.keys() if k.startswith('temp_')]
                for key in temp_keys:
                    self._temp_resume_storage.pop(key, None)
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced agentic analysis failed: {e}")
            # Fallback to simple analysis
            return await self._simple_analysis(resume_text, job_requirements)
            
    async def _agentic_analysis(self, resume_text: str, job_requirements: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Perform agentic 4-agent analysis"""
        try:
            # Create temporary resume ID for analysis
            resume_id = str(uuid.uuid4())
            
            # Store resume text temporarily
            self._temp_resume_storage[resume_id] = resume_text
            
            # Run 4-agent analysis
            result = await self.agentic_analyzer.analyze_resume(resume_id, job_requirements, user_id)
            
            # Add market context if available
            if self.market_provider:
                try:
                    market_context = self.market_provider.get_market_context(job_requirements.get('title', ''))
                    result['market_context'] = market_context
                except Exception as e:
                    logger.warning(f"Market context unavailable: {e}")
                    
            # Cleanup temporary storage
            if resume_id in self._temp_resume_storage:
                del self._temp_resume_storage[resume_id]
                
            return result
            
        except Exception as e:
            logger.error(f"Agentic analysis failed: {e}")
            return await self._simple_analysis(resume_text, job_requirements)
            
    async def _simple_analysis(self, resume_text: str, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Simple fallback analysis"""
        try:
            # Basic keyword matching
            required_skills = job_requirements.get('required_skills', [])
            
            skills_match = 0
            for skill in required_skills:
                if skill.lower() in resume_text.lower():
                    skills_match += 1
                    
            match_score = skills_match / len(required_skills) if required_skills else 0.5
            
            return {
                "analysis_type": "simple_fallback",
                "overall_score": match_score,
                "skills_matched": skills_match,
                "total_required_skills": len(required_skills),
                "recommendation": "Consider" if match_score > 0.5 else "Review Required",
                "analysis_summary": {
                    "technical_fit": match_score,
                    "experience_fit": 0.5,
                    "cultural_fit": 0.5,
                    "legal_compliance": 0.8
                },
                "timestamp": datetime.utcnow().isoformat(),
                "fallback_reason": "Agentic AI not available"
            }
            
        except Exception as e:
            logger.error(f"Simple analysis failed: {e}")
            return self._get_error_response(str(e))
            
    def _get_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "analysis_type": "error",
            "overall_score": 0.0,
            "recommendation": "Manual Review Required",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _parse_resume_text(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text into structured data for enhanced analysis"""
        try:
            # Basic parsing - can be enhanced with proper NLP
            lines = resume_text.split('\n')
            
            # Extract basic sections
            skills = []
            experience = []
            education = []
            
            current_section = None
            current_exp = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect section headers
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ['skill', 'technical', 'technologies']):
                    current_section = 'skills'
                elif any(keyword in line_lower for keyword in ['experience', 'work', 'employment']):
                    current_section = 'experience'
                elif any(keyword in line_lower for keyword in ['education', 'qualification', 'degree']):
                    current_section = 'education'
                else:
                    # Process content based on current section
                    if current_section == 'skills':
                        # Extract skills from line
                        potential_skills = [s.strip() for s in line.replace(',', ' ').split() if len(s.strip()) > 2]
                        skills.extend(potential_skills)
                    elif current_section == 'experience':
                        # Simple experience parsing
                        if any(word in line_lower for word in ['company', 'corp', 'inc', 'ltd']):
                            if current_exp:
                                experience.append(current_exp)
                            current_exp = {'company': line, 'title': '', 'description': ''}
                        elif any(word in line_lower for word in ['manager', 'developer', 'analyst', 'engineer']):
                            current_exp['title'] = line
                        else:
                            if 'description' in current_exp:
                                current_exp['description'] += ' ' + line
                    elif current_section == 'education':
                        if any(word in line_lower for word in ['university', 'college', 'institute']):
                            education.append({'institution': line, 'degree': ''})
            
            # Add final experience if exists
            if current_exp:
                experience.append(current_exp)
            
            return {
                'skills': list(set(skills))[:20],  # Limit and deduplicate
                'experience': experience,
                'education': education,
                'raw_text': resume_text
            }
            
        except Exception as e:
            logger.error(f"Resume parsing failed: {e}")
            return {
                'skills': [],
                'experience': [],
                'education': [],
                'raw_text': resume_text
            }
    
    def _create_job_description(self, job_requirements: Dict[str, Any]) -> str:
        """Create job description from requirements dict"""
        parts = []
        
        if job_requirements.get('title'):
            parts.append(f"Position: {job_requirements['title']}")
        
        if job_requirements.get('required_skills'):
            parts.append(f"Required Skills: {', '.join(job_requirements['required_skills'])}")
        
        if job_requirements.get('preferred_skills'):
            parts.append(f"Preferred Skills: {', '.join(job_requirements['preferred_skills'])}")
        
        if job_requirements.get('experience_years'):
            parts.append(f"Experience Required: {job_requirements['experience_years']} years")
        
        if job_requirements.get('description'):
            parts.append(f"Description: {job_requirements['description']}")
        
        return '\n'.join(parts) if parts else "General position requirements"
    
    async def _get_hr_legal_context(self, resume_data: Dict, job_requirements: Dict) -> Dict[str, Any]:
        """Get HR legal context for the analysis"""
        try:
            # Create legal query based on resume/job data
            query_parts = []
            
            if job_requirements.get('title'):
                query_parts.append(f"hiring for {job_requirements['title']}")
            
            if resume_data.get('experience'):
                query_parts.append("employment verification")
            
            query_parts.append("legal compliance in hiring")
            
            legal_query = " ".join(query_parts)
            return await self.rag_system.query_legal_knowledge(legal_query)
            
        except Exception as e:
            logger.error(f"HR legal context failed: {e}")
            return {"legal_analysis": "Legal context unavailable", "recommendations": []}
    
    async def analyze_resume_batch(self, resume_batch: List[Dict], job_requirements: Dict[str, Any], user_id: str = None) -> List[Dict[str, Any]]:
        """
        Analyze multiple resumes with comparative ranking and realistic scoring
        
        Args:
            resume_batch: List of dictionaries with 'text' and optional 'id' keys
            job_requirements: Job requirements dictionary
            user_id: User identifier
        
        Returns:
            List of analysis results with realistic score distribution
        """
        try:
            if not self.fallback_mode and hasattr(self, 'enhanced_agentic_processor'):
                # Use enhanced batch processing with realistic scoring
                resume_data_batch = []
                
                for resume_item in resume_batch:
                    resume_text = resume_item.get('text', '')
                    resume_data = self._parse_resume_text(resume_text)
                    resume_data['original_id'] = resume_item.get('id', str(uuid.uuid4()))
                    resume_data_batch.append(resume_data)
                
                # Create job description
                job_description = self._create_job_description(job_requirements)
                
                # Run enhanced batch analysis with realistic scoring
                batch_results = self.enhanced_agentic_processor.analyze_batch(resume_data_batch, job_description)
                
                # Add metadata and clean up results
                for i, result in enumerate(batch_results):
                    result['original_id'] = resume_data_batch[i].get('original_id')
                    result['batch_position'] = i + 1
                    result['total_in_batch'] = len(batch_results)
                
                logger.info(f"Enhanced batch analysis completed for {len(batch_results)} resumes")
                return batch_results
                
            else:
                # Fallback: analyze each resume individually
                individual_results = []
                for resume_item in resume_batch:
                    result = await self.analyze_resume(
                        resume_item.get('text', ''), 
                        job_requirements, 
                        user_id
                    )
                    result['original_id'] = resume_item.get('id', str(uuid.uuid4()))
                    individual_results.append(result)
                
                # Sort by overall score for basic ranking
                individual_results.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
                
                # Add ranking metadata
                for i, result in enumerate(individual_results):
                    result['batch_position'] = i + 1
                    result['total_in_batch'] = len(individual_results)
                
                logger.info(f"Individual batch analysis completed for {len(individual_results)} resumes")
                return individual_results
                
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return [self._get_error_response(f"Batch analysis failed: {str(e)}")]
    
    def get_enhanced_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the enhanced agentic system"""
        try:
            base_status = {
                "fallback_mode": self.fallback_mode,
                "timestamp": datetime.utcnow().isoformat(),
                "system_components": {
                    "enhanced_agentic_processor": hasattr(self, 'enhanced_agentic_processor'),
                    "fallback_agentic_analyzer": hasattr(self, 'agentic_analyzer'),
                    "multi_provider_ai": hasattr(self, 'multi_ai') and self.multi_ai is not None,
                    "market_data_provider": hasattr(self, 'market_provider') and self.market_provider is not None,
                    "hr_legal_rag": hasattr(self, 'rag_system') and self.rag_system is not None
                }
            }
            
            # Get enhanced processor status if available
            if hasattr(self, 'enhanced_agentic_processor'):
                enhanced_status = self.enhanced_agentic_processor.get_system_status()
                base_status["enhanced_processor_details"] = enhanced_status
                
            return base_status
            
        except Exception as e:
            logger.error(f"System status check failed: {e}")
            return {
                "fallback_mode": True,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        
    async def process_legal_query(self, query_text: str, user_id: str = None) -> Dict[str, Any]:
        """Process HR legal query with premium routing (Phase 2)"""
        try:
            # Determine processing tier based on user credits/payment status
            processing_tier = "free_trial"  # Default
            
            if self.credit_manager and user_id:
                try:
                    user_id_int = int(user_id) if isinstance(user_id, str) else user_id
                    credit_status = self.credit_manager.get_credit_status(user_id_int)
                    processing_tier = credit_status.processing_tier.value
                    
                    logger.info(f"User {user_id} legal query processing tier: {processing_tier}")
                except Exception as e:
                    logger.warning(f"Failed to get credit status for legal query user {user_id}: {e}")
            
            # Route to premium AI if user has paid
            if processing_tier in ["premium_instant", "queue_skip", "enterprise"]:
                logger.info(f"Routing user {user_id} to premium legal AI processing")
                result = await self.premium_router.route_premium_legal_query(query_text, processing_tier)
                
                # Add premium processing indicators
                result['is_premium'] = True
                result['processing_tier'] = processing_tier
                result['timestamp'] = datetime.now().isoformat()
                
                return result
            
            # Use free tier processing for trial users
            # Try RAG system first for enhanced legal analysis
            if self.rag_system and not self.fallback_mode:
                try:
                    rag_response = await self.rag_system.query_legal_knowledge(query_text)
                    rag_response['is_premium'] = False
                    rag_response['processing_tier'] = processing_tier
                    logger.info("Legal query processed using RAG system (free tier)")
                    return rag_response
                except Exception as rag_error:
                    logger.warning(f"RAG system failed, falling back to agentic analyzer: {rag_error}")
            
            # Fall back to agentic analyzer
            if not self.fallback_mode and self.agentic_analyzer:
                result = await self.agentic_analyzer.process_legal_query(query_text, user_id)
                result['is_premium'] = False
                result['processing_tier'] = processing_tier
                return result
            else:
                # Final fallback
                return {
                    "query": query_text,
                    "response": {
                        "legal_analysis": "Legal analysis not available - upgrade to premium for enhanced legal assistance",
                        "recommendations": ["Consider upgrading to premium for detailed legal analysis", "Consult with qualified legal professional"],
                        "risk_level": "Unknown",
                        "compliance_steps": [],
                        "sources": [],
                        "confidence_score": 0.1
                    },
                    "is_premium": False,
                    "processing_tier": processing_tier,
                    "timestamp": datetime.now().isoformat(),
                    "method": "basic_fallback",
                    "upgrade_message": "Upgrade to premium for comprehensive legal analysis with AI-powered insights"
                }
        except Exception as e:
            logger.error(f"Legal query processing error: {e}")
            return self._get_error_response(str(e))
            
    def get_resume_content(self, resume_id: str) -> str:
        """Get resume content by ID (for built-in analyzer)"""
        return self._temp_resume_storage.get(resume_id, "Resume content not found")
            
    def health_check(self) -> Dict[str, Any]:
        """Check system health including RAG system"""
        try:
            base_health = {}
            
            if not self.fallback_mode and self.agentic_analyzer:
                base_health = self.agentic_analyzer.health_check()
            else:
                base_health = {
                    "status": "fallback_mode",
                    "message": "Using simple analysis",
                    "agentic_available": False
                }
            
            # Add RAG system health
            if self.rag_system:
                try:
                    rag_health = self.rag_system.health_check()
                    base_health["rag_system"] = rag_health
                except Exception as e:
                    base_health["rag_system"] = {
                        "system_status": "error",
                        "error": str(e)
                    }
            else:
                base_health["rag_system"] = {
                    "system_status": "unavailable",
                    "message": "RAG system not initialized"
                }
                
            return base_health
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "agentic_available": False,
                "rag_system": {"system_status": "error"}
            }

def extract_resume_data_for_database(ai_analysis_result: Dict[str, Any], raw_text: str, filename: str) -> Dict[str, Any]:
    """
    Extract and format AI analysis data to match Supabase database schema exactly
    
    Args:
        ai_analysis_result: Result from AI resume analysis
        raw_text: Original resume text content
        filename: Original filename
    
    Returns:
        Dictionary matching the Supabase resumes table schema
    """
    try:
        # Import here to avoid circular import
        import json
        import hashlib
        from datetime import datetime
        
        # Generate file hash for deduplication
        file_hash = hashlib.md5(raw_text.encode('utf-8')).hexdigest()
        
        # Extract candidate information with fallbacks
        candidate_name = ai_analysis_result.get('candidate_name', '')
        if not candidate_name:
            # Try to extract from analysis summary or other fields
            candidate_name = ai_analysis_result.get('analysis_summary', {}).get('candidate_name', '')
        
        candidate_email = ai_analysis_result.get('candidate_email', '')
        candidate_phone = ai_analysis_result.get('candidate_phone', '')
        
        # Extract skills array (ensure it's a list)
        skills = ai_analysis_result.get('skills', [])
        if isinstance(skills, str):
            skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
        elif not isinstance(skills, list):
            skills = []
        
        # Extract experience years (ensure it's an integer)
        experience_years = 0
        try:
            exp_years = ai_analysis_result.get('experience_years', 0)
            if isinstance(exp_years, str):
                # Try to extract number from string like "5 years" or "5-7 years"
                import re
                match = re.search(r'(\d+)', exp_years)
                experience_years = int(match.group(1)) if match else 0
            else:
                experience_years = int(exp_years) if exp_years else 0
        except (ValueError, TypeError):
            experience_years = 0
        
        # Ensure experience_years is within valid range
        experience_years = max(0, min(experience_years, 100))
        
        # Extract education level
        education_level = ai_analysis_result.get('education_level', '')
        if not education_level:
            education_level = ai_analysis_result.get('education', {}).get('level', '') if isinstance(ai_analysis_result.get('education'), dict) else ''
        
        # Extract scores (ensure they're integers 0-100)
        def safe_score_extract(score_key: str, default: int = 0) -> int:
            score = ai_analysis_result.get(score_key, default)
            if isinstance(score, str):
                try:
                    # Handle percentage strings like "85%" or "85.5"
                    score = float(score.replace('%', ''))
                except (ValueError, AttributeError):
                    score = default
            elif isinstance(score, float):
                score = int(score)
            elif not isinstance(score, int):
                score = default
            return max(0, min(int(score), 100))
        
        overall_score = safe_score_extract('overall_score', 0)
        technical_score = safe_score_extract('technical_score', 0)
        experience_score = safe_score_extract('experience_score', 0)
        education_score = safe_score_extract('education_score', 0)
        role_fit_score = safe_score_extract('role_fit_score', 0)
        
        # If we have analysis_summary with different score names, map them
        if 'analysis_summary' in ai_analysis_result:
            summary = ai_analysis_result['analysis_summary']
            if isinstance(summary, dict):
                overall_score = overall_score or safe_score_extract('technical_fit', 0) or safe_score_extract('overall_score', 0)
                technical_score = technical_score or safe_score_extract('technical_fit', 0)
                experience_score = experience_score or safe_score_extract('experience_fit', 0)
                role_fit_score = role_fit_score or safe_score_extract('cultural_fit', 0)
        
        # Extract additional metadata arrays
        job_titles = ai_analysis_result.get('job_titles', [])
        if isinstance(job_titles, str):
            job_titles = [title.strip() for title in job_titles.split(',') if title.strip()]
        elif not isinstance(job_titles, list):
            job_titles = []
        
        companies = ai_analysis_result.get('companies', [])
        if isinstance(companies, str):
            companies = [company.strip() for company in companies.split(',') if company.strip()]
        elif not isinstance(companies, list):
            companies = []
        
        programming_languages = ai_analysis_result.get('programming_languages', [])
        if isinstance(programming_languages, str):
            programming_languages = [lang.strip() for lang in programming_languages.split(',') if lang.strip()]
        elif not isinstance(programming_languages, list):
            programming_languages = []
        
        certifications = ai_analysis_result.get('certifications', [])
        if isinstance(certifications, str):
            certifications = [cert.strip() for cert in certifications.split(',') if cert.strip()]
        elif not isinstance(certifications, list):
            certifications = []
        
        # Extract AI feedback
        ai_feedback = ai_analysis_result.get('ai_feedback', '')
        if not ai_feedback:
            ai_feedback = ai_analysis_result.get('detailed_analysis', '')
            if not ai_feedback:
                ai_feedback = ai_analysis_result.get('feedback', '')
        
        # Get AI model used
        ai_model_used = ai_analysis_result.get('ai_model_used', 'ollama:qwen2.5:7b')
        if not ai_model_used:
            ai_model_used = ai_analysis_result.get('model_used', 'ollama:qwen2.5:7b')
        
        # Get processing time
        ai_processing_time = ai_analysis_result.get('ai_processing_time', 0)
        if not ai_processing_time:
            ai_processing_time = ai_analysis_result.get('processing_time', 0)
        
        # Create compressed content (full AI analysis as JSON)
        compressed_content = json.dumps({
            'original_analysis': ai_analysis_result,
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'extracted_by': 'ai_first_pipeline'
        })
        
        # Create the database record matching Supabase schema exactly
        database_record = {
            'filename': filename,
            'file_hash': file_hash,
            'file_size': len(raw_text.encode('utf-8')),
            'file_type': 'pdf',  # Default, can be updated based on actual file type
            'processing_status': 'completed',
            'processing_started_at': datetime.utcnow().isoformat(),
            'processing_completed_at': datetime.utcnow().isoformat(),
            'compressed_content': compressed_content,
            'raw_text': raw_text,
            
            # Extracted candidate information
            'candidate_name': candidate_name[:255] if candidate_name else '',  # Ensure string length limits
            'candidate_email': candidate_email[:255] if candidate_email else '',
            'candidate_phone': candidate_phone[:50] if candidate_phone else '',
            'experience_years': experience_years,
            'education_level': education_level[:100] if education_level else '',
            
            # AI Analysis scores (0-100 range)
            'overall_score': overall_score,
            'technical_score': technical_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'role_fit_score': role_fit_score,
            
            # AI Analysis details
            'ai_feedback': ai_feedback,
            'ai_model_used': ai_model_used,
            'ai_processing_time': int(ai_processing_time) if ai_processing_time else 0,
            
            # Arrays for search and analytics (ensure they're lists)
            'skills': skills[:50],  # Limit array size for performance
            'job_titles': job_titles[:20],
            'companies': companies[:20],
            'programming_languages': programming_languages[:30],
            'certifications': certifications[:20],
            
            # Default values for other fields
            'tags': [],
            'category': 'general',
            'priority': 0,
            'is_shortlisted': False,
            'is_archived': False,
            'notes': '',
        }
        
        logger.info(f"Successfully extracted database record for resume: {filename}")
        logger.debug(f"Extracted scores - Overall: {overall_score}, Technical: {technical_score}, Experience: {experience_score}")
        
        return database_record
        
    except Exception as e:
        logger.error(f"Failed to extract resume data for database: {e}")
        # Return minimal valid record on error
        return {
            'filename': filename,
            'file_hash': hashlib.md5(raw_text.encode('utf-8')).hexdigest() if raw_text else 'error',
            'file_size': len(raw_text.encode('utf-8')) if raw_text else 0,
            'file_type': 'pdf',
            'processing_status': 'failed',
            'processing_error': str(e),
            'compressed_content': json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()}),
            'raw_text': raw_text or '',
            'candidate_name': '',
            'candidate_email': '',
            'candidate_phone': '',
            'skills': [],
            'experience_years': 0,
            'education_level': '',
            'overall_score': 0,
            'technical_score': 0,
            'experience_score': 0,
            'education_score': 0,
            'role_fit_score': 0,
            'ai_feedback': f'Processing failed: {str(e)}',
            'ai_model_used': 'error',
            'ai_processing_time': 0,
            'job_titles': [],
            'companies': [],
            'programming_languages': [],
            'certifications': [],
            'tags': [],
            'category': 'general',
            'priority': 0,
            'is_shortlisted': False,
            'is_archived': False,
            'notes': f'Processing error: {str(e)}',
        }

# Built-in classes for when modules are not available
class ResumeAnalysisContext:
    """Context shared between analysis agents"""
    
    def __init__(self, resume_text: str, job_requirements: Dict[str, Any], insights: Dict = None, candidate_profile: Dict = None):
        self.resume_text = resume_text
        self.job_requirements = job_requirements
        self.insights = insights or {}
        self.candidate_profile = candidate_profile or {}
        
    def add_insight(self, agent_name: str, insight: Dict[str, Any]):
        """Add insight from an agent"""
        self.insights[agent_name] = insight

class BuiltInAIProvider:
    """Built-in AI Provider with Railway Pro timeout optimization"""
    
    def __init__(self):
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Progressive timeouts for Railway Pro (32 CPU, 32GB RAM)
        self.ai_timeout = int(os.getenv('AI_TIMEOUT', 900))  # 15 minutes for resume analysis
        self.batch_timeout = int(os.getenv('OLLAMA_BATCH_TIMEOUT', 1800))  # 30 minutes for batch
        self.simple_timeout = int(os.getenv('OLLAMA_SIMPLE_TIMEOUT', 180))  # 3 minutes for simple queries
        
        logger.info(f"BuiltInAIProvider initialized with Railway Pro timeouts - Resume: {self.ai_timeout}s, Batch: {self.batch_timeout}s, Simple: {self.simple_timeout}s")
        
    async def generate_response(self, prompt: str, operation_type: str = 'resume_analysis') -> str:
        """Generate AI response with progressive timeout based on operation type"""
        if not requests:
            return '{"error": "requests module not available"}'
        
        # Select appropriate timeout based on operation
        if operation_type == 'batch_processing':
            timeout = self.batch_timeout
        elif operation_type == 'simple_query':
            timeout = self.simple_timeout
        else:  # resume_analysis or default
            timeout = self.ai_timeout
        
        logger.debug(f"Using {timeout}s timeout for {operation_type}")
            
        # Try Ollama first with appropriate timeout
        try:
            return await self._ollama_request(prompt, timeout)
        except Exception as ollama_error:
            logger.warning(f"Ollama failed with {timeout}s timeout: {ollama_error}")
            
            # Fallback to OpenAI if available (use shorter timeout for cloud service)
            if self.openai_api_key:
                try:
                    return await self._openai_request(prompt)
                except Exception as openai_error:
                    logger.error(f"OpenAI also failed: {openai_error}")
                    
            # Return empty response if all fail
            return '{"error": "AI providers unavailable"}'
            
    async def _ollama_request(self, prompt: str, timeout: int = None) -> str:
        """Make request to Ollama with specified timeout"""
        if timeout is None:
            timeout = self.ai_timeout
            
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        
        return response.json().get('response', '{}')
        
    async def _openai_request(self, prompt: str) -> str:
        """Make request to OpenAI"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content or "{}"
        except ImportError:
            logger.error("OpenAI library not available")
            return '{"error": "OpenAI library not available"}'
        
    def health_check(self) -> Dict[str, Any]:
        """Check AI provider health"""
        status = {"ollama": False, "openai": False}
        
        if requests:
            # Check Ollama
            try:
                response = requests.get(f"{self.ollama_url}/api/version", timeout=5)
                status["ollama"] = response.status_code == 200
            except:
                pass
                
        # Check OpenAI
        status["openai"] = bool(self.openai_api_key)
        
        return {
            "status": "healthy" if any(status.values()) else "unhealthy",
            "providers": status
        }

class BuiltInAgenticResumeAnalyzer:
    """Built-in agentic resume analyzer when modules are not available"""
    
    def __init__(self):
        """Initialize the built-in 4-agent system"""
        self.ai_provider = BuiltInAIProvider()
        
    async def analyze_resume(self, resume_id: str, job_requirements: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Run simplified 4-agent analysis pipeline"""
        try:
            # Get the processor instance that created this analyzer
            processor = None
            for obj in globals().values():
                if isinstance(obj, AgenticResumeProcessor):
                    processor = obj
                    break
                    
            if not processor:
                raise Exception("Cannot find processor instance")
                
            resume_text = processor.get_resume_content(resume_id)
            
            # Create shared context
            context = ResumeAnalysisContext(
                resume_text=resume_text,
                job_requirements=job_requirements,
                insights={},
                candidate_profile={}
            )
            
            logger.info(f"Starting built-in 4-agent analysis for resume {resume_id}")
            
            # Simplified analysis with basic scoring
            technical_score = self._analyze_technical_skills(context)
            experience_score = self._analyze_experience(context)
            cultural_score = self._analyze_cultural_fit(context)
            legal_score = 0.8  # Assume legal compliance unless flagged
            
            # Build consensus assessment
            consensus_score = (
                technical_score * 0.3 +
                experience_score * 0.3 +
                cultural_score * 0.2 +
                legal_score * 0.2
            )
            
            # Generate overall recommendation
            if consensus_score >= 0.8:
                recommendation = "Highly Recommended"
            elif consensus_score >= 0.6:
                recommendation = "Recommended"
            elif consensus_score >= 0.4:
                recommendation = "Consider with Reservations"
            else:
                recommendation = "Not Recommended"
                
            return {
                "consensus_score": consensus_score,
                "overall_recommendation": recommendation,
                "analysis_summary": {
                    "technical_fit": technical_score,
                    "experience_fit": experience_score,
                    "cultural_fit": cultural_score,
                    "legal_compliance": legal_score
                },
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_version": "built-in-1.0",
                "analysis_type": "built_in_agentic"
            }
            
        except Exception as e:
            logger.error(f"Built-in agentic analysis error: {e}")
            return self._get_fallback_assessment(resume_id)
            
    def _analyze_technical_skills(self, context: ResumeAnalysisContext) -> float:
        """Analyze technical skills match"""
        try:
            required_skills = context.job_requirements.get('required_skills', [])
            resume_text = context.resume_text.lower()
            
            matches = 0
            for skill in required_skills:
                if skill.lower() in resume_text:
                    matches += 1
                    
            return matches / len(required_skills) if required_skills else 0.5
        except:
            return 0.5
            
    def _analyze_experience(self, context: ResumeAnalysisContext) -> float:
        """Analyze experience level"""
        try:
            resume_text = context.resume_text.lower()
            
            # Look for experience indicators
            experience_keywords = ['years', 'experience', 'worked', 'managed', 'led', 'developed']
            score = 0.5
            
            for keyword in experience_keywords:
                if keyword in resume_text:
                    score += 0.1
                    
            return min(score, 1.0)
        except:
            return 0.5
            
    def _analyze_cultural_fit(self, context: ResumeAnalysisContext) -> float:
        """Analyze cultural fit indicators"""
        try:
            resume_text = context.resume_text.lower()
            
            # Look for collaboration indicators
            cultural_keywords = ['team', 'collaboration', 'communication', 'leadership', 'project']
            score = 0.3
            
            for keyword in cultural_keywords:
                if keyword in resume_text:
                    score += 0.1
                    
            return min(score, 1.0)
        except:
            return 0.5
            
    def _get_fallback_assessment(self, resume_id: str) -> Dict[str, Any]:
        """Fallback assessment if analysis fails"""
        return {
            "consensus_score": 0.5,
            "overall_recommendation": "Manual Review Required",
            "analysis_summary": {
                "technical_fit": 0.5,
                "experience_fit": 0.5,
                "cultural_fit": 0.5,
                "legal_compliance": 0.8
            },
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_version": "built-in-1.0",
            "error": "Built-in analysis failed - manual review required"
        }
        
    async def process_legal_query(self, query_text: str, user_id: str) -> Dict[str, Any]:
        """Process HR legal query with built-in system"""
        try:
            # Use AI provider if available
            if self.ai_provider:
                prompt = f"""
                You are an HR Legal consultant. Analyze this query: {query_text}
                
                Respond with JSON containing:
                - legal_analysis: Brief analysis
                - recommendations: List of recommendations
                - risk_level: Low/Medium/High
                - confidence_score: 0-1
                """
                
                response = await self.ai_provider.generate_response(prompt, 'resume_analysis')
                
                try:
                    legal_response = json.loads(response)
                    legal_response["timestamp"] = datetime.utcnow().isoformat()
                    return legal_response
                except json.JSONDecodeError:
                    pass
                    
            # Fallback response
            return {
                "legal_analysis": "Legal analysis unavailable - consult with legal professional",
                "recommendations": ["Seek professional legal advice"],
                "risk_level": "Medium",
                "confidence_score": 0.1,
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_type": "built_in_fallback"
            }
                
        except Exception as e:
            logger.error(f"Legal query processing error: {e}")
            return {
                "legal_analysis": "Legal analysis unavailable",
                "recommendations": ["Consult with legal professional"],
                "risk_level": "Medium",
                "confidence_score": 0.1,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            
    def health_check(self) -> Dict[str, Any]:
        """Check built-in analyzer system health"""
        ai_health = self.ai_provider.health_check()
        
        return {
            "status": "healthy" if ai_health["status"] == "healthy" else "degraded",
            "analysis_type": "built_in",
            "agents": {
                "technical_agent": "built_in_ready",
                "experience_agent": "built_in_ready", 
                "cultural_agent": "built_in_ready",
                "legal_agent": "built_in_ready"
            },
            "ai_providers": ai_health["providers"]
        }

# Global processor instance for backward compatibility
_global_processor = None

def get_processor():
    """Get global processor instance"""
    global _global_processor
    if _global_processor is None:
        _global_processor = AgenticResumeProcessor()
    return _global_processor

# Backward compatibility functions
async def analyze_resume(resume_text: str, job_requirements: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """Backward compatible resume analysis function"""
    processor = get_processor()
    return await processor.analyze_resume(resume_text, job_requirements, user_id)

async def process_legal_query(query_text: str, user_id: str = None) -> Dict[str, Any]:
    """Backward compatible legal query function"""
    processor = get_processor()
    return await processor.process_legal_query(query_text, user_id)

def health_check() -> Dict[str, Any]:
    """Backward compatible health check function"""
    processor = get_processor()
    return processor.health_check()
