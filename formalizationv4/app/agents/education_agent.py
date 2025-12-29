from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import json
import re
import time
import logging

logger = logging.getLogger(__name__)

class EducationAgent(BaseAgent):
    """Agent specialized in analyzing educational background, certifications, and continuous learning across all industries in Indian context."""
    
    def __init__(self, model_service, config: Dict[str, Any] = None):
        super().__init__("EducationAgent", model_service, config)
        
        # Indian education system and qualification mapping
        self.indian_education_context = {
            "degree_hierarchy": ["Diploma", "Bachelor's", "Master's", "Doctorate"],
            "indian_boards": ["CBSE", "ICSE", "State Boards"],
            "professional_bodies": {
                "engineering": ["AICTE", "UGC", "IIT", "NIT", "IIIT"],
                "medical": ["MCI", "NMC", "AIIMS", "JIPMER"],
                "management": ["AICTE", "IIM", "XLRI", "FMS"],
                "finance": ["ICAI", "ICSI", "ICWA", "NISM"],
                "law": ["BCI", "NLU", "Delhi University"],
                "science": ["UGC", "CSIR", "IISc", "TIFR"]
            },
            "entrance_exams": {
                "engineering": ["JEE", "BITSAT", "VITEEE", "COMEDK"],
                "medical": ["NEET", "AIIMS", "JIPMER"],
                "management": ["CAT", "XAT", "GMAT", "MAT"],
                "law": ["CLAT", "LSAT"],
                "research": ["GATE", "NET", "SET"]
            }
        }
    
    def get_prompt_template(self) -> str:
        return """
You are a comprehensive education and qualification analysis expert with deep knowledge of the Indian education system, professional certifications, and industry-specific requirements. Analyze the following resume for educational qualifications across ALL industries and career paths.

RESUME TEXT:
{resume_text}

ANALYSIS REQUIREMENTS:
1. Evaluate formal education quality, relevance, and institution reputation in Indian context
2. Assess professional certifications, licenses, and their industry recognition
3. Analyze continuous learning patterns and skill development initiatives
4. Review specialized training, courses, and professional development
5. Evaluate academic achievements, honors, and research contributions
6. Assess educational institution ranking and accreditation status
7. Review entrance exam scores and competitive achievements
8. Analyze alignment between education and career trajectory
9. Evaluate international qualifications and their Indian equivalency
10. Assess overall learning commitment and intellectual curiosity

INDIAN EDUCATION SYSTEM CONTEXTS:
- School Education: CBSE, ICSE, State Boards, International Boards
- Higher Education: Central Universities, State Universities, Deemed Universities, Private Universities
- Technical Education: IITs, NITs, IIITs, Government Engineering Colleges, Private Engineering Colleges
- Medical Education: AIIMS, Government Medical Colleges, Private Medical Colleges
- Management Education: IIMs, Top B-Schools, Regional Management Institutes
- Professional Education: CA, CS, CMA, Law, Architecture, Pharmacy
- Research Institutions: IISc, CSIR Labs, DRDO, ISRO, BARC
- Distance Learning: IGNOU, State Open Universities, Online Platforms

INDUSTRY-SPECIFIC EDUCATIONAL REQUIREMENTS:
- Technology: Engineering, Computer Science, IT, Data Science
- Healthcare: MBBS, BDS, BAMS, BHMS, Nursing, Pharmacy, Allied Health
- Engineering: Mechanical, Civil, Electrical, Chemical, Aerospace, etc.
- Finance: CA, CS, CMA, MBA Finance, Economics, Commerce
- Legal: LLB, LLM, Company Secretary, Legal Practice
- Government: Civil Services, Public Administration, Specialized Training
- Education: B.Ed, M.Ed, PhD, Teaching Certifications
- Media: Journalism, Mass Communication, Digital Media

RESPONSE FORMAT (JSON):
{{
    "education_overview": {{
        "highest_qualification": "Master of Technology",
        "primary_field": "Computer Science Engineering",
        "education_level_score": 88,
        "institution_prestige_score": 92,
        "academic_performance_score": 85,
        "industry_alignment_score": 90
    }},
    "formal_education": [
        {{
            "degree": "Bachelor of Technology",
            "field": "Computer Science Engineering",
            "institution": "Indian Institute of Technology, Delhi",
            "university": "IIT Delhi",
            "year_of_passing": 2020,
            "duration": "4 years",
            "grade": "8.5 CGPA",
            "percentage": "85%",
            "class": "First Class with Distinction",
            "institution_ranking": {{
                "nirf_ranking": 2,
                "global_ranking": "QS 185",
                "tier": "Tier 1",
                "accreditation": ["NAAC A++", "NBA", "AICTE"]
            }},
            "entrance_exam": {{
                "exam": "JEE Advanced",
                "rank": "AIR 1250",
                "percentile": "99.2"
            }},
            "specialization": "Artificial Intelligence & Machine Learning",
            "thesis_project": "Deep Learning for Natural Language Processing",
            "relevance_score": 95,
            "prestige_score": 98,
            "indian_context": {{
                "recognized_by": ["UGC", "AICTE"],
                "indian_equivalent": "B.Tech CSE",
                "industry_recognition": "Highest"
            }}
        }}
    ],
    "professional_certifications": [
        {{
            "name": "Chartered Accountant",
            "issuing_body": "Institute of Chartered Accountants of India (ICAI)",
            "year_obtained": 2023,
            "registration_number": "123456",
            "status": "Active",
            "validity": "Lifetime",
            "exam_attempts": 2,
            "rank": "AIR 45",
            "indian_recognition": "Highest",
            "global_recognition": "High",
            "industry_relevance": 98,
            "continuing_education": "40 hours annually"
        }},
        {{
            "name": "AWS Solutions Architect Professional",
            "issuing_organization": "Amazon Web Services",
            "year_obtained": 2023,
            "expiry_date": "2026",
            "status": "Active",
            "difficulty_level": "Advanced",
            "global_recognition": "High",
            "indian_market_value": "Very High",
            "relevance_score": 92
        }}
    ],
    "specialized_training": [
        {{
            "course": "Advanced Data Analytics",
            "provider": "Indian Statistical Institute",
            "completion_year": 2023,
            "duration": "6 months",
            "mode": "Full-time",
            "certificate": "Yes",
            "grade": "A+",
            "industry_relevance": 88,
            "skills_gained": ["Statistical Modeling", "Python", "R", "Machine Learning"]
        }}
    ],
    "academic_achievements": [
        {{
            "achievement": "University Gold Medal",
            "year": 2020,
            "institution": "IIT Delhi",
            "category": "Academic Excellence",
            "description": "Highest CGPA in Computer Science Engineering"
        }},
        {{
            "achievement": "National Science Talent Search Scholar",
            "year": 2016,
            "organization": "NCERT",
            "scholarship_amount": "₹1,25,000 annually"
        }}
    ],
    "research_experience": [
        {{
            "type": "Undergraduate Research",
            "project": "Machine Learning for Healthcare Applications",
            "institution": "IIT Delhi",
            "supervisor": "Dr. Rajesh Kumar",
            "duration": "1 year",
            "publications": 2,
            "conferences": 1,
            "research_area": "Applied AI in Healthcare"
        }}
    ],
    "competitive_exams": [
        {{
            "exam": "GATE Computer Science",
            "year": 2020,
            "score": 985,
            "rank": "AIR 25",
            "percentile": "99.8",
            "qualifying_score": 25.0
        }}
    ],
    "international_education": [
        {{
            "type": "Exchange Program",
            "institution": "Stanford University",
            "country": "USA",
            "duration": "1 semester",
            "year": 2019,
            "program": "Computer Science Research",
            "credits_earned": 15,
            "indian_equivalency": "Recognized by UGC"
        }}
    ],
    "online_learning": [
        {{
            "platform": "Coursera",
            "course": "Machine Learning Specialization",
            "provider": "Stanford University",
            "completion_year": 2022,
            "certificate": "Verified Certificate",
            "skills": ["Supervised Learning", "Unsupervised Learning", "Neural Networks"]
        }}
    ],
    "language_proficiency": [
        {{
            "language": "English",
            "proficiency": "Native/Bilingual",
            "certification": "IELTS 8.5",
            "context": "Academic and Professional"
        }},
        {{
            "language": "Hindi",
            "proficiency": "Native",
            "context": "Professional communication"
        }}
    ],
    "education_metrics": {{
        "total_years_education": 18,
        "formal_education_years": 16,
        "professional_development_hours": 200,
        "certifications_count": 8,
        "active_certifications": 6,
        "research_publications": 3,
        "conference_presentations": 2,
        "learning_frequency": "Regular",
        "recent_learning": "Yes"
    }},
    "education_quality_assessment": {{
        "institution_prestige": {{
            "tier_1_institutions": 2,
            "tier_2_institutions": 0,
            "tier_3_institutions": 0,
            "overall_prestige_score": 95
        }},
        "academic_performance": {{
            "consistent_high_grades": "Yes",
            "competitive_exam_success": "Excellent",
            "scholarship_recipient": "Yes",
            "performance_score": 92
        }},
        "specialization_depth": {{
            "focused_specialization": "Yes",
            "interdisciplinary_knowledge": "Yes",
            "depth_vs_breadth": "Balanced",
            "specialization_score": 88
        }},
        "continuous_learning": {{
            "recent_certifications": "Yes",
            "skill_updates": "Regular",
            "industry_awareness": "High",
            "learning_score": 90
        }}
    }},
    "indian_education_context": {{
        "education_board": "CBSE",
        "school_performance": {{
            "class_10_percentage": "95%",
            "class_12_percentage": "96%",
            "stream": "Science (PCM)"
        }},
        "entrance_exam_performance": {{
            "jee_main_rank": "AIR 245",
            "jee_advanced_rank": "AIR 1250",
            "state_entrance_rank": "State Rank 15"
        }},
        "reservation_category": "General",
        "scholarship_history": [
            "Merit-cum-Means Scholarship",
            "National Talent Search Scholarship"
        ],
        "regional_advantages": [
            "Multilingual communication",
            "Cultural adaptability",
            "Local market understanding"
        ]
    }},
    "career_education_alignment": {{
        "education_career_match": 95,
        "skill_transferability": 88,
        "knowledge_application": 92,
        "career_progression_support": 90,
        "future_learning_needs": [
            "Advanced AI/ML certifications",
            "Leadership development programs",
            "Industry-specific domain knowledge"
        ]
    }},
    "strengths": [
        "Excellent academic track record from premier institutions",
        "Strong foundation in core subjects with specialized expertise",
        "Consistent high performance in competitive examinations",
        "Active pursuit of continuous learning and certifications",
        "Well-rounded education with research experience"
    ],
    "weaknesses": [
        "Limited international education exposure",
        "Could benefit from more industry-specific certifications",
        "No management or business education background"
    ],
    "recommendations": [
        "Consider pursuing advanced management education (MBA/PGDM)",
        "Obtain international certifications for global recognition",
        "Pursue industry-specific advanced certifications",
        "Consider doctoral studies for research-oriented career paths",
        "Develop cross-functional knowledge through interdisciplinary courses"
    ],
    "overall_education_score": 91,
    "confidence_level": 0.88
}}

Provide comprehensive analysis considering the Indian education system, institutional rankings, professional body recognition, and industry-specific educational requirements.
"""
    
    async def analyze(self, resume_text: str, context: Dict[str, Any] = None) -> AgentResult:
        start_time = time.time()
        
        try:
            # Build and execute prompt
            prompt = self._build_prompt(resume_text, context)
            raw_response = await self._call_model(prompt)
            
            # Parse response
            analysis = self._parse_education_response(raw_response)
            
            # Calculate metrics
            score = analysis.get('overall_education_score', 0)
            confidence = analysis.get('confidence_level', 0.5)
            strengths = analysis.get('strengths', [])
            weaknesses = analysis.get('weaknesses', [])
            recommendations = analysis.get('recommendations', [])
            
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_name=self.name,
                score=score,
                confidence=confidence,
                analysis=analysis,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                processing_time=processing_time,
                raw_output=raw_response
            )
            
        except Exception as e:
            logger.error(f"Education analysis failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_name=self.name,
                score=0,
                confidence=0,
                analysis={"error": str(e)},
                strengths=[],
                weaknesses=["Analysis failed"],
                recommendations=["Retry analysis"],
                processing_time=processing_time,
                raw_output=f"Error: {str(e)}"
            )
    
    def _parse_education_response(self, response: str) -> Dict[str, Any]:
        """Parse the education analysis response."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback parsing if JSON extraction fails
        return self._fallback_parse_education(response)
    
    def _fallback_parse_education(self, response: str) -> Dict[str, Any]:
        """Fallback parsing method when JSON parsing fails."""
        return {
            "formal_education": [],
            "certifications": [],
            "professional_training": [],
            "academic_achievements": [],
            "research_experience": [],
            "learning_metrics": {
                "education_level": "Unknown",
                "years_since_graduation": 0,
                "certification_count": 0,
                "active_certifications": 0,
                "recent_learning": "Unknown",
                "learning_frequency": "Unknown"
            },
            "education_quality": {
                "institution_prestige": 70,
                "degree_relevance": 70,
                "academic_performance": 70,
                "specialization_depth": 70,
                "overall_quality_score": 70
            },
            "certification_assessment": {
                "industry_recognition": 60,
                "technical_depth": 60,
                "currency": 60,
                "diversity": 60,
                "career_alignment": 60,
                "certification_score": 60
            },
            "continuous_learning": {
                "recent_courses": 0,
                "learning_platforms": [],
                "skill_areas": [],
                "learning_commitment": "Unknown",
                "growth_mindset": "Unknown",
                "learning_score": 60
            },
            "knowledge_gaps": ["Insufficient educational data"],
            "strengths": [],
            "weaknesses": ["Limited educational information"],
            "recommendations": ["Provide more detailed educational background"],
            "overall_education_score": 65,
            "confidence_level": 0.3,
            "parsing_method": "fallback"
        }
