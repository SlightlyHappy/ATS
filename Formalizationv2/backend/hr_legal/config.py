"""
Configuration classes for the Enhanced Agentic RAG System
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ResponseLength(Enum):
    """Response length options."""
    SHORT = "short"          # 50-150 words
    MEDIUM = "medium"        # 150-400 words  
    LONG = "long"           # 400-800 words
    DETAILED = "detailed"   # 800+ words
    CUSTOM = "custom"       # User-defined

class ResponseStyle(Enum):
    """Response style options."""
    PROFESSIONAL = "professional"
    LEGAL = "legal"
    CASUAL = "casual" 
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"

class DetailLevel(Enum):
    """Detail level options."""
    BRIEF = "brief"
    BALANCED = "balanced"
    COMPREHENSIVE = "comprehensive"

class AudienceLevel(Enum):
    """Target audience level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

@dataclass
class AgenticRAGConfig:
    """Configuration for the agentic RAG system."""
    
    # Response Configuration
    response_length: ResponseLength = ResponseLength.MEDIUM
    custom_word_count: Optional[int] = None
    max_tokens: int = 2048  # Increased for better responses
    response_style: ResponseStyle = ResponseStyle.PROFESSIONAL
    detail_level: DetailLevel = DetailLevel.BALANCED
    audience_level: AudienceLevel = AudienceLevel.INTERMEDIATE
    
    # Content Options - Enhanced defaults for legal responses
    include_citations: bool = True
    include_confidence: bool = True
    show_reasoning_chain: bool = True  # Enable for better transparency
    include_follow_up_questions: bool = True
    include_case_examples: bool = True
    structured_output: bool = True
    include_metadata: bool = True
    include_legal_disclaimers: bool = True  # New: Always include legal disclaimers
    include_risk_assessment: bool = True   # New: Include risk assessments
    
    # Retrieval Settings - Enhanced for better context
    retrieval_depth: int = 7  # Increased from 5 for more context
    similarity_threshold: float = 0.65  # Lowered slightly for broader context
    cross_reference: bool = True
    jurisdiction_focus: str = "central"  # central, state, both
    
    # Processing Options - Enhanced quality control
    enable_multi_step_reasoning: bool = True
    quality_check: bool = True
    response_validation: bool = True
    auto_improve: bool = True  # Enable auto-improvement
    use_enhanced_prompts: bool = True  # New: Use enhanced prompt templates
    
    # Performance Settings
    timeout_seconds: int = 360  # Increased from 180 to 360 seconds for limited hardware
    enable_caching: bool = True
    cache_ttl_minutes: int = 60
    
    # Quality Thresholds - New section
    minimum_quality_score: float = 0.7
    require_legal_citations: bool = True
    require_actionable_guidance: bool = True

@dataclass 
class LegalQueryContext:
    """Context for a legal query."""
    
    query: str
    query_type: str = "general"  # compliance, policy, document, general
    conversation_id: Optional[str] = None
    user_role: str = "hr_professional"  # hr_professional, manager, employee
    urgency: str = "normal"  # low, normal, high, urgent
    specific_documents: List[str] = field(default_factory=list)
    previous_context: Optional[Dict[str, Any]] = None

@dataclass
class ResponseMetadata:
    """Metadata for generated responses."""
    
    confidence_score: float = 0.0
    processing_time: float = 0.0
    sources_used: List[str] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    follow_up_suggestions: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    validation_passed: bool = True
    improvement_suggestions: List[str] = field(default_factory=list)

@dataclass
class LegalResponse:
    """Complete legal response object."""
    
    content: str
    metadata: ResponseMetadata
    config_used: AgenticRAGConfig
    query_context: LegalQueryContext
    response_id: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "content": self.content,
            "metadata": {
                "confidence_score": self.metadata.confidence_score,
                "processing_time": self.metadata.processing_time,
                "sources_used": self.metadata.sources_used,
                "reasoning_steps": self.metadata.reasoning_steps,
                "follow_up_suggestions": self.metadata.follow_up_suggestions,
                "quality_score": self.metadata.quality_score,
                "validation_passed": self.metadata.validation_passed,
                "improvement_suggestions": self.metadata.improvement_suggestions
            },
            "config": {
                "response_length": self.config_used.response_length.value,
                "response_style": self.config_used.response_style.value,
                "detail_level": self.config_used.detail_level.value,
                "audience_level": self.config_used.audience_level.value
            },
            "query_info": {
                "query": self.query_context.query,
                "query_type": self.query_context.query_type,
                "user_role": self.query_context.user_role,
                "urgency": self.query_context.urgency
            },
            "response_id": self.response_id,
            "timestamp": self.timestamp
        }
