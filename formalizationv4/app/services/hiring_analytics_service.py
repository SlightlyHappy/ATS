"""
Hiring Analytics Service for candidate journey and conversion tracking.
Provides comprehensive analytics and insights on hiring performance.
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, extract, case
from app.models.candidate import (Candidate, CandidateActivity, PipelineStageHistory, 
                                HiringAnalytics, PipelineStage, CandidateStatus, Priority)
from app.models.user import User
from app.models.analysis import Analysis
import json

logger = logging.getLogger(__name__)

class HiringAnalyticsService:
    """Service for candidate journey and conversion tracking analytics."""
    
    def __init__(self):
        self.default_period_days = 30
    
    def generate_hiring_analytics(self, user_id: str = None, period_days: int = None) -> Dict:
        """Generate comprehensive hiring analytics for a period."""
        try:
            period_days = period_days or self.default_period_days
            end_date = date.today()
            start_date = end_date - timedelta(days=period_days)
            
            logger.info(f"Generating hiring analytics for {period_days} days (user: {user_id})")
            
            # Get candidates for the period
            query = Candidate.query.filter(
                Candidate.created_at >= start_date,
                Candidate.created_at <= end_date + timedelta(days=1)
            )
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            candidates = query.all()
            
            if not candidates:
                return {
                    'message': 'No candidates found for the specified period',
                    'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()}
                }
            
            # Calculate core metrics
            analytics = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': period_days
                },
                'overview': self._calculate_overview_metrics(candidates),
                'pipeline_metrics': self._calculate_pipeline_metrics(candidates),
                'conversion_funnel': self._calculate_conversion_funnel(candidates, user_id),
                'time_metrics': self._calculate_time_metrics(candidates, user_id),
                'quality_metrics': self._calculate_quality_metrics(candidates),
                'source_analytics': self._calculate_source_analytics(candidates),
                'trend_analysis': self._calculate_trend_analysis(user_id, period_days),
                'performance_insights': self._generate_performance_insights(candidates),
                'recommendations': self._generate_analytics_recommendations(candidates)
            }
            
            # Store analytics snapshot
            self._store_analytics_snapshot(user_id, analytics, start_date, end_date)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating hiring analytics: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_overview_metrics(self, candidates: List[Candidate]) -> Dict:
        """Calculate high-level overview metrics."""
        total_candidates = len(candidates)
        active_candidates = len([c for c in candidates if c.status == CandidateStatus.ACTIVE.value])
        hired_candidates = len([c for c in candidates if c.status == CandidateStatus.HIRED.value])
        rejected_candidates = len([c for c in candidates if c.status == CandidateStatus.REJECTED.value])
        
        # Calculate rates
        hire_rate = (hired_candidates / total_candidates * 100) if total_candidates > 0 else 0
        rejection_rate = (rejected_candidates / total_candidates * 100) if total_candidates > 0 else 0
        
        # Priority distribution
        priority_dist = {}
        for priority in Priority:
            priority_dist[priority.value] = len([c for c in candidates if c.priority == priority.value])
        
        # Score statistics
        scored_candidates = [c for c in candidates if c.overall_score and c.overall_score > 0]
        
        return {
            'total_candidates': total_candidates,
            'active_candidates': active_candidates,
            'hired_candidates': hired_candidates,
            'rejected_candidates': rejected_candidates,
            'hire_rate': round(hire_rate, 2),
            'rejection_rate': round(rejection_rate, 2),
            'priority_distribution': priority_dist,
            'scoring_stats': {
                'total_scored': len(scored_candidates),
                'average_score': round(sum([c.overall_score for c in scored_candidates]) / len(scored_candidates), 2) if scored_candidates else 0,
                'highest_score': max([c.overall_score for c in scored_candidates]) if scored_candidates else 0,
                'lowest_score': min([c.overall_score for c in scored_candidates]) if scored_candidates else 0
            }
        }
    
    def _calculate_pipeline_metrics(self, candidates: List[Candidate]) -> Dict:
        """Calculate pipeline stage distribution and metrics."""
        # Stage distribution
        stage_distribution = {}
        for stage in PipelineStage:
            stage_candidates = [c for c in candidates if c.current_stage == stage.value]
            stage_distribution[stage.value] = {
                'count': len(stage_candidates),
                'percentage': round(len(stage_candidates) / len(candidates) * 100, 2) if candidates else 0,
                'avg_score': round(sum([c.overall_score for c in stage_candidates if c.overall_score]) / 
                                len([c for c in stage_candidates if c.overall_score]), 2) if stage_candidates else 0,
                'avg_days_in_stage': round(sum([c.days_in_current_stage for c in stage_candidates]) / 
                                         len(stage_candidates), 2) if stage_candidates else 0
            }
        
        # Pipeline velocity (average days to move through each stage)
        velocity_metrics = self._calculate_pipeline_velocity(candidates)
        
        return {
            'stage_distribution': stage_distribution,
            'pipeline_velocity': velocity_metrics,
            'bottlenecks': self._identify_pipeline_bottlenecks(stage_distribution, velocity_metrics)
        }
    
    def _calculate_conversion_funnel(self, candidates: List[Candidate], user_id: str = None) -> Dict:
        """Calculate conversion rates between pipeline stages."""
        try:
            # Get stage history for all candidates
            query = PipelineStageHistory.query.join(Candidate)
            
            if user_id:
                query = query.filter(Candidate.user_id == user_id)
            
            # Get stage changes from the last 90 days for more data
            since_date = datetime.utcnow() - timedelta(days=90)
            stage_history = query.filter(
                PipelineStageHistory.changed_at >= since_date
            ).all()
            
            # Count stage entries and progressions
            stage_counts = {}
            stage_progressions = {}
            
            # Initialize counters
            for stage in PipelineStage:
                stage_counts[stage.value] = 0
                stage_progressions[stage.value] = 0
            
            # Count initial applications
            initial_candidates = [c for c in candidates]
            stage_counts[PipelineStage.APPLIED.value] = len(initial_candidates)
            
            # Count stage transitions
            for history in stage_history:
                if history.to_stage in stage_counts:
                    stage_counts[history.to_stage] += 1
                
                if history.from_stage and history.from_stage in stage_progressions:
                    stage_progressions[history.from_stage] += 1
            
            # Calculate conversion rates
            conversion_rates = {}
            stage_order = [
                PipelineStage.APPLIED.value,
                PipelineStage.SCREENING.value,
                PipelineStage.PHONE_INTERVIEW.value,
                PipelineStage.TECHNICAL_ASSESSMENT.value,
                PipelineStage.ON_SITE_INTERVIEW.value,
                PipelineStage.FINAL_INTERVIEW.value,
                PipelineStage.REFERENCE_CHECK.value,
                PipelineStage.OFFER_MADE.value,
                PipelineStage.OFFER_ACCEPTED.value,
                PipelineStage.HIRED.value
            ]
            
            for i, stage in enumerate(stage_order[:-1]):
                next_stage = stage_order[i + 1]
                
                current_count = stage_counts.get(stage, 0)
                next_count = stage_counts.get(next_stage, 0)
                
                if current_count > 0:
                    rate = (next_count / current_count) * 100
                    conversion_rates[f"{stage}_to_{next_stage}"] = round(rate, 2)
                else:
                    conversion_rates[f"{stage}_to_{next_stage}"] = 0
            
            return {
                'stage_counts': stage_counts,
                'conversion_rates': conversion_rates,
                'funnel_efficiency': self._calculate_funnel_efficiency(conversion_rates),
                'drop_off_points': self._identify_drop_off_points(conversion_rates)
            }
            
        except Exception as e:
            logger.error(f"Error calculating conversion funnel: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_time_metrics(self, candidates: List[Candidate], user_id: str = None) -> Dict:
        """Calculate time-based hiring metrics."""
        try:
            # Overall time to hire for completed hires
            hired_candidates = [c for c in candidates if c.status == CandidateStatus.HIRED.value and c.hired_at]
            
            if hired_candidates:
                time_to_hire_days = [(c.hired_at - c.applied_at).days for c in hired_candidates]
                avg_time_to_hire = sum(time_to_hire_days) / len(time_to_hire_days)
                median_time_to_hire = sorted(time_to_hire_days)[len(time_to_hire_days) // 2]
            else:
                avg_time_to_hire = 0
                median_time_to_hire = 0
                time_to_hire_days = []
            
            # Time spent in each stage
            stage_times = {}
            for stage in PipelineStage:
                stage_candidates = [c for c in candidates if c.current_stage == stage.value]
                if stage_candidates:
                    avg_time = sum([c.days_in_current_stage for c in stage_candidates]) / len(stage_candidates)
                    stage_times[stage.value] = round(avg_time, 1)
                else:
                    stage_times[stage.value] = 0
            
            # Time distribution analysis
            time_distribution = {
                'fast_hires': len([days for days in time_to_hire_days if days <= 14]),  # <= 2 weeks
                'normal_hires': len([days for days in time_to_hire_days if 14 < days <= 30]),  # 2-4 weeks
                'slow_hires': len([days for days in time_to_hire_days if days > 30])  # > 4 weeks
            }
            
            return {
                'average_time_to_hire': round(avg_time_to_hire, 1),
                'median_time_to_hire': median_time_to_hire,
                'time_to_hire_distribution': time_distribution,
                'average_stage_times': stage_times,
                'pipeline_velocity_score': self._calculate_velocity_score(avg_time_to_hire, stage_times)
            }
            
        except Exception as e:
            logger.error(f"Error calculating time metrics: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_quality_metrics(self, candidates: List[Candidate]) -> Dict:
        """Calculate candidate quality and success metrics."""
        try:
            scored_candidates = [c for c in candidates if c.overall_score and c.overall_score > 0]
            
            if not scored_candidates:
                return {'message': 'No scored candidates available for quality analysis'}
            
            # Score distribution
            score_ranges = {
                'excellent': len([c for c in scored_candidates if c.overall_score >= 90]),  # 90-100
                'good': len([c for c in scored_candidates if 75 <= c.overall_score < 90]),  # 75-89
                'average': len([c for c in scored_candidates if 50 <= c.overall_score < 75]),  # 50-74
                'poor': len([c for c in scored_candidates if c.overall_score < 50])  # <50
            }
            
            # Quality vs. outcome correlation
            hired_candidates = [c for c in scored_candidates if c.status == CandidateStatus.HIRED.value]
            rejected_candidates = [c for c in scored_candidates if c.status == CandidateStatus.REJECTED.value]
            
            avg_score_hired = (sum([c.overall_score for c in hired_candidates]) / len(hired_candidates)) if hired_candidates else 0
            avg_score_rejected = (sum([c.overall_score for c in rejected_candidates]) / len(rejected_candidates)) if rejected_candidates else 0
            
            # Source quality analysis
            source_quality = {}
            for candidate in scored_candidates:
                source = candidate.source or 'unknown'
                if source not in source_quality:
                    source_quality[source] = {'scores': [], 'hired': 0, 'total': 0}
                
                source_quality[source]['scores'].append(candidate.overall_score)
                source_quality[source]['total'] += 1
                if candidate.status == CandidateStatus.HIRED.value:
                    source_quality[source]['hired'] += 1
            
            # Calculate source averages
            for source in source_quality:
                scores = source_quality[source]['scores']
                source_quality[source]['avg_score'] = round(sum(scores) / len(scores), 2)
                source_quality[source]['hire_rate'] = round((source_quality[source]['hired'] / source_quality[source]['total']) * 100, 2)
            
            return {
                'score_distribution': score_ranges,
                'average_candidate_score': round(sum([c.overall_score for c in scored_candidates]) / len(scored_candidates), 2),
                'quality_outcome_correlation': {
                    'avg_score_hired': round(avg_score_hired, 2),
                    'avg_score_rejected': round(avg_score_rejected, 2),
                    'score_difference': round(avg_score_hired - avg_score_rejected, 2)
                },
                'source_quality_analysis': source_quality,
                'quality_trends': self._analyze_quality_trends(scored_candidates)
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_source_analytics(self, candidates: List[Candidate]) -> Dict:
        """Analyze candidate sources and their performance."""
        try:
            # Source distribution
            source_distribution = {}
            for candidate in candidates:
                source = candidate.source or 'unknown'
                if source not in source_distribution:
                    source_distribution[source] = {
                        'count': 0,
                        'hired': 0,
                        'rejected': 0,
                        'active': 0,
                        'scores': []
                    }
                
                source_distribution[source]['count'] += 1
                
                if candidate.status == CandidateStatus.HIRED.value:
                    source_distribution[source]['hired'] += 1
                elif candidate.status == CandidateStatus.REJECTED.value:
                    source_distribution[source]['rejected'] += 1
                else:
                    source_distribution[source]['active'] += 1
                
                if candidate.overall_score:
                    source_distribution[source]['scores'].append(candidate.overall_score)
            
            # Calculate source performance metrics
            source_performance = {}
            for source, data in source_distribution.items():
                total = data['count']
                hire_rate = (data['hired'] / total * 100) if total > 0 else 0
                avg_score = (sum(data['scores']) / len(data['scores'])) if data['scores'] else 0
                
                source_performance[source] = {
                    'total_candidates': total,
                    'hire_rate': round(hire_rate, 2),
                    'average_score': round(avg_score, 2),
                    'hired_count': data['hired'],
                    'active_count': data['active'],
                    'percentage_of_total': round((total / len(candidates)) * 100, 2) if candidates else 0
                }
            
            # Rank sources by performance
            top_sources = sorted(source_performance.items(), 
                               key=lambda x: (x[1]['hire_rate'], x[1]['average_score']), 
                               reverse=True)
            
            return {
                'source_distribution': source_distribution,
                'source_performance': source_performance,
                'top_performing_sources': dict(top_sources[:5]),
                'source_recommendations': self._generate_source_recommendations(source_performance)
            }
            
        except Exception as e:
            logger.error(f"Error calculating source analytics: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_trend_analysis(self, user_id: str = None, period_days: int = 30) -> Dict:
        """Calculate trends over time periods."""
        try:
            # Compare current period with previous period
            end_date = date.today()
            current_start = end_date - timedelta(days=period_days)
            previous_start = current_start - timedelta(days=period_days)
            
            # Get candidates for both periods
            query_base = Candidate.query
            if user_id:
                query_base = query_base.filter_by(user_id=user_id)
            
            current_candidates = query_base.filter(
                Candidate.created_at >= current_start,
                Candidate.created_at <= end_date + timedelta(days=1)
            ).all()
            
            previous_candidates = query_base.filter(
                Candidate.created_at >= previous_start,
                Candidate.created_at < current_start
            ).all()
            
            # Calculate trend metrics
            current_metrics = self._calculate_overview_metrics(current_candidates)
            previous_metrics = self._calculate_overview_metrics(previous_candidates)
            
            # Calculate changes
            trends = {}
            for metric in ['total_candidates', 'hired_candidates', 'hire_rate']:
                current_value = current_metrics.get(metric, 0)
                previous_value = previous_metrics.get(metric, 0)
                
                if previous_value > 0:
                    change_percent = ((current_value - previous_value) / previous_value) * 100
                else:
                    change_percent = 100 if current_value > 0 else 0
                
                trends[metric] = {
                    'current': current_value,
                    'previous': previous_value,
                    'change_percent': round(change_percent, 2),
                    'trend': 'up' if change_percent > 0 else 'down' if change_percent < 0 else 'stable'
                }
            
            return {
                'period_comparison': {
                    'current_period': f"{current_start.isoformat()} to {end_date.isoformat()}",
                    'previous_period': f"{previous_start.isoformat()} to {current_start.isoformat()}"
                },
                'trends': trends,
                'trend_summary': self._generate_trend_summary(trends)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend analysis: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_pipeline_velocity(self, candidates: List[Candidate]) -> Dict:
        """Calculate how quickly candidates move through pipeline stages."""
        # This would ideally use historical stage transition data
        # For now, we'll use current stage durations as a proxy
        
        velocity_metrics = {}
        for stage in PipelineStage:
            stage_candidates = [c for c in candidates if c.current_stage == stage.value]
            if stage_candidates:
                avg_duration = sum([c.days_in_current_stage for c in stage_candidates]) / len(stage_candidates)
                velocity_metrics[stage.value] = {
                    'avg_duration_days': round(avg_duration, 1),
                    'candidate_count': len(stage_candidates),
                    'velocity_score': self._calculate_stage_velocity_score(avg_duration)
                }
            else:
                velocity_metrics[stage.value] = {
                    'avg_duration_days': 0,
                    'candidate_count': 0,
                    'velocity_score': 0
                }
        
        return velocity_metrics
    
    def _calculate_stage_velocity_score(self, avg_duration: float) -> int:
        """Calculate velocity score based on average duration in stage."""
        # Optimal durations per stage (in days)
        optimal_durations = {
            PipelineStage.APPLIED.value: 2,
            PipelineStage.SCREENING.value: 5,
            PipelineStage.PHONE_INTERVIEW.value: 7,
            PipelineStage.TECHNICAL_ASSESSMENT.value: 10,
            PipelineStage.ON_SITE_INTERVIEW.value: 5,
            PipelineStage.FINAL_INTERVIEW.value: 3,
            PipelineStage.REFERENCE_CHECK.value: 5,
            PipelineStage.OFFER_MADE.value: 3
        }
        
        # Default optimal duration if not specified
        optimal = optimal_durations.get(PipelineStage.APPLIED.value, 7)
        
        # Calculate score (100 = optimal, decreases as duration increases)
        if avg_duration <= optimal:
            return 100
        elif avg_duration <= optimal * 2:
            return int(100 - ((avg_duration - optimal) / optimal) * 50)
        else:
            return max(0, int(50 - ((avg_duration - optimal * 2) / optimal) * 25))
    
    def _identify_pipeline_bottlenecks(self, stage_distribution: Dict, velocity_metrics: Dict) -> List[Dict]:
        """Identify pipeline bottlenecks based on stage distribution and velocity."""
        bottlenecks = []
        
        for stage, metrics in velocity_metrics.items():
            # High candidate count + low velocity = bottleneck
            candidate_count = metrics['candidate_count']
            velocity_score = metrics['velocity_score']
            
            if candidate_count > 5 and velocity_score < 50:  # Thresholds
                bottlenecks.append({
                    'stage': stage,
                    'candidate_count': candidate_count,
                    'avg_duration': metrics['avg_duration_days'],
                    'velocity_score': velocity_score,
                    'severity': 'high' if velocity_score < 30 else 'medium'
                })
        
        return sorted(bottlenecks, key=lambda x: x['velocity_score'])
    
    def _calculate_funnel_efficiency(self, conversion_rates: Dict) -> Dict:
        """Calculate overall funnel efficiency metrics."""
        rates = list(conversion_rates.values())
        
        if not rates:
            return {'overall_efficiency': 0, 'bottleneck_stage': None}
        
        overall_efficiency = sum(rates) / len(rates)
        bottleneck_stage = min(conversion_rates.items(), key=lambda x: x[1])[0] if rates else None
        
        return {
            'overall_efficiency': round(overall_efficiency, 2),
            'bottleneck_stage': bottleneck_stage,
            'efficiency_grade': self._grade_efficiency(overall_efficiency)
        }
    
    def _grade_efficiency(self, efficiency: float) -> str:
        """Grade funnel efficiency."""
        if efficiency >= 80:
            return 'A'
        elif efficiency >= 60:
            return 'B'
        elif efficiency >= 40:
            return 'C'
        elif efficiency >= 20:
            return 'D'
        else:
            return 'F'
    
    def _identify_drop_off_points(self, conversion_rates: Dict) -> List[Dict]:
        """Identify major drop-off points in the funnel."""
        drop_offs = []
        
        for transition, rate in conversion_rates.items():
            if rate < 30:  # Less than 30% conversion is concerning
                drop_offs.append({
                    'transition': transition,
                    'conversion_rate': rate,
                    'severity': 'high' if rate < 15 else 'medium'
                })
        
        return sorted(drop_offs, key=lambda x: x['conversion_rate'])
    
    def _calculate_velocity_score(self, avg_time_to_hire: float, stage_times: Dict) -> int:
        """Calculate overall pipeline velocity score."""
        # Industry benchmark: 30 days average time to hire
        benchmark = 30
        
        if avg_time_to_hire <= benchmark:
            return min(100, int(100 - (avg_time_to_hire / benchmark) * 20))
        else:
            return max(0, int(80 - ((avg_time_to_hire - benchmark) / benchmark) * 40))
    
    def _analyze_quality_trends(self, candidates: List[Candidate]) -> Dict:
        """Analyze quality trends over the period."""
        # Sort candidates by application date
        sorted_candidates = sorted(candidates, key=lambda c: c.applied_at)
        
        # Split into first half and second half of period
        mid_point = len(sorted_candidates) // 2
        first_half = sorted_candidates[:mid_point]
        second_half = sorted_candidates[mid_point:]
        
        first_half_scores = [c.overall_score for c in first_half if c.overall_score]
        second_half_scores = [c.overall_score for c in second_half if c.overall_score]
        
        first_avg = sum(first_half_scores) / len(first_half_scores) if first_half_scores else 0
        second_avg = sum(second_half_scores) / len(second_half_scores) if second_half_scores else 0
        
        trend = 'improving' if second_avg > first_avg else 'declining' if second_avg < first_avg else 'stable'
        
        return {
            'first_half_avg_score': round(first_avg, 2),
            'second_half_avg_score': round(second_avg, 2),
            'trend': trend,
            'change_points': round(second_avg - first_avg, 2)
        }
    
    def _generate_source_recommendations(self, source_performance: Dict) -> List[str]:
        """Generate recommendations based on source performance."""
        recommendations = []
        
        if not source_performance:
            return recommendations
        
        # Find best performing source
        best_source = max(source_performance.items(), key=lambda x: (x[1]['hire_rate'], x[1]['average_score']))
        recommendations.append(f"Best performing source: {best_source[0]} (hire rate: {best_source[1]['hire_rate']}%)")
        
        # Find underperforming sources
        poor_sources = [source for source, data in source_performance.items() 
                       if data['hire_rate'] < 10 and data['total_candidates'] > 5]
        
        if poor_sources:
            recommendations.append(f"Consider reviewing these low-performing sources: {', '.join(poor_sources)}")
        
        # Find sources with high volume but low quality
        high_volume_low_quality = [source for source, data in source_performance.items() 
                                  if data['total_candidates'] > 10 and data['average_score'] < 50]
        
        if high_volume_low_quality:
            recommendations.append(f"High volume but low quality sources need screening improvement: {', '.join(high_volume_low_quality)}")
        
        return recommendations
    
    def _generate_performance_insights(self, candidates: List[Candidate]) -> List[str]:
        """Generate performance insights based on analytics."""
        insights = []
        
        if not candidates:
            return insights
        
        # Overall pipeline health
        total = len(candidates)
        active = len([c for c in candidates if c.status == CandidateStatus.ACTIVE.value])
        hired = len([c for c in candidates if c.status == CandidateStatus.HIRED.value])
        
        if hired / total > 0.2:
            insights.append(f"Strong hiring performance: {(hired/total)*100:.1f}% conversion rate")
        elif hired / total < 0.05:
            insights.append("Low hiring conversion rate - review qualification criteria")
        
        # Quality insights
        scored = [c for c in candidates if c.overall_score]
        if scored:
            avg_score = sum([c.overall_score for c in scored]) / len(scored)
            if avg_score > 75:
                insights.append("High quality candidate pool - strong sourcing strategy")
            elif avg_score < 50:
                insights.append("Low average candidate quality - improve sourcing and screening")
        
        # Priority insights
        high_priority = len([c for c in candidates if c.priority in [Priority.HIGH.value, Priority.URGENT.value]])
        if high_priority / total > 0.3:
            insights.append("High percentage of priority candidates - ensure fast-track process")
        
        return insights
    
    def _generate_analytics_recommendations(self, candidates: List[Candidate]) -> List[str]:
        """Generate actionable recommendations based on analytics."""
        recommendations = []
        
        if not candidates:
            return ["Increase candidate sourcing efforts"]
        
        # Time-based recommendations
        long_pipeline = [c for c in candidates if c.days_in_pipeline > 45]
        if len(long_pipeline) / len(candidates) > 0.3:
            recommendations.append("30%+ of candidates have been in pipeline >45 days - accelerate decision-making")
        
        # Quality-based recommendations
        scored = [c for c in candidates if c.overall_score]
        if scored:
            low_scores = [c for c in scored if c.overall_score < 40]
            if len(low_scores) / len(scored) > 0.5:
                recommendations.append("50%+ of candidates score below 40 - improve initial screening")
        
        # Stage-based recommendations
        stuck_in_screening = len([c for c in candidates 
                                if c.current_stage == PipelineStage.SCREENING.value 
                                and c.days_in_current_stage > 7])
        
        if stuck_in_screening > 5:
            recommendations.append(f"{stuck_in_screening} candidates stuck in screening >7 days - review screening process")
        
        return recommendations
    
    def _generate_trend_summary(self, trends: Dict) -> str:
        """Generate human-readable trend summary."""
        summaries = []
        
        for metric, data in trends.items():
            change = data['change_percent']
            trend = data['trend']
            
            if abs(change) > 10:  # Significant change
                direction = "increased" if trend == 'up' else "decreased"
                summaries.append(f"{metric.replace('_', ' ').title()} {direction} by {abs(change):.1f}%")
        
        if summaries:
            return "; ".join(summaries)
        else:
            return "Stable performance across all metrics"
    
    def _store_analytics_snapshot(self, user_id: str, analytics: Dict, 
                                start_date: date, end_date: date):
        """Store analytics snapshot in database."""
        try:
            if not user_id:
                return  # Don't store system-wide analytics
            
            # Create or update hiring analytics record
            period_type = "monthly" if (end_date - start_date).days > 20 else "weekly"
            
            analytics_record = HiringAnalytics(
                user_id=user_id,
                period_start=start_date,
                period_end=end_date,
                period_type=period_type,
                total_candidates=analytics['overview']['total_candidates'],
                active_candidates=analytics['overview']['active_candidates'],
                hired_candidates=analytics['overview']['hired_candidates'],
                rejected_candidates=analytics['overview']['rejected_candidates'],
                overall_conversion_rate=analytics['overview']['hire_rate'],
                avg_candidate_score=analytics['overview']['scoring_stats']['average_score'],
                high_priority_candidates=analytics['overview']['priority_distribution'].get(Priority.HIGH.value, 0),
                ai_match_score_avg=analytics['quality_metrics'].get('average_candidate_score', 0),
                source_breakdown=analytics['source_analytics']['source_performance'],
                avg_time_to_hire=analytics['time_metrics']['average_time_to_hire']
            )
            
            from app import db
            db.session.add(analytics_record)
            db.session.commit()
            
            logger.info(f"Analytics snapshot stored for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing analytics snapshot: {str(e)}")
    
    def get_historical_analytics(self, user_id: str, months: int = 6) -> Dict:
        """Get historical analytics trends."""
        try:
            # Get historical analytics records
            since_date = date.today() - timedelta(days=months * 30)
            
            historical_records = HiringAnalytics.query.filter(
                HiringAnalytics.user_id == user_id,
                HiringAnalytics.period_start >= since_date
            ).order_by(HiringAnalytics.period_start.desc()).all()
            
            if not historical_records:
                return {'message': 'No historical analytics data available'}
            
            # Format historical data
            historical_data = []
            for record in historical_records:
                historical_data.append({
                    'period': f"{record.period_start.isoformat()} to {record.period_end.isoformat()}",
                    'total_candidates': record.total_candidates,
                    'hire_rate': record.overall_conversion_rate,
                    'avg_score': record.avg_candidate_score,
                    'avg_time_to_hire': record.avg_time_to_hire
                })
            
            return {
                'historical_data': historical_data,
                'trends': self._analyze_historical_trends(historical_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting historical analytics: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_historical_trends(self, historical_data: List[Dict]) -> Dict:
        """Analyze trends in historical data."""
        if len(historical_data) < 2:
            return {'message': 'Insufficient data for trend analysis'}
        
        # Calculate trends for key metrics
        metrics = ['total_candidates', 'hire_rate', 'avg_score', 'avg_time_to_hire']
        trends = {}
        
        for metric in metrics:
            values = [record[metric] for record in historical_data if record[metric] is not None]
            
            if len(values) >= 2:
                recent_avg = sum(values[:3]) / min(3, len(values))  # Last 3 periods
                older_avg = sum(values[-3:]) / min(3, len(values))   # Earlier periods
                
                if older_avg > 0:
                    change_percent = ((recent_avg - older_avg) / older_avg) * 100
                    trend_direction = 'improving' if change_percent > 5 else 'declining' if change_percent < -5 else 'stable'
                else:
                    change_percent = 0
                    trend_direction = 'stable'
                
                trends[metric] = {
                    'change_percent': round(change_percent, 2),
                    'trend': trend_direction,
                    'recent_average': round(recent_avg, 2),
                    'historical_average': round(older_avg, 2)
                }
        
        return trends
