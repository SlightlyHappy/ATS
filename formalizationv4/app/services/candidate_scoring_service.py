"""
Candidate Scoring Service for automated qualification and ranking.
Integrates with AI analysis and manual assessments to provide comprehensive scoring.
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.models.candidate import Candidate, CandidateActivity, Priority, CandidateStatus, PipelineStage
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.services.analytics_service import AnalyticsService
import json

logger = logging.getLogger(__name__)

class CandidateScoringService:
    """Service for automated candidate qualification and ranking."""
    
    # Scoring weights (should sum to 1.0)
    SCORING_WEIGHTS = {
        'ai_analysis': 0.40,      # 40% - AI resume analysis score
        'technical_skills': 0.25, # 25% - Technical assessment results
        'experience': 0.20,       # 20% - Experience relevance and depth
        'cultural_fit': 0.10,     # 10% - Cultural fit assessment
        'engagement': 0.05        # 5% - Candidate engagement and responsiveness
    }
    
    # Priority thresholds
    PRIORITY_THRESHOLDS = {
        'urgent': 90,   # 90+ overall score
        'high': 75,     # 75-89 overall score
        'medium': 50,   # 50-74 overall score
        'low': 0        # <50 overall score
    }
    
    # Stage progression weights
    STAGE_PROGRESSION_BONUS = {
        PipelineStage.APPLIED.value: 0,
        PipelineStage.SCREENING.value: 5,
        PipelineStage.PHONE_INTERVIEW.value: 10,
        PipelineStage.TECHNICAL_ASSESSMENT.value: 15,
        PipelineStage.ON_SITE_INTERVIEW.value: 20,
        PipelineStage.FINAL_INTERVIEW.value: 25,
        PipelineStage.REFERENCE_CHECK.value: 30,
        PipelineStage.OFFER_MADE.value: 35
    }
    
    def __init__(self, analytics_service: AnalyticsService = None):
        self.analytics_service = analytics_service or AnalyticsService()
    
    def score_candidate(self, candidate: Candidate, recalculate: bool = False) -> Dict:
        """
        Calculate comprehensive score for a candidate.
        
        Args:
            candidate: Candidate object to score
            recalculate: Force recalculation even if scores exist
            
        Returns:
            Dictionary with scoring breakdown and recommendations
        """
        try:
            logger.info(f"Scoring candidate: {candidate.full_name} (ID: {candidate.id})")
            
            # Skip if already scored and not forcing recalculation
            if not recalculate and candidate.overall_score and candidate.overall_score > 0:
                logger.info(f"Candidate {candidate.full_name} already scored: {candidate.overall_score}")
                return self._get_existing_score_breakdown(candidate)
            
            # Initialize scoring components
            scoring_breakdown = {
                'ai_analysis_score': 0,
                'technical_skills_score': 0,
                'experience_score': 0,
                'cultural_fit_score': 0,
                'engagement_score': 0,
                'stage_progression_bonus': 0,
                'overall_score': 0,
                'priority': Priority.MEDIUM.value,
                'recommendations': [],
                'scoring_factors': []
            }
            
            # 1. AI Analysis Score (from resume analysis)
            ai_score = self._calculate_ai_analysis_score(candidate)
            scoring_breakdown['ai_analysis_score'] = ai_score
            candidate.ai_match_score = ai_score
            
            # 2. Technical Skills Score
            tech_score = self._calculate_technical_score(candidate)
            scoring_breakdown['technical_skills_score'] = tech_score
            candidate.technical_score = tech_score
            
            # 3. Experience Score
            exp_score = self._calculate_experience_score(candidate)
            scoring_breakdown['experience_score'] = exp_score
            candidate.experience_score = exp_score
            
            # 4. Cultural Fit Score
            culture_score = self._calculate_cultural_fit_score(candidate)
            scoring_breakdown['cultural_fit_score'] = culture_score
            candidate.cultural_fit_score = culture_score
            
            # 5. Engagement Score
            engagement_score = self._calculate_engagement_score(candidate)
            scoring_breakdown['engagement_score'] = engagement_score
            
            # 6. Stage Progression Bonus
            stage_bonus = self.STAGE_PROGRESSION_BONUS.get(candidate.current_stage, 0)
            scoring_breakdown['stage_progression_bonus'] = stage_bonus
            
            # Calculate weighted overall score
            overall_score = (
                ai_score * self.SCORING_WEIGHTS['ai_analysis'] +
                tech_score * self.SCORING_WEIGHTS['technical_skills'] +
                exp_score * self.SCORING_WEIGHTS['experience'] +
                culture_score * self.SCORING_WEIGHTS['cultural_fit'] +
                engagement_score * self.SCORING_WEIGHTS['engagement']
            ) + stage_bonus
            
            # Cap at 100
            overall_score = min(overall_score, 100)
            scoring_breakdown['overall_score'] = round(overall_score, 2)
            candidate.overall_score = overall_score
            
            # Determine priority based on score
            priority = self._determine_priority(overall_score)
            scoring_breakdown['priority'] = priority
            candidate.priority = priority
            
            # Generate recommendations
            recommendations = self._generate_recommendations(candidate, scoring_breakdown)
            scoring_breakdown['recommendations'] = recommendations
            
            # Generate scoring factors explanation
            scoring_factors = self._generate_scoring_factors(scoring_breakdown)
            scoring_breakdown['scoring_factors'] = scoring_factors
            
            # Log scoring activity
            candidate.add_activity(
                activity_type='scoring',
                description=f"Candidate scored: {overall_score:.1f}/100 (Priority: {priority})",
                details=scoring_breakdown,
                created_by='CandidateScoringService'
            )
            
            logger.info(f"Candidate {candidate.full_name} scored: {overall_score:.1f}/100 (Priority: {priority})")
            return scoring_breakdown
            
        except Exception as e:
            logger.error(f"Error scoring candidate {candidate.full_name}: {str(e)}")
            return {
                'error': str(e),
                'overall_score': 0,
                'priority': Priority.LOW.value
            }
    
    def _calculate_ai_analysis_score(self, candidate: Candidate) -> float:
        """Calculate score based on AI resume analysis."""
        if not candidate.resume_id:
            return 0
        
        try:
            # Get the latest analysis for this candidate's resume
            analysis = Analysis.query.filter_by(
                resume_id=candidate.resume_id,
                status='completed'
            ).order_by(Analysis.completed_at.desc()).first()
            
            if not analysis or not analysis.overall_score:
                return 0
            
            # AI analysis score is already 0-100, so return as-is
            return float(analysis.overall_score)
            
        except Exception as e:
            logger.warning(f"Could not retrieve AI analysis for candidate {candidate.full_name}: {str(e)}")
            return 0
    
    def _calculate_technical_score(self, candidate: Candidate) -> float:
        """Calculate technical skills score based on assessments and interviews."""
        if candidate.technical_score and candidate.technical_score > 0:
            return candidate.technical_score
        
        # Look for technical assessment activities
        technical_activities = candidate.activities.filter_by(
            activity_type='technical_assessment'
        ).order_by(CandidateActivity.created_at.desc()).all()
        
        if not technical_activities:
            return 0
        
        # Get the latest technical assessment score
        latest_assessment = technical_activities[0]
        if latest_assessment.details and 'score' in latest_assessment.details:
            return float(latest_assessment.details['score'])
        
        return 0
    
    def _calculate_experience_score(self, candidate: Candidate) -> float:
        """Calculate experience relevance score."""
        if candidate.experience_score and candidate.experience_score > 0:
            return candidate.experience_score
        
        # Base score on AI analysis of experience
        if candidate.resume_id:
            try:
                analysis = Analysis.query.filter_by(
                    resume_id=candidate.resume_id,
                    status='completed'
                ).order_by(Analysis.completed_at.desc()).first()
                
                if analysis and analysis.experience_result:
                    exp_result = analysis.experience_result
                    if isinstance(exp_result, dict) and 'score' in exp_result:
                        return float(exp_result['score'])
                    elif isinstance(exp_result, dict) and 'relevance_score' in exp_result:
                        return float(exp_result['relevance_score'])
                        
            except Exception as e:
                logger.warning(f"Could not calculate experience score for {candidate.full_name}: {str(e)}")
        
        return 0
    
    def _calculate_cultural_fit_score(self, candidate: Candidate) -> float:
        """Calculate cultural fit score based on interviews and assessments."""
        if candidate.cultural_fit_score and candidate.cultural_fit_score > 0:
            return candidate.cultural_fit_score
        
        # Look for cultural fit interview feedback
        cultural_activities = candidate.activities.filter(
            CandidateActivity.activity_type.in_(['interview', 'cultural_assessment'])
        ).order_by(CandidateActivity.created_at.desc()).all()
        
        scores = []
        for activity in cultural_activities:
            if activity.details and 'cultural_fit_score' in activity.details:
                scores.append(float(activity.details['cultural_fit_score']))
        
        if scores:
            return sum(scores) / len(scores)
        
        # Default moderate score if no specific cultural fit data
        return 60
    
    def _calculate_engagement_score(self, candidate: Candidate) -> float:
        """Calculate engagement score based on responsiveness and initiative."""
        try:
            # Factors for engagement scoring
            engagement_factors = {
                'response_time': 0,      # How quickly they respond
                'initiative': 0,         # Do they ask questions, show interest?
                'communication': 0,      # Quality of communication
                'follow_through': 0      # Do they complete requested actions?
            }
            
            # Analyze communication activities
            comm_activities = candidate.activities.filter(
                CandidateActivity.activity_type.in_(['email', 'call', 'interview'])
            ).order_by(CandidateActivity.created_at.desc()).limit(10).all()
            
            if not comm_activities:
                return 50  # Neutral score if no data
            
            # Score based on communication frequency and quality
            recent_activities = [a for a in comm_activities if 
                               (datetime.utcnow() - a.created_at).days <= 14]
            
            if recent_activities:
                # High engagement if frequent recent communication
                engagement_factors['communication'] = min(len(recent_activities) * 10, 100)
            
            # Look for positive engagement indicators in activity details
            for activity in comm_activities[:5]:  # Check last 5 activities
                if activity.details:
                    if activity.details.get('response_time_hours', 48) <= 24:
                        engagement_factors['response_time'] += 20
                    if activity.details.get('asked_questions', False):
                        engagement_factors['initiative'] += 15
                    if activity.details.get('completed_task', False):
                        engagement_factors['follow_through'] += 20
            
            # Calculate average engagement score
            valid_scores = [score for score in engagement_factors.values() if score > 0]
            if valid_scores:
                return min(sum(valid_scores) / len(valid_scores), 100)
            
            return 50  # Default neutral score
            
        except Exception as e:
            logger.warning(f"Could not calculate engagement score for {candidate.full_name}: {str(e)}")
            return 50
    
    def _determine_priority(self, overall_score: float) -> str:
        """Determine candidate priority based on overall score."""
        for priority, threshold in sorted(self.PRIORITY_THRESHOLDS.items(), 
                                        key=lambda x: x[1], reverse=True):
            if overall_score >= threshold:
                return priority
        return Priority.LOW.value
    
    def _generate_recommendations(self, candidate: Candidate, breakdown: Dict) -> List[str]:
        """Generate actionable recommendations based on scoring."""
        recommendations = []
        
        # AI Analysis recommendations
        if breakdown['ai_analysis_score'] < 60:
            recommendations.append("Review resume analysis - may need additional skills assessment")
        elif breakdown['ai_analysis_score'] > 85:
            recommendations.append("Strong AI match - prioritize for technical interview")
        
        # Technical skills recommendations
        if breakdown['technical_skills_score'] < 50:
            recommendations.append("Schedule technical assessment to verify skills")
        elif breakdown['technical_skills_score'] > 80:
            recommendations.append("Excellent technical skills - fast-track interview process")
        
        # Experience recommendations
        if breakdown['experience_score'] < 40:
            recommendations.append("Experience may not align - consider for junior role or training")
        elif breakdown['experience_score'] > 85:
            recommendations.append("Highly relevant experience - consider for senior position")
        
        # Engagement recommendations
        if breakdown['engagement_score'] < 40:
            recommendations.append("Low engagement - follow up to gauge continued interest")
        elif breakdown['engagement_score'] > 80:
            recommendations.append("Highly engaged candidate - expedite process to avoid losing them")
        
        # Overall score recommendations
        if breakdown['overall_score'] > 90:
            recommendations.append("Top candidate - schedule final interviews immediately")
        elif breakdown['overall_score'] < 30:
            recommendations.append("Consider rejection or significant skill development program")
        
        # Stage-specific recommendations
        stage = candidate.current_stage
        days_in_stage = candidate.days_in_current_stage
        
        if days_in_stage > 7 and stage == PipelineStage.SCREENING.value:
            recommendations.append("Candidate stalled in screening - schedule phone interview")
        elif days_in_stage > 14 and stage in [PipelineStage.PHONE_INTERVIEW.value, 
                                              PipelineStage.TECHNICAL_ASSESSMENT.value]:
            recommendations.append("Extended time in current stage - check for blockers")
        
        return recommendations
    
    def _generate_scoring_factors(self, breakdown: Dict) -> List[str]:
        """Generate explanations for scoring factors."""
        factors = []
        
        # AI Analysis factor
        ai_score = breakdown['ai_analysis_score']
        if ai_score > 0:
            factors.append(f"AI Resume Analysis: {ai_score:.1f}/100 ({self.SCORING_WEIGHTS['ai_analysis']*100:.0f}% weight)")
        
        # Technical skills factor
        tech_score = breakdown['technical_skills_score']
        if tech_score > 0:
            factors.append(f"Technical Skills: {tech_score:.1f}/100 ({self.SCORING_WEIGHTS['technical_skills']*100:.0f}% weight)")
        
        # Experience factor
        exp_score = breakdown['experience_score']
        if exp_score > 0:
            factors.append(f"Experience Relevance: {exp_score:.1f}/100 ({self.SCORING_WEIGHTS['experience']*100:.0f}% weight)")
        
        # Cultural fit factor
        culture_score = breakdown['cultural_fit_score']
        if culture_score > 0:
            factors.append(f"Cultural Fit: {culture_score:.1f}/100 ({self.SCORING_WEIGHTS['cultural_fit']*100:.0f}% weight)")
        
        # Engagement factor
        engagement_score = breakdown['engagement_score']
        if engagement_score > 0:
            factors.append(f"Candidate Engagement: {engagement_score:.1f}/100 ({self.SCORING_WEIGHTS['engagement']*100:.0f}% weight)")
        
        # Stage progression bonus
        bonus = breakdown['stage_progression_bonus']
        if bonus > 0:
            factors.append(f"Pipeline Progression Bonus: +{bonus} points")
        
        return factors
    
    def _get_existing_score_breakdown(self, candidate: Candidate) -> Dict:
        """Get existing score breakdown for already-scored candidate."""
        return {
            'ai_analysis_score': candidate.ai_match_score or 0,
            'technical_skills_score': candidate.technical_score or 0,
            'experience_score': candidate.experience_score or 0,
            'cultural_fit_score': candidate.cultural_fit_score or 0,
            'engagement_score': 0,  # Would need to recalculate
            'stage_progression_bonus': self.STAGE_PROGRESSION_BONUS.get(candidate.current_stage, 0),
            'overall_score': candidate.overall_score or 0,
            'priority': candidate.priority,
            'recommendations': [],
            'scoring_factors': []
        }
    
    def score_all_candidates(self, user_id: str = None, force_recalculate: bool = False) -> Dict:
        """Score all candidates for a user or all users."""
        try:
            query = Candidate.query
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            # Only score active candidates
            candidates = query.filter_by(status=CandidateStatus.ACTIVE.value).all()
            
            results = {
                'total_candidates': len(candidates),
                'scored_candidates': 0,
                'skipped_candidates': 0,
                'errors': 0,
                'score_distribution': {
                    'urgent': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0
                }
            }
            
            for candidate in candidates:
                try:
                    if force_recalculate or not candidate.overall_score:
                        self.score_candidate(candidate, recalculate=force_recalculate)
                        results['scored_candidates'] += 1
                    else:
                        results['skipped_candidates'] += 1
                    
                    # Update distribution
                    priority = candidate.priority or Priority.MEDIUM.value
                    results['score_distribution'][priority] += 1
                    
                except Exception as e:
                    logger.error(f"Error scoring candidate {candidate.full_name}: {str(e)}")
                    results['errors'] += 1
            
            logger.info(f"Batch scoring completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch candidate scoring: {str(e)}")
            return {'error': str(e)}
    
    def get_top_candidates(self, user_id: str = None, limit: int = 10, 
                          stage: str = None) -> List[Dict]:
        """Get top-scoring candidates."""
        try:
            query = Candidate.query.filter_by(status=CandidateStatus.ACTIVE.value)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            if stage:
                query = query.filter_by(current_stage=stage)
            
            # Order by overall score descending
            candidates = query.order_by(
                Candidate.overall_score.desc().nullslast(),
                Candidate.priority.desc(),
                Candidate.created_at.desc()
            ).limit(limit).all()
            
            return [candidate.to_dict() for candidate in candidates]
            
        except Exception as e:
            logger.error(f"Error getting top candidates: {str(e)}")
            return []
    
    def get_scoring_analytics(self, user_id: str = None, days: int = 30) -> Dict:
        """Get scoring analytics and insights."""
        try:
            query = Candidate.query
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            # Filter by date range
            since_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Candidate.created_at >= since_date)
            
            candidates = query.all()
            
            if not candidates:
                return {'message': 'No candidates found for the specified period'}
            
            # Calculate analytics
            scores = [c.overall_score for c in candidates if c.overall_score]
            
            analytics = {
                'total_candidates': len(candidates),
                'scored_candidates': len(scores),
                'average_score': round(sum(scores) / len(scores), 2) if scores else 0,
                'score_distribution': {
                    'urgent': len([c for c in candidates if c.priority == Priority.URGENT.value]),
                    'high': len([c for c in candidates if c.priority == Priority.HIGH.value]),
                    'medium': len([c for c in candidates if c.priority == Priority.MEDIUM.value]),
                    'low': len([c for c in candidates if c.priority == Priority.LOW.value])
                },
                'stage_distribution': {},
                'top_score': max(scores) if scores else 0,
                'bottom_score': min(scores) if scores else 0
            }
            
            # Stage distribution
            for stage in PipelineStage:
                stage_candidates = [c for c in candidates if c.current_stage == stage.value]
                analytics['stage_distribution'][stage.value] = {
                    'count': len(stage_candidates),
                    'avg_score': round(sum([c.overall_score for c in stage_candidates if c.overall_score]) / 
                                     len([c for c in stage_candidates if c.overall_score]), 2) 
                                if stage_candidates else 0
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting scoring analytics: {str(e)}")
            return {'error': str(e)}
