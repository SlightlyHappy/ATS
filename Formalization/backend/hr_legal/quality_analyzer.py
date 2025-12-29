"""
Legal Response Quality Analyzer
==============================

Analyzes and scores the quality of legal responses to ensure
high standards and consistency.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from .config import ResponseStyle, DetailLevel

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics for legal responses."""
    overall_score: float
    structure_score: float
    content_score: float
    legal_accuracy_score: float
    clarity_score: float
    completeness_score: float
    actionability_score: float
    detailed_breakdown: Dict[str, Any]

class LegalResponseQualityAnalyzer:
    """Analyzes quality of legal responses."""
    
    def __init__(self):
        # Quality scoring weights
        self.quality_weights = {
            'structure': 0.20,
            'content': 0.25,
            'legal_accuracy': 0.25,
            'clarity': 0.15,
            'completeness': 0.10,
            'actionability': 0.05
        }
        
        # Quality patterns for analysis
        self.quality_patterns = {
            'structure': {
                'has_headings': r'(^|\n)#{1,3}\s+[A-Z][^\n]+',
                'has_sections': r'(\n\n|\n\s*[-•*]\s|\n\s*\d+\.)',
                'has_conclusion': r'(conclusion|summary|in summary|to conclude)',
                'logical_flow': r'(first|second|third|next|then|finally|therefore|however|moreover)'
            },
            'content': {
                'legal_citations': r'(section|subsection|act|regulation|code|title)\s+\d+',
                'case_references': r'(v\.|vs\.|versus|\w+\s+v\.\s+\w+)',
                'regulatory_refs': r'(CFR|USC|FR|Fed\.\s*Reg\.)',
                'statute_refs': r'(\d+\s+(U\.S\.C\.|USC)|\d+\s+Stat\.)',
                'jurisdiction_refs': r'(federal|state|local|municipal|county)'
            },
            'legal_accuracy': {
                'proper_terminology': r'(shall|must|may|pursuant to|in accordance with|notwithstanding)',
                'legal_concepts': r'(due process|equal protection|at-will|wrongful termination|discrimination)',
                'compliance_terms': r'(compliant|violation|breach|adherence|conformity)',
                'risk_language': r'(liability|exposure|risk|potential|may result|could lead)'
            },
            'clarity': {
                'clear_sentences': r'[.!?]\s+[A-Z]',
                'transition_words': r'(however|therefore|moreover|furthermore|in addition|for example)',
                'defined_terms': r'(defined as|means|refers to|is understood as)',
                'explanatory_phrases': r'(in other words|that is|specifically|for instance)'
            },
            'completeness': {
                'addresses_question': True,  # Requires semantic analysis
                'provides_context': r'(background|context|historically|traditionally)',
                'covers_implications': r'(implications|consequences|effects|results)',
                'includes_alternatives': r'(alternatively|another option|consider|also)'
            },
            'actionability': {
                'recommendations': r'(recommend|suggest|advise|should|must|need to)',
                'next_steps': r'(next steps|action items|follow up|implement|proceed)',
                'timelines': r'(immediately|within|by|deadline|timeframe)',
                'responsible_parties': r'(HR|management|employee|legal|supervisor)'
            }
        }
        
        # Red flag patterns that indicate quality issues
        self.red_flag_patterns = {
            'vague_language': r'(maybe|perhaps|possibly|might be|unclear|uncertain)',
            'contradictions': r'(however.*but|although.*however|despite.*but)',
            'excessive_hedging': r'(may|might|could|possibly|potentially){3,}',
            'no_citations': r'^(?!.*(?:section|act|regulation|code|title)\s+\d+).*$',
            'too_generic': r'(consult.*attorney|seek.*legal.*advice|depends.*circumstances){2,}'
        }
    
    def analyze_response_quality(self, 
                               response_text: str,
                               query_text: str,
                               style: ResponseStyle,
                               detail_level: DetailLevel) -> QualityMetrics:
        """
        Analyze the quality of a legal response.
        
        Args:
            response_text: The generated response
            query_text: Original query
            style: Response style used
            detail_level: Detail level requested
            
        Returns:
            Quality metrics and scores
        """
        scores = {}
        detailed_breakdown = {}
        
        # Analyze structure quality
        structure_score, structure_details = self._analyze_structure(response_text, style)
        scores['structure'] = structure_score
        detailed_breakdown['structure'] = structure_details
        
        # Analyze content quality
        content_score, content_details = self._analyze_content(response_text)
        scores['content'] = content_score
        detailed_breakdown['content'] = content_details
        
        # Analyze legal accuracy
        legal_score, legal_details = self._analyze_legal_accuracy(response_text)
        scores['legal_accuracy'] = legal_score
        detailed_breakdown['legal_accuracy'] = legal_details
        
        # Analyze clarity
        clarity_score, clarity_details = self._analyze_clarity(response_text, detail_level)
        scores['clarity'] = clarity_score
        detailed_breakdown['clarity'] = clarity_details
        
        # Analyze completeness
        completeness_score, completeness_details = self._analyze_completeness(
            response_text, query_text
        )
        scores['completeness'] = completeness_score
        detailed_breakdown['completeness'] = completeness_details
        
        # Analyze actionability
        actionability_score, actionability_details = self._analyze_actionability(response_text)
        scores['actionability'] = actionability_score
        detailed_breakdown['actionability'] = actionability_details
        
        # Calculate overall score
        overall_score = sum(
            scores[category] * self.quality_weights[category]
            for category in scores
        )
        
        # Check for red flags
        red_flags = self._check_red_flags(response_text)
        if red_flags:
            overall_score *= 0.8  # Penalty for red flags
            detailed_breakdown['red_flags'] = red_flags
        
        return QualityMetrics(
            overall_score=overall_score,
            structure_score=scores['structure'],
            content_score=scores['content'],
            legal_accuracy_score=scores['legal_accuracy'],
            clarity_score=scores['clarity'],
            completeness_score=scores['completeness'],
            actionability_score=scores['actionability'],
            detailed_breakdown=detailed_breakdown
        )
    
    def _analyze_structure(self, text: str, style: ResponseStyle) -> Tuple[float, Dict]:
        """Analyze structural quality of response."""
        score = 0.0
        details = {}
        
        patterns = self.quality_patterns['structure']
        
        # Check for headings
        if re.search(patterns['has_headings'], text, re.IGNORECASE | re.MULTILINE):
            score += 0.3
            details['has_headings'] = True
        
        # Check for sections/organization
        sections = len(re.findall(patterns['has_sections'], text))
        if sections >= 3:
            score += 0.3
        elif sections >= 1:
            score += 0.15
        details['section_count'] = sections
        
        # Check for conclusion
        if re.search(patterns['has_conclusion'], text, re.IGNORECASE):
            score += 0.2
            details['has_conclusion'] = True
        
        # Check logical flow
        flow_indicators = len(re.findall(patterns['logical_flow'], text, re.IGNORECASE))
        if flow_indicators >= 3:
            score += 0.2
        elif flow_indicators >= 1:
            score += 0.1
        details['flow_indicators'] = flow_indicators
        
        return min(score, 1.0), details
    
    def _analyze_content(self, text: str) -> Tuple[float, Dict]:
        """Analyze content quality and legal references."""
        score = 0.0
        details = {}
        
        patterns = self.quality_patterns['content']
        
        # Legal citations
        citations = len(re.findall(patterns['legal_citations'], text, re.IGNORECASE))
        if citations >= 3:
            score += 0.3
        elif citations >= 1:
            score += 0.15
        details['legal_citations'] = citations
        
        # Case references
        cases = len(re.findall(patterns['case_references'], text, re.IGNORECASE))
        if cases >= 1:
            score += 0.2
        details['case_references'] = cases
        
        # Regulatory references
        regs = len(re.findall(patterns['regulatory_refs'], text, re.IGNORECASE))
        if regs >= 1:
            score += 0.2
        details['regulatory_refs'] = regs
        
        # Statute references
        statutes = len(re.findall(patterns['statute_refs'], text, re.IGNORECASE))
        if statutes >= 1:
            score += 0.2
        details['statute_refs'] = statutes
        
        # Jurisdiction references
        jurisdictions = len(re.findall(patterns['jurisdiction_refs'], text, re.IGNORECASE))
        if jurisdictions >= 1:
            score += 0.1
        details['jurisdiction_refs'] = jurisdictions
        
        return min(score, 1.0), details
    
    def _analyze_legal_accuracy(self, text: str) -> Tuple[float, Dict]:
        """Analyze legal accuracy indicators."""
        score = 0.0
        details = {}
        
        patterns = self.quality_patterns['legal_accuracy']
        
        # Proper legal terminology
        legal_terms = len(re.findall(patterns['proper_terminology'], text, re.IGNORECASE))
        if legal_terms >= 5:
            score += 0.3
        elif legal_terms >= 2:
            score += 0.15
        details['legal_terminology'] = legal_terms
        
        # Legal concepts
        concepts = len(re.findall(patterns['legal_concepts'], text, re.IGNORECASE))
        if concepts >= 2:
            score += 0.25
        elif concepts >= 1:
            score += 0.15
        details['legal_concepts'] = concepts
        
        # Compliance terms
        compliance = len(re.findall(patterns['compliance_terms'], text, re.IGNORECASE))
        if compliance >= 2:
            score += 0.25
        elif compliance >= 1:
            score += 0.15
        details['compliance_terms'] = compliance
        
        # Risk language
        risk_terms = len(re.findall(patterns['risk_language'], text, re.IGNORECASE))
        if risk_terms >= 2:
            score += 0.2
        elif risk_terms >= 1:
            score += 0.1
        details['risk_language'] = risk_terms
        
        return min(score, 1.0), details
    
    def _analyze_clarity(self, text: str, detail_level: DetailLevel) -> Tuple[float, Dict]:
        """Analyze clarity and readability."""
        score = 0.0
        details = {}
        
        patterns = self.quality_patterns['clarity']
        
        # Sentence structure
        sentences = len(re.findall(patterns['clear_sentences'], text))
        avg_sentence_length = len(text.split()) / max(sentences, 1)
        
        if avg_sentence_length <= 25:  # Good sentence length
            score += 0.3
        elif avg_sentence_length <= 35:
            score += 0.15
        details['avg_sentence_length'] = avg_sentence_length
        
        # Transition words
        transitions = len(re.findall(patterns['transition_words'], text, re.IGNORECASE))
        if transitions >= 3:
            score += 0.25
        elif transitions >= 1:
            score += 0.15
        details['transition_words'] = transitions
        
        # Defined terms
        definitions = len(re.findall(patterns['defined_terms'], text, re.IGNORECASE))
        if definitions >= 1:
            score += 0.25
        details['defined_terms'] = definitions
        
        # Explanatory phrases
        explanations = len(re.findall(patterns['explanatory_phrases'], text, re.IGNORECASE))
        if explanations >= 2:
            score += 0.2
        elif explanations >= 1:
            score += 0.1
        details['explanatory_phrases'] = explanations
        
        return min(score, 1.0), details
    
    def _analyze_completeness(self, response_text: str, query_text: str) -> Tuple[float, Dict]:
        """Analyze completeness of response."""
        score = 0.0
        details = {}
        
        patterns = self.quality_patterns['completeness']
        
        # Basic completeness indicators
        if len(response_text.split()) >= 100:  # Minimum substance
            score += 0.2
        
        # Context provision
        if re.search(patterns['provides_context'], response_text, re.IGNORECASE):
            score += 0.25
            details['provides_context'] = True
        
        # Covers implications
        if re.search(patterns['covers_implications'], response_text, re.IGNORECASE):
            score += 0.25
            details['covers_implications'] = True
        
        # Includes alternatives
        if re.search(patterns['includes_alternatives'], response_text, re.IGNORECASE):
            score += 0.2
            details['includes_alternatives'] = True
        
        # Question addressing (basic keyword matching)
        query_keywords = set(query_text.lower().split())
        response_keywords = set(response_text.lower().split())
        keyword_overlap = len(query_keywords.intersection(response_keywords)) / len(query_keywords)
        
        if keyword_overlap >= 0.3:
            score += 0.1
        details['keyword_overlap'] = keyword_overlap
        
        return min(score, 1.0), details
    
    def _analyze_actionability(self, text: str) -> Tuple[float, Dict]:
        """Analyze actionability of response."""
        score = 0.0
        details = {}
        
        patterns = self.quality_patterns['actionability']
        
        # Recommendations
        recommendations = len(re.findall(patterns['recommendations'], text, re.IGNORECASE))
        if recommendations >= 3:
            score += 0.4
        elif recommendations >= 1:
            score += 0.2
        details['recommendations'] = recommendations
        
        # Next steps
        next_steps = len(re.findall(patterns['next_steps'], text, re.IGNORECASE))
        if next_steps >= 1:
            score += 0.3
        details['next_steps'] = next_steps
        
        # Timelines
        timelines = len(re.findall(patterns['timelines'], text, re.IGNORECASE))
        if timelines >= 1:
            score += 0.2
        details['timelines'] = timelines
        
        # Responsible parties
        parties = len(re.findall(patterns['responsible_parties'], text, re.IGNORECASE))
        if parties >= 1:
            score += 0.1
        details['responsible_parties'] = parties
        
        return min(score, 1.0), details
    
    def _check_red_flags(self, text: str) -> List[str]:
        """Check for quality red flags."""
        red_flags = []
        
        for flag_name, pattern in self.red_flag_patterns.items():
            if isinstance(pattern, str) and re.search(pattern, text, re.IGNORECASE):
                red_flags.append(flag_name)
        
        return red_flags
    
    def get_improvement_suggestions(self, metrics: QualityMetrics) -> List[str]:
        """Generate improvement suggestions based on quality analysis."""
        suggestions = []
        
        if metrics.structure_score < 0.7:
            suggestions.append("Improve response structure with clear headings and logical organization")
        
        if metrics.content_score < 0.6:
            suggestions.append("Include more specific legal citations and regulatory references")
        
        if metrics.legal_accuracy_score < 0.7:
            suggestions.append("Use more precise legal terminology and compliance language")
        
        if metrics.clarity_score < 0.6:
            suggestions.append("Enhance clarity with better sentence structure and explanations")
        
        if metrics.completeness_score < 0.6:
            suggestions.append("Provide more comprehensive coverage of the topic and implications")
        
        if metrics.actionability_score < 0.5:
            suggestions.append("Include more specific recommendations and actionable next steps")
        
        if 'red_flags' in metrics.detailed_breakdown:
            suggestions.append("Address red flag issues: avoid vague language and provide more specific guidance")
        
        return suggestions
