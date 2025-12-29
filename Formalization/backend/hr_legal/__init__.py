"""
HR Legal Module - Enhanced Agentic RAG System
============================================

This module provides advanced legal assistance capabilities for HR processes,
including compliance checking, policy guidance, and document generation.

Features:
- Agentic RAG with configurable response generation
- Multi-step reasoning for complex legal queries
- Integration with existing AI provider infrastructure
- Legal knowledge base management
- Response customization and quality scoring
"""

try:
    from .config import (
        AgenticRAGConfig, LegalQueryContext, LegalResponse, ResponseMetadata,
        ResponseLength, ResponseStyle, DetailLevel, AudienceLevel
    )
    from .rag_engine import EnhancedRAGEngine
    from .agent_controller import LegalAgent
    from .response_generator import ResponseController
    from .vector_store import LegalVectorStore
    from .legal_knowledge import LegalKnowledgeBase
    from .prompt_templates import PromptTemplate
    from .quality_analyzer import LegalResponseQualityAnalyzer, QualityMetrics

    __all__ = [
        'EnhancedRAGEngine',
        'LegalAgent', 
        'ResponseController',
        'LegalVectorStore',
        'LegalKnowledgeBase',
        'PromptTemplate',
        'LegalResponseQualityAnalyzer',
        'QualityMetrics',
        'AgenticRAGConfig',
        'LegalQueryContext', 
        'LegalResponse',
        'ResponseMetadata',
        'ResponseLength',
        'ResponseStyle', 
        'DetailLevel',
        'AudienceLevel'
    ]
except ImportError as e:
    # Handle missing dependencies gracefully
    print(f"Warning: Some HR Legal dependencies are missing: {e}")
    __all__ = []

__version__ = "1.0.0"
