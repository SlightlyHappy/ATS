"""
AI-Powered HR Communication Template Service.
Generates personalized, legally compliant HR communication templates.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app import db
from app.models.communication import (HRTemplate, TemplateGeneration, ComplianceRule, 
                                    TemplateCategory, TemplateType, ComplianceLevel, TemplateStatus)
from app.models.candidate import Candidate
from app.models.analysis import Analysis
from app.services.ollama_service import OllamaService
from app.config import Config

logger = logging.getLogger(__name__)

class HRTemplateService:
    """Service for AI-powered HR communication template generation and management."""
    
    def __init__(self):
        self.ollama_service = OllamaService()
        
        # Template prompts for different categories
        self.category_prompts = {
            TemplateCategory.SCREENING: {
                'system': "You are an expert HR professional creating screening communication templates for Indian job market.",
                'description': "professional screening communication to initiate candidate evaluation"
            },
            TemplateCategory.PHONE_INTERVIEW: {
                'system': "You are an expert HR professional creating phone interview scheduling templates for Indian corporate environment.",
                'description': "phone interview invitation with cultural sensitivity"
            },
            TemplateCategory.TECHNICAL_INTERVIEW: {
                'system': "You are an expert HR professional creating technical interview scheduling templates for Indian IT industry.",
                'description': "technical interview invitation with clear expectations"
            },
            TemplateCategory.ON_SITE_INTERVIEW: {
                'system': "You are an expert HR professional creating on-site interview templates for Indian corporate culture.",
                'description': "on-site interview invitation with location and timing details"
            },
            TemplateCategory.FINAL_INTERVIEW: {
                'system': "You are an expert HR professional creating final interview templates for senior positions in India.",
                'description': "final interview invitation emphasizing importance and preparation"
            },
            TemplateCategory.OFFER: {
                'system': "You are an expert HR professional creating job offer templates compliant with Indian employment law.",
                'description': "job offer letter with all legal requirements and cultural considerations"
            },
            TemplateCategory.OFFER_FOLLOWUP: {
                'system': "You are an expert HR professional creating offer follow-up templates for Indian market.",
                'description': "offer follow-up communication to maintain candidate engagement"
            },
            TemplateCategory.REJECTION: {
                'system': "You are an expert HR professional creating respectful rejection templates for Indian candidates.",
                'description': "professional rejection letter maintaining candidate relationship"
            },
            TemplateCategory.ONBOARDING: {
                'system': "You are an expert HR professional creating onboarding welcome templates for Indian employees.",
                'description': "comprehensive onboarding welcome message with cultural integration"
            },
            TemplateCategory.REFERENCE_REQUEST: {
                'system': "You are an expert HR professional creating reference request templates for Indian business context.",
                'description': "professional reference request maintaining confidentiality"
            },
            TemplateCategory.FEEDBACK_REQUEST: {
                'system': "You are an expert HR professional creating feedback request templates for continuous improvement.",
                'description': "feedback request emphasizing process improvement"
            },
            TemplateCategory.GENERAL_UPDATE: {
                'system': "You are an expert HR professional creating general update templates for candidate communication.",
                'description': "general status update maintaining transparency and engagement"
            }
        }
    
    async def generate_template(self, 
                              user_id: str,
                              category: TemplateCategory, 
                              template_type: TemplateType = TemplateType.EMAIL,
                              compliance_level: ComplianceLevel = ComplianceLevel.STANDARD,
                              personalization_data: Dict = None,
                              custom_requirements: str = None) -> HRTemplate:
        """
        Generate a new AI-powered HR communication template.
        
        Args:
            user_id: User creating the template
            category: Template category (screening, interview, etc.)
            template_type: Type of communication (email, sms, etc.)
            compliance_level: Required legal compliance level
            personalization_data: Additional data for personalization
            custom_requirements: Custom requirements for the template
            
        Returns:
            Generated HRTemplate instance
        """
        try:
            start_time = datetime.utcnow()
            
            # Get compliance rules for this category and level
            compliance_rules = await self._get_compliance_rules(category, compliance_level)
            
            # Build AI prompt
            prompt = await self._build_generation_prompt(
                category, template_type, compliance_level, 
                compliance_rules, personalization_data, custom_requirements
            )
            
            # Generate template using AI
            async with self.ollama_service as ollama:
                template_data = await self._generate_with_ai(ollama, prompt, category)
            
            # Create template record
            template = HRTemplate(
                user_id=user_id,
                name=template_data['name'],
                description=template_data['description'],
                category=category,
                template_type=template_type,
                subject_template=template_data.get('subject_template'),
                content_template=template_data['content_template'],
                variables=template_data.get('variables', []),
                compliance_level=compliance_level,
                legal_notes=template_data.get('legal_notes'),
                compliance_tags=template_data.get('compliance_tags', []),
                ai_model_used=Config.OLLAMA_MODEL,
                generation_prompt=prompt[:1000],  # Store truncated prompt
                ai_confidence_score=template_data.get('confidence_score', 0.85),
                status=TemplateStatus.DRAFT
            )
            
            db.session.add(template)
            db.session.commit()
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Generated template {template.id} in {generation_time:.2f} seconds")
            
            return template
            
        except Exception as e:
            logger.error(f"Template generation failed: {str(e)}")
            db.session.rollback()
            raise
    
    async def personalize_template(self, 
                                 template_id: str,
                                 user_id: str,
                                 candidate_id: str = None,
                                 personalization_data: Dict = None) -> TemplateGeneration:
        """
        Generate personalized content from a template.
        
        Args:
            template_id: Template to personalize
            user_id: User requesting personalization
            candidate_id: Optional candidate for personalization
            personalization_data: Additional personalization data
            
        Returns:
            TemplateGeneration instance with personalized content
        """
        try:
            start_time = datetime.utcnow()
            
            # Get template
            template = HRTemplate.query.filter_by(id=template_id, user_id=user_id).first()
            if not template:
                raise ValueError("Template not found")
            
            # Get candidate data if provided
            candidate_data = {}
            if candidate_id:
                candidate = Candidate.query.filter_by(id=candidate_id, user_id=user_id).first()
                if candidate:
                    candidate_data = await self._extract_candidate_data(candidate)
            
            # Merge personalization data
            all_data = {**candidate_data, **(personalization_data or {})}
            
            # Generate personalized content
            async with self.ollama_service as ollama:
                personalized_content = await self._personalize_with_ai(
                    ollama, template, all_data
                )
            
            # Create generation record
            generation = TemplateGeneration(
                template_id=template_id,
                user_id=user_id,
                candidate_id=candidate_id,
                subject=personalized_content.get('subject'),
                content=personalized_content['content'],
                personalization_data=all_data,
                ai_model_used=Config.OLLAMA_MODEL,
                generation_time=(datetime.utcnow() - start_time).total_seconds(),
                quality_score=personalized_content.get('quality_score', 0.9)
            )
            
            db.session.add(generation)
            
            # Update template usage
            template.increment_usage()
            
            db.session.commit()
            
            logger.info(f"Personalized template {template_id} for user {user_id}")
            return generation
            
        except Exception as e:
            logger.error(f"Template personalization failed: {str(e)}")
            db.session.rollback()
            raise
    
    async def get_templates(self, 
                          user_id: str,
                          category: TemplateCategory = None,
                          status: TemplateStatus = None,
                          include_system: bool = True) -> List[HRTemplate]:
        """Get templates for a user with optional filtering."""
        query = HRTemplate.query.filter(
            db.or_(
                HRTemplate.user_id == user_id,
                HRTemplate.is_system_template == True if include_system else False
            )
        )
        
        if category:
            query = query.filter(HRTemplate.category == category)
        
        if status:
            query = query.filter(HRTemplate.status == status)
        
        return query.order_by(HRTemplate.created_at.desc()).all()
    
    async def validate_compliance(self, 
                                template: HRTemplate) -> Tuple[bool, List[str]]:
        """
        Validate template compliance with legal requirements.
        
        Returns:
            Tuple of (is_compliant, issues_list)
        """
        try:
            # Get applicable compliance rules
            rules = await self._get_compliance_rules(
                template.category, 
                template.compliance_level
            )
            
            issues = []
            
            # Check required clauses
            for rule in rules:
                required_clauses = rule.required_clauses or []
                for clause in required_clauses:
                    if clause.lower() not in template.content_template.lower():
                        issues.append(f"Missing required clause: {clause}")
                
                # Check prohibited content
                prohibited_content = rule.prohibited_content or []
                for prohibited in prohibited_content:
                    if prohibited.lower() in template.content_template.lower():
                        issues.append(f"Contains prohibited content: {prohibited}")
            
            is_compliant = len(issues) == 0
            return is_compliant, issues
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    async def _get_compliance_rules(self, 
                                  category: TemplateCategory,
                                  compliance_level: ComplianceLevel) -> List[ComplianceRule]:
        """Get applicable compliance rules for category and level."""
        return ComplianceRule.query.filter(
            ComplianceRule.is_active == True,
            ComplianceRule.applicable_categories.op('?')(category.value),
            ComplianceRule.compliance_level == compliance_level
        ).all()
    
    async def _build_generation_prompt(self, 
                                     category: TemplateCategory,
                                     template_type: TemplateType,
                                     compliance_level: ComplianceLevel,
                                     compliance_rules: List[ComplianceRule],
                                     personalization_data: Dict,
                                     custom_requirements: str) -> str:
        """Build AI prompt for template generation."""
        
        category_info = self.category_prompts.get(category, {})
        system_prompt = category_info.get('system', "You are an expert HR professional.")
        description = category_info.get('description', "professional HR communication")
        
        # Build compliance requirements
        compliance_text = ""
        if compliance_rules:
            compliance_text = "\n\nCOMPLIANCE REQUIREMENTS:\n"
            for rule in compliance_rules:
                compliance_text += f"- {rule.name}: {rule.rule_text}\n"
                if rule.required_clauses:
                    compliance_text += f"  Required clauses: {', '.join(rule.required_clauses)}\n"
                if rule.prohibited_content:
                    compliance_text += f"  Avoid: {', '.join(rule.prohibited_content)}\n"
        
        # Build personalization context
        personalization_text = ""
        if personalization_data:
            personalization_text = f"\n\nPERSONALIZATION CONTEXT:\n{json.dumps(personalization_data, indent=2)}"
        
        # Custom requirements
        custom_text = ""
        if custom_requirements:
            custom_text = f"\n\nCUSTOM REQUIREMENTS:\n{custom_requirements}"
        
        prompt = f"""
{system_prompt}

Create a {description} template for {category.value} communication via {template_type.value}.

REQUIREMENTS:
- Professional, respectful tone appropriate for Indian corporate culture
- Include placeholder variables for personalization (use {{variable_name}} format)
- Ensure cultural sensitivity for diverse Indian workforce
- Include proper greetings and closings
- Compliance level: {compliance_level.value}

{compliance_text}
{personalization_text}
{custom_text}

Generate a JSON response with the following structure:
{{
    "name": "Template name",
    "description": "Brief description",
    "subject_template": "Email subject (if applicable)",
    "content_template": "Main template content with {{variables}}",
    "variables": ["list", "of", "available", "variables"],
    "legal_notes": "Legal compliance notes",
    "compliance_tags": ["relevant", "compliance", "tags"],
    "confidence_score": 0.95
}}

Ensure the template is professional, legally compliant, and culturally appropriate for Indian business environment.
"""
        
        return prompt.strip()
    
    async def _generate_with_ai(self, 
                              ollama: OllamaService,
                              prompt: str,
                              category: TemplateCategory) -> Dict[str, Any]:
        """Generate template using AI with robust parsing."""
        try:
            response = await ollama.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse JSON response
            try:
                template_data = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    template_data = json.loads(json_match.group())
                else:
                    # Fallback: create structured response
                    template_data = {
                        "name": f"{category.value.title()} Template",
                        "description": f"AI-generated {category.value} communication template",
                        "subject_template": "{{subject}}" if category != TemplateCategory.SMS else None,
                        "content_template": response,
                        "variables": ["candidate_name", "position_title", "company_name"],
                        "legal_notes": "Please review for compliance",
                        "compliance_tags": ["standard"],
                        "confidence_score": 0.8
                    }
            
            # Validate required fields
            required_fields = ['name', 'content_template']
            for field in required_fields:
                if field not in template_data:
                    template_data[field] = f"Generated {field}"
            
            return template_data
            
        except Exception as e:
            logger.error(f"AI template generation failed: {str(e)}")
            raise
    
    async def _personalize_with_ai(self, 
                                 ollama: OllamaService,
                                 template: HRTemplate,
                                 personalization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize template content using AI."""
        try:
            prompt = f"""
You are an expert HR professional personalizing communication templates.

TEMPLATE TO PERSONALIZE:
Subject: {template.subject_template or 'N/A'}
Content: {template.content_template}

PERSONALIZATION DATA:
{json.dumps(personalization_data, indent=2)}

INSTRUCTIONS:
1. Replace all {{variable}} placeholders with appropriate values from personalization data
2. If data is missing for a variable, use a professional default
3. Maintain the professional tone and structure
4. Ensure cultural appropriateness for Indian business context
5. Add personal touches where appropriate

Generate a JSON response:
{{
    "subject": "Personalized subject line",
    "content": "Fully personalized content",
    "quality_score": 0.95
}}
"""
            
            response = await ollama.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=1500
            )
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # Fallback parsing
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Manual personalization fallback
                    personalized_content = template.content_template
                    personalized_subject = template.subject_template
                    
                    for key, value in personalization_data.items():
                        placeholder = f"{{{key}}}"
                        if personalized_content:
                            personalized_content = personalized_content.replace(placeholder, str(value))
                        if personalized_subject:
                            personalized_subject = personalized_subject.replace(placeholder, str(value))
                    
                    result = {
                        "subject": personalized_subject,
                        "content": personalized_content,
                        "quality_score": 0.8
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Template personalization failed: {str(e)}")
            raise
    
    async def _extract_candidate_data(self, candidate: Candidate) -> Dict[str, Any]:
        """Extract personalization data from candidate record."""
        data = {
            "candidate_name": f"{candidate.first_name} {candidate.last_name}".strip(),
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "position_title": candidate.position_title,
            "department": candidate.department,
            "hiring_manager": candidate.hiring_manager,
            "recruiter": candidate.recruiter,
            "pipeline_stage": candidate.pipeline_stage.value if candidate.pipeline_stage else "applied",
            "priority": candidate.priority.value if candidate.priority else "medium",
            "applied_date": candidate.applied_date.strftime("%Y-%m-%d") if candidate.applied_date else None
        }
        
        # Add analysis data if available
        if candidate.resume_id:
            analysis = Analysis.query.filter_by(
                resume_id=candidate.resume_id,
                status='completed'
            ).order_by(Analysis.created_at.desc()).first()
            
            if analysis:
                data.update({
                    "overall_score": analysis.overall_score,
                    "analysis_strengths": analysis.strengths[:3] if analysis.strengths else [],
                    "technical_skills": self._extract_technical_skills(analysis),
                    "experience_years": self._extract_experience_years(analysis)
                })
        
        return data
    
    def _extract_technical_skills(self, analysis: Analysis) -> List[str]:
        """Extract key technical skills from analysis."""
        if not analysis.technical_skills_result:
            return []
        
        skills = []
        tech_result = analysis.technical_skills_result
        
        # Extract programming languages
        if 'technical_skills' in tech_result and 'programming_languages' in tech_result['technical_skills']:
            prog_langs = tech_result['technical_skills']['programming_languages']
            skills.extend([lang.get('name', '') for lang in prog_langs[:3]])
        
        return skills
    
    def _extract_experience_years(self, analysis: Analysis) -> str:
        """Extract experience years from analysis."""
        if not analysis.experience_result:
            return "experienced"
        
        exp_result = analysis.experience_result
        if 'career_overview' in exp_result and 'total_experience' in exp_result['career_overview']:
            return exp_result['career_overview']['total_experience']
        
        return "experienced"


class TemplateLibraryService:
    """Service for managing system template library and best practices."""
    
    def __init__(self):
        self.system_templates = [
            # Screening templates
            {
                'category': TemplateCategory.SCREENING,
                'name': 'Initial Screening Email',
                'description': 'Professional initial screening communication',
                'subject_template': 'Application Received - {{position_title}} at {{company_name}}',
                'content_template': '''Dear {{candidate_name}},

Thank you for your interest in the {{position_title}} position at {{company_name}}. We have received your application and are pleased to inform you that your profile meets our initial requirements.

Our hiring team will review your application within the next 2-3 business days. We will contact you shortly to discuss the next steps in our selection process.

We appreciate your patience and look forward to the possibility of working together.

Best regards,
{{recruiter}}
{{company_name}} HR Team

Note: This is an automated message. Please do not reply to this email. For any queries, contact us at hr@{{company_domain}}.''',
                'variables': ['candidate_name', 'position_title', 'company_name', 'recruiter', 'company_domain'],
                'compliance_level': ComplianceLevel.STANDARD
            },
            # Phone interview template
            {
                'category': TemplateCategory.PHONE_INTERVIEW,
                'name': 'Phone Interview Invitation',
                'description': 'Professional phone interview scheduling email',
                'subject_template': 'Phone Interview Invitation - {{position_title}} Position',
                'content_template': '''Dear {{candidate_name}},

We are pleased to invite you for a phone interview for the {{position_title}} position at {{company_name}}.

Interview Details:
- Date: {{interview_date}}
- Time: {{interview_time}} (IST)
- Duration: Approximately 30-45 minutes
- Interviewer: {{interviewer_name}}, {{interviewer_title}}

We will call you at {{phone_number}}. Please ensure you are in a quiet location with good network connectivity.

Discussion Topics:
- Your background and experience
- Role requirements and expectations  
- Company culture and growth opportunities
- Your questions about the role

Please confirm your availability by replying to this email.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
                'variables': ['candidate_name', 'position_title', 'company_name', 'interview_date', 'interview_time', 'interviewer_name', 'interviewer_title', 'phone_number', 'recruiter'],
                'compliance_level': ComplianceLevel.STANDARD
            },
            # Offer template
            {
                'category': TemplateCategory.OFFER,
                'name': 'Job Offer Letter',
                'description': 'Comprehensive job offer letter template',
                'subject_template': 'Job Offer - {{position_title}} at {{company_name}}',
                'content_template': '''Dear {{candidate_name}},

We are delighted to extend an offer for the position of {{position_title}} at {{company_name}}.

OFFER DETAILS:
Position: {{position_title}}
Department: {{department}}
Reporting Manager: {{hiring_manager}}
Start Date: {{start_date}}
Location: {{work_location}}

COMPENSATION:
Annual CTC: ₹{{annual_ctc}} 
Monthly Gross: ₹{{monthly_gross}}
{{compensation_details}}

BENEFITS:
{{benefits_list}}

This offer is contingent upon:
- Satisfactory completion of background verification
- Submission of required documents
- Medical clearance (if applicable)

Please confirm your acceptance by {{offer_deadline}}. This offer will be valid until {{offer_expiry_date}}.

We are excited about the possibility of you joining our team and contributing to our continued success.

Welcome to {{company_name}}!

Best regards,
{{hiring_manager}}
{{title}}
{{company_name}}

Legal Note: This offer is subject to the terms and conditions outlined in the detailed offer letter to be provided upon acceptance.''',
                'variables': ['candidate_name', 'position_title', 'company_name', 'department', 'hiring_manager', 'start_date', 'work_location', 'annual_ctc', 'monthly_gross', 'compensation_details', 'benefits_list', 'offer_deadline', 'offer_expiry_date', 'title'],
                'compliance_level': ComplianceLevel.STRICT
            },
            # Rejection template
            {
                'category': TemplateCategory.REJECTION,
                'name': 'Professional Rejection Email',
                'description': 'Respectful candidate rejection communication',
                'subject_template': 'Update on Your Application - {{position_title}} Position',
                'content_template': '''Dear {{candidate_name}},

Thank you for your interest in the {{position_title}} position at {{company_name}} and for taking the time to participate in our selection process.

After careful consideration, we have decided to proceed with other candidates whose qualifications more closely match our current requirements for this role.

This decision was not easy, as we were impressed with {{positive_feedback}}. We encourage you to apply for future opportunities that align with your skills and career goals.

We will keep your profile on file for 12 months and may reach out if suitable positions become available.

Thank you again for your time and interest in {{company_name}}. We wish you all the best in your career endeavors.

Best regards,
{{recruiter}}
{{company_name}} HR Team''',
                'variables': ['candidate_name', 'position_title', 'company_name', 'positive_feedback', 'recruiter'],
                'compliance_level': ComplianceLevel.STANDARD
            }
        ]
    
    async def initialize_system_templates(self) -> List[HRTemplate]:
        """Initialize system templates in database."""
        created_templates = []
        
        for template_data in self.system_templates:
            # Check if template already exists
            existing = HRTemplate.query.filter_by(
                name=template_data['name'],
                is_system_template=True
            ).first()
            
            if not existing:
                template = HRTemplate(
                    user_id=None,  # System template
                    name=template_data['name'],
                    description=template_data['description'],
                    category=template_data['category'],
                    template_type=TemplateType.EMAIL,
                    subject_template=template_data['subject_template'],
                    content_template=template_data['content_template'],
                    variables=template_data['variables'],
                    compliance_level=template_data['compliance_level'],
                    status=TemplateStatus.ACTIVE,
                    is_system_template=True,
                    ai_model_used='system_generated',
                    ai_confidence_score=1.0
                )
                
                db.session.add(template)
                created_templates.append(template)
        
        db.session.commit()
        logger.info(f"Initialized {len(created_templates)} system templates")
        return created_templates
