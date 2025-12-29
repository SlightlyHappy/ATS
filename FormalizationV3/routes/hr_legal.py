"""
HR Legal and RAG System Routes
Handles legal queries, compliance checks, and document generation
"""

import logging
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from functools import wraps

logger = logging.getLogger(__name__)

# Create Blueprint
hr_legal_bp = Blueprint('hr_legal', __name__, url_prefix='/api/hr-legal')

# Global references (will be set by init_hr_legal_routes)
_ai_processor = None
_auth_middleware = None
_cache_manager = None

def init_hr_legal_routes(ai_processor, auth_middleware, cache_manager=None):
    """Initialize HR legal routes with dependencies"""
    global _ai_processor, _auth_middleware, _cache_manager
    _ai_processor = ai_processor
    _auth_middleware = auth_middleware
    _cache_manager = cache_manager
    logger.info("✅ HR Legal routes initialized")

@hr_legal_bp.route('/health', methods=['GET'])
def rag_health_check():
    """HR Legal RAG System health check endpoint"""
    try:
        # Check if AI processor is available
        if not _ai_processor:
            return jsonify({
                "status": "unavailable",
                "message": "HR Legal system not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }), 503
        
        # Try to perform a simple health check
        health_result = _ai_processor.health_check() if hasattr(_ai_processor, 'health_check') else {"status": "ok"}
        
        return jsonify({
            "status": "healthy",
            "service": "hr-legal-rag",
            "ai_processor": health_result.get("status", "ok"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"HR Legal health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

@hr_legal_bp.route('/query', methods=['POST'])
def process_legal_query():
    """Process HR legal query with RAG system"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data or not data.get('query'):
            return jsonify({"error": "Query is required"}), 400
        
        query = data['query']
        context = data.get('context', {})
        
        # Process with AI
        if not _ai_processor:
            return jsonify({
                "error": "HR Legal system not available",
                "fallback": "Please consult your HR handbook or legal team"
            }), 503
        
        # Try to process legal query
        try:
            if hasattr(_ai_processor, 'process_legal_query'):
                result = _ai_processor.process_legal_query(query, context)
            else:
                # Fallback to general AI processing
                result = _ai_processor.process_query(query, context_type="legal")
            
            return jsonify({
                "success": True,
                "query": query,
                "response": result.get('response', 'No response generated'),
                "sources": result.get('sources', []),
                "confidence": result.get('confidence', 0.5),
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as ai_error:
            logger.error(f"AI processing error: {ai_error}")
            return jsonify({
                "error": "Legal query processing failed",
                "fallback": "Please consult your HR handbook or legal team",
                "technical_error": str(ai_error)
            }), 500
        
    except Exception as e:
        logger.error(f"Legal query error: {e}")
        return jsonify({
            "error": "Legal query failed",
            "message": str(e)
        }), 500

@hr_legal_bp.route('/compliance-check', methods=['POST'])
def compliance_check():
    """Check document compliance with HR legal standards"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data or not data.get('content'):
            return jsonify({"error": "Content is required for compliance check"}), 400
        
        content = data['content']
        document_type = data.get('document_type', 'general')
        
        # Process compliance check
        if not _ai_processor:
            return jsonify({
                "error": "Compliance check system not available",
                "recommendation": "Please have your legal team review the document"
            }), 503
        
        try:
            if hasattr(_ai_processor, 'check_compliance'):
                result = _ai_processor.check_compliance(content, document_type)
            else:
                # Fallback compliance check
                result = _ai_processor.process_query(
                    f"Check this {document_type} document for HR compliance issues: {content[:1000]}...",
                    context_type="compliance"
                )
            
            return jsonify({
                "success": True,
                "document_type": document_type,
                "compliant": result.get('compliant', True),
                "issues": result.get('issues', []),
                "recommendations": result.get('recommendations', []),
                "confidence": result.get('confidence', 0.5),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as ai_error:
            logger.error(f"Compliance check AI error: {ai_error}")
            return jsonify({
                "error": "Compliance check processing failed",
                "recommendation": "Please have your legal team review the document",
                "technical_error": str(ai_error)
            }), 500
        
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        return jsonify({
            "error": "Compliance check failed",
            "message": str(e)
        }), 500

@hr_legal_bp.route('/generate-document', methods=['POST'])
def generate_document():
    """Generate HR legal documents from templates"""
    try:
        # Check authentication
        if _auth_middleware and not _auth_middleware.is_authenticated():
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data or not data.get('template_type'):
            return jsonify({"error": "Template type is required"}), 400
        
        template_type = data['template_type']
        template_data = data.get('data', {})
        
        # Generate document
        if not _ai_processor:
            return jsonify({
                "error": "Document generation system not available",
                "recommendation": "Please use standard templates from your legal team"
            }), 503
        
        try:
            if hasattr(_ai_processor, 'generate_document'):
                result = _ai_processor.generate_document(template_type, template_data)
            else:
                # Fallback document generation
                prompt = f"Generate a {template_type} document with the following details: {json.dumps(template_data)}"
                result = _ai_processor.process_query(prompt, context_type="document_generation")
            
            return jsonify({
                "success": True,
                "template_type": template_type,
                "document": result.get('document', ''),
                "format": result.get('format', 'markdown'),
                "warnings": result.get('warnings', []),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as ai_error:
            logger.error(f"Document generation AI error: {ai_error}")
            return jsonify({
                "error": "Document generation failed",
                "recommendation": "Please use standard templates from your legal team",
                "technical_error": str(ai_error)
            }), 500
        
    except Exception as e:
        logger.error(f"Document generation error: {e}")
        return jsonify({
            "error": "Document generation failed",
            "message": str(e)
        }), 500
