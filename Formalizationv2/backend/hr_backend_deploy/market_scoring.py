"""
Advanced Market-Based Scoring System
Implements realistic resume scoring based on market standards and competition levels
"""

import json
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from config import config

logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Market context data for realistic scoring"""
    role_type: str
    location: str
    experience_level: str
    skill_demand: Dict[str, float]  # skill -> demand score (0-1)
    salary_range: Tuple[int, int]
    market_saturation: float  # 0-1, higher means more competitive
    years_experience_benchmark: Dict[str, int]  # level -> typical years

@dataclass
class ScoringFactors:
    """Factors that influence resume scoring"""
    base_score: float
    experience_adjustment: float
    skills_adjustment: float
    education_adjustment: float
    market_adjustment: float
    competition_penalty: float
    final_score: float

class MarketBasedScoring:
    """Advanced scoring system based on market realities"""
    
    def __init__(self):
        """Initialize market-based scoring system"""
        self.score_distribution = config.SCORING_DISTRIBUTION
        self.market_adjustments = config.MARKET_ADJUSTMENTS
        self.experience_benchmarks = config.EXPERIENCE_BENCHMARKS
        
        # Skill demand data (simplified - in production, this would come from job market APIs)
        self.skill_demand_map = {
            # High demand skills (2023-2024)
            'python': 0.9, 'javascript': 0.9, 'react': 0.85, 'node.js': 0.8,
            'aws': 0.9, 'docker': 0.85, 'kubernetes': 0.8, 'terraform': 0.75,
            'machine learning': 0.85, 'data science': 0.8, 'ai': 0.9,
            'cloud computing': 0.9, 'microservices': 0.8, 'devops': 0.85,
            
            # Medium demand skills
            'java': 0.7, 'c++': 0.6, 'php': 0.5, 'ruby': 0.4,
            'angular': 0.6, 'vue.js': 0.7, 'typescript': 0.8,
            'postgresql': 0.7, 'mongodb': 0.75, 'redis': 0.7,
            
            # Lower demand skills
            'vb.net': 0.3, 'cobol': 0.2, 'perl': 0.3, 'cold fusion': 0.1,
            'flash': 0.1, 'silverlight': 0.1
        }
        
        # Role competitiveness levels
        self.role_competitiveness = {
            'software engineer': 0.8,
            'data scientist': 0.9,
            'product manager': 0.95,
            'ux designer': 0.75,
            'devops engineer': 0.7,
            'backend developer': 0.65,
            'frontend developer': 0.7,
            'full stack developer': 0.8,
            'machine learning engineer': 0.85,
            'ai engineer': 0.9
        }
        
        logger.info("Market-based scoring system initialized")
    
    def calculate_realistic_score(self, analysis: Dict[str, Any], role_context: str = None) -> Dict[str, Any]:
        """Calculate realistic score based on market conditions"""
        try:
            # Extract base scores from AI analysis
            base_scores = analysis.get('scores', {})
            base_overall = base_scores.get('overall_score', 50)
            
            # Create market context
            market_context = self._create_market_context(analysis, role_context)
            
            # Calculate scoring factors
            factors = self._calculate_scoring_factors(analysis, market_context, base_overall)
            
            # Apply realistic score adjustments
            realistic_scores = self._apply_realistic_adjustments(base_scores, factors, market_context)
            
            # Update analysis with realistic scores
            enhanced_analysis = analysis.copy()
            enhanced_analysis['scores'] = realistic_scores
            enhanced_analysis['market_analysis'] = {
                'market_context': market_context.__dict__,
                'scoring_factors': factors.__dict__,
                'competitiveness_level': self._get_competitiveness_level(realistic_scores['overall_score']),
                'market_percentile': self._calculate_market_percentile(realistic_scores['overall_score']),
                'salary_estimate': self._estimate_salary_range(analysis, realistic_scores['overall_score'])
            }
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Error in realistic scoring: {str(e)}")
            # Return original analysis if scoring fails
            return analysis
    
    def _create_market_context(self, analysis: Dict[str, Any], role_context: str = None) -> MarketContext:
        """Create market context from analysis data"""
        
        # Determine role type from experience or context
        role_type = self._determine_role_type(analysis, role_context)
        
        # Estimate experience level
        experience_level = self._estimate_experience_level(analysis)
        
        # Calculate skill demand scores
        skills = analysis.get('skills', [])
        skill_demand = {}
        for skill in skills:
            skill_lower = skill.lower()
            demand_score = 0.5  # Default medium demand
            
            # Check for exact matches or partial matches
            for market_skill, demand in self.skill_demand_map.items():
                if market_skill in skill_lower or skill_lower in market_skill:
                    demand_score = max(demand_score, demand)
            
            skill_demand[skill] = demand_score
        
        # Calculate market saturation based on role competitiveness
        market_saturation = self.role_competitiveness.get(role_type.lower(), 0.6)
        
        return MarketContext(
            role_type=role_type,
            location="General",  # Could be enhanced with location data
            experience_level=experience_level,
            skill_demand=skill_demand,
            salary_range=(50000, 120000),  # Could be enhanced with real salary data
            market_saturation=market_saturation,
            years_experience_benchmark=self.experience_benchmarks
        )
    
    def _determine_role_type(self, analysis: Dict[str, Any], role_context: str = None) -> str:
        """Determine role type from analysis or context"""
        if role_context:
            return role_context.lower()
        
        # Try to infer from experience titles
        experience = analysis.get('experience', [])
        if experience:
            latest_title = experience[0].get('title', '').lower()
            
            # Map common titles to role types
            title_mapping = {
                'software engineer': 'software engineer',
                'developer': 'software engineer',
                'programmer': 'software engineer',
                'data scientist': 'data scientist',
                'analyst': 'data analyst',
                'product manager': 'product manager',
                'designer': 'ux designer',
                'devops': 'devops engineer',
                'machine learning': 'machine learning engineer'
            }
            
            for key, role in title_mapping.items():
                if key in latest_title:
                    return role
        
        # Default to general software role
        return 'software engineer'
    
    def _estimate_experience_level(self, analysis: Dict[str, Any]) -> str:
        """Estimate experience level from resume data"""
        experience = analysis.get('experience', [])
        
        if not experience:
            return 'junior'
        
        # Calculate total years of experience (simplified)
        total_years = len(experience) * 1.5  # Rough estimate
        
        if total_years <= 2:
            return 'junior'
        elif total_years <= 5:
            return 'mid'
        elif total_years <= 10:
            return 'senior'
        elif total_years <= 15:
            return 'lead'
        else:
            return 'executive'
    
    def _calculate_scoring_factors(self, analysis: Dict[str, Any], market_context: MarketContext, base_score: float) -> ScoringFactors:
        """Calculate various scoring factors"""
        
        # Experience adjustment
        experience_adj = self._calculate_experience_adjustment(analysis, market_context)
        
        # Skills adjustment based on market demand
        skills_adj = self._calculate_skills_adjustment(analysis, market_context)
        
        # Education adjustment
        education_adj = self._calculate_education_adjustment(analysis)
        
        # Market adjustment based on competition
        market_adj = self._calculate_market_adjustment(market_context)
        
        # Competition penalty
        competition_penalty = market_context.market_saturation * 10
        
        # Calculate final score
        final_score = (
            base_score +
            experience_adj +
            skills_adj +
            education_adj +
            market_adj -
            competition_penalty
        )
        
        # Ensure score stays within realistic bounds
        final_score = max(25, min(95, final_score))
        
        return ScoringFactors(
            base_score=base_score,
            experience_adjustment=experience_adj,
            skills_adjustment=skills_adj,
            education_adjustment=education_adj,
            market_adjustment=market_adj,
            competition_penalty=competition_penalty,
            final_score=final_score
        )
    
    def _calculate_experience_adjustment(self, analysis: Dict[str, Any], market_context: MarketContext) -> float:
        """Calculate experience-based score adjustment"""
        experience = analysis.get('experience', [])
        
        if not experience:
            return -15  # Penalty for no experience
        
        # Bonus for relevant experience
        experience_bonus = min(len(experience) * 3, 15)  # Max 15 points
        
        # Bonus for experience quality (simplified)
        quality_bonus = 0
        for exp in experience:
            description = exp.get('description', '').lower()
            # Look for achievement indicators
            if any(word in description for word in ['led', 'managed', 'increased', 'improved', 'developed']):
                quality_bonus += 2
        
        return min(experience_bonus + quality_bonus, 20)  # Cap at 20 points
    
    def _calculate_skills_adjustment(self, analysis: Dict[str, Any], market_context: MarketContext) -> float:
        """Calculate skills-based score adjustment"""
        skills = analysis.get('skills', [])
        
        if not skills:
            return -10  # Penalty for no identified skills
        
        # Calculate weighted skill score based on market demand
        total_demand = sum(market_context.skill_demand.values())
        avg_demand = total_demand / len(market_context.skill_demand) if market_context.skill_demand else 0.5
        
        # Bonus for high-demand skills
        if avg_demand > 0.7:
            return 10
        elif avg_demand > 0.5:
            return 5
        else:
            return 0
    
    def _calculate_education_adjustment(self, analysis: Dict[str, Any]) -> float:
        """Calculate education-based score adjustment"""
        education = analysis.get('education', [])
        
        if not education:
            return -5  # Small penalty for no education info
        
        education_bonus = 0
        for edu in education:
            degree = edu.get('degree', '').lower()
            
            # Degree level bonuses
            if 'phd' in degree or 'doctorate' in degree:
                education_bonus += 8
            elif 'master' in degree or 'mba' in degree:
                education_bonus += 5
            elif 'bachelor' in degree:
                education_bonus += 3
            elif 'associate' in degree:
                education_bonus += 1
        
        return min(education_bonus, 10)  # Cap at 10 points
    
    def _calculate_market_adjustment(self, market_context: MarketContext) -> float:
        """Calculate market-based adjustment"""
        # This is a simplified version - in production, this would use real market data
        base_adjustment = 0
        
        # Adjust based on role demand
        role_demand_map = {
            'software engineer': 2,
            'data scientist': 3,
            'ai engineer': 4,
            'devops engineer': 2,
            'product manager': -1  # Oversaturated market
        }
        
        return role_demand_map.get(market_context.role_type, 0)
    
    def _apply_realistic_adjustments(self, base_scores: Dict[str, Any], factors: ScoringFactors, market_context: MarketContext) -> Dict[str, Any]:
        """Apply realistic adjustments to all scores"""
        
        # Calculate the adjustment ratio
        base_overall = base_scores.get('overall_score', 50)
        adjustment_ratio = factors.final_score / base_overall if base_overall > 0 else 1
        
        # Apply proportional adjustments to all scores
        realistic_scores = {}
        for score_key, score_value in base_scores.items():
            if isinstance(score_value, (int, float)):
                adjusted_score = score_value * adjustment_ratio
                # Apply some randomness to make scores more realistic
                adjusted_score += (hash(score_key) % 10 - 5)  # ±5 points variation
                realistic_scores[score_key] = max(20, min(95, int(adjusted_score)))
            else:
                realistic_scores[score_key] = score_value
        
        # Ensure overall score matches calculated final score
        realistic_scores['overall_score'] = int(factors.final_score)
        
        return realistic_scores
    
    def _get_competitiveness_level(self, score: float) -> str:
        """Get competitiveness level based on score"""
        if score >= 85:
            return 'exceptional'
        elif score >= 75:
            return 'excellent'
        elif score >= 65:
            return 'good'
        elif score >= 50:
            return 'average'
        else:
            return 'below_average'
    
    def _calculate_market_percentile(self, score: float) -> float:
        """Calculate market percentile based on score"""
        # Simplified percentile calculation
        if score >= 90:
            return 95.0
        elif score >= 80:
            return 85.0
        elif score >= 70:
            return 70.0
        elif score >= 60:
            return 50.0
        elif score >= 50:
            return 30.0
        else:
            return 15.0
    
    def _estimate_salary_range(self, analysis: Dict[str, Any], score: float) -> Tuple[int, int]:
        """Estimate salary range based on analysis and score"""
        
        # Base salary ranges by experience level (simplified)
        base_ranges = {
            'junior': (50000, 80000),
            'mid': (80000, 120000),
            'senior': (120000, 180000),
            'lead': (150000, 220000),
            'executive': (200000, 350000)
        }
        
        experience_level = self._estimate_experience_level(analysis)
        base_min, base_max = base_ranges.get(experience_level, (60000, 100000))
        
        # Adjust based on score
        score_multiplier = score / 70.0  # 70 is considered average
        
        adjusted_min = int(base_min * score_multiplier)
        adjusted_max = int(base_max * score_multiplier)
        
        return (adjusted_min, adjusted_max)
    
    def rank_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Rank candidates and apply realistic score distribution"""
        if not candidates:
            return candidates
        
        # Sort by overall score
        sorted_candidates = sorted(candidates, key=lambda x: x.get('scores', {}).get('overall_score', 0), reverse=True)
        
        # Apply percentile-based adjustments to ensure realistic distribution
        total_candidates = len(sorted_candidates)
        
        for i, candidate in enumerate(sorted_candidates):
            percentile = (total_candidates - i) / total_candidates
            
            # Adjust scores based on target distribution
            target_score = self._get_target_score_for_percentile(percentile)
            current_score = candidate.get('scores', {}).get('overall_score', 50)
            
            # Blend current score with target score (60% current, 40% target)
            blended_score = int(current_score * 0.6 + target_score * 0.4)
            
            candidate['scores']['overall_score'] = blended_score
            candidate['market_rank'] = i + 1
            candidate['market_percentile'] = round(percentile * 100, 1)
        
        return sorted_candidates
    
    def _get_target_score_for_percentile(self, percentile: float) -> int:
        """Get target score for a given percentile"""
        if percentile >= 0.95:
            return 90  # Top 5%
        elif percentile >= 0.80:
            return 80  # Top 20%
        elif percentile >= 0.50:
            return 70  # Top 50%
        elif percentile >= 0.20:
            return 60  # Top 80%
        else:
            return 45  # Bottom 20%

# Global market scoring instance
market_scoring = MarketBasedScoring()
