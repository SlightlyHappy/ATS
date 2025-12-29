"""
Multi-Agent Resume Analysis Pipeline with Realistic Scoring Framework
This module implements specialized AI agents for comprehensive resume evaluation.
"""

import json
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
from multi_provider_ai import multi_provider_ai
from market_config import (
    get_market_data, get_skill_market_value, calculate_realistic_score_adjustment,
    SCORING_DISTRIBUTION, MARKET_ADJUSTMENTS, EXPERIENCE_BENCHMARKS
)

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
    
    def __init__(self):
        # Use scoring distribution from market config
        self.score_distribution = SCORING_DISTRIBUTION
        
        # Historical scoring data for calibration
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
        
        # Ensure score stays within bounds
        return max(20, min(95, calibrated))
    
    def _get_role_competitiveness_adjustment(self, role_type: str) -> float:
        """Get competitiveness adjustment based on role type."""
        # More competitive roles should have lower average scores
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
                target_range = self.score_distribution["exceptional"]["range"]
            elif percentile >= 0.80:
                target_range = self.score_distribution["strong"]["range"]
            elif percentile >= 0.50:
                target_range = self.score_distribution["good"]["range"]
            elif percentile >= 0.15:
                target_range = self.score_distribution["average"]["range"]
            else:
                target_range = self.score_distribution["below_average"]["range"]
            
            # Adjust score to fit target range while maintaining relative ranking
            current_score = candidate.get('overall_score', 50)
            target_min, target_max = target_range
            
            # Calculate adjusted score within target range
            position_in_range = (i % (total_candidates // 5)) / max(1, (total_candidates // 5))
            adjusted_score = target_min + (target_max - target_min) * (1 - position_in_range)
            
            candidate['overall_score'] = round(adjusted_score, 1)
            candidate['market_percentile'] = round(percentile * 100, 1)
        
        return sorted_candidates

class SkillsValidatorAgent:
    """Agent specialized in validating technical skills and experience claims."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.agent_name = "Skills Validator"
        
        # Use skill market data from config
        self.skill_market_data = {}
        # Will be populated from market_config when needed
    
    def analyze(self, resume_data: Dict, market_context: MarketContext) -> AgentResult:
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
            response = self.ai_provider.generate_response(prompt, format_json=True)
            
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
            logger.error(f"Skills validation failed: {e}")
            return self._create_fallback_result()
    
    def _apply_market_adjustments(self, raw_score: float, resume_data: Dict, market_context: MarketContext) -> float:
        """Apply market-based adjustments to technical skills score."""
        skills = [skill.lower() for skill in resume_data.get('skills', [])]
        
        # Use market config for skill evaluation
        demand_bonus = 0
        rare_skill_bonus = 0
        
        for skill in skills:
            skill_data = get_skill_market_value(skill)
            demand_bonus += skill_data['demand'] * 2
            if skill_data['market_value'] > 85:  # High-value skill
                rare_skill_bonus += 3
        
        # Apply market saturation penalty from config
        saturation_penalty = market_context.market_saturation * MARKET_ADJUSTMENTS['high_saturation'] if market_context.market_saturation > 0.7 else 0
        
        adjusted_score = raw_score + demand_bonus + rare_skill_bonus + saturation_penalty
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

class ExperienceAssessorAgent:
    """Agent specialized in evaluating work experience and career progression."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.agent_name = "Experience Assessor"
        
        # Use career benchmarks from config
        self.career_benchmarks = EXPERIENCE_BENCHMARKS.get("title_progression_patterns", {})
    
    def analyze(self, resume_data: Dict, market_context: MarketContext) -> AgentResult:
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
            response = self.ai_provider.generate_response(prompt, format_json=True)
            
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
            start_date = exp.get('start_date')
            end_date = exp.get('end_date')
            
            if start_date:
                try:
                    if end_date and end_date.lower() != 'present':
                        # Calculate actual duration
                        start_year = int(start_date.split('-')[0])
                        end_year = int(end_date.split('-')[0])
                        total_months += (end_year - start_year) * 12
                    else:
                        # Current job - calculate from start to now
                        start_year = int(start_date.split('-')[0])
                        current_year = datetime.now().year
                        total_months += (current_year - start_year) * 12
                except:
                    # Fallback: assume 2 years per position
                    total_months += 24
        
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

class RoleFitAnalyzerAgent:
    """Agent specialized in analyzing role fit and requirements matching."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.agent_name = "Role Fit Analyzer"
    
    def analyze(self, resume_data: Dict, role_requirements: str, market_context: MarketContext) -> AgentResult:
        """Analyze role fit against specific requirements."""
        
        prompt = f"""
        You are a role fit assessment expert. Analyze how well this candidate matches the specific role requirements.
        
        ROLE REQUIREMENTS:
        {role_requirements}
        
        MARKET CONTEXT:
        - Role Type: {market_context.role_type}
        - Market Saturation: {market_context.market_saturation:.1%}
        - Expected Salary Range: ${market_context.salary_range[0]:,} - ${market_context.salary_range[1]:,}
        
        CANDIDATE DATA:
        {json.dumps(resume_data, indent=2)}
        
        ASSESSMENT CRITERIA:
        1. Must-have requirements fulfillment
        2. Nice-to-have requirements coverage
        3. Role-specific skill alignment
        4. Cultural and soft skills fit
        5. Overqualification/underqualification risk
        
        Provide detailed analysis in JSON format:
        {{
            "role_fit_score": <20-85>,
            "requirements_match_percentage": <0-100>,
            "must_have_requirements": {{
                "met": ["requirements clearly satisfied"],
                "partially_met": ["requirements somewhat satisfied"],
                "missing": ["critical requirements not met"]
            }},
            "nice_to_have_requirements": {{
                "met": ["bonus requirements satisfied"],
                "missing": ["bonus requirements not met"]
            }},
            "overqualification_risk": <0-100>,
            "underqualification_concerns": ["specific areas of concern"],
            "cultural_fit_indicators": ["positive cultural fit signals"],
            "role_specific_strengths": ["strengths specific to this role"],
            "adaptation_potential": <0-100>,
            "red_flags": ["role-specific concerns"],
            "interview_focus_areas": ["areas to explore in interview"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            response = self.ai_provider.generate_response(prompt, format_json=True)
            
            # Apply role-specific scoring adjustments
            raw_score = response.get('role_fit_score', 50)
            adjusted_score = self._apply_role_fit_adjustments(raw_score, response, market_context)
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "role_fit": adjusted_score,
                    "requirements_match": response.get('requirements_match_percentage', 50),
                    "adaptation_potential": response.get('adaptation_potential', 50)
                },
                analysis=response,
                confidence=response.get('confidence_level', 70),
                red_flags=response.get('red_flags', []),
                strengths=response.get('role_specific_strengths', []),
                recommendations=response.get('interview_focus_areas', [])
            )
            
        except Exception as e:
            logger.error(f"Role fit analysis failed: {e}")
            return self._create_fallback_result()
    
    def _apply_role_fit_adjustments(self, raw_score: float, analysis: Dict, market_context: MarketContext) -> float:
        """Apply market-based adjustments to role fit score."""
        adjusted_score = raw_score
        
        # Penalty for high overqualification risk
        overqualification_risk = analysis.get('overqualification_risk', 0)
        if overqualification_risk > 70:
            adjusted_score -= 10
        
        # Penalty for missing must-have requirements
        missing_requirements = len(analysis.get('must_have_requirements', {}).get('missing', []))
        adjusted_score -= missing_requirements * 15
        
        # Market competition adjustment
        if market_context.market_saturation > 0.7:
            adjusted_score -= 5  # Higher standards in saturated markets
        
        return max(20, min(85, adjusted_score))
    
    def _create_fallback_result(self) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"role_fit": 40, "requirements_match": 40},
            analysis={},
            confidence=30,
            red_flags=["Analysis failed - manual review required"],
            strengths=[],
            recommendations=["Manual role fit assessment recommended"]
        )

class MarketContextProviderAgent:
    """Agent that provides market context and comparative analysis."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.agent_name = "Market Context Provider"
        
        # Sample market data (in a real system, this would come from APIs/databases)
        self.market_data = {
            "software_engineer": {
                "high_demand_locations": ["San Francisco", "New York", "Seattle", "Austin"],
                "salary_ranges": {
                    "junior": (70000, 120000),
                    "mid": (120000, 180000),
                    "senior": (180000, 300000)
                },
                "market_saturation": 0.7,
                "growth_rate": 0.15
            },
            "product_manager": {
                "high_demand_locations": ["San Francisco", "New York", "Seattle"],
                "salary_ranges": {
                    "junior": (80000, 130000),
                    "mid": (130000, 200000),
                    "senior": (200000, 350000)
                },
                "market_saturation": 0.8,
                "growth_rate": 0.12
            }
        }
    
    def get_market_context(self, role_type: str, location: str = "general") -> MarketContext:
        """Generate market context for the given role and location."""
        
        # Get market data from config
        market_data = get_market_data(role_type)
        
        # Determine experience level (this would be calculated from resume in real implementation)
        experience_levels = {
            "junior": {"min": 0, "max": 2},
            "mid": {"min": 2, "max": 5}, 
            "senior": {"min": 5, "max": 15}
        }
        
        return MarketContext(
            role_type=role_type,
            location=location,
            experience_level="mid",  # Default, should be determined from resume
            skill_demand=self._get_skill_demand_data(role_type),
            salary_range=market_data["salary_ranges"]["mid"],
            market_saturation=market_data["market_saturation"],
            years_experience_benchmark={"junior": 1, "mid": 3, "senior": 6}
        )
    
    def analyze(self, resume_data: Dict, market_context: MarketContext, comparative_scores: List[float]) -> AgentResult:
        """Provide market context analysis and comparative ranking."""
        
        prompt = f"""
        You are a market analysis expert. Provide context for this candidate relative to market standards.
        
        MARKET DATA:
        - Role: {market_context.role_type}
        - Market Saturation: {market_context.market_saturation:.1%}
        - Salary Range: ${market_context.salary_range[0]:,} - ${market_context.salary_range[1]:,}
        - Location: {market_context.location}
        
        COMPARATIVE DATA:
        - Other Candidate Scores: {comparative_scores}
        - This Candidate's Skills: {resume_data.get('skills', [])}
        
        Provide market analysis in JSON format:
        {{
            "market_competitiveness": <0-100>,
            "salary_expectation_alignment": <0-100>,
            "skill_market_value": <0-100>,
            "location_advantage": <0-100>,
            "market_positioning": "top_tier|competitive|average|below_average",
            "comparative_ranking": "percentile among current batch",
            "market_insights": {{
                "demand_trends": "increasing|stable|declining",
                "competition_level": "low|medium|high|extreme",
                "skill_gaps_in_market": ["skills in short supply"],
                "oversupplied_skills": ["common skills with high competition"]
            }},
            "salary_insights": {{
                "expected_range": [min, max],
                "negotiation_potential": <0-100>,
                "compensation_competitiveness": "below|at|above market"
            }},
            "recommendations": ["market-based recommendations"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            response = self.ai_provider.generate_response(prompt, format_json=True)
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "market_competitiveness": response.get('market_competitiveness', 50),
                    "salary_alignment": response.get('salary_expectation_alignment', 50),
                    "skill_market_value": response.get('skill_market_value', 50)
                },
                analysis=response,
                confidence=response.get('confidence_level', 70),
                red_flags=[],
                strengths=[],
                recommendations=response.get('recommendations', [])
            )
            
        except Exception as e:
            logger.error(f"Market context analysis failed: {e}")
            return self._create_fallback_result()
    
    def _get_skill_demand_data(self, role_type: str) -> Dict[str, float]:
        """Get skill demand data for market context."""
        # Use skill market value data from config
        skill_data = get_skill_market_value()
        
        # Map role types to relevant skills
        role_skill_mapping = {
            "software": ["Python", "React", "Node.js", "SQL", "Docker"],
            "data": ["Python", "SQL", "Machine Learning", "Statistics"],
            "frontend": ["React", "JavaScript", "CSS", "HTML"],
            "backend": ["Python", "Node.js", "SQL", "Docker"],
            "devops": ["Docker", "Kubernetes", "AWS", "CI/CD"],
            "marketing": ["Analytics", "SEO", "Content Marketing"],
            "sales": ["CRM", "Lead Generation", "Negotiation"],
            "finance": ["Excel", "Financial Analysis", "Accounting"]
        }
        
        # Get relevant skills for this role
        relevant_skills = role_skill_mapping.get(role_type, ["General Skills"])
        
        # Return demand scores for relevant skills
        return {skill: skill_data.get(skill, {"demand": 0.5})["demand"] 
                for skill in relevant_skills}
    
    def _create_fallback_result(self) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"market_competitiveness": 50},
            analysis={},
            confidence=30,
            red_flags=[],
            strengths=[],
            recommendations=["Market analysis unavailable"]
        )

class AgenticResumeAnalyzer:
    """Main orchestrator for multi-agent resume analysis."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.scoring_framework = RealisticScoringFramework()
        
        # Initialize specialized agents
        self.skills_validator = SkillsValidatorAgent(ai_provider)
        self.experience_assessor = ExperienceAssessorAgent(ai_provider)
        self.role_fit_analyzer = RoleFitAnalyzerAgent(ai_provider)
        self.market_context_provider = MarketContextProviderAgent(ai_provider)
        
        # Store for comparative analysis
        self.batch_scores = []
    
    def analyze_resume(self, resume_data: Dict, role_requirements: str = "", 
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
            market_context = self.market_context_provider.get_market_context(role_type)
        
        # Run all agents in parallel (conceptually - actual implementation would use threading/async)
        agent_results = []
        
        try:
            # Skills validation
            skills_result = self.skills_validator.analyze(resume_data, market_context)
            agent_results.append(skills_result)
            
            # Experience assessment
            experience_result = self.experience_assessor.analyze(resume_data, market_context)
            agent_results.append(experience_result)
            
            # Role fit analysis (only if role requirements provided)
            if role_requirements:
                role_fit_result = self.role_fit_analyzer.analyze(resume_data, role_requirements, market_context)
                agent_results.append(role_fit_result)
            
            # Market context analysis
            market_result = self.market_context_provider.analyze(
                resume_data, market_context, self.batch_scores
            )
            agent_results.append(market_result)
            
            # Aggregate results
            final_analysis = self._aggregate_agent_results(agent_results, resume_data, market_context)
            
            # Store score for batch comparison
            overall_score = final_analysis.get('scores', {}).get('overall_score', 50)
            self.batch_scores.append(overall_score)
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"Multi-agent analysis failed: {e}")
            return self._create_fallback_analysis(resume_data)
    
    def analyze_batch(self, resume_batch: List[Dict], role_requirements: str = "") -> List[Dict]:
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
        
        # Analyze each resume
        batch_results = []
        for resume_data in resume_batch:
            result = self.analyze_resume(resume_data, role_requirements)
            batch_results.append(result)
        
        # Apply realistic scoring distribution
        batch_results = self.scoring_framework.rank_candidates(batch_results)
        
        return batch_results
    
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
            "technical_skills": 0.25,
            "experience": 0.25,
            "role_fit": 0.30,
            "market_competitiveness": 0.20
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
                "confidence_level": round(statistics.mean(confidence_scores), 1)
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
                "market_calibration_applied": True
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
            f"This candidate scores in the {score_tier} range ({overall_score:.1f}/100) based on comprehensive multi-agent analysis."
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
        experience = resume_data.get('experience', [])
        
        # Check for common role indicators
        if any(skill in skills for skill in ['python', 'javascript', 'java', 'programming']):
            return "Software Engineer"
        elif any(skill in skills for skill in ['product management', 'roadmap', 'user research']):
            return "Product Manager"
        elif any(skill in skills for skill in ['data science', 'machine learning', 'analytics']):
            return "Data Scientist"
        elif role_requirements:
            # Try to extract from role requirements
            if 'engineer' in role_requirements.lower():
                return "Software Engineer"
            elif 'product' in role_requirements.lower():
                return "Product Manager"
        
        return "General"
    
    def _create_fallback_analysis(self, resume_data: Dict) -> Dict[str, Any]:
        """Create fallback analysis if multi-agent analysis fails."""
        return {
            "scores": {
                "overall_score": 40.0,
                "technical_skills": 40.0,
                "experience": 40.0,
                "confidence_level": 30.0
            },
            "analysis": {"error": "Multi-agent analysis failed"},
            "red_flags": ["Analysis system error - manual review required"],
            "strengths": [],
            "recommendations": ["Manual assessment recommended"],
            "executive_summary": "Analysis failed due to system error. Manual review required.",
            "processing_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "error": True
            }
        }
