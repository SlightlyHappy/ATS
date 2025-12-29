"""
HR Legal RAG Module Init
Exposes the HR Legal RAG system for easy import
"""

from .hr_legal_rag import (
    HRLegalRAGSystem,
    get_rag_system,
    query_hr_legal,
    add_legal_document,
    get_rag_health
)

__all__ = [
    'HRLegalRAGSystem',
    'get_rag_system', 
    'query_hr_legal',
    'add_legal_document',
    'get_rag_health'
]
