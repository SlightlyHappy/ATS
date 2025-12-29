from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import json
import re
import time
import logging

logger = logging.getLogger(__name__)

class ExperienceAgent(BaseAgent):
    """Agent specialized in analyzing work experience, career progression, and achievements across all industries in Indian context."""
    
    def __init__(self, model_service, config: Dict[str, Any] = None):
        super().__init__("ExperienceAgent", model_service, config)
        
        # Industry-specific experience evaluation criteria
        self.industry_contexts = {
            "technology": {
                "key_metrics": ["code quality", "system scalability", "user adoption"],
                "career_progression": ["developer", "senior developer", "tech lead", "architect"],
                "achievement_indicators": ["performance optimization", "system design", "team leadership"]
            },
            "healthcare": {
                "key_metrics": ["patient outcomes", "safety protocols", "compliance adherence"],
                "career_progression": ["junior doctor", "resident", "consultant", "department head"],
                "achievement_indicators": ["patient satisfaction", "medical innovations", "research publications"]
            },
            "engineering": {
                "key_metrics": ["project delivery", "quality standards", "cost optimization"],
                "career_progression": ["engineer", "senior engineer", "project manager", "chief engineer"],
                "achievement_indicators": ["design improvements", "cost savings", "safety enhancements"]
            },
            "finance": {
                "key_metrics": ["risk management", "compliance", "profitability"],
                "career_progression": ["analyst", "senior analyst", "manager", "director"],
                "achievement_indicators": ["revenue growth", "risk reduction", "process improvements"]
            }
        }
    
    def get_prompt_template(self) -> str:
        return """
You are a comprehensive career experience analysis expert with deep knowledge of Indian industries, corporate culture, and career progression patterns. Analyze the following resume for work experience quality, achievements, and professional growth across ALL industries.

RESUME TEXT:
{resume_text}

ANALYSIS REQUIREMENTS:
1. Evaluate career progression and growth trajectory across industries
2. Assess role responsibilities and impact in Indian corporate context
3. Analyze achievement quantification and business impact
4. Review industry experience and domain expertise
5. Evaluate leadership and team management in Indian work culture
6. Assess project complexity, scale, and delivery success
7. Review employment stability and career transitions
8. Identify career gaps, job changes, and explanations
9. Evaluate relevance to Indian market requirements
10. Assess overall professional maturity and experience quality

INDIAN INDUSTRY CONTEXTS TO CONSIDER:
- IT Services & Software Development
- Engineering & Manufacturing
- Healthcare & Pharmaceuticals
- Banking & Financial Services
- Government & Public Sector
- Education & Research
- Retail & E-commerce
- Telecommunications
- Energy & Infrastructure
- Agriculture & Food Processing
- Media & Entertainment
- Consulting & Professional Services

INDIAN WORK CULTURE CONSIDERATIONS:
- Hierarchical organizational structures
- Team collaboration and cultural sensitivity
- Multi-generational workplace dynamics
- Regional and linguistic diversity management
- Government compliance and regulatory experience
- Cost optimization and efficiency focus
- Innovation within resource constraints

RESPONSE FORMAT (JSON):
{{
    "career_overview": {{
        "total_experience": "8 years 6 months",
        "relevant_experience": "7 years 2 months",
        "primary_industry": "Information Technology",
        "industry_diversity": ["Technology", "Finance", "Healthcare"],
        "career_level": "Senior Professional",
        "progression_pattern": "Ascending"
    }},
    "career_progression": {{
        "trajectory": "Ascending",
        "growth_rate": "Moderate",
        "consistency": "High",
        "role_transitions": [
            {{
                "from": "Software Engineer",
                "to": "Senior Software Engineer",
                "duration": "2 years",
                "growth_indicators": ["Team leadership", "Technical mentoring"]
            }}
        ],
        "progression_score": 85
    }},
    "work_experience": [
        {{
            "company": "Infosys Limited",
            "role": "Senior Software Engineer",
            "duration": "2 years 3 months",
            "company_type": "MNC",
            "company_size": "Large (>10000)",
            "industry": "IT Services",
            "location": "Bangalore",
            "responsibilities": [
                "Led development team of 8 members",
                "Architected microservices for banking client",
                "Mentored junior developers in technical skills"
            ],
            "achievements": [
                "Reduced system latency by 40% saving ₹2 crore annually",
                "Delivered 3 major projects on time and under budget",
                "Received 'Excellence in Innovation' award"
            ],
            "technologies": ["Java", "Spring Boot", "AWS", "PostgreSQL"],
            "impact_score": 88,
            "relevance_score": 92,
            "leadership_scope": "Team Lead",
            "client_interaction": "Direct",
            "indian_context": {{
                "multicultural_team": "Yes",
                "compliance_experience": "Banking regulations",
                "cost_optimization": "Significant focus"
            }}
        }}
    ],
    "experience_metrics": {{
        "total_years": 8.5,
        "relevant_years": 7.2,
        "leadership_years": 3.5,
        "management_years": 2.0,
        "average_tenure": "2.8 years",
        "career_gaps": [],
        "job_changes": 3,
        "industry_diversity_score": 75,
        "company_diversity": ["Startup", "MNC", "Indian Company"]
    }},
    "achievements_analysis": {{
        "quantified_achievements": 12,
        "revenue_impact_statements": 4,
        "cost_saving_examples": 3,
        "process_improvements": 6,
        "team_building_examples": 2,
        "innovation_examples": 3,
        "client_satisfaction": 2,
        "quality_score": 87,
        "business_impact": "High"
    }},
    "leadership_assessment": {{
        "people_management": {{
            "direct_reports": [3, 5, 8],
            "team_sizes_led": [5, 12, 20],
            "leadership_style": "Collaborative",
            "cross_functional_leadership": "Yes",
            "cultural_sensitivity": "High",
            "mentoring_record": "Strong"
        }},
        "project_leadership": {{
            "project_sizes": ["Small", "Medium", "Large"],
            "budget_responsibility": "₹5 crore",
            "stakeholder_management": "Multi-level",
            "delivery_record": "Excellent"
        }},
        "thought_leadership": {{
            "industry_recognition": "Yes",
            "publications": 2,
            "conference_speaking": 3,
            "community_contributions": "Open source"
        }},
        "leadership_score": 82
    }},
    "domain_expertise": [
        {{
            "domain": "Banking & Financial Services",
            "years": 4,
            "depth": "Deep",
            "specific_areas": ["Core Banking", "Payment Systems", "Risk Management"],
            "compliance_knowledge": ["RBI Guidelines", "SEBI Norms"],
            "evidence": ["Led digital transformation project", "Implemented regulatory compliance"]
        }}
    ],
    "employment_stability": {{
        "average_tenure": 2.8,
        "tenure_trend": "Increasing",
        "job_hopping_risk": "Low",
        "reason_quality": "Career growth focused",
        "stability_score": 84,
        "loyalty_indicators": ["Long tenure at current company", "Internal promotions"]
    }},
    "indian_market_fit": {{
        "cultural_adaptability": {{
            "regional_experience": ["North India", "South India"],
            "language_skills": ["Hindi", "English", "Local language"],
            "cultural_sensitivity": "High",
            "diversity_management": "Proven"
        }},
        "market_understanding": {{
            "indian_business_practices": "Strong",
            "government_sector_experience": "Yes",
            "regulatory_compliance": "Expert",
            "cost_conscious_approach": "Evident"
        }},
        "network_strength": {{
            "industry_connections": "Strong",
            "professional_associations": ["CII", "NASSCOM"],
            "alumni_network": "Active",
            "reference_quality": "High"
        }},
        "market_fit_score": 89
    }},
    "professional_growth": {{
        "skill_development": {{
            "continuous_learning": "Yes",
            "certification_pursuit": "Active",
            "technology_adoption": "Fast",
            "knowledge_sharing": "Regular"
        }},
        "responsibility_growth": {{
            "scope_expansion": "Consistent",
            "complexity_increase": "Yes",
            "decision_making_authority": "Growing",
            "strategic_involvement": "Increasing"
        }},
        "growth_score": 86
    }},
    "strengths": [
        "Excellent career progression with consistent growth",
        "Strong leadership track record in Indian corporate environment",
        "Proven ability to deliver quantified business results",
        "Deep domain expertise in financial services",
        "Cultural adaptability and team management skills"
    ],
    "weaknesses": [
        "Limited international exposure",
        "Could benefit from broader industry experience",
        "No experience with emerging technologies like AI/ML"
    ],
    "recommendations": [
        "Seek international assignment or global project exposure",
        "Consider cross-industry experience to broaden perspective",
        "Pursue advanced leadership development programs",
        "Gain experience with emerging technologies",
        "Build stronger thought leadership through publications"
    ],
    "overall_experience_score": 85,
    "confidence_level": 0.87
}}

Provide comprehensive analysis considering Indian corporate culture, industry-specific expectations, career progression patterns, and the unique aspects of the Indian job market.
"""
    
    async def analyze(self, resume_text: str, context: Dict[str, Any] = None) -> AgentResult:
        start_time = time.time()
        
        try:
            # Build and execute prompt
            prompt = self._build_prompt(resume_text, context)
            raw_response = await self._call_model(prompt)
            
            # Parse response
            analysis = self._parse_experience_response(raw_response)
            
            # Calculate metrics
            score = analysis.get('overall_experience_score', 0)
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
            logger.error(f"Experience analysis failed: {str(e)}")
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
    
    def _parse_experience_response(self, response: str) -> Dict[str, Any]:
        """Parse the experience analysis response."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback parsing if JSON extraction fails
        return self._fallback_parse_experience(response)
    
    def _fallback_parse_experience(self, response: str) -> Dict[str, Any]:
        """Fallback parsing method when JSON parsing fails."""
        return {
            "career_progression": {
                "trajectory": "Unknown",
                "growth_rate": "Unknown", 
                "consistency": "Unknown",
                "score": 70
            },
            "work_experience": [],
            "experience_metrics": {
                "total_years": 0,
                "relevant_years": 0,
                "leadership_years": 0,
                "average_tenure": "Unknown",
                "career_gaps": [],
                "industry_diversity": "Unknown"
            },
            "achievements_quality": {
                "quantified_achievements": 0,
                "impact_statements": 0,
                "leadership_examples": 0,
                "innovation_examples": 0,
                "quality_score": 60
            },
            "domain_expertise": [],
            "leadership_assessment": {
                "people_management": "Unknown",
                "team_sizes": [],
                "leadership_style": "Unknown",
                "mentoring_experience": "Unknown",
                "score": 60
            },
            "employment_stability": {
                "average_tenure": 0,
                "job_hopping_risk": "Unknown",
                "explanation_quality": "Unknown",
                "stability_score": 60
            },
            "strengths": [],
            "weaknesses": ["Insufficient data for analysis"],
            "recommendations": ["Provide more detailed work experience"],
            "overall_experience_score": 65,
            "confidence_level": 0.3,
            "parsing_method": "fallback"
        }
