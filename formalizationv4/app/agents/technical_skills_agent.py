from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import json
import re
import time
import logging

logger = logging.getLogger(__name__)

class TechnicalSkillsAgent(BaseAgent):
    """Agent specialized in analyzing technical and professional skills across all industries in Indian context."""
    
    def __init__(self, model_service, config: Dict[str, Any] = None):
        super().__init__("TechnicalSkillsAgent", model_service, config)
        
        # Comprehensive skill categories for all industries
        self.skill_categories = {
            # Technology & IT
            "programming_languages": ["Python", "Java", "JavaScript", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Swift"],
            "frameworks": ["React", "Angular", "Vue", "Django", "Flask", "Spring", "Express", "Laravel"],
            "databases": ["MySQL", "PostgreSQL", "MongoDB", "Oracle", "SQL Server", "Redis", "Cassandra"],
            "cloud_platforms": ["AWS", "Azure", "GCP", "IBM Cloud", "Digital Ocean"],
            "devops_tools": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Ansible"],
            
            # Engineering & Manufacturing
            "engineering_software": ["AutoCAD", "SolidWorks", "CATIA", "ANSYS", "MATLAB", "PTC Creo", "Fusion 360"],
            "design_tools": ["Pro/ENGINEER", "Inventor", "NX", "Rhino", "SketchUp"],
            "simulation_tools": ["COMSOL", "Abaqus", "HyperMesh", "Adams", "Fluent"],
            
            # Healthcare & Medical
            "medical_software": ["Epic", "Cerner", "MEDITECH", "Allscripts", "Practice Fusion"],
            "healthcare_systems": ["HMIS", "EMR", "EHR", "PACS", "RIS", "LIS"],
            "medical_devices": ["MRI", "CT Scanner", "Ultrasound", "X-Ray", "ECG", "Ventilators"],
            
            # Finance & Banking
            "financial_software": ["SAP", "Oracle Financials", "QuickBooks", "Tally", "Bloomberg Terminal"],
            "trading_platforms": ["MetaTrader", "E-Trade", "Zerodha Kite", "Upstox", "Angel Broking"],
            "risk_management": ["SAS", "R", "SPSS", "Stata", "Moody's Analytics"],
            
            # Sales & Marketing
            "crm_tools": ["Salesforce", "HubSpot", "Zoho CRM", "Pipedrive", "Freshworks"],
            "marketing_tools": ["Google Analytics", "AdWords", "Facebook Ads", "Mailchimp", "Hootsuite"],
            "analytics_tools": ["Tableau", "Power BI", "Google Data Studio", "Qlik", "Looker"],
            
            # Indian Context Specific
            "indian_compliance": ["GST", "TDS", "PF", "ESI", "Labor Laws", "FEMA", "RBI Guidelines"],
            "indian_software": ["Tally ERP", "Busy", "Marg ERP", "SAP India", "Oracle India"],
            "regional_languages": ["Hindi", "Tamil", "Telugu", "Marathi", "Bengali", "Gujarati"],
            
            # Professional Certifications
            "certifications": [],
            "methodologies": ["Agile", "Scrum", "Kanban", "DevOps", "Six Sigma", "Lean", "ITIL"]
        }
    
    def get_prompt_template(self) -> str:
        return """
You are a comprehensive technical and professional skills analysis expert with deep knowledge of the Indian job market and industry requirements. Analyze the following resume for technical competencies across ALL industries.

RESUME TEXT:
{resume_text}

ANALYSIS REQUIREMENTS:
1. Identify programming languages and technical skills (if applicable)
2. List industry-specific software and tools
3. Identify domain-specific technologies and platforms
4. Note professional certifications and licenses
5. Assess methodologies and frameworks knowledge
6. Evaluate Indian market relevance and compliance knowledge
7. Identify regional language capabilities
8. Assess technical depth vs breadth across industries
9. Evaluate skill currency and market demand
10. Identify skill gaps for Indian market requirements

INDUSTRY CONTEXTS TO CONSIDER:
- Information Technology & Software
- Engineering (Mechanical, Civil, Electrical, Chemical)
- Healthcare & Medical Sciences
- Finance & Banking
- Manufacturing & Automotive
- Pharmaceuticals & Biotechnology
- Telecommunications
- Energy & Power
- Agriculture & Food Processing
- Education & Research
- Government & Public Sector
- Retail & E-commerce
- Media & Entertainment
- Construction & Real Estate

INDIAN MARKET SPECIFIC CONSIDERATIONS:
- GST, compliance, and regulatory knowledge
- Indian software solutions (Tally, SAP India, etc.)
- Regional language proficiency
- Government schemes and initiatives knowledge
- Local industry standards and practices

RESPONSE FORMAT (JSON):
{{
    "industry_classification": {{
        "primary_industry": "Information Technology",
        "secondary_industries": ["Finance", "Healthcare"],
        "industry_experience_years": 5,
        "industry_expertise_level": "Advanced"
    }},
    "technical_skills": {{
        "programming_languages": [
            {{"name": "Python", "proficiency": "Advanced", "years_experience": 5, "industry_context": "Data Science", "indian_demand": "High"}}
        ],
        "software_tools": [
            {{"name": "AutoCAD", "proficiency": "Intermediate", "context": "Mechanical Design", "certification": "Yes"}}
        ],
        "platforms_systems": [
            {{"name": "SAP", "modules": ["FI/CO", "MM"], "proficiency": "Advanced", "indian_implementation": "Yes"}}
        ],
        "databases": [
            {{"name": "Oracle", "proficiency": "Advanced", "context": "Enterprise applications"}}
        ],
        "cloud_platforms": [
            {{"name": "AWS", "services": ["EC2", "S3", "Lambda"], "certification_level": "Associate"}}
        ]
    }},
    "professional_skills": {{
        "methodologies": [
            {{"name": "Agile", "proficiency": "Advanced", "certification": "Scrum Master", "years_experience": 3}}
        ],
        "compliance_knowledge": [
            {{"domain": "GST", "proficiency": "Advanced", "practical_experience": "Yes"}},
            {{"domain": "ISO Standards", "specific_standards": ["ISO 9001", "ISO 27001"]}}
        ],
        "quality_frameworks": ["Six Sigma", "Lean Manufacturing", "CMMI"]
    }},
    "certifications": [
        {{
            "name": "Chartered Accountant",
            "issuing_body": "ICAI",
            "year": 2022,
            "status": "Active",
            "indian_recognition": "High",
            "industry_relevance": 95
        }}
    ],
    "indian_market_skills": {{
        "regulatory_knowledge": [
            {{"domain": "Banking", "regulations": ["RBI Guidelines", "SEBI Norms"], "proficiency": "Intermediate"}}
        ],
        "regional_languages": [
            {{"language": "Hindi", "proficiency": "Native"}}
        ],
        "local_software": [
            {{"name": "Tally ERP", "version": "9.0", "proficiency": "Expert", "years_experience": 4}}
        ],
        "government_schemes": [
            {{"scheme": "Digital India", "involvement": "Project Implementation", "duration": "2 years"}}
        ]
    }},
    "skill_assessment": {{
        "technical_depth_score": 85,
        "technical_breadth_score": 78,
        "indian_market_relevance": 92,
        "skill_currency": 88,
        "industry_alignment": 90,
        "certification_value": 87
    }},
    "market_analysis": {{
        "high_demand_skills": ["Cloud Computing", "Data Analytics", "Digital Marketing"],
        "emerging_skills": ["AI/ML", "Blockchain", "IoT"],
        "skill_gaps": ["Advanced Analytics", "Cloud Security"],
        "indian_market_advantage": ["Multilingual capability", "Cost optimization"],
        "global_competitiveness": 82
    }},
    "strengths": [
        "Strong technical foundation in multiple technologies",
        "Excellent Indian market knowledge and compliance understanding",
        "Proven track record with Indian enterprise software"
    ],
    "weaknesses": [
        "Limited exposure to latest cloud technologies",
        "No recent international certifications"
    ],
    "recommendations": [
        "Consider AWS/Azure certification for cloud skills",
        "Gain experience with modern DevOps tools",
        "Develop expertise in emerging technologies like AI/ML"
    ],
    "overall_technical_score": 84,
    "confidence_level": 0.89
}}

Provide detailed, evidence-based analysis considering the Indian job market context, industry-specific requirements, and both technical and professional skills relevant to the candidate's domain.
"""
    
    async def analyze(self, resume_text: str, context: Dict[str, Any] = None) -> AgentResult:
        start_time = time.time()
        
        try:
            # Build and execute prompt
            prompt = self._build_prompt(resume_text, context)
            raw_response = await self._call_model(prompt)
            
            # Parse response
            analysis = self._parse_technical_response(raw_response)
            
            # Calculate metrics
            score = analysis.get('overall_technical_score', 0)
            confidence = analysis.get('confidence_level', 0.5)
            strengths = analysis.get('strengths', [])
            weaknesses = analysis.get('weaknesses', [])
            recommendations = analysis.get('recommendations', [])
            
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_name=self.name,
                score=score,
                confidence=confidence,
                analysis=analysis,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                processing_time=processing_time,
                raw_output=raw_response
            )
            
        except Exception as e:
            logger.error(f"Technical skills analysis failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_name=self.name,
                score=0,
                confidence=0,
                analysis={"error": str(e)},
                strengths=[],
                weaknesses=["Analysis failed"],
                recommendations=["Retry analysis"],
                processing_time=processing_time,
                raw_output=f"Error: {str(e)}"
            )
    
    def _parse_technical_response(self, response: str) -> Dict[str, Any]:
        """Parse the technical skills analysis response."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback parsing if JSON extraction fails
        return self._fallback_parse_technical(response)
    
    def _fallback_parse_technical(self, response: str) -> Dict[str, Any]:
        """Fallback parsing method when JSON parsing fails."""
        # Basic text parsing for key information
        analysis = {
            "programming_languages": [],
            "frameworks": [],
            "databases": [],
            "cloud_platforms": [],
            "tools": [],
            "methodologies": [],
            "certifications": [],
            "technical_depth_score": 70,
            "technical_breadth_score": 70,
            "career_progression_score": 70,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "overall_technical_score": 70,
            "confidence_level": 0.6,
            "parsing_method": "fallback"
        }
        
        # Extract common programming languages
        languages = ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'TypeScript']
        for lang in languages:
            if lang.lower() in response.lower():
                analysis["programming_languages"].append({
                    "name": lang,
                    "proficiency": "Unknown",
                    "evidence": ["Mentioned in resume"]
                })
        
        return analysis
