"""
Enhanced Agentic Resume Analyzer - Railway Compatible
===================================================

Advanced multi-agent resume analysis with market-aware scoring and realistic calibration.
Built for dynamic initialization on Railway platform.
"""

import json
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

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

@dataclass
class MarketContext:
    """Market context data for realistic scoring."""
    role_type: str
    location: str
    experience_level: str
    market_saturation: float
    salary_range: Tuple[int, int]
    skill_demand: Dict[str, float]

class RealisticScoringFramework:
    """Framework for realistic resume scoring based on market standards."""
    
    def __init__(self):
        # Realistic score distribution (prevents AI score inflation)
        self.score_distribution = {
            "exceptional": {"range": (85, 95), "percentage": 5},
            "strong": {"range": (70, 84), "percentage": 15},
            "good": {"range": (55, 69), "percentage": 30},
            "average": {"range": (40, 54), "percentage": 35},
            "below_average": {"range": (20, 39), "percentage": 15}
        }
        
        self.historical_scores = []
        
    def calibrate_score(self, raw_score: float, role_type: str, market_context: MarketContext) -> float:
        """Calibrate raw AI score to realistic market standards."""
        # Apply market saturation penalty (more competitive = lower scores)
        saturation_penalty = market_context.market_saturation * 12
        
        # Apply role competitiveness adjustment
        role_adjustment = self._get_role_competitiveness_adjustment(role_type)
        
        # Calculate calibrated score
        calibrated = raw_score - saturation_penalty - role_adjustment
        
        # Ensure realistic bounds (AI tends to over-score)
        return max(25, min(90, calibrated))
    
    def _get_role_competitiveness_adjustment(self, role_type: str) -> float:
        """Get competitiveness adjustment based on role type."""
        competitive_roles = {
            "software engineer": 8,
            "product manager": 10,
            "data scientist": 9,
            "ux designer": 7,
            "marketing manager": 5,
            "sales": 4,
            "hr": 3
        }
        
        for role, adjustment in competitive_roles.items():
            if role.lower() in role_type.lower():
                return adjustment
        
        return 5  # Default adjustment
    
    def rank_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Rank candidates and apply realistic score distribution."""
        if not candidates:
            return candidates
        
        # Sort by overall score
        sorted_candidates = sorted(candidates, key=lambda x: x.get('overall_score', 0), reverse=True)
        total_candidates = len(sorted_candidates)
        
        # Apply percentile-based realistic scoring
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
            
            # Adjust score to fit realistic distribution
            target_min, target_max = target_range
            position_in_tier = (i % max(1, (total_candidates // 5))) / max(1, (total_candidates // 5))
            adjusted_score = target_min + (target_max - target_min) * (1 - position_in_tier)
            
            candidate['overall_score'] = round(adjusted_score, 1)
            candidate['market_percentile'] = round(percentile * 100, 1)
        
        return sorted_candidates

class TechnicalSkillsAgent:
    """Agent specialized in validating technical skills and experience claims."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.agent_name = "Technical Skills Agent"
        
        # High-demand skills by category
        self.skill_categories = {
            "programming": ["Python", "JavaScript", "Java", "C++", "Go", "Rust"],
            "web": ["React", "Vue", "Angular", "Node.js", "Django", "Flask"],
            "data": ["SQL", "MongoDB", "PostgreSQL", "Redis"],
            "cloud": ["AWS", "Azure", "GCP", "Docker", "Kubernetes"],
            "ai_ml": ["Machine Learning", "TensorFlow", "PyTorch", "NLP"],
            "tools": ["Git", "Jenkins", "CI/CD", "Linux"]
        }
    
    def analyze(self, resume_data: Dict, market_context: MarketContext) -> AgentResult:
        """Analyze and validate technical skills."""
        
        skills = resume_data.get('skills', [])
        experience = resume_data.get('experience', [])
        
        prompt = f"""
        Analyze this candidate's technical skills for authenticity and market relevance.
        
        SKILLS: {skills}
        EXPERIENCE: {json.dumps(experience, indent=2)}
        ROLE TYPE: {market_context.role_type}
        MARKET SATURATION: {market_context.market_saturation:.1%}
        
        Evaluate based on:
        1. Skill-experience alignment (realistic for their experience level?)
        2. Technology stack coherence (do skills work together?)
        3. Market demand vs. candidate's skill level
        4. Red flags (unrealistic combinations, buzzword stuffing)
        
        Respond in JSON format:
        {{
            "technical_skills_score": <25-85>,
            "skill_market_alignment": <0-100>,
            "experience_consistency": <0-100>,
            "validated_skills": ["skills that seem authentic"],
            "questionable_skills": ["skills needing verification"],
            "high_value_skills": ["market-valuable skills they possess"],
            "missing_skills": ["important skills missing for this role"],
            "red_flags": ["specific technical concerns"],
            "strengths": ["validated technical strengths"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            if hasattr(self.ai_provider, 'generate_with_config'):
                response = self.ai_provider.generate_with_config(prompt, format_json=True)
            else:
                response_text = self.ai_provider.generate_text(prompt)
                try:
                    response = json.loads(response_text)
                except:
                    response = {"technical_skills_score": 50, "confidence_level": 40}
            
            # Apply market-based scoring adjustments
            raw_score = response.get('technical_skills_score', 50)
            adjusted_score = self._apply_market_adjustments(raw_score, skills, market_context)
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "technical_skills": adjusted_score,
                    "skill_market_alignment": response.get('skill_market_alignment', 50),
                    "experience_consistency": response.get('experience_consistency', 50)
                },
                analysis=response,
                confidence=response.get('confidence_level', 70),
                red_flags=response.get('red_flags', []),
                strengths=response.get('strengths', []),
                recommendations=self._generate_skill_recommendations(response)
            )
            
        except Exception as e:
            logger.error(f"Technical skills analysis failed: {e}")
            return self._create_fallback_result()
    
    def _apply_market_adjustments(self, raw_score: float, skills: List[str], market_context: MarketContext) -> float:
        """Apply market-based adjustments to technical skills score."""
        adjusted_score = raw_score
        
        # High-demand skill bonus
        high_demand_skills = ["Python", "React", "AWS", "Docker", "Kubernetes", "Machine Learning"]
        demand_bonus = sum(2 for skill in skills if any(hd_skill.lower() in skill.lower() for hd_skill in high_demand_skills))
        
        # Rare skill bonus
        rare_skills = ["Rust", "Go", "Blockchain", "WebAssembly"]
        rare_bonus = sum(3 for skill in skills if any(rare.lower() in skill.lower() for rare in rare_skills))
        
        # Market saturation penalty
        saturation_penalty = market_context.market_saturation * 8
        
        adjusted_score = adjusted_score + demand_bonus + rare_bonus - saturation_penalty
        return max(25, min(85, adjusted_score))
    
    def _generate_skill_recommendations(self, analysis: Dict) -> List[str]:
        """Generate skill-specific recommendations."""
        recommendations = []
        
        missing_skills = analysis.get('missing_skills', [])
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
            scores={"technical_skills": 45, "skill_market_alignment": 45},
            analysis={},
            confidence=35,
            red_flags=["Analysis failed - manual review required"],
            strengths=[],
            recommendations=["Manual technical assessment recommended"]
        )

class ExperienceEvaluatorAgent:
    """Agent specialized in evaluating work experience and career progression."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.agent_name = "Experience Evaluator Agent"
        
        # Career progression benchmarks
        self.progression_patterns = {
            "junior": {"min_years": 0, "max_years": 2, "expected_roles": ["intern", "junior", "associate"]},
            "mid": {"min_years": 2, "max_years": 5, "expected_roles": ["developer", "analyst", "specialist"]},
            "senior": {"min_years": 5, "max_years": 10, "expected_roles": ["senior", "lead", "principal"]},
            "expert": {"min_years": 10, "max_years": 20, "expected_roles": ["staff", "architect", "director"]}
        }
    
    def analyze(self, resume_data: Dict, market_context: MarketContext) -> AgentResult:
        """Analyze work experience and career progression."""
        
        experience = resume_data.get('experience', [])
        total_years = self._calculate_total_experience(experience)
        
        prompt = f"""
        Analyze this candidate's work experience for authenticity and career progression.
        
        EXPERIENCE DATA:
        Total Years: {total_years}
        Positions: {json.dumps(experience, indent=2)}
        
        MARKET CONTEXT:
        Role Type: {market_context.role_type}
        Expected Level: {market_context.experience_level}
        Market Saturation: {market_context.market_saturation:.1%}
        
        Evaluate:
        1. Career progression logic (natural advancement?)
        2. Job title vs. years of experience alignment
        3. Responsibility claims vs. experience level
        4. Employment gaps and job stability
        5. Company quality and industry relevance
        
        Respond in JSON format:
        {{
            "experience_score": <25-85>,
            "career_progression_score": <0-100>,
            "responsibility_authenticity": <0-100>,
            "employment_stability": <0-100>,
            "total_years_experience": {total_years},
            "experience_level_assessment": "junior|mid|senior|expert",
            "progression_pattern": "excellent|good|average|concerning",
            "red_flags": ["specific experience concerns"],
            "employment_gaps": ["identified gaps"],
            "strengths": ["validated experience strengths"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            if hasattr(self.ai_provider, 'generate_with_config'):
                response = self.ai_provider.generate_with_config(prompt, format_json=True)
            else:
                response_text = self.ai_provider.generate_text(prompt)
                try:
                    response = json.loads(response_text)
                except:
                    response = {"experience_score": 50, "confidence_level": 40}
            
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
                recommendations=self._generate_experience_recommendations(response, total_years)
            )
            
        except Exception as e:
            logger.error(f"Experience evaluation failed: {e}")
            return self._create_fallback_result(total_years)
    
    def _calculate_total_experience(self, experience: List[Dict]) -> float:
        """Calculate total years of experience."""
        total_months = 0
        for exp in experience:
            start_date = exp.get('start_date', '2020-01-01')
            end_date = exp.get('end_date', 'present')
            
            try:
                if end_date and end_date.lower() != 'present':
                    start_year = int(start_date.split('-')[0])
                    end_year = int(end_date.split('-')[0])
                    total_months += (end_year - start_year) * 12
                else:
                    start_year = int(start_date.split('-')[0])
                    current_year = datetime.now().year
                    total_months += (current_year - start_year) * 12
            except:
                # Fallback: assume 2 years per position
                total_months += 24
        
        return max(0.5, total_months / 12)
    
    def _apply_experience_adjustments(self, raw_score: float, analysis: Dict, market_context: MarketContext) -> float:
        """Apply market-based adjustments to experience score."""
        adjusted_score = raw_score
        
        # Penalty for employment gaps
        gaps = analysis.get('employment_gaps', [])
        adjusted_score -= len(gaps) * 6
        
        # Penalty for job hopping (more than 4 jobs in 5 years)
        if analysis.get('employment_stability', 100) < 60:
            adjusted_score -= 8
        
        # Market saturation penalty
        adjusted_score -= market_context.market_saturation * 7
        
        return max(25, min(85, adjusted_score))
    
    def _generate_experience_recommendations(self, analysis: Dict, total_years: float) -> List[str]:
        """Generate experience-specific recommendations."""
        recommendations = []
        
        if total_years < 2:
            recommendations.append("Focus on building more substantial work experience")
        
        if analysis.get('employment_gaps'):
            recommendations.append("Address employment gaps in cover letter")
        
        progression = analysis.get('progression_pattern', '')
        if progression == 'concerning':
            recommendations.append("Be prepared to explain career progression choices")
        
        return recommendations
    
    def _create_fallback_result(self, total_years: float) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"experience": 45, "career_progression": 45},
            analysis={"total_years_experience": total_years},
            confidence=35,
            red_flags=["Analysis failed - manual review required"],
            strengths=[],
            recommendations=["Manual experience assessment recommended"]
        )

class CulturalFitAgent:
    """Agent specialized in analyzing cultural fit and soft skills."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.agent_name = "Cultural Fit Agent"
    
    def analyze(self, resume_data: Dict, job_description: str, market_context: MarketContext) -> AgentResult:
        """Analyze cultural fit and soft skills alignment."""
        
        prompt = f"""
        Analyze this candidate's cultural fit and soft skills based on their resume.
        
        CANDIDATE DATA:
        Skills: {resume_data.get('skills', [])}
        Experience: {resume_data.get('experience', [])}
        Education: {resume_data.get('education', [])}
        Projects: {resume_data.get('projects', [])}
        
        JOB DESCRIPTION:
        {job_description}
        
        Evaluate:
        1. Communication skills (evident from resume presentation)
        2. Leadership potential (from experience descriptions)
        3. Collaboration indicators (team projects, cross-functional work)
        4. Learning agility (diverse experiences, continuous learning)
        5. Cultural alignment with role requirements
        
        Respond in JSON format:
        {{
            "cultural_fit_score": <25-85>,
            "communication_skills": <0-100>,
            "leadership_potential": <0-100>,
            "collaboration_indicators": <0-100>,
            "learning_agility": <0-100>,
            "soft_skills_identified": ["identified soft skills"],
            "cultural_fit_indicators": ["positive cultural signals"],
            "red_flags": ["cultural fit concerns"],
            "strengths": ["cultural/soft skill strengths"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            if hasattr(self.ai_provider, 'generate_with_config'):
                response = self.ai_provider.generate_with_config(prompt, format_json=True)
            else:
                response_text = self.ai_provider.generate_text(prompt)
                try:
                    response = json.loads(response_text)
                except:
                    response = {"cultural_fit_score": 50, "confidence_level": 40}
            
            raw_score = response.get('cultural_fit_score', 50)
            adjusted_score = self._apply_cultural_adjustments(raw_score, response)
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "cultural_fit": adjusted_score,
                    "communication_skills": response.get('communication_skills', 50),
                    "leadership_potential": response.get('leadership_potential', 50),
                    "learning_agility": response.get('learning_agility', 50)
                },
                analysis=response,
                confidence=response.get('confidence_level', 65),
                red_flags=response.get('red_flags', []),
                strengths=response.get('strengths', []),
                recommendations=self._generate_cultural_recommendations(response)
            )
            
        except Exception as e:
            logger.error(f"Cultural fit analysis failed: {e}")
            return self._create_fallback_result()
    
    def _apply_cultural_adjustments(self, raw_score: float, analysis: Dict) -> float:
        """Apply adjustments based on cultural fit indicators."""
        adjusted_score = raw_score
        
        # Bonus for strong soft skills
        soft_skills = analysis.get('soft_skills_identified', [])
        if len(soft_skills) > 3:
            adjusted_score += 5
        
        # Penalty for red flags
        red_flags = analysis.get('red_flags', [])
        adjusted_score -= len(red_flags) * 4
        
        return max(25, min(85, adjusted_score))
    
    def _generate_cultural_recommendations(self, analysis: Dict) -> List[str]:
        """Generate cultural fit recommendations."""
        recommendations = []
        
        if analysis.get('communication_skills', 50) < 60:
            recommendations.append("Focus on demonstrating communication skills in interview")
        
        if analysis.get('leadership_potential', 50) < 50:
            recommendations.append("Prepare examples of leadership or initiative-taking")
        
        return recommendations
    
    def _create_fallback_result(self) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"cultural_fit": 50, "communication_skills": 50},
            analysis={},
            confidence=35,
            red_flags=["Analysis failed - manual review required"],
            strengths=[],
            recommendations=["Manual cultural assessment recommended"]
        )

class LegalComplianceAgent:
    """Agent specialized in legal compliance and bias detection."""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.agent_name = "Legal Compliance Agent"
        
        # Protected characteristics to avoid bias
        self.protected_characteristics = [
            "age", "gender", "race", "ethnicity", "religion", "disability",
            "sexual orientation", "marital status", "pregnancy", "nationality"
        ]
    
    def analyze(self, resume_data: Dict, evaluation_notes: str = "") -> AgentResult:
        """Analyze for legal compliance and bias detection."""
        
        prompt = f"""
        Review this resume analysis for legal compliance and bias detection.
        
        RESUME DATA:
        {json.dumps(resume_data, indent=2)}
        
        EVALUATION NOTES:
        {evaluation_notes}
        
        Check for:
        1. Bias indicators in skills assessment
        2. Discriminatory language or assumptions
        3. Over-emphasis on protected characteristics
        4. Fair and objective evaluation criteria
        5. Compliance with employment law
        
        Respond in JSON format:
        {{
            "compliance_score": <0-100>,
            "bias_detected": <0-100>,
            "legal_risks": ["potential legal issues"],
            "bias_indicators": ["detected bias patterns"],
            "compliance_strengths": ["good compliance practices"],
            "recommendations": ["compliance improvements"],
            "red_flags": ["serious legal concerns"],
            "confidence_level": <0-100>
        }}
        """
        
        try:
            if hasattr(self.ai_provider, 'generate_with_config'):
                response = self.ai_provider.generate_with_config(prompt, format_json=True)
            else:
                response_text = self.ai_provider.generate_text(prompt)
                try:
                    response = json.loads(response_text)
                except:
                    response = {"compliance_score": 85, "confidence_level": 70}
            
            return AgentResult(
                agent_name=self.agent_name,
                scores={
                    "legal_compliance": response.get('compliance_score', 85),
                    "bias_risk": 100 - response.get('bias_detected', 15)  # Invert bias score
                },
                analysis=response,
                confidence=response.get('confidence_level', 75),
                red_flags=response.get('red_flags', []),
                strengths=response.get('compliance_strengths', []),
                recommendations=response.get('recommendations', [])
            )
            
        except Exception as e:
            logger.error(f"Legal compliance analysis failed: {e}")
            return self._create_fallback_result()
    
    def _create_fallback_result(self) -> AgentResult:
        """Create fallback result if analysis fails."""
        return AgentResult(
            agent_name=self.agent_name,
            scores={"legal_compliance": 85, "bias_risk": 85},
            analysis={},
            confidence=70,
            red_flags=["Compliance analysis failed - manual review required"],
            strengths=[],
            recommendations=["Manual legal compliance review recommended"]
        )

class EnhancedAgenticResumeProcessor:
    """Main orchestrator for enhanced multi-agent resume analysis."""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider
        self.scoring_framework = RealisticScoringFramework()
        
        # Initialize specialized agents
        self.technical_agent = TechnicalSkillsAgent(ai_provider)
        self.experience_agent = ExperienceEvaluatorAgent(ai_provider)
        self.cultural_agent = CulturalFitAgent(ai_provider)
        self.legal_agent = LegalComplianceAgent(ai_provider)
        
        # Store for batch processing
        self.batch_scores = []
    
    def analyze_resume(self, resume_data: Dict, job_description: str = "") -> Dict[str, Any]:
        """
        Perform comprehensive multi-agent analysis of a resume.
        
        Args:
            resume_data: Parsed resume data
            job_description: Job description for role-specific analysis
        
        Returns:
            Comprehensive analysis results with realistic scoring
        """
        try:
            # Create market context
            market_context = self._create_market_context(resume_data, job_description)
            
            # Run all agents
            agent_results = []
            
            # Technical skills analysis
            technical_result = self.technical_agent.analyze(resume_data, market_context)
            agent_results.append(technical_result)
            
            # Experience evaluation
            experience_result = self.experience_agent.analyze(resume_data, market_context)
            agent_results.append(experience_result)
            
            # Cultural fit analysis
            cultural_result = self.cultural_agent.analyze(resume_data, job_description, market_context)
            agent_results.append(cultural_result)
            
            # Legal compliance check
            legal_result = self.legal_agent.analyze(resume_data)
            agent_results.append(legal_result)
            
            # Aggregate results with realistic scoring
            final_analysis = self._aggregate_results(agent_results, market_context)
            
            # Store score for batch comparison
            overall_score = final_analysis.get('overall_score', 50)
            self.batch_scores.append(overall_score)
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"Enhanced agentic analysis failed: {e}")
            return self._create_fallback_analysis(resume_data)
    
    def analyze_batch(self, resume_batch: List[Dict], job_description: str = "") -> List[Dict]:
        """
        Analyze a batch of resumes with comparative ranking and realistic scoring.
        
        Args:
            resume_batch: List of resume data dictionaries
            job_description: Job description for role-specific analysis
        
        Returns:
            List of analysis results with realistic score distribution
        """
        # Clear previous batch scores
        self.batch_scores = []
        
        # Analyze each resume
        batch_results = []
        for resume_data in resume_batch:
            result = self.analyze_resume(resume_data, job_description)
            batch_results.append(result)
        
        # Apply realistic scoring distribution
        batch_results = self.scoring_framework.rank_candidates(batch_results)
        
        return batch_results
    
    def _create_market_context(self, resume_data: Dict, job_description: str) -> MarketContext:
        """Create market context for scoring calibration."""
        # Infer role type from job description or resume
        role_type = self._infer_role_type(job_description, resume_data)
        
        # Create realistic market context
        return MarketContext(
            role_type=role_type,
            location="general",
            experience_level="mid",  # Default
            market_saturation=0.7,  # Assume competitive market
            salary_range=(60000, 120000),  # Default range
            skill_demand={"python": 0.8, "javascript": 0.7, "sql": 0.6}
        )
    
    def _infer_role_type(self, job_description: str, resume_data: Dict) -> str:
        """Infer role type from job description and resume data."""
        text_to_analyze = (job_description + " " + 
                          " ".join(resume_data.get('skills', [])) + " " +
                          " ".join([exp.get('title', '') for exp in resume_data.get('experience', [])])).lower()
        
        # Role type detection patterns
        if any(keyword in text_to_analyze for keyword in ['software', 'developer', 'engineer', 'programming']):
            return "Software Engineer"
        elif any(keyword in text_to_analyze for keyword in ['product manager', 'product owner', 'pm']):
            return "Product Manager"
        elif any(keyword in text_to_analyze for keyword in ['data scientist', 'data analyst', 'machine learning']):
            return "Data Scientist"
        elif any(keyword in text_to_analyze for keyword in ['designer', 'ux', 'ui']):
            return "UX Designer"
        elif any(keyword in text_to_analyze for keyword in ['marketing', 'digital marketing']):
            return "Marketing Manager"
        elif any(keyword in text_to_analyze for keyword in ['sales', 'business development']):
            return "Sales"
        elif any(keyword in text_to_analyze for keyword in ['hr', 'human resources', 'recruiter']):
            return "HR"
        else:
            return "General"
    
    def _aggregate_results(self, agent_results: List[AgentResult], market_context: MarketContext) -> Dict[str, Any]:
        """Aggregate results from all agents with realistic scoring."""
        
        # Collect all scores and insights
        all_scores = {}
        all_red_flags = []
        all_strengths = []
        all_recommendations = []
        confidence_scores = []
        
        for result in agent_results:
            all_scores.update(result.scores)
            all_red_flags.extend(result.red_flags)
            all_strengths.extend(result.strengths)
            all_recommendations.extend(result.recommendations)
            confidence_scores.append(result.confidence)
        
        # Calculate weighted overall score with realistic weights
        score_weights = {
            "technical_skills": 0.30,
            "experience": 0.25,
            "cultural_fit": 0.25,
            "legal_compliance": 0.20
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
        
        # Apply market calibration for realistic scoring
        calibrated_score = self.scoring_framework.calibrate_score(
            overall_score, market_context.role_type, market_context
        )
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            agent_results, calibrated_score, all_strengths, all_red_flags
        )
        
        return {
            "overall_score": round(calibrated_score, 1),
            "individual_scores": {k: round(v, 1) for k, v in all_scores.items()},
            "confidence_level": round(statistics.mean(confidence_scores), 1),
            "agent_analyses": [
                {
                    "agent": result.agent_name,
                    "analysis": result.analysis,
                    "confidence": result.confidence
                } for result in agent_results
            ],
            "red_flags": list(set(all_red_flags)),  # Remove duplicates
            "strengths": list(set(all_strengths)),
            "recommendations": list(set(all_recommendations)),
            "executive_summary": executive_summary,
            "market_context": {
                "role_type": market_context.role_type,
                "market_saturation": market_context.market_saturation,
                "scoring_calibrated": True
            },
            "processing_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "agents_used": [result.agent_name for result in agent_results],
                "realistic_scoring_applied": True
            }
        }
    
    def _generate_executive_summary(self, agent_results: List[AgentResult], 
                                   overall_score: float, strengths: List[str], 
                                   red_flags: List[str]) -> str:
        """Generate executive summary with realistic language."""
        
        # Determine score tier with realistic language
        if overall_score >= 80:
            tier = "strong candidate"
        elif overall_score >= 65:
            tier = "solid candidate"
        elif overall_score >= 50:
            tier = "average candidate"
        elif overall_score >= 35:
            tier = "below-average candidate"
        else:
            tier = "weak candidate"
        
        summary_parts = [
            f"This is a {tier} with an overall score of {overall_score:.1f}/100 "
            f"based on comprehensive multi-agent analysis."
        ]
        
        if strengths:
            summary_parts.append(f"Key strengths include: {', '.join(strengths[:3])}.")
        
        if red_flags:
            summary_parts.append(f"Areas requiring attention: {', '.join(red_flags[:2])}.")
        
        summary_parts.append("Scoring has been calibrated against realistic market standards to prevent AI over-scoring.")
        
        return " ".join(summary_parts)
    
    def _create_fallback_analysis(self, resume_data: Dict) -> Dict[str, Any]:
        """Create fallback analysis if multi-agent analysis fails."""
        return {
            "overall_score": 45.0,
            "individual_scores": {
                "technical_skills": 45.0,
                "experience": 45.0,
                "cultural_fit": 45.0,
                "legal_compliance": 80.0
            },
            "confidence_level": 35.0,
            "agent_analyses": [],
            "red_flags": ["Multi-agent analysis failed - manual review required"],
            "strengths": [],
            "recommendations": ["Manual assessment recommended"],
            "executive_summary": "Analysis failed due to system error. Manual review required.",
            "market_context": {"role_type": "Unknown", "scoring_calibrated": False},
            "processing_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "error": True,
                "realistic_scoring_applied": False
            }
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "ai_provider_available": self.ai_provider is not None,
            "agents_initialized": {
                "technical_agent": self.technical_agent is not None,
                "experience_agent": self.experience_agent is not None,
                "cultural_agent": self.cultural_agent is not None,
                "legal_agent": self.legal_agent is not None
            },
            "scoring_framework_active": True,
            "batch_scores_stored": len(self.batch_scores),
            "realistic_scoring_enabled": True
        }
    
    def clear_batch_history(self):
        """Clear batch scoring history."""
        self.batch_scores.clear()
        logger.info("Batch scoring history cleared")
