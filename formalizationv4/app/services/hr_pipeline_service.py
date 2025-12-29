"""
HR Pipeline Management Service - CRM for HR functionality.
Manages candidate relationships, pipeline workflows, and hiring processes.
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from app.models.candidate import (Candidate, CandidateActivity, PipelineStageHistory, 
                                Interview, CandidateAlert, HiringAnalytics, 
                                PipelineStage, CandidateStatus, Priority)
from app.models.user import User
from app.services.candidate_scoring_service import CandidateScoringService
from app.services.websocket_service import WebSocketService
import json

logger = logging.getLogger(__name__)

class HRPipelineService:
    """Service for managing HR pipeline and candidate relationships."""
    
    # Pipeline stage order for progression logic
    STAGE_ORDER = [
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
    
    # Stage time limits (in days) for automatic alerts
    STAGE_TIME_LIMITS = {
        PipelineStage.APPLIED.value: 3,
        PipelineStage.SCREENING.value: 7,
        PipelineStage.PHONE_INTERVIEW.value: 10,
        PipelineStage.TECHNICAL_ASSESSMENT.value: 14,
        PipelineStage.ON_SITE_INTERVIEW.value: 7,
        PipelineStage.FINAL_INTERVIEW.value: 5,
        PipelineStage.REFERENCE_CHECK.value: 7,
        PipelineStage.OFFER_MADE.value: 5
    }
    
    def __init__(self, scoring_service: CandidateScoringService = None, 
                 websocket_service: WebSocketService = None):
        self.scoring_service = scoring_service or CandidateScoringService()
        self.websocket_service = websocket_service
    
    def create_candidate(self, user_id: str, candidate_data: Dict, resume_id: str = None) -> Dict:
        """Create a new candidate record."""
        try:
            logger.info(f"Creating new candidate: {candidate_data.get('first_name')} {candidate_data.get('last_name')}")
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email', 'position_title']
            for field in required_fields:
                if not candidate_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Check for duplicate candidates
            existing = Candidate.query.filter_by(
                user_id=user_id,
                email=candidate_data['email'],
                position_title=candidate_data['position_title']
            ).first()
            
            if existing:
                logger.warning(f"Candidate already exists: {existing.full_name}")
                return {'error': 'Candidate already exists with this email and position'}
            
            # Create candidate record
            candidate = Candidate(
                user_id=user_id,
                resume_id=resume_id,
                first_name=candidate_data['first_name'],
                last_name=candidate_data['last_name'],
                email=candidate_data['email'],
                phone=candidate_data.get('phone'),
                position_title=candidate_data['position_title'],
                department=candidate_data.get('department'),
                hiring_manager=candidate_data.get('hiring_manager'),
                recruiter=candidate_data.get('recruiter'),
                job_req_id=candidate_data.get('job_req_id'),
                source=candidate_data.get('source', 'manual'),
                linkedin_url=candidate_data.get('linkedin_url'),
                portfolio_url=candidate_data.get('portfolio_url'),
                salary_expectation=candidate_data.get('salary_expectation'),
                notice_period=candidate_data.get('notice_period'),
                expected_start_date=candidate_data.get('expected_start_date'),
                referrer_name=candidate_data.get('referrer_name'),
                referrer_email=candidate_data.get('referrer_email')
            )
            
            from app import db
            db.session.add(candidate)
            db.session.flush()  # Get the ID
            
            # Add initial activity
            candidate.add_activity(
                activity_type='created',
                description=f"Candidate added to pipeline for {candidate.position_title}",
                details={
                    'source': candidate.source,
                    'initial_stage': candidate.current_stage
                },
                created_by=candidate_data.get('created_by', 'System')
            )
            
            # Create initial stage history
            initial_stage = PipelineStageHistory(
                candidate_id=candidate.id,
                from_stage=None,
                to_stage=candidate.current_stage,
                notes="Candidate added to pipeline",
                moved_by=candidate_data.get('created_by', 'System'),
                changed_at=datetime.utcnow()
            )
            db.session.add(initial_stage)
            
            # If resume is linked, trigger scoring
            if resume_id:
                try:
                    scoring_result = self.scoring_service.score_candidate(candidate)
                    logger.info(f"Candidate scored: {scoring_result.get('overall_score', 0)}")
                except Exception as e:
                    logger.warning(f"Could not score candidate immediately: {str(e)}")
            
            db.session.commit()
            
            # Send real-time notification
            if self.websocket_service:
                self._send_pipeline_update('candidate_created', candidate)
            
            logger.info(f"Candidate created successfully: {candidate.full_name} (ID: {candidate.id})")
            return {
                'success': True,
                'candidate': candidate.to_dict(include_sensitive=True),
                'message': f"Candidate {candidate.full_name} added to pipeline"
            }
            
        except Exception as e:
            logger.error(f"Error creating candidate: {str(e)}")
            from app import db
            db.session.rollback()
            return {'error': str(e)}
    
    def update_candidate(self, candidate_id: str, update_data: Dict, updated_by: str = None) -> Dict:
        """Update candidate information."""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {'error': 'Candidate not found'}
            
            logger.info(f"Updating candidate: {candidate.full_name}")
            
            # Track changes for activity log
            changes = []
            
            # Update basic fields
            updateable_fields = [
                'first_name', 'last_name', 'email', 'phone', 'position_title',
                'department', 'hiring_manager', 'recruiter', 'job_req_id',
                'linkedin_url', 'portfolio_url', 'salary_expectation',
                'notice_period', 'expected_start_date', 'qualification_notes',
                'communication_notes', 'last_contact_date', 'next_followup_date'
            ]
            
            for field in updateable_fields:
                if field in update_data:
                    old_value = getattr(candidate, field)
                    new_value = update_data[field]
                    if old_value != new_value:
                        setattr(candidate, field, new_value)
                        changes.append(f"{field}: {old_value} → {new_value}")
            
            # Handle manual score updates
            score_fields = ['technical_score', 'cultural_fit_score', 'experience_score']
            for field in score_fields:
                if field in update_data:
                    old_value = getattr(candidate, field)
                    new_value = float(update_data[field])
                    if old_value != new_value:
                        setattr(candidate, field, new_value)
                        changes.append(f"{field}: {old_value} → {new_value}")
                        
                        # Recalculate overall score
                        candidate.calculate_overall_score()
            
            # Handle priority updates
            if 'priority' in update_data and update_data['priority'] != candidate.priority:
                old_priority = candidate.priority
                candidate.priority = update_data['priority']
                changes.append(f"priority: {old_priority} → {candidate.priority}")
            
            candidate.updated_at = datetime.utcnow()
            
            # Log activity if there were changes
            if changes:
                candidate.add_activity(
                    activity_type='updated',
                    description=f"Candidate information updated: {', '.join(changes[:3])}{'...' if len(changes) > 3 else ''}",
                    details={'changes': changes},
                    created_by=updated_by or 'System'
                )
            
            from app import db
            db.session.commit()
            
            # Send real-time notification
            if self.websocket_service:
                self._send_pipeline_update('candidate_updated', candidate)
            
            logger.info(f"Candidate updated successfully: {candidate.full_name}")
            return {
                'success': True,
                'candidate': candidate.to_dict(include_sensitive=True),
                'changes': changes
            }
            
        except Exception as e:
            logger.error(f"Error updating candidate {candidate_id}: {str(e)}")
            from app import db
            db.session.rollback()
            return {'error': str(e)}
    
    def move_candidate_stage(self, candidate_id: str, new_stage: str, 
                           notes: str = None, moved_by: str = None) -> Dict:
        """Move candidate to a new pipeline stage."""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {'error': 'Candidate not found'}
            
            # Validate stage
            if new_stage not in [stage.value for stage in PipelineStage]:
                return {'error': 'Invalid pipeline stage'}
            
            old_stage = candidate.current_stage
            
            if old_stage == new_stage:
                return {'error': 'Candidate already in this stage'}
            
            logger.info(f"Moving candidate {candidate.full_name} from {old_stage} to {new_stage}")
            
            # Use the candidate's move_to_stage method
            candidate.move_to_stage(new_stage, notes, moved_by)
            
            # Add activity record
            candidate.add_activity(
                activity_type='stage_change',
                description=f"Moved from {old_stage} to {new_stage}",
                details={
                    'from_stage': old_stage,
                    'to_stage': new_stage,
                    'notes': notes
                },
                created_by=moved_by or 'System'
            )
            
            # Recalculate score (stage progression affects scoring)
            try:
                self.scoring_service.score_candidate(candidate, recalculate=True)
            except Exception as e:
                logger.warning(f"Could not recalculate score after stage move: {str(e)}")
            
            from app import db
            db.session.commit()
            
            # Send real-time notification
            if self.websocket_service:
                self._send_pipeline_update('stage_changed', candidate, {
                    'from_stage': old_stage,
                    'to_stage': new_stage
                })
            
            logger.info(f"Candidate {candidate.full_name} moved to {new_stage}")
            return {
                'success': True,
                'candidate': candidate.to_dict(),
                'from_stage': old_stage,
                'to_stage': new_stage
            }
            
        except Exception as e:
            logger.error(f"Error moving candidate stage: {str(e)}")
            from app import db
            db.session.rollback()
            return {'error': str(e)}
    
    def get_pipeline_overview(self, user_id: str = None, department: str = None) -> Dict:
        """Get comprehensive pipeline overview."""
        try:
            query = Candidate.query.filter_by(status=CandidateStatus.ACTIVE.value)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            if department:
                query = query.filter_by(department=department)
            
            candidates = query.all()
            
            # Calculate stage distribution
            stage_distribution = {}
            for stage in PipelineStage:
                stage_candidates = [c for c in candidates if c.current_stage == stage.value]
                stage_distribution[stage.value] = {
                    'count': len(stage_candidates),
                    'candidates': [c.to_dict() for c in stage_candidates[:5]],  # Top 5
                    'avg_score': round(sum([c.overall_score for c in stage_candidates if c.overall_score]) /
                                     len([c for c in stage_candidates if c.overall_score]), 2) 
                                if stage_candidates else 0,
                    'high_priority_count': len([c for c in stage_candidates if c.priority == Priority.HIGH.value])
                }
            
            # Calculate priority distribution
            priority_distribution = {}
            for priority in Priority:
                priority_candidates = [c for c in candidates if c.priority == priority.value]
                priority_distribution[priority.value] = len(priority_candidates)
            
            # Get stalled candidates (those who have been in stage too long)
            stalled_candidates = self._get_stalled_candidates(candidates)
            
            # Get top candidates
            top_candidates = sorted([c for c in candidates if c.overall_score], 
                                  key=lambda x: x.overall_score, reverse=True)[:10]
            
            # Calculate conversion rates
            conversion_rates = self._calculate_conversion_rates(user_id)
            
            # Recent activity
            recent_activity = self._get_recent_pipeline_activity(user_id, limit=20)
            
            overview = {
                'summary': {
                    'total_active_candidates': len(candidates),
                    'total_stages': len(PipelineStage),
                    'avg_pipeline_score': round(sum([c.overall_score for c in candidates if c.overall_score]) /
                                               len([c for c in candidates if c.overall_score]), 2) 
                                          if candidates else 0,
                    'stalled_candidates_count': len(stalled_candidates),
                    'high_priority_count': priority_distribution.get(Priority.HIGH.value, 0) + 
                                         priority_distribution.get(Priority.URGENT.value, 0)
                },
                'stage_distribution': stage_distribution,
                'priority_distribution': priority_distribution,
                'conversion_rates': conversion_rates,
                'top_candidates': [c.to_dict() for c in top_candidates],
                'stalled_candidates': [c.to_dict() for c in stalled_candidates],
                'recent_activity': recent_activity,
                'pipeline_health': self._calculate_pipeline_health(candidates)
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting pipeline overview: {str(e)}")
            return {'error': str(e)}
    
    def get_candidate_timeline(self, candidate_id: str) -> Dict:
        """Get comprehensive timeline for a candidate."""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {'error': 'Candidate not found'}
            
            # Get stage history
            stage_history = candidate.stage_history.order_by(
                PipelineStageHistory.changed_at.asc()
            ).all()
            
            # Get activities
            activities = candidate.activities.order_by(
                CandidateActivity.created_at.asc()
            ).all()
            
            # Get interviews
            interviews = candidate.interviews.order_by(
                Interview.scheduled_at.asc()
            ).all()
            
            # Combine into timeline
            timeline_events = []
            
            # Add stage changes
            for stage in stage_history:
                timeline_events.append({
                    'type': 'stage_change',
                    'timestamp': stage.changed_at,
                    'data': stage.to_dict()
                })
            
            # Add activities
            for activity in activities:
                timeline_events.append({
                    'type': 'activity',
                    'timestamp': activity.created_at,
                    'data': activity.to_dict()
                })
            
            # Add interviews
            for interview in interviews:
                timeline_events.append({
                    'type': 'interview',
                    'timestamp': interview.scheduled_at,
                    'data': interview.to_dict()
                })
            
            # Sort by timestamp
            timeline_events.sort(key=lambda x: x['timestamp'])
            
            return {
                'candidate': candidate.to_dict(include_sensitive=True),
                'timeline': timeline_events,
                'timeline_summary': {
                    'total_events': len(timeline_events),
                    'stage_changes': len(stage_history),
                    'activities': len(activities),
                    'interviews': len(interviews),
                    'days_in_pipeline': candidate.days_in_pipeline,
                    'current_stage_duration': candidate.days_in_current_stage
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting candidate timeline: {str(e)}")
            return {'error': str(e)}
    
    def schedule_interview(self, candidate_id: str, interview_data: Dict) -> Dict:
        """Schedule an interview for a candidate."""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {'error': 'Candidate not found'}
            
            # Validate required fields
            required_fields = ['interview_type', 'scheduled_at', 'interviewer_name']
            for field in required_fields:
                if not interview_data.get(field):
                    return {'error': f"Missing required field: {field}"}
            
            # Create interview record
            interview = Interview(
                candidate_id=candidate.id,
                interview_type=interview_data['interview_type'],
                interviewer_name=interview_data['interviewer_name'],
                interviewer_email=interview_data.get('interviewer_email'),
                scheduled_at=datetime.fromisoformat(interview_data['scheduled_at'].replace('Z', '+00:00')),
                duration_minutes=interview_data.get('duration_minutes', 60),
                location=interview_data.get('location')
            )
            
            from app import db
            db.session.add(interview)
            
            # Add activity
            candidate.add_activity(
                activity_type='interview_scheduled',
                description=f"{interview_data['interview_type']} interview scheduled with {interview_data['interviewer_name']}",
                details={
                    'interview_type': interview_data['interview_type'],
                    'interviewer': interview_data['interviewer_name'],
                    'scheduled_at': interview_data['scheduled_at'],
                    'location': interview_data.get('location')
                },
                created_by=interview_data.get('scheduled_by', 'System')
            )
            
            db.session.commit()
            
            # Send real-time notification
            if self.websocket_service:
                self._send_pipeline_update('interview_scheduled', candidate, {
                    'interview': interview.to_dict()
                })
            
            logger.info(f"Interview scheduled for {candidate.full_name}: {interview_data['interview_type']}")
            return {
                'success': True,
                'interview': interview.to_dict(),
                'candidate': candidate.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling interview: {str(e)}")
            from app import db
            db.session.rollback()
            return {'error': str(e)}
    
    def add_candidate_note(self, candidate_id: str, note_data: Dict) -> Dict:
        """Add a note/activity to a candidate."""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {'error': 'Candidate not found'}
            
            activity = candidate.add_activity(
                activity_type=note_data.get('activity_type', 'note'),
                description=note_data['description'],
                details=note_data.get('details'),
                created_by=note_data.get('created_by', 'System')
            )
            
            from app import db
            db.session.commit()
            
            logger.info(f"Note added to candidate {candidate.full_name}")
            return {
                'success': True,
                'activity': activity.to_dict(),
                'candidate': candidate.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error adding candidate note: {str(e)}")
            from app import db
            db.session.rollback()
            return {'error': str(e)}
    
    def _get_stalled_candidates(self, candidates: List[Candidate]) -> List[Candidate]:
        """Identify candidates who have been stalled in their current stage."""
        stalled = []
        
        for candidate in candidates:
            stage_limit = self.STAGE_TIME_LIMITS.get(candidate.current_stage)
            if stage_limit and candidate.days_in_current_stage > stage_limit:
                stalled.append(candidate)
        
        return stalled
    
    def _calculate_conversion_rates(self, user_id: str = None) -> Dict:
        """Calculate conversion rates between pipeline stages."""
        try:
            query = PipelineStageHistory.query
            if user_id:
                query = query.join(Candidate).filter(Candidate.user_id == user_id)
            
            # Get last 90 days of stage changes
            since_date = datetime.utcnow() - timedelta(days=90)
            stage_changes = query.filter(
                PipelineStageHistory.changed_at >= since_date
            ).all()
            
            if not stage_changes:
                return {}
            
            # Count transitions
            transitions = {}
            for change in stage_changes:
                from_stage = change.from_stage
                to_stage = change.to_stage
                
                if from_stage:  # Skip initial stage assignments
                    key = f"{from_stage}_to_{to_stage}"
                    transitions[key] = transitions.get(key, 0) + 1
            
            # Calculate rates
            conversion_rates = {}
            for i, stage in enumerate(self.STAGE_ORDER[:-1]):
                next_stage = self.STAGE_ORDER[i + 1]
                
                # Count candidates who entered this stage
                entered = sum([v for k, v in transitions.items() if k.endswith(f"_to_{stage}")])
                if entered == 0:
                    # If no transitions TO this stage, count initial candidates
                    entered = len([c for c in stage_changes if c.to_stage == stage and not c.from_stage])
                
                # Count candidates who progressed from this stage to next
                progressed = transitions.get(f"{stage}_to_{next_stage}", 0)
                
                if entered > 0:
                    rate = (progressed / entered) * 100
                    conversion_rates[f"{stage}_to_{next_stage}"] = round(rate, 2)
            
            return conversion_rates
            
        except Exception as e:
            logger.error(f"Error calculating conversion rates: {str(e)}")
            return {}
    
    def _get_recent_pipeline_activity(self, user_id: str = None, limit: int = 20) -> List[Dict]:
        """Get recent pipeline activity across all candidates."""
        try:
            query = CandidateActivity.query.join(Candidate)
            
            if user_id:
                query = query.filter(Candidate.user_id == user_id)
            
            activities = query.order_by(
                CandidateActivity.created_at.desc()
            ).limit(limit).all()
            
            return [activity.to_dict() for activity in activities]
            
        except Exception as e:
            logger.error(f"Error getting recent pipeline activity: {str(e)}")
            return []
    
    def _calculate_pipeline_health(self, candidates: List[Candidate]) -> Dict:
        """Calculate overall pipeline health metrics."""
        if not candidates:
            return {'status': 'no_data', 'score': 0}
        
        health_factors = {
            'stage_distribution': 0,  # Even distribution across stages
            'progression_speed': 0,   # Candidates moving through stages
            'quality_score': 0,       # Average candidate quality
            'stalled_ratio': 0        # Ratio of stalled candidates
        }
        
        # Stage distribution health (0-25 points)
        stage_counts = {}
        for stage in PipelineStage:
            stage_counts[stage.value] = len([c for c in candidates if c.current_stage == stage.value])
        
        # Healthy pipeline has more candidates in early stages
        early_stages = [PipelineStage.APPLIED.value, PipelineStage.SCREENING.value, 
                       PipelineStage.PHONE_INTERVIEW.value]
        early_count = sum([stage_counts.get(stage, 0) for stage in early_stages])
        
        if len(candidates) > 0:
            early_ratio = early_count / len(candidates)
            health_factors['stage_distribution'] = min(early_ratio * 25, 25)
        
        # Quality score health (0-25 points)
        scored_candidates = [c for c in candidates if c.overall_score]
        if scored_candidates:
            avg_score = sum([c.overall_score for c in scored_candidates]) / len(scored_candidates)
            health_factors['quality_score'] = (avg_score / 100) * 25
        
        # Stalled ratio health (0-25 points)
        stalled_candidates = self._get_stalled_candidates(candidates)
        if len(candidates) > 0:
            stalled_ratio = len(stalled_candidates) / len(candidates)
            health_factors['stalled_ratio'] = max(0, 25 - (stalled_ratio * 50))
        
        # Progression speed (0-25 points) - simplified
        health_factors['progression_speed'] = 15  # Default moderate score
        
        # Calculate overall health score
        overall_score = sum(health_factors.values())
        
        # Determine health status
        if overall_score >= 80:
            status = 'excellent'
        elif overall_score >= 60:
            status = 'good'
        elif overall_score >= 40:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'status': status,
            'score': round(overall_score, 1),
            'factors': health_factors,
            'recommendations': self._generate_health_recommendations(health_factors, candidates)
        }
    
    def _generate_health_recommendations(self, health_factors: Dict, candidates: List[Candidate]) -> List[str]:
        """Generate recommendations based on pipeline health."""
        recommendations = []
        
        if health_factors['stage_distribution'] < 15:
            recommendations.append("Focus on attracting more candidates to fill the top of the pipeline")
        
        if health_factors['quality_score'] < 15:
            recommendations.append("Review sourcing strategies - candidate quality is below average")
        
        if health_factors['stalled_ratio'] < 15:
            recommendations.append("Too many stalled candidates - review and move or reject")
        
        if health_factors['progression_speed'] < 15:
            recommendations.append("Candidates are moving slowly through the pipeline - identify bottlenecks")
        
        # High priority candidates not progressing
        high_priority_stalled = [c for c in candidates 
                               if c.priority in [Priority.HIGH.value, Priority.URGENT.value] 
                               and c.days_in_current_stage > 7]
        
        if high_priority_stalled:
            recommendations.append(f"{len(high_priority_stalled)} high-priority candidates are stalled - immediate action needed")
        
        return recommendations
    
    def _send_pipeline_update(self, event_type: str, candidate: Candidate, extra_data: Dict = None):
        """Send real-time pipeline updates via WebSocket."""
        if not self.websocket_service:
            return
        
        try:
            update_data = {
                'event_type': event_type,
                'candidate_id': str(candidate.id),
                'candidate_name': candidate.full_name,
                'position': candidate.position_title,
                'stage': candidate.current_stage,
                'priority': candidate.priority,
                'score': candidate.overall_score,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if extra_data:
                update_data.update(extra_data)
            
            # Send to user's room
            self.websocket_service.send_to_user(
                str(candidate.user_id),
                'pipeline_update',
                update_data
            )
            
            # Send to admin room if applicable
            self.websocket_service.send_to_admins('pipeline_update', update_data)
            
        except Exception as e:
            logger.error(f"Error sending pipeline update: {str(e)}")
    
    def bulk_update_candidates(self, candidate_ids: List[str], update_data: Dict, 
                             updated_by: str = None) -> Dict:
        """Bulk update multiple candidates."""
        try:
            candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
            
            if not candidates:
                return {'error': 'No candidates found'}
            
            results = {
                'updated': 0,
                'errors': 0,
                'candidates': []
            }
            
            for candidate in candidates:
                try:
                    result = self.update_candidate(str(candidate.id), update_data, updated_by)
                    if result.get('success'):
                        results['updated'] += 1
                        results['candidates'].append(result['candidate'])
                    else:
                        results['errors'] += 1
                        logger.error(f"Error updating candidate {candidate.full_name}: {result.get('error')}")
                        
                except Exception as e:
                    results['errors'] += 1
                    logger.error(f"Error updating candidate {candidate.full_name}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk candidate update: {str(e)}")
            return {'error': str(e)}
