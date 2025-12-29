"""
Advanced Email Template System
Generates personalized HR emails for various candidate interactions
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EmailType(Enum):
    INTERVIEW_INVITATION = "interview_invitation"
    INTERVIEW_SCHEDULING = "interview_scheduling"
    REJECTION = "rejection"
    OFFER = "offer"
    FOLLOW_UP = "follow_up"
    CUSTOM = "custom"

@dataclass
class EmailTemplate:
    """Email template configuration"""
    name: str
    description: str
    subject_template: str
    body_template: str
    placeholders: List[str]
    template_type: EmailType

@dataclass
class GeneratedEmail:
    """Generated email data"""
    template_type: EmailType
    subject: str
    body: str
    recipient_name: str
    recipient_email: str
    placeholders_used: Dict[str, str]
    generated_at: datetime
    email_id: str

class EmailTemplateManager:
    """Manages email templates and generation"""
    
    def __init__(self):
        """Initialize email template manager"""
        self.templates = self._initialize_templates()
        self.generated_emails = []
        
        logger.info("Email template manager initialized")
    
    def _initialize_templates(self) -> Dict[EmailType, EmailTemplate]:
        """Initialize default email templates"""
        templates = {}
        
        # Interview Invitation Template
        templates[EmailType.INTERVIEW_INVITATION] = EmailTemplate(
            name="Interview Invitation",
            description="Invite candidate for an interview",
            subject_template="Interview Invitation - {position_title} at {company_name}",
            body_template="""Dear {candidate_name},

We hope this email finds you well. We were impressed with your application for the {position_title} position at {company_name}.

After reviewing your resume and qualifications, we would like to invite you for an interview to discuss this opportunity further.

Interview Details:
- Position: {position_title}
- Date: {interview_date}
- Time: {interview_time}
- Duration: Approximately {interview_duration}
- Format: {interview_format}
- Interviewer: {interviewer_name}

{interview_location_or_link}

Please confirm your availability by replying to this email or calling us at {contact_phone}. If the proposed time doesn't work for you, please let us know your preferred time slots, and we'll do our best to accommodate.

We look forward to meeting you and learning more about your experience and qualifications.

Best regards,
{interviewer_name}
{interviewer_title}
{company_name}
{contact_email}
{contact_phone}""",
            placeholders=[
                "candidate_name", "position_title", "company_name", "interview_date", 
                "interview_time", "interview_duration", "interview_format", 
                "interviewer_name", "interviewer_title", "interview_location_or_link",
                "contact_email", "contact_phone"
            ],
            template_type=EmailType.INTERVIEW_INVITATION
        )
        
        # Interview Scheduling Template
        templates[EmailType.INTERVIEW_SCHEDULING] = EmailTemplate(
            name="Interview Scheduling (Calendly)",
            description="Send scheduling link for candidate to book interview",
            subject_template="Schedule Your Interview - {position_title} at {company_name}",
            body_template="""Dear {candidate_name},

Thank you for your interest in the {position_title} position at {company_name}.

We would like to schedule an interview with you to discuss this exciting opportunity. To make the scheduling process convenient for you, we've set up a booking system where you can choose a time that works best with your schedule.

Please use the following link to book your interview:
{scheduling_link}

Interview Information:
- Position: {position_title}
- Duration: {interview_duration}
- Format: {interview_format}
- Interviewer: {interviewer_name}, {interviewer_title}

If you have any questions or face any issues with the scheduling system, please don't hesitate to reach out to us at {contact_email} or {contact_phone}.

We look forward to speaking with you soon!

Best regards,
{interviewer_name}
{interviewer_title}
{company_name}
{contact_email}
{contact_phone}""",
            placeholders=[
                "candidate_name", "position_title", "company_name", "scheduling_link",
                "interview_duration", "interview_format", "interviewer_name", 
                "interviewer_title", "contact_email", "contact_phone"
            ],
            template_type=EmailType.INTERVIEW_SCHEDULING
        )
        
        # Rejection Template
        templates[EmailType.REJECTION] = EmailTemplate(
            name="Application Rejection",
            description="Politely decline the application",
            subject_template="Update on Your Application - {position_title} at {company_name}",
            body_template="""Dear {candidate_name},

Thank you for your interest in the {position_title} position at {company_name} and for taking the time to apply and interview with us.

After careful consideration and review of all candidates, we have decided to move forward with another candidate whose background more closely matches our current needs for this particular role.

This was a difficult decision as we were impressed by {positive_feedback}. We encourage you to apply for future opportunities that may be a better fit for your skills and experience.

We will keep your resume on file and will reach out if a suitable position becomes available in the next {retention_period}.

Thank you again for your time and interest in {company_name}. We wish you the best of luck in your job search and future career endeavors.

Best regards,
{hiring_manager_name}
{hiring_manager_title}
{company_name}""",
            placeholders=[
                "candidate_name", "position_title", "company_name", "positive_feedback",
                "retention_period", "hiring_manager_name", "hiring_manager_title"
            ],
            template_type=EmailType.REJECTION
        )
        
        # Job Offer Template
        templates[EmailType.OFFER] = EmailTemplate(
            name="Job Offer",
            description="Extend a job offer to the candidate",
            subject_template="Job Offer - {position_title} at {company_name}",
            body_template="""Dear {candidate_name},

Congratulations! We are pleased to extend an offer for the position of {position_title} at {company_name}.

We were impressed with your qualifications, experience, and the enthusiasm you demonstrated throughout the interview process. We believe you will be a valuable addition to our team.

Offer Details:
- Position: {position_title}
- Department: {department}
- Reporting to: {supervisor_name}
- Start Date: {start_date}
- Annual Salary: {salary}
- Benefits: {benefits_summary}
- Work Arrangement: {work_arrangement}

{additional_offer_details}

This offer is contingent upon:
{contingencies}

Please confirm your acceptance of this offer by {response_deadline}. If you have any questions or would like to discuss any aspect of this offer, please don't hesitate to contact me.

We are excited about the possibility of you joining our team and look forward to your response.

Congratulations again!

Best regards,
{hiring_manager_name}
{hiring_manager_title}
{company_name}
{contact_email}
{contact_phone}""",
            placeholders=[
                "candidate_name", "position_title", "company_name", "department",
                "supervisor_name", "start_date", "salary", "benefits_summary",
                "work_arrangement", "additional_offer_details", "contingencies",
                "response_deadline", "hiring_manager_name", "hiring_manager_title",
                "contact_email", "contact_phone"
            ],
            template_type=EmailType.OFFER
        )
        
        # Follow-up Template
        templates[EmailType.FOLLOW_UP] = EmailTemplate(
            name="Follow-up Email",
            description="Follow up on application status",
            subject_template="Following Up - {position_title} Application",
            body_template="""Dear {candidate_name},

I hope this email finds you well. I wanted to follow up on your application for the {position_title} position at {company_name}.

{follow_up_context}

Current Status: {current_status}

Next Steps: {next_steps}

Timeline: {expected_timeline}

If you have any questions or need any additional information from us, please don't hesitate to reach out.

Thank you for your patience and continued interest in this opportunity.

Best regards,
{contact_person_name}
{contact_person_title}
{company_name}
{contact_email}
{contact_phone}""",
            placeholders=[
                "candidate_name", "position_title", "company_name", "follow_up_context",
                "current_status", "next_steps", "expected_timeline", "contact_person_name",
                "contact_person_title", "contact_email", "contact_phone"
            ],
            template_type=EmailType.FOLLOW_UP
        )
        
        return templates
    
    def generate_email(self, template_type: EmailType, candidate_data: Dict[str, Any], 
                      company_data: Dict[str, Any], custom_data: Dict[str, Any] = None) -> GeneratedEmail:
        """Generate a personalized email from template"""
        try:
            template = self.templates.get(template_type)
            if not template:
                raise ValueError(f"Template not found for type: {template_type}")
            
            # Combine all data sources
            placeholders = {}
            placeholders.update(candidate_data)
            placeholders.update(company_data)
            if custom_data:
                placeholders.update(custom_data)
            
            # Add default values for common placeholders
            placeholders.setdefault('interview_duration', '1 hour')
            placeholders.setdefault('interview_format', 'Virtual (Microsoft Teams)')
            placeholders.setdefault('retention_period', '6 months')
            placeholders.setdefault('response_deadline', (datetime.now() + timedelta(days=3)).strftime('%B %d, %Y'))
            placeholders.setdefault('expected_timeline', '1-2 weeks')
            
            # Generate subject and body
            subject = self._apply_template(template.subject_template, placeholders)
            body = self._apply_template(template.body_template, placeholders)
            
            # Create email ID
            email_id = f"{template_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(candidate_data.get('email', ''))}"
            
            # Create generated email object
            generated_email = GeneratedEmail(
                template_type=template_type,
                subject=subject,
                body=body,
                recipient_name=candidate_data.get('name', 'Candidate'),
                recipient_email=candidate_data.get('email', ''),
                placeholders_used=placeholders,
                generated_at=datetime.now(),
                email_id=email_id
            )
            
            # Store generated email
            self.generated_emails.append(generated_email)
            
            logger.info(f"Generated {template_type.value} email for {generated_email.recipient_name}")
            
            return generated_email
            
        except Exception as e:
            logger.error(f"Error generating email: {str(e)}")
            raise
    
    def _apply_template(self, template: str, placeholders: Dict[str, Any]) -> str:
        """Apply placeholders to template string"""
        try:
            # Handle missing placeholders gracefully
            result = template
            for key, value in placeholders.items():
                placeholder = f"{{{key}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
            
            # Check for any remaining placeholders and provide defaults
            import re
            remaining_placeholders = re.findall(r'\{([^}]+)\}', result)
            for placeholder in remaining_placeholders:
                default_value = self._get_default_placeholder_value(placeholder)
                result = result.replace(f"{{{placeholder}}}", default_value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return template
    
    def _get_default_placeholder_value(self, placeholder: str) -> str:
        """Get default value for missing placeholders"""
        defaults = {
            # Contact information
            'company_name': '[Company Name]',
            'contact_email': '[Contact Email]',
            'contact_phone': '[Contact Phone]',
            
            # Interview details
            'interviewer_name': '[Interviewer Name]',
            'interviewer_title': '[Interviewer Title]',
            'interview_date': '[Interview Date]',
            'interview_time': '[Interview Time]',
            'interview_location_or_link': '[Interview Details]',
            
            # Position details
            'position_title': '[Position Title]',
            'department': '[Department]',
            'supervisor_name': '[Supervisor]',
            
            # Offer details
            'salary': '[Salary Details]',
            'benefits_summary': '[Benefits Package]',
            'work_arrangement': '[Work Arrangement]',
            'start_date': '[Start Date]',
            
            # Scheduling
            'scheduling_link': '[Scheduling Link]',
            
            # Generic
            'candidate_name': '[Candidate Name]',
            'positive_feedback': 'your qualifications and experience',
            'follow_up_context': 'We wanted to provide you with an update on your application.',
            'current_status': 'Under review',
            'next_steps': 'We will be in touch soon with next steps.',
            'additional_offer_details': '',
            'contingencies': 'Standard background check and reference verification.'
        }
        
        return defaults.get(placeholder, f'[{placeholder.replace("_", " ").title()}]')
    
    def get_templates(self) -> Dict[str, Dict]:
        """Get all available templates"""
        result = {}
        for template_type, template in self.templates.items():
            result[template_type.value] = {
                'name': template.name,
                'description': template.description,
                'placeholders': template.placeholders,
                'subject_template': template.subject_template,
                'body_template': template.body_template
            }
        return result
    
    def get_generated_emails(self, limit: int = 50) -> List[Dict]:
        """Get recently generated emails"""
        recent_emails = sorted(self.generated_emails, key=lambda x: x.generated_at, reverse=True)[:limit]
        
        result = []
        for email in recent_emails:
            result.append({
                'email_id': email.email_id,
                'template_type': email.template_type.value,
                'subject': email.subject,
                'recipient_name': email.recipient_name,
                'recipient_email': email.recipient_email,
                'generated_at': email.generated_at.isoformat(),
                'preview': email.body[:200] + '...' if len(email.body) > 200 else email.body
            })
        
        return result
    
    def get_email_by_id(self, email_id: str) -> Optional[GeneratedEmail]:
        """Get generated email by ID"""
        for email in self.generated_emails:
            if email.email_id == email_id:
                return email
        return None
    
    def create_custom_template(self, name: str, description: str, subject_template: str, 
                             body_template: str, placeholders: List[str]) -> bool:
        """Create a custom email template"""
        try:
            custom_template = EmailTemplate(
                name=name,
                description=description,
                subject_template=subject_template,
                body_template=body_template,
                placeholders=placeholders,
                template_type=EmailType.CUSTOM
            )
            
            # Store custom template (in production, this would be saved to database)
            self.templates[EmailType.CUSTOM] = custom_template
            
            logger.info(f"Created custom template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating custom template: {str(e)}")
            return False

# Global email template manager instance
email_template_manager = EmailTemplateManager()
