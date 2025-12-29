"""
Legal RAG API endpoints for HR-Legal consultation
"""
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from app import db
from app.models.user import User, CreditTransaction
from app.models.legal import LegalQuery, LegalDocument, DocumentChunk, KnowledgeBaseUpdate
from app.services.legal_rag_service import LegalRAGService
from app.services.document_processor import DocumentProcessor
from app.services.auth_manager import auth_manager
from app.config import Config

logger = logging.getLogger(__name__)

# Create Blueprint
legal_bp = Blueprint('legal', __name__, url_prefix='/api/legal')

# Simple validation functions
def validate_legal_query(data):
    """Validate legal query request"""
    if not data:
        return False, "Request data is required"
    
    query = data.get('query', '').strip()
    if not query:
        return False, "Query is required"
    
    if len(query) < 10:
        return False, "Query must be at least 10 characters long"
    
    if len(query) > 1000:
        return False, "Query too long. Maximum 1000 characters allowed."
    
    max_sources = data.get('max_sources', 5)
    if not isinstance(max_sources, int) or not (1 <= max_sources <= 10):
        return False, "max_sources must be an integer between 1 and 10"
    
    return True, None

def validate_feedback(data):
    """Validate feedback request"""
    if not data:
        return False, "Request data is required"
    
    query_id = data.get('query_id', '').strip()
    if not query_id:
        return False, "query_id is required"
    
    rating = data.get('rating')
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return False, "rating must be an integer between 1 and 5"
    
    return True, None

# Helper Functions
def check_user_credits(user: User, required_credits: int) -> bool:
    """Check if user has sufficient credits"""
    if user.is_admin and Config.ADMIN_UNLIMITED_CREDITS:
        return True
    return user.credits >= required_credits

def deduct_user_credits(user: User, credits: int, description: str):
    """Deduct credits from user account"""
    if user.is_admin and Config.ADMIN_UNLIMITED_CREDITS:
        return  # Admins have unlimited credits
    
    user.credits -= credits
    
    # Create transaction record
    transaction = CreditTransaction(
        user_id=user.id,
        credits_used=credits,
        credits_remaining=user.credits,
        transaction_type='legal_query',
        description=description
    )
    db.session.add(transaction)

@legal_bp.route('/query', methods=['POST'])
def legal_query():
    """
    Legal RAG query endpoint
    
    Process legal questions using RAG system
    Cost: 2 credits per query
    """
    try:
        # Validate request
        data = request.get_json() or {}
        is_valid, error_msg = validate_legal_query(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Authenticate user
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        query_text = data['query'].strip()
        max_sources = data.get('max_sources', 5)
        
        # Check if Legal RAG is enabled
        if not Config.LEGAL_RAG_ENABLED:
            return jsonify({
                'error': 'Legal consultation service is currently unavailable'
            }), 503
        
        # Check credits
        required_credits = Config.CREDIT_COST_PER_LEGAL_QUERY
        if not check_user_credits(user, required_credits):
            return jsonify({
                'error': f'Insufficient credits. Legal queries require {required_credits} credits. You have {user.credits} credits.',
                'required_credits': required_credits,
                'current_credits': user.credits
            }), 402
        
        # Check query length
        if len(query_text) > 1000:
            return jsonify({
                'error': 'Query too long. Maximum 1000 characters allowed.'
            }), 400
        
        # Process legal query
        try:
            rag_service = LegalRAGService()
            result = asyncio.run(rag_service.query_legal_knowledge(
                query_text=query_text,
                user_id=str(user.id),
                max_sources=max_sources
            ))
            
            if result['status'] == 'success':
                # Deduct credits only on successful query
                deduct_user_credits(
                    user, 
                    required_credits, 
                    f"Legal query: {query_text[:50]}..."
                )
                db.session.commit()
                
                # Add user credit info to response
                result['credits_used'] = required_credits
                result['credits_remaining'] = user.credits
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Legal query processing failed: {str(e)}")
            return jsonify({
                'error': 'Failed to process legal query. Please try again.',
                'legal_disclaimer': 'This service provides AI-generated information for guidance only. Consult qualified legal counsel for specific advice.'
            }), 500
        
    except Exception as e:
        logger.error(f"Legal query endpoint error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'legal_disclaimer': 'This service provides AI-generated information for guidance only. Consult qualified legal counsel for specific advice.'
        }), 500

@legal_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for legal query response"""
    try:
        # Validate request
        data = request.get_json() or {}
        is_valid, error_msg = validate_feedback(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Authenticate user
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        
        # Find the query
        query = LegalQuery.query.filter_by(
            id=data['query_id'],
            user_id=user.id
        ).first()
        
        if not query:
            return jsonify({'error': 'Query not found'}), 404
        
        # Update feedback
        query.user_rating = data['rating']
        query.user_feedback = data.get('feedback', '')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Feedback submitted successfully',
            'query_id': data['query_id']
        })
        
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}")
        return jsonify({'error': 'Failed to submit feedback'}), 500

@legal_bp.route('/history', methods=['GET'])
def query_history():
    """Get user's legal query history"""
    try:
        # Authenticate user
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        
        # Get queries
        queries = LegalQuery.query.filter_by(user_id=user.id).order_by(
            LegalQuery.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'queries': [
                {
                    'id': str(query.id),
                    'query_text': query.query_text,
                    'response_preview': query.response[:200] + '...' if query.response and len(query.response) > 200 else query.response,
                    'confidence_score': query.confidence_score,
                    'status': query.status,
                    'user_rating': query.user_rating,
                    'processing_time': query.processing_time,
                    'created_at': query.created_at.isoformat() if query.created_at else None
                }
                for query in queries.items
            ],
            'pagination': {
                'page': page,
                'pages': queries.pages,
                'per_page': per_page,
                'total': queries.total,
                'has_next': queries.has_next,
                'has_prev': queries.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Query history error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve query history'}), 500

@legal_bp.route('/query/<query_id>', methods=['GET'])
def get_query_detail(query_id):
    """Get detailed information about a specific query"""
    try:
        # Authenticate user
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        
        # Find the query
        query = LegalQuery.query.filter_by(
            id=query_id,
            user_id=user.id
        ).first()
        
        if not query:
            return jsonify({'error': 'Query not found'}), 404
        
        return jsonify({
            'id': str(query.id),
            'query_text': query.query_text,
            'response': query.response,
            'confidence_score': query.confidence_score,
            'source_documents': query.source_documents,
            'retrieved_chunks': query.retrieved_chunks,
            'processing_time': query.processing_time,
            'embedding_time': query.embedding_time,
            'retrieval_time': query.retrieval_time,
            'generation_time': query.generation_time,
            'user_rating': query.user_rating,
            'user_feedback': query.user_feedback,
            'status': query.status,
            'created_at': query.created_at.isoformat() if query.created_at else None,
            'legal_disclaimer': 'This response is generated by AI and is for informational purposes only. Consult qualified legal counsel for specific advice.'
        })
        
    except Exception as e:
        logger.error(f"Query detail error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve query details'}), 500

@legal_bp.route('/knowledge-base/stats', methods=['GET'])
def knowledge_base_stats():
    """Get statistics about the legal knowledge base"""
    try:
        # Authenticate user (admin only for detailed stats)
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        
        rag_service = LegalRAGService()
        stats = asyncio.run(rag_service.get_knowledge_base_stats())
        
        # Add user-specific stats if not admin
        if not user.is_admin:
            user_queries = LegalQuery.query.filter_by(user_id=user.id).count()
            stats = {
                'total_documents': stats.get('total_documents', 0),
                'total_chunks': stats.get('total_chunks', 0),
                'your_queries': user_queries,
                'service_status': 'available' if stats.get('total_chunks', 0) > 0 else 'building'
            }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Knowledge base stats error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve knowledge base statistics'}), 500

# Admin-only endpoints
@legal_bp.route('/admin/documents', methods=['GET'])
def list_documents():
    """List all legal documents (admin only)"""
    try:
        # Authenticate admin
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        documents = LegalDocument.query.order_by(
            LegalDocument.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents.items],
            'pagination': {
                'page': page,
                'pages': documents.pages,
                'per_page': per_page,
                'total': documents.total,
                'has_next': documents.has_next,
                'has_prev': documents.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve documents'}), 500

@legal_bp.route('/admin/process-documents', methods=['POST'])
def process_documents():
    """Trigger document processing (admin only)"""
    try:
        # Authenticate admin
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get processing options
        data = request.get_json() or {}
        update_type = data.get('update_type', 'full_rebuild')
        
        # Start document processing
        processor = DocumentProcessor()
        result = asyncio.run(processor.process_all_documents(
            update_type=update_type,
            trigger='manual_admin'
        ))
        
        return jsonify({
            'message': 'Document processing completed',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        return jsonify({'error': 'Failed to process documents'}), 500

@legal_bp.route('/admin/updates', methods=['GET'])
def list_updates():
    """List knowledge base updates (admin only)"""
    try:
        # Authenticate admin
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        
        updates = KnowledgeBaseUpdate.query.order_by(
            KnowledgeBaseUpdate.started_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'updates': [update.to_dict() for update in updates.items],
            'pagination': {
                'page': page,
                'pages': updates.pages,
                'per_page': per_page,
                'total': updates.total,
                'has_next': updates.has_next,
                'has_prev': updates.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"List updates error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve updates'}), 500

@legal_bp.route('/admin/queries', methods=['GET'])
def list_all_queries():
    """List all legal queries (admin only)"""
    try:
        # Authenticate admin
        auth_result = auth_manager.authenticate_request(request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        user = auth_result['user']
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Pagination and filtering
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status')
        
        query = LegalQuery.query
        
        if status_filter:
            query = query.filter(LegalQuery.status == status_filter)
        
        queries = query.order_by(LegalQuery.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'queries': [
                {
                    'id': str(q.id),
                    'user_id': str(q.user_id),
                    'query_text': q.query_text[:200] + '...' if len(q.query_text) > 200 else q.query_text,
                    'confidence_score': q.confidence_score,
                    'processing_time': q.processing_time,
                    'user_rating': q.user_rating,
                    'status': q.status,
                    'created_at': q.created_at.isoformat() if q.created_at else None
                }
                for q in queries.items
            ],
            'pagination': {
                'page': page,
                'pages': queries.pages,
                'per_page': per_page,
                'total': queries.total,
                'has_next': queries.has_next,
                'has_prev': queries.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"List all queries error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve queries'}), 500

# Import asyncio at the top level for route handlers
import asyncio

# Health check endpoint
@legal_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for legal RAG service"""
    try:
        # Check if knowledge base has content
        total_documents = LegalDocument.query.count()
        processed_documents = LegalDocument.query.filter(
            LegalDocument.processing_status == 'completed'
        ).count()
        total_chunks = DocumentChunk.query.count()
        
        status = "healthy" if total_chunks > 0 else "building"
        
        return jsonify({
            'status': status,
            'total_documents': total_documents,
            'processed_documents': processed_documents,
            'total_chunks': total_chunks,
            'rag_enabled': Config.LEGAL_RAG_ENABLED,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Legal health check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
