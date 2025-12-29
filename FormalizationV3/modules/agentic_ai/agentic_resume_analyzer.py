"""
Enhanced Multi-Agent Resume Analysis Pipeline with Realistic Scoring Framework
Adapted for Railway deployment with comprehensive AI provider support
"""

import json
import logging
import statistics
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import os

# Import our enhanced components
from modules.enhanced_ai.multi_provider_ai import MultiProviderAI
from modules.enhanced_ai.market_config import MarketDataProvider
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Market context data for realistic scoring."""
    role_type: str
    location: str
    experience_level: str
    skill_demand: Dict[str, float]  # skill -> demand score (0-1)
    salary_range: Tuple[int, int]
    market_saturation: float  # 0-1, higher means more competitive
    years_experience_benchmark: Dict[str, int]  # level -> typical years

@dataclass
class AgentResult:
    """Result from a specialized agent."""
    agent_name: str
    scores: Dict[str, float]
    analysis: Dict[str, Any]
    confidence: float
    red_flags: List[str]
    strengths: List[str]
    recommendations: List[str]

class RealisticScoringFramework:
    """Framework for realistic resume scoring based on market standards."""
    
    def __init__(self, config: Config):
        self.config = config
        self.score_distribution = config.SCORING_DISTRIBUTION
        self.historical_scores = []
        self.role_benchmarks = {}
        
    def calibrate_score(self, raw_score: float, role_type: str, market_context: MarketContext) -> float:
        """Calibrate raw AI score to realistic market standards."""
        # Apply market saturation penalty
        saturation_penalty = market_context.market_saturation * 10
        
        # Adjust based on role competitiveness
        role_adjustment = self._get_role_competitiveness_adjustment(role_type)
        
        # Calculate calibrated score
        calibrated = raw_score - saturation_penalty - role_adjustment
        
        # Ensure score stays within realistic bounds
        return max(20, min(95, calibrated))
    
    def _get_role_competitiveness_adjustment(self, role_type: str) -> float:
        """Get competitiveness adjustment based on role type."""
        competitive_roles = {
            "software engineer": 5,
            "product manager": 8,
            "data scientist": 7,
            "ux designer": 6,
            "marketing manager": 4
        }
        
        for role, adjustment in competitive_roles.items():
            if role.lower() in role_type.lower():
                return adjustment
        
        return 3  # Default adjustment
    
    def rank_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Rank candidates and adjust scores for realistic distribution."""
        if not candidates:
            return candidates
        
        # Sort by overall score
        sorted_candidates = sorted(candidates, key=lambda x: x.get('overall_score', 0), reverse=True)
        
        # Apply percentile-based adjustments
        total_candidates = len(sorted_candidates)
        
        for i, candidate in enumerate(sorted_candidates):
            percentile = (total_candidates - i) / total_candidates
            
            # Determine target score range based on percentile
            if percentile >= 0.95:
                target_range = (85, 95)  # Exceptional
            elif percentile >= 0.80:
                target_range = (70, 84)  # Strong
            elif percentile >= 0.50:
                target_range = (55, 69)  # Good
            elif percentile >= 0.15:
                target_range = (40, 54)  # Average
            else:
                target_range = (20, 39)  # Below average
            
            # Adjust score to fit target range
            target_min, target_max = target_range
            position_in_range = (i % max(1, (total_candidates // 5))) / max(1, (total_candidates // 5))
            adjusted_score = target_min + (target_max - target_min) * (1 - position_in_range)
            
            candidate['overall_score'] = round(adjusted_score, 1)
            candidate['market_percentile'] = round(percentile * 100, 1)
        
        return sorted_candidates

class TechnicalSkillsAgent:
    """Agent specialized in validating technical skills and experience claims."""
    
    def __init__(self, ai_provider: MultiProviderAI, market_provider: MarketDataProvider):
        self.ai_provider = ai_provider
        self.market_provider = market_provider
        self.agent_name = "Technical Skills Agent"
    
    async def analyze(self, resume_data: Dict, market_context: MarketContext) -> AgentResult:
        """Analyze and validate technical skills."""
        
        prompt = f"""
        You are a technical skills validation expert. Analyze this resume for skill authenticity and market relevance.
        
        MARKET CONTEXT:
        - Role Type: {market_context.role_type}
        - Experience Level Expected: {market_context.experience_level}
        - Market Saturation: {market_context.market_saturation:.1%}
        
        RESUME DATA:
        Skills: {resume_data.get('skills', [])}
        Experience: {resume_data.get('experience', [])}
        Education: {resume_data.get('education', [])}
        Projects: {resume_data.get('projects', [])}
        
        VALIDATION CRITERIA:
        1. Skill-experience alignment (do years of experience match claimed skill levels?)
        2. Technology stack coherence (do skills make sense together?)
        3. Market demand vs. candidate supply
        4. Red flags (unrealistic combinations, buzzword stuffing)
        
        Provide analysis in JSON format:
        {{
            "technical_skills_score": <20-85>,
            "skill_market_alignment": <0-100>,
            "experience_skill_consistency": <0-100>,
            "technology_stack_coherence": <0-100>,
            "validated_skills": ["list of skills that seem authentic"],
            "questionable_skills": ["skills that need verification"],
            "missing_key_skills": ["important skills missing for this role"],
            "skill_demand_analysis": {{
                "high_demand_skills": ["skills in high market demand"],
                "rare_skills": ["uncommon/valuable skills"],
                "oversaturated_skills": ["common skills with high competition"]
            }},
            "red_flags": ["specific concerns about skill claims"],
            "strengths": ["validated technical strengths"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            response = await self.ai_provider.generate_response(prompt, format_json=True)
            
            # Apply market-based scoring adjustments
            raw_score = response.get('technical_skills_score', 50)
            adjusted_score = self._apply_market_adjustments(raw_score, resume_data, market_context)
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "technical_skills": adjusted_score,
                    "skill_market_alignment": response.get('skill_market_alignment', 50),
                    "experience_skill_consistency": response.get('experience_skill_consistency', 50)
                },
                analysis=response,
                confidence=response.get('confidence_level', 70),
                red_flags=response.get('red_flags', []),
                strengths=response.get('strengths', []),
                recommendations=self._generate_skill_recommendations(response, market_context)
            )
            
        except Exception as e:
            logger.error(f"Technical skills analysis failed: {e}")
            return self._create_fallback_result()
    
    def _apply_market_adjustments(self, raw_score: float, resume_data: Dict, market_context: MarketContext) -> float:
        """Apply market-based adjustments to technical skills score."""
        skills = [skill.lower() for skill in resume_data.get('skills', [])]
        
        demand_bonus = 0
        rare_skill_bonus = 0
        
        for skill in skills:
            skill_demand = market_context.skill_demand.get(skill, 0.5)
            demand_bonus += skill_demand * 2
            if skill_demand > 0.85:  # High-value skill
                rare_skill_bonus += 3
        
        # Apply market saturation penalty
        saturation_penalty = market_context.market_saturation * 8 if market_context.market_saturation > 0.7 else 0
        
        adjusted_score = raw_score + demand_bonus + rare_skill_bonus - saturation_penalty
        return max(20, min(85, adjusted_score))
    
    def _generate_skill_recommendations(self, analysis: Dict, market_context: MarketContext) -> List[str]:
        """Generate skill-specific recommendations."""
        recommendations = []
        
        missing_skills = analysis.get('missing_key_skills', [])
        if missing_skills:
            recommendations.append(f"Consider developing: {', '.join(missing_skills[:3])}")
        
        questionable_skills = analysis.get('questionable_skills', [])
        if questionable_skills:
            recommendations.append("Provide specific examples or certifications for claimed skills")
        
        return recommendations
    
    def _create_fallback_result(self) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"technical_skills": 40, "skill_market_alignment": 40},
            analysis={},
            confidence=30,
            red_flags=["Analysis failed - manual review required"],
            strengths=[],
            recommendations=["Manual technical assessment recommended"]
        )

class ExperienceEvaluatorAgent:
    """Agent specialized in evaluating work experience and career progression."""
    
    def __init__(self, ai_provider: MultiProviderAI, market_provider: MarketDataProvider):
        self.ai_provider = ai_provider
        self.market_provider = market_provider
        self.agent_name = "Experience Evaluator Agent"
        
    async def analyze(self, resume_data: Dict, market_context: MarketContext) -> AgentResult:
        """Analyze work experience and career progression."""
        
        experience = resume_data.get('experience', [])
        total_years = self._calculate_total_experience(experience)
        
        prompt = f"""
        You are a career progression expert. Analyze this work experience for authenticity and market standards.
        
        MARKET CONTEXT:
        - Role Type: {market_context.role_type}
        - Expected Experience Level: {market_context.experience_level}
        - Market Benchmarks: {market_context.years_experience_benchmark}
        
        EXPERIENCE DATA:
        Total Years: {total_years}
        Positions: {json.dumps(experience, indent=2)}
        
        ASSESSMENT CRITERIA:
        1. Career progression logic (promotions, responsibility growth)
        2. Job title vs. years of experience alignment
        3. Responsibility claims vs. experience level
        4. Employment gaps and job hopping patterns
        5. Company tier and industry relevance
        
        Analyze in JSON format:
        {{
            "experience_score": <20-85>,
            "career_progression_score": <0-100>,
            "responsibility_authenticity": <0-100>,
            "employment_stability": <0-100>,
            "total_years_experience": {total_years},
            "experience_level_assessment": "junior|mid|senior|expert",
            "career_progression_analysis": {{
                "progression_pattern": "rapid|steady|slow|concerning",
                "title_progression": ["list of title progression"],
                "responsibility_growth": "excellent|good|average|poor"
            }},
            "red_flags": ["specific experience concerns"],
            "employment_gaps": ["identified gaps with analysis"],
            "strengths": ["validated experience strengths"],
            "company_tier_analysis": "startup|mid-size|enterprise|mixed",
            "industry_relevance": <0-100>,
            "confidence_level": <0-100>
        }}
        """
        
        try:
            response = await self.ai_provider.generate_response(prompt, format_json=True)
            
            # Apply experience-based scoring adjustments
            raw_score = response.get('experience_score', 50)
            adjusted_score = self._apply_experience_adjustments(raw_score, response, market_context)
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "experience": adjusted_score,
                    "career_progression": response.get('career_progression_score', 50),
                    "employment_stability": response.get('employment_stability', 50)
                },
                analysis=response,
                confidence=response.get('confidence_level', 70),
                red_flags=response.get('red_flags', []),
                strengths=response.get('strengths', []),
                recommendations=self._generate_experience_recommendations(response, total_years, market_context)
            )
            
        except Exception as e:
            logger.error(f"Experience assessment failed: {e}")
            return self._create_fallback_result(total_years)
    
    def _calculate_total_experience(self, experience: List[Dict]) -> float:
        """Calculate total years of experience."""
        total_months = 0
        for exp in experience:
            duration = exp.get('duration', '')
            
            try:
                # Try to extract years from duration string
                if 'year' in duration.lower():
                    years = float(''.join(filter(str.isdigit, duration.split('year')[0])))
                    total_months += years * 12
                elif 'month' in duration.lower():
                    months = float(''.join(filter(str.isdigit, duration.split('month')[0])))
                    total_months += months
                else:
                    # Fallback: assume 2 years per position
                    total_months += 24
            except:
                total_months += 24  # Default fallback
        
        return total_months / 12
    
    def _apply_experience_adjustments(self, raw_score: float, analysis: Dict, market_context: MarketContext) -> float:
        """Apply market-based adjustments to experience score."""
        adjusted_score = raw_score
        
        # Penalty for employment gaps
        gaps = analysis.get('employment_gaps', [])
        if gaps:
            adjusted_score -= len(gaps) * 5
        
        # Bonus for industry relevance
        industry_relevance = analysis.get('industry_relevance', 50)
        if industry_relevance > 80:
            adjusted_score += 5
        elif industry_relevance < 40:
            adjusted_score -= 10
        
        # Market saturation adjustment
        adjusted_score -= market_context.market_saturation * 8
        
        return max(20, min(85, adjusted_score))
    
    def _generate_experience_recommendations(self, analysis: Dict, total_years: float, market_context: MarketContext) -> List[str]:
        """Generate experience-specific recommendations."""
        recommendations = []
        
        expected_years = market_context.years_experience_benchmark.get(market_context.experience_level, 3)
        
        if total_years < expected_years * 0.8:
            recommendations.append(f"Experience below market expectations for {market_context.experience_level} level")
        
        if analysis.get('employment_gaps'):
            recommendations.append("Address employment gaps in cover letter or interview")
        
        progression = analysis.get('career_progression_analysis', {}).get('progression_pattern', '')
        if progression == 'concerning':
            recommendations.append("Career progression may need explanation")
        
        return recommendations
    
    def _create_fallback_result(self, total_years: float) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"experience": 40, "career_progression": 40},
            analysis={"total_years_experience": total_years},
            confidence=30,
            red_flags=["Analysis failed - manual review required"],
            strengths=[],
            recommendations=["Manual experience assessment recommended"]
        )

class CulturalFitAgent:
    """Agent specialized in analyzing cultural fit and soft skills."""
    
    def __init__(self, ai_provider: MultiProviderAI):
        self.ai_provider = ai_provider
        self.agent_name = "Cultural Fit Agent"
    
    async def analyze(self, resume_data: Dict, market_context: MarketContext) -> AgentResult:
        """Analyze cultural fit and soft skills indicators."""
        
        prompt = f"""
        You are a cultural fit and soft skills expert. Analyze this resume for team compatibility indicators.
        
        ROLE CONTEXT:
        - Role Type: {market_context.role_type}
        - Experience Level: {market_context.experience_level}
        
        RESUME DATA:
        Experience: {resume_data.get('experience', [])}
        Education: {resume_data.get('education', [])}
        Projects: {resume_data.get('projects', [])}
        Summary: {resume_data.get('summary', '')}
        
        ASSESSMENT CRITERIA:
        1. Leadership and teamwork indicators
        2. Communication skills evidence
        3. Adaptability and learning mindset
        4. Problem-solving approach
        5. Cultural values alignment signals
        
        Analyze in JSON format:
        {{
            "cultural_fit_score": <20-85>,
            "leadership_indicators": <0-100>,
            "teamwork_evidence": <0-100>,
            "communication_skills": <0-100>,
            "adaptability_score": <0-100>,
            "soft_skills_analysis": {{
                "identified_soft_skills": ["list of evident soft skills"],
                "leadership_examples": ["evidence of leadership"],
                "collaboration_indicators": ["teamwork evidence"],
                "communication_evidence": ["communication skill indicators"]
            }},
            "cultural_strengths": ["positive cultural fit indicators"],
            "potential_concerns": ["areas that might need attention"],
            "red_flags": ["cultural fit concerns"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            response = await self.ai_provider.generate_response(prompt, format_json=True)
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "cultural_fit": response.get('cultural_fit_score', 50),
                    "leadership_indicators": response.get('leadership_indicators', 50),
                    "communication_skills": response.get('communication_skills', 50)
                },
                analysis=response,
                confidence=response.get('confidence_level', 70),
                red_flags=response.get('red_flags', []),
                strengths=response.get('cultural_strengths', []),
                recommendations=response.get('potential_concerns', [])
            )
            
        except Exception as e:
            logger.error(f"Cultural fit analysis failed: {e}")
            return self._create_fallback_result()
    
    def _create_fallback_result(self) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"cultural_fit": 50},
            analysis={},
            confidence=30,
            red_flags=["Analysis failed - manual review required"],
            strengths=[],
            recommendations=["Manual cultural fit assessment recommended"]
        )

class LegalComplianceAgent:
    """Agent specialized in legal compliance and bias detection."""
    
    def __init__(self, ai_provider: MultiProviderAI):
        self.ai_provider = ai_provider
        self.agent_name = "Legal Compliance Agent"
    
    async def analyze(self, resume_data: Dict, market_context: MarketContext) -> AgentResult:
        """Analyze for legal compliance and bias indicators."""
        
        prompt = f"""
        You are a legal compliance expert specializing in hiring practices. Analyze this resume for compliance issues.
        
        COMPLIANCE CRITERIA:
        1. Age discrimination indicators
        2. Gender bias potential
        3. Disability bias concerns
        4. Educational bias
        5. Geographic bias
        6. Name bias potential
        
        RESUME DATA:
        Name: {resume_data.get('basic_info', {}).get('name', 'N/A')}
        Education: {resume_data.get('education', [])}
        Experience: {resume_data.get('experience', [])}
        Location: {resume_data.get('basic_info', {}).get('location', 'N/A')}
        
        Analyze in JSON format:
        {{
            "compliance_score": <0-100>,
            "bias_risk_assessment": {{
                "age_bias_risk": <0-100>,
                "gender_bias_risk": <0-100>,
                "name_bias_risk": <0-100>,
                "location_bias_risk": <0-100>,
                "education_bias_risk": <0-100>
            }},
            "compliance_flags": ["specific compliance concerns"],
            "bias_mitigation_recommendations": ["recommendations to reduce bias"],
            "legal_strengths": ["positive compliance indicators"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            response = await self.ai_provider.generate_response(prompt, format_json=True)
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "compliance_score": response.get('compliance_score', 85),
                    "bias_risk": 100 - max(response.get('bias_risk_assessment', {}).values()) if response.get('bias_risk_assessment') else 85
                },
                analysis=response,
                confidence=response.get('confidence_level', 80),
                red_flags=response.get('compliance_flags', []),
                strengths=response.get('legal_strengths', []),
                recommendations=response.get('bias_mitigation_recommendations', [])
            )
            
        except Exception as e:
            logger.error(f"Legal compliance analysis failed: {e}")
            return self._create_fallback_result()
    
    def _create_fallback_result(self) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"compliance_score": 85, "bias_risk": 85},
            analysis={},
            confidence=30,
            red_flags=[],
            strengths=[],
            recommendations=["Manual compliance review recommended"]
        )

class AgenticResumeAnalyzer:
    """Main orchestrator for multi-agent resume analysis."""
    
    def __init__(self, config: Config):
        self.config = config
        self.ai_provider = MultiProviderAI(config)
        self.market_provider = MarketDataProvider(config)
        self.scoring_framework = RealisticScoringFramework(config)
        
        # Initialize specialized agents
        self.technical_agent = TechnicalSkillsAgent(self.ai_provider, self.market_provider)
        self.experience_agent = ExperienceEvaluatorAgent(self.ai_provider, self.market_provider)
        self.cultural_agent = CulturalFitAgent(self.ai_provider)
        self.legal_agent = LegalComplianceAgent(self.ai_provider)
        
        # Store for comparative analysis
        self.batch_scores = []
    
    async def analyze_resume(self, resume_data: Dict, role_requirements: str = "", 
                            market_context: Optional[MarketContext] = None) -> Dict[str, Any]:
        """
        Perform comprehensive multi-agent analysis of a resume.
        
        Args:
            resume_data: Parsed resume data
            role_requirements: Job requirements description
            market_context: Market context data
        
        Returns:
            Comprehensive analysis results
        """
        
        # Generate market context if not provided
        if not market_context:
            role_type = self._infer_role_type(resume_data, role_requirements)
            market_context = await self.market_provider.get_market_context(role_type)
        
        # Run all agents concurrently
        agent_tasks = [
            self.technical_agent.analyze(resume_data, market_context),
            self.experience_agent.analyze(resume_data, market_context),
            self.cultural_agent.analyze(resume_data, market_context),
            self.legal_agent.analyze(resume_data, market_context)
        ]
        
        try:
            # Execute all agent analyses concurrently
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            # Filter out any exceptions and create fallback results
            valid_results = []
            for i, result in enumerate(agent_results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {i} failed: {result}")
                    # Create a generic fallback result
                    valid_results.append(AgentResult(
                        agent_name=f"Agent {i}",
                        scores={"score": 40},
                        analysis={},
                        confidence=30,
                        red_flags=["Analysis failed"],
                        strengths=[],
                        recommendations=[]
                    ))
                else:
                    valid_results.append(result)
            
            # Aggregate results
            final_analysis = self._aggregate_agent_results(valid_results, resume_data, market_context)
            
            # Store score for batch comparison
            overall_score = final_analysis.get('scores', {}).get('overall_score', 50)
            self.batch_scores.append(overall_score)
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"Multi-agent analysis failed: {e}")
            return self._create_fallback_analysis(resume_data)
    
    async def analyze_batch(self, resume_batch: List[Dict], role_requirements: str = "") -> List[Dict]:
        """
        Analyze a batch of resumes with comparative ranking.
        
        Args:
            resume_batch: List of resume data dictionaries
            role_requirements: Job requirements description
        
        Returns:
            List of analysis results with comparative rankings
        """
        
        # Clear previous batch scores
        self.batch_scores = []
        
        # Analyze each resume concurrently
        analysis_tasks = [
            self.analyze_resume(resume_data, role_requirements)
            for resume_data in resume_batch
        ]
        
        batch_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [result for result in batch_results if not isinstance(result, Exception)]
        
        # Apply realistic scoring distribution
        ranked_results = self.scoring_framework.rank_candidates(valid_results)
        
        return ranked_results
    
    def _aggregate_agent_results(self, agent_results: List[AgentResult], 
                                resume_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Aggregate results from all agents into final analysis."""
        
        # Collect all scores
        all_scores = {}
        all_red_flags = []
        all_strengths = []
        all_recommendations = []
        confidence_scores = []
        
        for result in agent_results:
            # Aggregate scores
            all_scores.update(result.scores)
            
            # Aggregate insights
            all_red_flags.extend(result.red_flags)
            all_strengths.extend(result.strengths)
            all_recommendations.extend(result.recommendations)
            confidence_scores.append(result.confidence)
        
        # Calculate weighted overall score
        score_weights = {
            "technical_skills": 0.30,
            "experience": 0.30,
            "cultural_fit": 0.25,
            "compliance_score": 0.15
        }
        
        weighted_score = 0
        total_weight = 0
        
        for score_type, weight in score_weights.items():
            if score_type in all_scores:
                weighted_score += all_scores[score_type] * weight
                total_weight += weight
        
        if total_weight > 0:
            overall_score = weighted_score / total_weight
        else:
            overall_score = 50
        
        # Apply final market calibration
        calibrated_score = self.scoring_framework.calibrate_score(
            overall_score, market_context.role_type, market_context
        )
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            agent_results, calibrated_score, all_strengths, all_red_flags
        )
        
        return {
            "scores": {
                "overall_score": round(calibrated_score, 1),
                **{k: round(v, 1) for k, v in all_scores.items()},
                "confidence_level": round(statistics.mean(confidence_scores) if confidence_scores else 50, 1)
            },
            "analysis": {
                "agent_results": [
                    {
                        "agent": result.agent_name,
                        "analysis": result.analysis,
                        "confidence": result.confidence
                    } for result in agent_results
                ],
                "market_context": {
                    "role_type": market_context.role_type,
                    "market_saturation": market_context.market_saturation,
                    "salary_range": market_context.salary_range,
                    "location": market_context.location
                }
            },
            "red_flags": list(set(all_red_flags)),  # Remove duplicates
            "strengths": list(set(all_strengths)),
            "recommendations": list(set(all_recommendations)),
            "executive_summary": executive_summary,
            "processing_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "agents_used": [result.agent_name for result in agent_results],
                "market_calibration_applied": True,
                "agentic_analysis": True
            }
        }
    
    def _generate_executive_summary(self, agent_results: List[AgentResult], 
                                   overall_score: float, strengths: List[str], 
                                   red_flags: List[str]) -> str:
        """Generate executive summary of the analysis."""
        
        score_tier = "exceptional" if overall_score >= 85 else \
                    "strong" if overall_score >= 70 else \
                    "good" if overall_score >= 55 else \
                    "average" if overall_score >= 40 else "below average"
        
        summary_parts = [
            f"This candidate scores in the {score_tier} range ({overall_score:.1f}/100) based on comprehensive 4-agent analysis."
        ]
        
        if strengths:
            summary_parts.append(f"Key strengths include: {', '.join(strengths[:3])}.")
        
        if red_flags:
            summary_parts.append(f"Areas of concern: {', '.join(red_flags[:2])}.")
        
        summary_parts.append("Scores have been calibrated against current market standards and competitive landscape.")
        
        return " ".join(summary_parts)
    
    def _infer_role_type(self, resume_data: Dict, role_requirements: str) -> str:
        """Infer role type from resume data and requirements."""
        
        # Simple inference based on skills and experience
        skills = [skill.lower() for skill in resume_data.get('skills', [])]
        
        # Check for common role indicators
        if any(skill in skills for skill in ['python', 'javascript', 'java', 'programming', 'software']):
            return "software_engineer"
        elif any(skill in skills for skill in ['product management', 'roadmap', 'user research']):
            return "product_manager"
        elif any(skill in skills for skill in ['data science', 'machine learning', 'analytics']):
            return "data_scientist"
        elif any(skill in skills for skill in ['design', 'figma', 'ui', 'ux']):
            return "designer"
        elif role_requirements:
            # Try to extract from role requirements
            if 'engineer' in role_requirements.lower():
                return "software_engineer"
            elif 'product' in role_requirements.lower():
                return "product_manager"
            elif 'data' in role_requirements.lower():
                return "data_scientist"
        
        return "general"
    
    def _create_fallback_analysis(self, resume_data: Dict) -> Dict[str, Any]:
        """Create fallback analysis if multi-agent analysis fails."""
        return {
            "scores": {
                "overall_score": 40.0,
                "technical_skills": 40.0,
                "experience": 40.0,
                "cultural_fit": 40.0,
                "confidence_level": 30.0
            },
            "analysis": {"error": "Multi-agent analysis failed"},
            "red_flags": ["Analysis system error - manual review required"],
            "strengths": [],
            "recommendations": ["Manual assessment recommended"],
            "executive_summary": "Analysis failed due to system error. Manual review required.",
            "processing_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "error": True,
                "agentic_analysis": False
            }
        }
