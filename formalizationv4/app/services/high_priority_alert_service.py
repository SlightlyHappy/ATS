"""
High-Priority Alert Service for real-time notifications about top candidates.
Monitors candidate status and generates alerts for important events.
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.models.candidate import (Candidate, CandidateAlert, CandidateActivity, PipelineStageHistory,
                                PipelineStage, CandidateStatus, Priority)
from app.models.user import User
from app.services.websocket_service import WebSocketService
import json

logger = logging.getLogger(__name__)

class HighPriorityAlertService:
    """Service for generating and managing high-priority candidate alerts."""
    
    # Alert types and their configurations
    ALERT_CONFIGS = {
        'high_score_candidate': {
            'threshold': 85,
            'priority': Priority.HIGH.value,
            'expires_hours': 72,
            'auto_dismiss': False
        },
        'urgent_candidate': {
            'threshold': 95,
            'priority': Priority.URGENT.value,
            'expires_hours': 24,
            'auto_dismiss': False
        },
        'stalled_high_priority': {
            'days_threshold': 7,
            'priority': Priority.HIGH.value,
            'expires_hours': 48,
            'auto_dismiss': False
        },
        'offer_deadline_approaching': {
            'days_before': 2,
            'priority': Priority.URGENT.value,
            'expires_hours': 48,
            'auto_dismiss': True
        },
        'competitor_risk': {
            'priority': Priority.HIGH.value,
            'expires_hours': 48,
            'auto_dismiss': False
        },
        'interview_no_show': {
            'priority': Priority.MEDIUM.value,
            'expires_hours': 24,
            'auto_dismiss': False
        },
        'follow_up_overdue': {
            'days_overdue': 3,
            'priority': Priority.MEDIUM.value,
            'expires_hours': 24,
            'auto_dismiss': False
        },
        'reference_check_needed': {
            'priority': Priority.MEDIUM.value,
            'expires_hours': 72,
            'auto_dismiss': False
        }
    }
    
    def __init__(self, websocket_service: WebSocketService = None):
        self.websocket_service = websocket_service
    
    def check_and_generate_alerts(self, user_id: str = None) -> Dict:
        """Check all candidates and generate necessary alerts."""
        try:
            logger.info(f"Checking for high-priority alerts (user: {user_id})")
            
            # Get active candidates
            query = Candidate.query.filter_by(status=CandidateStatus.ACTIVE.value)
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            candidates = query.all()
            
            alerts_generated = {
                'total_checked': len(candidates),
                'alerts_created': 0,
                'alerts_by_type': {},
                'candidates_with_alerts': [],
                'errors': 0
            }
            
            for candidate in candidates:
                try:
                    candidate_alerts = self._check_candidate_alerts(candidate)
                    
                    for alert_data in candidate_alerts:
                        alert = self._create_alert(candidate, alert_data)
                        if alert:
                            alerts_generated['alerts_created'] += 1
                            alert_type = alert_data['alert_type']
                            alerts_generated['alerts_by_type'][alert_type] = alerts_generated['alerts_by_type'].get(alert_type, 0) + 1
                            
                            if candidate.id not in [c['id'] for c in alerts_generated['candidates_with_alerts']]:
                                alerts_generated['candidates_with_alerts'].append({
                                    'id': str(candidate.id),
                                    'name': candidate.full_name,
                                    'position': candidate.position_title,
                                    'priority': candidate.priority
                                })
                
                except Exception as e:
                    logger.error(f"Error checking alerts for candidate {candidate.full_name}: {str(e)}")
                    alerts_generated['errors'] += 1
            
            # Clean up expired alerts
            self._cleanup_expired_alerts()
            
            logger.info(f"Alert check completed: {alerts_generated['alerts_created']} alerts generated")
            return alerts_generated
            
        except Exception as e:
            logger.error(f"Error in alert generation process: {str(e)}")
            return {'error': str(e)}
    
    def _check_candidate_alerts(self, candidate: Candidate) -> List[Dict]:
        """Check a single candidate for all possible alerts."""
        alerts_to_create = []
        
        # 1. High Score Candidate Alert
        if (candidate.overall_score and 
            candidate.overall_score >= self.ALERT_CONFIGS['high_score_candidate']['threshold'] and
            not self._alert_exists(candidate, 'high_score_candidate')):
            
            alerts_to_create.append({
                'alert_type': 'high_score_candidate',
                'title': f"High-Scoring Candidate: {candidate.full_name}",
                'message': f"Candidate scored {candidate.overall_score:.1f}/100 for {candidate.position_title}. Consider fast-tracking through pipeline.",
                'priority': self.ALERT_CONFIGS['high_score_candidate']['priority']
            })
        
        # 2. Urgent Candidate Alert
        if (candidate.overall_score and 
            candidate.overall_score >= self.ALERT_CONFIGS['urgent_candidate']['threshold'] and
            not self._alert_exists(candidate, 'urgent_candidate')):
            
            alerts_to_create.append({
                'alert_type': 'urgent_candidate',
                'title': f"URGENT: Top Candidate {candidate.full_name}",
                'message': f"Exceptional candidate (score: {candidate.overall_score:.1f}/100) - immediate action required to secure hire.",
                'priority': self.ALERT_CONFIGS['urgent_candidate']['priority']
            })
        
        # 3. Stalled High Priority Candidate
        if (candidate.priority in [Priority.HIGH.value, Priority.URGENT.value] and
            candidate.days_in_current_stage >= self.ALERT_CONFIGS['stalled_high_priority']['days_threshold'] and
            not self._alert_exists(candidate, 'stalled_high_priority')):
            
            alerts_to_create.append({
                'alert_type': 'stalled_high_priority',
                'title': f"High-Priority Candidate Stalled: {candidate.full_name}",
                'message': f"High-priority candidate has been in {candidate.current_stage} stage for {candidate.days_in_current_stage} days. Action needed.",
                'priority': self.ALERT_CONFIGS['stalled_high_priority']['priority']
            })
        
        # 4. Offer Deadline Approaching
        if candidate.current_stage == PipelineStage.OFFER_MADE.value:
            # Look for offer deadline in activities or calculate default
            offer_deadline = self._get_offer_deadline(candidate)
            if offer_deadline:
                days_until_deadline = (offer_deadline - datetime.utcnow()).days
                
                if (days_until_deadline <= self.ALERT_CONFIGS['offer_deadline_approaching']['days_before'] and
                    days_until_deadline >= 0 and
                    not self._alert_exists(candidate, 'offer_deadline_approaching')):
                    
                    alerts_to_create.append({
                        'alert_type': 'offer_deadline_approaching',
                        'title': f"Offer Deadline Approaching: {candidate.full_name}",
                        'message': f"Offer deadline in {days_until_deadline} days. Follow up required.",
                        'priority': self.ALERT_CONFIGS['offer_deadline_approaching']['priority']
                    })
        
        # 5. Follow-up Overdue
        if (candidate.next_followup_date and 
            candidate.next_followup_date < datetime.utcnow() and
            (datetime.utcnow() - candidate.next_followup_date).days >= self.ALERT_CONFIGS['follow_up_overdue']['days_overdue'] and
            not self._alert_exists(candidate, 'follow_up_overdue')):
            
            days_overdue = (datetime.utcnow() - candidate.next_followup_date).days
            alerts_to_create.append({
                'alert_type': 'follow_up_overdue',
                'title': f"Follow-up Overdue: {candidate.full_name}",
                'message': f"Follow-up is {days_overdue} days overdue. Contact candidate immediately.",
                'priority': self.ALERT_CONFIGS['follow_up_overdue']['priority']
            })
        
        # 6. Reference Check Needed
        if (candidate.current_stage == PipelineStage.FINAL_INTERVIEW.value and
            candidate.days_in_current_stage >= 3 and
            not self._alert_exists(candidate, 'reference_check_needed')):
            
            alerts_to_create.append({
                'alert_type': 'reference_check_needed',
                'title': f"Reference Check Required: {candidate.full_name}",
                'message': f"Candidate has completed final interview. Initiate reference check process.",
                'priority': self.ALERT_CONFIGS['reference_check_needed']['priority']
            })
        
        # 7. Interview No-Show (check recent activities)
        recent_no_show = self._check_interview_no_show(candidate)
        if recent_no_show and not self._alert_exists(candidate, 'interview_no_show', hours=24):
            alerts_to_create.append({
                'alert_type': 'interview_no_show',
                'title': f"Interview No-Show: {candidate.full_name}",
                'message': f"Candidate missed scheduled interview. Determine next steps.",
                'priority': self.ALERT_CONFIGS['interview_no_show']['priority']
            })
        
        # 8. Competitor Risk (check for competitor mentions in activities)
        competitor_risk = self._check_competitor_risk(candidate)
        if competitor_risk and not self._alert_exists(candidate, 'competitor_risk'):
            alerts_to_create.append({
                'alert_type': 'competitor_risk',
                'title': f"Competitor Risk: {candidate.full_name}",
                'message': f"Candidate may have competing offers. Accelerate process or improve offer.",
                'priority': self.ALERT_CONFIGS['competitor_risk']['priority']
            })
        
        return alerts_to_create
    
    def _create_alert(self, candidate: Candidate, alert_data: Dict) -> Optional[CandidateAlert]:
        """Create a new candidate alert."""
        try:
            # Calculate expiration time
            alert_config = self.ALERT_CONFIGS.get(alert_data['alert_type'], {})
            expires_hours = alert_config.get('expires_hours', 48)
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            # Create alert
            alert = CandidateAlert(
                candidate_id=candidate.id,
                alert_type=alert_data['alert_type'],
                priority=alert_data['priority'],
                title=alert_data['title'],
                message=alert_data['message'],
                expires_at=expires_at,
                auto_generated=True
            )
            
            from app import db
            db.session.add(alert)
            
            # Add activity to candidate
            candidate.add_activity(
                activity_type='alert_generated',
                description=f"Alert created: {alert_data['title']}",
                details={
                    'alert_type': alert_data['alert_type'],
                    'priority': alert_data['priority'],
                    'auto_generated': True
                },
                created_by='HighPriorityAlertService'
            )
            
            db.session.commit()
            
            # Send real-time notification
            self._send_alert_notification(candidate, alert)
            
            logger.info(f"Alert created for {candidate.full_name}: {alert_data['alert_type']}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert for {candidate.full_name}: {str(e)}")
            from app import db
            db.session.rollback()
            return None
    
    def _alert_exists(self, candidate: Candidate, alert_type: str, hours: int = None) -> bool:
        """Check if an alert of this type already exists for the candidate."""
        query = CandidateAlert.query.filter_by(
            candidate_id=candidate.id,
            alert_type=alert_type,
            is_dismissed=False
        )
        
        # Check for recent alerts if hours specified
        if hours:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(CandidateAlert.created_at >= since_time)
        
        return query.first() is not None
    
    def _get_offer_deadline(self, candidate: Candidate) -> Optional[datetime]:
        """Get offer deadline from candidate activities or calculate default."""
        # Look for offer deadline in activities
        offer_activities = candidate.activities.filter_by(activity_type='offer_made').order_by(
            CandidateActivity.created_at.desc()
        ).first()
        
        if offer_activities and offer_activities.details:
            deadline_str = offer_activities.details.get('deadline')
            if deadline_str:
                try:
                    return datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                except:
                    pass
        
        # Default: 7 days from when offer was made (when they entered OFFER_MADE stage)
        offer_stage_history = candidate.stage_history.filter_by(
            to_stage=PipelineStage.OFFER_MADE.value
        ).order_by(PipelineStageHistory.changed_at.desc()).first()
        
        if offer_stage_history:
            return offer_stage_history.changed_at + timedelta(days=7)
        
        return None
    
    def _check_interview_no_show(self, candidate: Candidate) -> bool:
        """Check if candidate recently missed an interview."""
        # Look for no-show activities in the last 24 hours
        since_time = datetime.utcnow() - timedelta(hours=24)
        
        no_show_activity = candidate.activities.filter(
            and_(
                CandidateActivity.activity_type == 'interview',
                CandidateActivity.created_at >= since_time
            )
        ).filter(
            CandidateActivity.description.ilike('%no show%') |
            CandidateActivity.description.ilike('%missed%') |
            CandidateActivity.description.ilike('%absent%')
        ).first()
        
        return no_show_activity is not None
    
    def _check_competitor_risk(self, candidate: Candidate) -> bool:
        """Check if candidate has mentioned competitors or other offers."""
        # Look for competitor mentions in recent activities
        since_time = datetime.utcnow() - timedelta(days=7)
        
        competitor_keywords = [
            'other offer', 'competing offer', 'another company', 'competitor',
            'other opportunity', 'considering other', 'multiple offers',
            'deadline', 'decision soon'
        ]
        
        recent_activities = candidate.activities.filter(
            CandidateActivity.created_at >= since_time
        ).all()
        
        for activity in recent_activities:
            description_lower = activity.description.lower()
            
            # Check description for competitor keywords
            if any(keyword in description_lower for keyword in competitor_keywords):
                return True
            
            # Check activity details
            if activity.details:
                details_str = json.dumps(activity.details).lower()
                if any(keyword in details_str for keyword in competitor_keywords):
                    return True
        
        return False
    
    def _send_alert_notification(self, candidate: Candidate, alert: CandidateAlert):
        """Send real-time notification for new alert."""
        if not self.websocket_service:
            return
        
        try:
            notification_data = {
                'alert_id': str(alert.id),
                'candidate_id': str(candidate.id),
                'candidate_name': candidate.full_name,
                'position': candidate.position_title,
                'alert_type': alert.alert_type,
                'priority': alert.priority,
                'title': alert.title,
                'message': alert.message,
                'created_at': alert.created_at.isoformat(),
                'expires_at': alert.expires_at.isoformat() if alert.expires_at else None
            }
            
            # Send to user
            self.websocket_service.send_to_user(
                str(candidate.user_id),
                'candidate_alert',
                notification_data
            )
            
            # Send to admins if high/urgent priority
            if alert.priority in [Priority.HIGH.value, Priority.URGENT.value]:
                self.websocket_service.send_to_admins('candidate_alert', notification_data)
            
            logger.info(f"Alert notification sent for {candidate.full_name}: {alert.alert_type}")
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {str(e)}")
    
    def get_active_alerts(self, user_id: str = None, priority: str = None) -> List[Dict]:
        """Get all active alerts."""
        try:
            query = CandidateAlert.query.filter_by(
                is_dismissed=False,
                is_read=False
            ).join(Candidate)
            
            if user_id:
                query = query.filter(Candidate.user_id == user_id)
            
            if priority:
                query = query.filter(CandidateAlert.priority == priority)
            
            # Filter out expired alerts
            query = query.filter(
                or_(
                    CandidateAlert.expires_at.is_(None),
                    CandidateAlert.expires_at > datetime.utcnow()
                )
            )
            
            alerts = query.order_by(
                CandidateAlert.priority.desc(),
                CandidateAlert.created_at.desc()
            ).all()
            
            return [alert.to_dict() for alert in alerts]
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return []
    
    def mark_alert_read(self, alert_id: str, user_id: str = None) -> Dict:
        """Mark an alert as read."""
        try:
            query = CandidateAlert.query.filter_by(id=alert_id)
            
            # If user_id provided, ensure alert belongs to user's candidate
            if user_id:
                query = query.join(Candidate).filter(Candidate.user_id == user_id)
            
            alert = query.first()
            if not alert:
                return {'error': 'Alert not found'}
            
            alert.is_read = True
            alert.read_at = datetime.utcnow()
            
            from app import db
            db.session.commit()
            
            return {'success': True, 'alert': alert.to_dict()}
            
        except Exception as e:
            logger.error(f"Error marking alert as read: {str(e)}")
            return {'error': str(e)}
    
    def dismiss_alert(self, alert_id: str, user_id: str = None) -> Dict:
        """Dismiss an alert."""
        try:
            query = CandidateAlert.query.filter_by(id=alert_id)
            
            if user_id:
                query = query.join(Candidate).filter(Candidate.user_id == user_id)
            
            alert = query.first()
            if not alert:
                return {'error': 'Alert not found'}
            
            alert.is_dismissed = True
            alert.dismissed_at = datetime.utcnow()
            
            from app import db
            db.session.commit()
            
            return {'success': True, 'alert': alert.to_dict()}
            
        except Exception as e:
            logger.error(f"Error dismissing alert: {str(e)}")
            return {'error': str(e)}
    
    def bulk_mark_read(self, alert_ids: List[str], user_id: str = None) -> Dict:
        """Mark multiple alerts as read."""
        try:
            query = CandidateAlert.query.filter(CandidateAlert.id.in_(alert_ids))
            
            if user_id:
                query = query.join(Candidate).filter(Candidate.user_id == user_id)
            
            alerts = query.all()
            
            for alert in alerts:
                alert.is_read = True
                alert.read_at = datetime.utcnow()
            
            from app import db
            db.session.commit()
            
            return {
                'success': True,
                'marked_read': len(alerts),
                'alerts': [alert.to_dict() for alert in alerts]
            }
            
        except Exception as e:
            logger.error(f"Error bulk marking alerts as read: {str(e)}")
            return {'error': str(e)}
    
    def _cleanup_expired_alerts(self):
        """Remove expired alerts."""
        try:
            expired_count = CandidateAlert.query.filter(
                and_(
                    CandidateAlert.expires_at < datetime.utcnow(),
                    CandidateAlert.auto_generated == True
                )
            ).delete()
            
            if expired_count > 0:
                from app import db
                db.session.commit()
                logger.info(f"Cleaned up {expired_count} expired alerts")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired alerts: {str(e)}")
    
    def create_manual_alert(self, candidate_id: str, alert_data: Dict, created_by: str = None) -> Dict:
        """Create a manual alert for a candidate."""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {'error': 'Candidate not found'}
            
            # Validate required fields
            required_fields = ['title', 'message', 'priority']
            for field in required_fields:
                if not alert_data.get(field):
                    return {'error': f"Missing required field: {field}"}
            
            # Create alert
            alert = CandidateAlert(
                candidate_id=candidate.id,
                alert_type=alert_data.get('alert_type', 'manual'),
                priority=alert_data['priority'],
                title=alert_data['title'],
                message=alert_data['message'],
                expires_at=datetime.fromisoformat(alert_data['expires_at']) if alert_data.get('expires_at') else None,
                auto_generated=False
            )
            
            from app import db
            db.session.add(alert)
            
            # Add activity
            candidate.add_activity(
                activity_type='manual_alert',
                description=f"Manual alert created: {alert_data['title']}",
                details={
                    'alert_type': alert_data.get('alert_type', 'manual'),
                    'priority': alert_data['priority'],
                    'auto_generated': False
                },
                created_by=created_by or 'System'
            )
            
            db.session.commit()
            
            # Send notification
            self._send_alert_notification(candidate, alert)
            
            return {
                'success': True,
                'alert': alert.to_dict(),
                'candidate': candidate.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error creating manual alert: {str(e)}")
            from app import db
            db.session.rollback()
            return {'error': str(e)}
    
    def get_alert_summary(self, user_id: str = None) -> Dict:
        """Get summary of alerts by type and priority."""
        try:
            query = CandidateAlert.query.filter_by(
                is_dismissed=False
            ).join(Candidate)
            
            if user_id:
                query = query.filter(Candidate.user_id == user_id)
            
            # Filter out expired alerts
            query = query.filter(
                or_(
                    CandidateAlert.expires_at.is_(None),
                    CandidateAlert.expires_at > datetime.utcnow()
                )
            )
            
            alerts = query.all()
            
            # Group by priority
            priority_summary = {}
            for priority in Priority:
                priority_alerts = [a for a in alerts if a.priority == priority.value]
                priority_summary[priority.value] = {
                    'total': len(priority_alerts),
                    'unread': len([a for a in priority_alerts if not a.is_read])
                }
            
            # Group by type
            type_summary = {}
            for alert in alerts:
                alert_type = alert.alert_type
                if alert_type not in type_summary:
                    type_summary[alert_type] = {'total': 0, 'unread': 0}
                
                type_summary[alert_type]['total'] += 1
                if not alert.is_read:
                    type_summary[alert_type]['unread'] += 1
            
            return {
                'total_alerts': len(alerts),
                'unread_alerts': len([a for a in alerts if not a.is_read]),
                'priority_breakdown': priority_summary,
                'type_breakdown': type_summary,
                'urgent_count': priority_summary.get(Priority.URGENT.value, {}).get('total', 0),
                'high_count': priority_summary.get(Priority.HIGH.value, {}).get('total', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting alert summary: {str(e)}")
            return {'error': str(e)}
