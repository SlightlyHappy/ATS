"""
Hot Lead Alert Service - Real-time notifications for high-scoring leads
using the existing WebSocket infrastructure.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app import db
from app.models.sales import Lead, LeadStatus
from app.models.admin import AdminUser
from app.services.websocket_service import WebSocketService

logger = logging.getLogger(__name__)

class HotLeadAlertService:
    """Service for managing hot lead alerts and notifications."""
    
    def __init__(self, websocket_service: Optional[WebSocketService] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.websocket_service = websocket_service
        
        # Alert thresholds
        self.HOT_LEAD_THRESHOLD = 80
        self.SUPER_HOT_THRESHOLD = 90
        self.ALERT_COOLDOWN_HOURS = 24  # Don't spam alerts for same lead
    
    def check_and_send_hot_lead_alerts(self) -> Dict[str, int]:
        """
        Check for new hot leads and send alerts to admin users.
        
        Returns:
            Dictionary with alert statistics
        """
        try:
            alerts_sent = 0
            super_hot_alerts = 0
            
            # Find leads that crossed into hot territory recently
            hot_leads = self._get_new_hot_leads()
            
            for lead in hot_leads:
                alert_sent = self._send_hot_lead_alert(lead)
                if alert_sent:
                    alerts_sent += 1
                    if lead.overall_score >= self.SUPER_HOT_THRESHOLD:
                        super_hot_alerts += 1
            
            self.logger.info(f"Hot lead alert check completed: {alerts_sent} alerts sent, "
                           f"{super_hot_alerts} super hot leads")
            
            return {
                'alerts_sent': alerts_sent,
                'super_hot_alerts': super_hot_alerts,
                'total_hot_leads': len(hot_leads)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking hot lead alerts: {str(e)}")
            return {'alerts_sent': 0, 'super_hot_alerts': 0, 'total_hot_leads': 0}
    
    def _get_new_hot_leads(self) -> List[Lead]:
        """Get leads that recently became hot and haven't been alerted on recently."""
        try:
            # Find leads with hot scores
            hot_leads = Lead.query.filter(
                Lead.overall_score >= self.HOT_LEAD_THRESHOLD,
                Lead.status.in_([LeadStatus.WARM.value, LeadStatus.HOT.value])
            ).all()
            
            # Filter out leads we've alerted on recently
            new_hot_leads = []
            cooldown_time = datetime.utcnow() - timedelta(hours=self.ALERT_COOLDOWN_HOURS)
            
            for lead in hot_leads:
                # Check if we've sent an alert recently
                recent_alert = lead.activities.filter(
                    lead.activities.c.activity_type == 'hot_lead_alert',
                    lead.activities.c.created_at >= cooldown_time
                ).first()
                
                if not recent_alert:
                    new_hot_leads.append(lead)
            
            return new_hot_leads
            
        except Exception as e:
            self.logger.error(f"Error getting new hot leads: {str(e)}")
            return []
    
    def _send_hot_lead_alert(self, lead: Lead) -> bool:
        """
        Send hot lead alert to admin users via WebSocket and email.
        
        Args:
            lead: The hot lead to alert about
            
        Returns:
            True if alert was sent successfully
        """
        try:
            # Determine alert level
            if lead.overall_score >= self.SUPER_HOT_THRESHOLD:
                alert_level = 'super_hot'
                alert_title = '🔥 SUPER HOT LEAD ALERT'
                priority = 'high'
            else:
                alert_level = 'hot'
                alert_title = '🌡️ Hot Lead Alert'
                priority = 'medium'
            
            # Create alert message
            alert_data = {
                'type': 'hot_lead_alert',
                'level': alert_level,
                'priority': priority,
                'title': alert_title,
                'message': f'Lead {lead.user.email} scored {lead.overall_score}/100',
                'lead_data': {
                    'id': str(lead.id),
                    'user_email': lead.user.email,
                    'user_name': f"{lead.user.first_name} {lead.user.last_name}",
                    'score': lead.overall_score,
                    'status': lead.status,
                    'company': lead.company_name,
                    'industry': lead.industry,
                    'last_activity': lead.last_activity.isoformat(),
                    'score_breakdown': {
                        'engagement': lead.engagement_score,
                        'usage': lead.usage_score,
                        'potential': lead.potential_score
                    }
                },
                'actions': [
                    {
                        'label': 'View Lead Details',
                        'url': f'/admin/leads/{lead.id}',
                        'type': 'primary'
                    },
                    {
                        'label': 'Qualify Lead',
                        'url': f'/admin/leads/{lead.id}/qualify',
                        'type': 'secondary'
                    }
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send WebSocket notification to all admin users
            if self.websocket_service:
                self.websocket_service.broadcast_to_admins('hot_lead_alert', alert_data)
            
            # Send browser push notification
            self._send_browser_notification(alert_data)
            
            # Log the alert activity
            lead.log_activity(
                'hot_lead_alert',
                f'Hot lead alert sent (score: {lead.overall_score})',
                {
                    'alert_level': alert_level,
                    'alert_sent_at': datetime.utcnow().isoformat()
                }
            )
            
            db.session.commit()
            
            self.logger.info(f"Hot lead alert sent for {lead.user.email} (score: {lead.overall_score})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending hot lead alert for lead {lead.id}: {str(e)}")
            return False
    
    def _send_browser_notification(self, alert_data: Dict):
        """Send browser push notification via WebSocket."""
        try:
            notification_data = {
                'title': alert_data['title'],
                'body': alert_data['message'],
                'icon': '/static/icon-192x192.png',
                'tag': 'hot-lead-alert',
                'data': {
                    'lead_id': alert_data['lead_data']['id'],
                    'url': alert_data['actions'][0]['url'] if alert_data['actions'] else None
                }
            }
            
            if self.websocket_service:
                self.websocket_service.broadcast_to_admins('push_notification', notification_data)
                
        except Exception as e:
            self.logger.error(f"Error sending browser notification: {str(e)}")
    
    def send_test_alert(self, admin_user_id: str) -> bool:
        """
        Send a test hot lead alert to verify the system is working.
        
        Args:
            admin_user_id: ID of admin user to send test to
            
        Returns:
            True if test alert was sent successfully
        """
        try:
            test_alert_data = {
                'type': 'hot_lead_alert',
                'level': 'test',
                'priority': 'low',
                'title': '🧪 Test Hot Lead Alert',
                'message': 'This is a test alert to verify the hot lead notification system',
                'lead_data': {
                    'id': 'test-lead-id',
                    'user_email': 'test@example.com',
                    'user_name': 'Test User',
                    'score': 95,
                    'status': 'hot',
                    'company': 'Test Company',
                    'industry': 'Testing',
                    'last_activity': datetime.utcnow().isoformat(),
                    'score_breakdown': {
                        'engagement': 35,
                        'usage': 30,
                        'potential': 30
                    }
                },
                'actions': [
                    {
                        'label': 'This is a test',
                        'url': '/admin/test',
                        'type': 'primary'
                    }
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if self.websocket_service:
                self.websocket_service.send_to_user(admin_user_id, 'hot_lead_alert', test_alert_data)
            
            self.logger.info(f"Test hot lead alert sent to admin {admin_user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending test alert: {str(e)}")
            return False
    
    def get_alert_history(self, days: int = 7) -> List[Dict]:
        """
        Get history of hot lead alerts sent in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of alert history records
        """
        try:
            from app.models.sales import LeadActivity
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            alert_activities = LeadActivity.query.filter(
                LeadActivity.activity_type == 'hot_lead_alert',
                LeadActivity.created_at >= cutoff_date
            ).order_by(LeadActivity.created_at.desc()).all()
            
            alert_history = []
            for activity in alert_activities:
                alert_history.append({
                    'lead_id': str(activity.lead_id),
                    'lead_email': activity.lead.user.email if activity.lead.user else 'Unknown',
                    'description': activity.description,
                    'alert_level': activity.metadata.get('alert_level', 'unknown'),
                    'sent_at': activity.created_at.isoformat(),
                    'lead_score': activity.lead.overall_score
                })
            
            return alert_history
            
        except Exception as e:
            self.logger.error(f"Error getting alert history: {str(e)}")
            return []
    
    def configure_alert_settings(self, settings: Dict) -> bool:
        """
        Configure hot lead alert settings.
        
        Args:
            settings: Dictionary with alert configuration
            
        Returns:
            True if settings were updated successfully
        """
        try:
            if 'hot_threshold' in settings:
                self.HOT_LEAD_THRESHOLD = max(50, min(100, settings['hot_threshold']))
            
            if 'super_hot_threshold' in settings:
                self.SUPER_HOT_THRESHOLD = max(self.HOT_LEAD_THRESHOLD, 
                                               min(100, settings['super_hot_threshold']))
            
            if 'cooldown_hours' in settings:
                self.ALERT_COOLDOWN_HOURS = max(1, min(168, settings['cooldown_hours']))  # 1 hour to 1 week
            
            self.logger.info(f"Alert settings updated: hot={self.HOT_LEAD_THRESHOLD}, "
                           f"super_hot={self.SUPER_HOT_THRESHOLD}, cooldown={self.ALERT_COOLDOWN_HOURS}h")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring alert settings: {str(e)}")
            return False
    
    def get_current_settings(self) -> Dict:
        """Get current alert settings."""
        return {
            'hot_threshold': self.HOT_LEAD_THRESHOLD,
            'super_hot_threshold': self.SUPER_HOT_THRESHOLD,
            'cooldown_hours': self.ALERT_COOLDOWN_HOURS
        }
