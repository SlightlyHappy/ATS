from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import json
import re
import time
import logging

logger = logging.getLogger(__name__)

class SoftSkillsAgent(BaseAgent):
    """Agent specialized in analyzing soft skills, interpersonal abilities, and cultural fit across all industries in Indian context."""
    
    def __init__(self, model_service, config: Dict[str, Any] = None):
        super().__init__("SoftSkillsAgent", model_service, config)
        
        # Indian workplace soft skills framework
        self.indian_soft_skills_context = {
            "cultural_competencies": [
                "respect_for_hierarchy", "team_harmony", "relationship_building",
                "cultural_sensitivity", "multi_generational_collaboration"
            ],
            "communication_styles": [
                "diplomatic_communication", "indirect_feedback", "consensus_building",
                "multilingual_adaptation", "cross_cultural_communication"
            ],
            "leadership_styles": [
                "inclusive_leadership", "mentoring_culture", "collaborative_decision_making",
                "servant_leadership", "transformational_leadership"
            ],
            "work_values": [
                "family_work_balance", "loyalty_commitment", "respect_for_elders",
                "community_orientation", "continuous_learning"
            ]
        }
    
    def get_prompt_template(self) -> str:
        return """
You are a comprehensive soft skills and behavioral competency analysis expert with deep understanding of Indian workplace culture, interpersonal dynamics, and industry-specific soft skill requirements. Analyze the following resume for soft skills, cultural fit, and behavioral indicators across ALL industries.

RESUME TEXT:
{resume_text}

ANALYSIS REQUIREMENTS:
1. Evaluate communication skills in Indian multicultural context
2. Assess leadership abilities and styles suitable for Indian workplace
3. Analyze teamwork and collaboration in hierarchical structures
4. Review problem-solving and critical thinking capabilities
5. Evaluate emotional intelligence and cultural sensitivity
6. Assess adaptability and change management skills
7. Review conflict resolution and negotiation abilities
8. Analyze innovation, creativity, and entrepreneurial mindset
9. Evaluate work ethics, integrity, and professional values
10. Assess customer service orientation and stakeholder management

INDIAN WORKPLACE CONTEXT CONSIDERATIONS:
- Hierarchical organizational structures and respect for authority
- Multi-generational workforce dynamics
- Regional and linguistic diversity management
- Relationship-based business culture
- Consensus-building and collective decision making
- Work-life integration and family values
- Mentoring and knowledge sharing traditions
- Jugaad (innovative problem-solving) mindset
- Community and social responsibility orientation

INDUSTRY-SPECIFIC SOFT SKILL REQUIREMENTS:
- Technology: Innovation, collaboration, continuous learning, client communication
- Healthcare: Empathy, patience, crisis management, ethical decision-making
- Finance: Integrity, analytical thinking, risk assessment, regulatory compliance
- Education: Patience, communication, mentoring, cultural sensitivity
- Sales/Marketing: Persuasion, relationship building, resilience, customer focus
- Manufacturing: Safety consciousness, teamwork, process orientation, continuous improvement
- Government: Public service orientation, policy understanding, stakeholder management
- Consulting: Problem-solving, communication, adaptability, client relationship

RESPONSE FORMAT (JSON):
{{
    "soft_skills_overview": {{
        "overall_soft_skills_score": 84,
        "cultural_fit_score": 88,
        "interpersonal_effectiveness": 82,
        "leadership_potential": 86,
        "communication_excellence": 85
    }},
    "communication_skills": {{
        "verbal_communication": {{
            "clarity_of_expression": 85,
            "public_speaking": "Conference presentations",
            "presentation_skills": "Advanced",
            "multilingual_ability": ["Hindi", "English", "Tamil"],
            "cross_cultural_communication": "Strong",
            "evidence": ["Led client presentations", "Conducted training sessions"],
            "score": 87
        }},
        "written_communication": {{
            "technical_writing": "Reports, documentation",
            "business_communication": "Emails, proposals",
            "creative_writing": "Blog posts, articles",
            "documentation_skills": "Excellent",
            "evidence": ["Published research papers", "Created user manuals"],
            "score": 85
        }},
        "listening_skills": {{
            "active_listening": "Demonstrated in team settings",
            "empathy": "High emotional intelligence",
            "feedback_reception": "Open to constructive criticism",
            "score": 82
        }},
        "digital_communication": {{
            "virtual_collaboration": "Experienced in remote work",
            "social_media_presence": "Professional LinkedIn profile",
            "online_presentation": "Conducted webinars",
            "score": 84
        }},
        "overall_communication_score": 84
    }},
    "leadership_skills": {{
        "leadership_style": {{
            "style_type": "Transformational",
            "approach": "Collaborative and inclusive",
            "cultural_sensitivity": "High",
            "mentoring_ability": "Strong track record",
            "decision_making": "Consultative",
            "conflict_resolution": "Diplomatic approach"
        }},
        "team_leadership": {{
            "team_building": "Created cohesive cross-functional teams",
            "motivation_skills": "Inspired team to exceed targets",
            "delegation": "Effective task distribution",
            "performance_management": "Regular feedback and coaching",
            "diversity_management": "Led multicultural teams",
            "score": 88
        }},
        "strategic_leadership": {{
            "vision_setting": "Developed department roadmap",
            "change_management": "Led digital transformation",
            "innovation_leadership": "Championed new processes",
            "stakeholder_management": "Managed executive relationships",
            "score": 82
        }},
        "thought_leadership": {{
            "industry_expertise": "Recognized subject matter expert",
            "knowledge_sharing": "Regular speaker at conferences",
            "mentoring_others": "Guided 15+ junior professionals",
            "community_contribution": "Active in professional associations",
            "score": 85
        }},
        "overall_leadership_score": 85
    }},
    "interpersonal_skills": {{
        "relationship_building": {{
            "networking": "Strong professional network",
            "trust_building": "Established long-term client relationships",
            "rapport_establishment": "Quick to connect with diverse groups",
            "relationship_maintenance": "Consistent follow-up and engagement",
            "score": 87
        }},
        "teamwork_collaboration": {{
            "team_player": "Consistently praised for collaboration",
            "cross_functional_work": "Worked across departments",
            "knowledge_sharing": "Regular contributor to team learning",
            "collective_problem_solving": "Facilitated brainstorming sessions",
            "cultural_bridge_building": "Connected diverse team members",
            "score": 86
        }},
        "emotional_intelligence": {{
            "self_awareness": "Understands strengths and limitations",
            "empathy": "Considers others' perspectives",
            "social_awareness": "Reads organizational dynamics well",
            "relationship_management": "Maintains positive relationships",
            "stress_management": "Remains calm under pressure",
            "score": 84
        }},
        "cultural_competence": {{
            "cultural_sensitivity": "Respectful of diverse backgrounds",
            "inclusive_behavior": "Promotes equality and inclusion",
            "adaptation_skills": "Adjusts style for different audiences",
            "regional_awareness": "Understands local business practices",
            "score": 89
        }},
        "overall_interpersonal_score": 86
    }},
    "problem_solving_thinking": {{
        "analytical_thinking": {{
            "data_analysis": "Uses data to inform decisions",
            "root_cause_analysis": "Identifies underlying issues",
            "systematic_approach": "Follows structured problem-solving",
            "evidence": ["Reduced costs by analyzing processes", "Improved efficiency through data insights"],
            "score": 88
        }},
        "creative_thinking": {{
            "innovation": "Developed novel solutions",
            "out_of_box_thinking": "Approached challenges creatively",
            "jugaad_mindset": "Resourceful problem-solving with constraints",
            "design_thinking": "User-centric solution development",
            "score": 82
        }},
        "critical_thinking": {{
            "logical_reasoning": "Makes sound judgments",
            "evaluation_skills": "Assesses options objectively",
            "decision_making": "Makes informed choices",
            "strategic_thinking": "Considers long-term implications",
            "score": 85
        }},
        "adaptability": {{
            "change_acceptance": "Embraces new ways of working",
            "learning_agility": "Quickly masters new skills",
            "flexibility": "Adjusts to changing priorities",
            "resilience": "Bounces back from setbacks",
            "score": 87
        }},
        "overall_problem_solving_score": 85
    }},
    "work_ethics_values": {{
        "integrity": {{
            "honesty": "Transparent in all dealings",
            "ethical_behavior": "Upholds moral standards",
            "accountability": "Takes responsibility for outcomes",
            "reliability": "Consistently meets commitments",
            "score": 92
        }},
        "professionalism": {{
            "punctuality": "Always arrives on time",
            "dress_code": "Maintains appropriate appearance",
            "workplace_conduct": "Respectful and courteous",
            "confidentiality": "Maintains sensitive information",
            "score": 89
        }},
        "work_commitment": {{
            "dedication": "Goes above and beyond requirements",
            "persistence": "Continues despite obstacles",
            "quality_focus": "Strives for excellence",
            "continuous_improvement": "Seeks ways to enhance performance",
            "score": 88
        }},
        "social_responsibility": {{
            "community_service": "Volunteers for social causes",
            "environmental_consciousness": "Promotes sustainable practices",
            "diversity_advocacy": "Supports inclusive initiatives",
            "knowledge_sharing": "Contributes to collective learning",
            "score": 83
        }},
        "overall_ethics_score": 88
    }},
    "customer_service_orientation": {{
        "customer_focus": {{
            "client_centricity": "Prioritizes customer needs",
            "service_excellence": "Exceeds customer expectations",
            "relationship_management": "Builds long-term partnerships",
            "problem_resolution": "Quickly addresses customer issues",
            "score": 86
        }},
        "stakeholder_management": {{
            "multi_level_interaction": "Manages diverse stakeholders",
            "expectation_management": "Sets and manages realistic expectations",
            "communication_adaptation": "Tailors message for different audiences",
            "conflict_mediation": "Resolves stakeholder conflicts",
            "score": 84
        }},
        "overall_service_score": 85
    }},
    "indian_workplace_fit": {{
        "hierarchical_navigation": {{
            "respect_for_authority": "Shows appropriate deference",
            "chain_of_command": "Follows organizational structure",
            "upward_management": "Effectively manages up",
            "peer_collaboration": "Works well at same level",
            "score": 87
        }},
        "cultural_adaptation": {{
            "festival_awareness": "Respects religious and cultural celebrations",
            "regional_sensitivity": "Understands local customs",
            "language_flexibility": "Code-switches appropriately",
            "inclusive_behavior": "Embraces diversity",
            "score": 90
        }},
        "relationship_orientation": {{
            "personal_connections": "Builds meaningful relationships",
            "trust_development": "Establishes credibility over time",
            "long_term_thinking": "Focuses on sustained partnerships",
            "family_integration": "Balances work and family commitments",
            "score": 88
        }},
        "mentoring_culture": {{
            "knowledge_transfer": "Shares expertise willingly",
            "junior_development": "Invests in others' growth",
            "reverse_mentoring": "Open to learning from juniors",
            "institutional_memory": "Preserves organizational knowledge",
            "score": 85
        }},
        "overall_cultural_fit_score": 87
    }},
    "industry_specific_soft_skills": {{
        "identified_industry": "Information Technology",
        "key_soft_skills_for_industry": [
            "Technical communication",
            "Cross-functional collaboration",
            "Continuous learning mindset",
            "Client relationship management",
            "Innovation and creativity"
        ],
        "skill_gaps": [
            "Advanced negotiation skills",
            "Public speaking confidence"
        ],
        "industry_alignment_score": 84
    }},
    "strengths": [
        "Excellent cultural sensitivity and cross-cultural communication",
        "Strong leadership capabilities with inclusive approach",
        "High emotional intelligence and relationship building skills",
        "Demonstrated integrity and professional work ethics",
        "Effective problem-solving with creative and analytical thinking"
    ],
    "weaknesses": [
        "Could enhance public speaking and presentation confidence",
        "Limited experience in crisis management situations",
        "Needs to develop stronger negotiation and persuasion skills"
    ],
    "recommendations": [
        "Join Toastmasters or similar public speaking organizations",
        "Pursue advanced leadership development programs",
        "Gain experience in high-stakes negotiation scenarios",
        "Develop crisis management and decision-making skills",
        "Consider executive coaching for leadership enhancement"
    ],
    "development_priorities": [
        {{
            "skill": "Advanced Communication",
            "timeline": "3-6 months",
            "approach": "Public speaking training, presentation workshops"
        }},
        {{
            "skill": "Strategic Leadership",
            "timeline": "6-12 months", 
            "approach": "Leadership development program, executive mentoring"
        }}
    ],
    "overall_soft_skills_score": 85,
    "confidence_level": 0.86
}}

Provide comprehensive analysis considering Indian workplace culture, industry-specific soft skill requirements, and behavioral competencies essential for professional success.
"""
    
    async def analyze(self, resume_text: str, context: Dict[str, Any] = None) -> AgentResult:
        start_time = time.time()
        
        try:
            # Build and execute prompt
            prompt = self._build_prompt(resume_text, context)
            raw_response = await self._call_model(prompt)
            
            # Parse response
            analysis = self._parse_soft_skills_response(raw_response)
            
            # Calculate metrics
            score = analysis.get('overall_soft_skills_score', 0)
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
            logger.error(f"Soft skills analysis failed: {str(e)}")
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
    
    def _parse_soft_skills_response(self, response: str) -> Dict[str, Any]:
        """Parse the soft skills analysis response."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback parsing if JSON extraction fails
        return self._fallback_parse_soft_skills(response)
    
    def _fallback_parse_soft_skills(self, response: str) -> Dict[str, Any]:
        """Fallback parsing method when JSON parsing fails."""
        return {
            "communication_skills": {
                "written_communication": {"clarity": 70, "evidence": [], "score": 70},
                "verbal_communication": {"presentation_experience": "Unknown", "evidence": [], "score": 70},
                "overall_communication_score": 70
            },
            "leadership_skills": {
                "people_leadership": {"team_management": "Unknown", "score": 65},
                "thought_leadership": {"industry_recognition": "Unknown", "score": 65},
                "overall_leadership_score": 65
            },
            "collaboration_skills": {
                "teamwork": {"cross_functional": "Unknown", "score": 70},
                "stakeholder_management": {"client_interaction": "Unknown", "score": 70},
                "overall_collaboration_score": 70
            },
            "problem_solving": {
                "analytical_thinking": {"complex_problems": "Unknown", "score": 70},
                "creativity": {"innovative_projects": 0, "score": 65},
                "overall_problem_solving_score": 68
            },
            "adaptability": {
                "change_management": {"technology_adoption": "Unknown", "score": 70},
                "learning_agility": {"new_skills": "Unknown", "score": 70},
                "overall_adaptability_score": 70
            },
            "emotional_intelligence": {
                "self_awareness": {"strengths_acknowledgment": "Unknown", "score": 65},
                "empathy": {"team_support": "Unknown", "score": 65},
                "overall_ei_score": 65
            },
            "cultural_indicators": {
                "values_alignment": [],
                "diversity_inclusion": {"awareness": "Unknown", "score": 60},
                "work_life_balance": {"indicators": "Unknown", "score": 60},
                "cultural_fit_score": 60
            },
            "volunteer_community": [],
            "personality_traits": [],
            "strengths": [],
            "weaknesses": ["Limited soft skills information available"],
            "recommendations": ["Provide more examples of leadership and teamwork"],
            "overall_soft_skills_score": 67,
            "confidence_level": 0.4,
            "parsing_method": "fallback"
        }
