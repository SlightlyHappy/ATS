"""
Legal RAG Service for HR-Legal AI Consultation
Handles query processing, retrieval, and response generation
"""
import asyncio
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import numpy as np

# Import sentence transformers with error handling for compatibility
try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logging.warning(f"Failed to import sentence_transformers: {e}")
    # Create a dummy class to prevent initialization errors
    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("SentenceTransformer not available due to dependency issues")
        
        def encode(self, *args, **kwargs):
            raise NotImplementedError("SentenceTransformer not available due to dependency issues")

from sklearn.metrics.pairwise import cosine_similarity

from app import db
from app.models.legal import LegalDocument, DocumentChunk, LegalQuery
from app.models.user import User, CreditTransaction
from app.services.ollama_service import OllamaService
from app.config import Config

logger = logging.getLogger(__name__)

class LegalRAGService:
    """Production-grade Legal RAG service with high accuracy"""
    
    def __init__(self):
        self.embedding_model = None
        self.top_k = Config.RAG_TOP_K
        self.similarity_threshold = Config.RAG_SIMILARITY_THRESHOLD
        self.max_context_length = Config.MAX_CONTEXT_LENGTH
        self.enable_caching = Config.ENABLE_QUERY_CACHING
        self.cache_ttl = Config.QUERY_CACHE_TTL
        
    async def initialize(self):
        """Initialize the RAG service"""
        try:
            logger.info(f"Initializing Legal RAG service with model: {Config.LEGAL_EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(Config.LEGAL_EMBEDDING_MODEL)
            logger.info("Legal RAG service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Legal RAG service: {str(e)}")
            raise
    
    async def query_legal_knowledge(self, 
                                  query_text: str, 
                                  user_id: str,
                                  max_sources: int = 5) -> Dict:
        """
        Main RAG query method with high accuracy retrieval and response generation
        
        Args:
            query_text: User's legal question
            user_id: ID of the user making the query
            max_sources: Maximum number of source documents to include
            
        Returns:
            Dict containing response, confidence, sources, and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            if not self.embedding_model:
                await self.initialize()
            
            # Check for cached response
            query_hash = LegalQuery.generate_query_hash(query_text)
            if self.enable_caching:
                cached_response = await self._get_cached_response(query_hash)
                if cached_response:
                    logger.info(f"Returning cached response for query hash: {query_hash[:8]}")
                    return cached_response
            
            # Step 1: Generate query embedding
            embedding_start = datetime.utcnow()
            query_embedding = self.embedding_model.encode([query_text])[0]
            embedding_time = (datetime.utcnow() - embedding_start).total_seconds()
            
            # Step 2: Retrieve relevant chunks using hybrid search
            retrieval_start = datetime.utcnow()
            relevant_chunks = await self._hybrid_retrieval(query_text, query_embedding)
            retrieval_time = (datetime.utcnow() - retrieval_start).total_seconds()
            
            if not relevant_chunks:
                return {
                    'response': "I couldn't find relevant legal information for your query. Please try rephrasing your question or contact a legal expert for specific advice.",
                    'confidence_score': 0.0,
                    'source_documents': [],
                    'legal_disclaimer': self._get_legal_disclaimer(),
                    'retrieved_chunks': [],
                    'processing_time': (datetime.utcnow() - start_time).total_seconds(),
                    'status': 'no_results'
                }
            
            # Step 3: Prepare context and generate response
            generation_start = datetime.utcnow()
            context = self._prepare_context(relevant_chunks)
            
            response_text, confidence = await self._generate_legal_response(
                query_text, context, relevant_chunks
            )
            generation_time = (datetime.utcnow() - generation_start).total_seconds()
            
            # Step 4: Prepare source information
            source_documents = self._prepare_source_documents(relevant_chunks, max_sources)
            
            # Step 5: Calculate total processing time
            total_processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Step 6: Store query record
            query_record = await self._store_query_record(
                user_id=user_id,
                query_text=query_text,
                query_hash=query_hash,
                response=response_text,
                confidence_score=confidence,
                relevant_chunks=relevant_chunks,
                source_documents=source_documents,
                processing_time=total_processing_time,
                embedding_time=embedding_time,
                retrieval_time=retrieval_time,
                generation_time=generation_time
            )
            
            # Step 7: Update chunk retrieval statistics
            await self._update_chunk_statistics(relevant_chunks)
            
            result = {
                'response': response_text,
                'confidence_score': confidence,
                'source_documents': source_documents,
                'legal_disclaimer': self._get_legal_disclaimer(),
                'retrieved_chunks': [
                    {
                        'chunk_id': str(chunk['chunk'].id),
                        'similarity_score': chunk['similarity_score'],
                        'document_title': chunk['document_title']
                    }
                    for chunk in relevant_chunks
                ],
                'processing_time': total_processing_time,
                'query_id': str(query_record.id),
                'status': 'success'
            }
            
            # Cache the response if caching is enabled
            if self.enable_caching:
                await self._cache_response(query_hash, result)
            
            logger.info(f"Legal query processed successfully in {total_processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Legal RAG query failed: {str(e)}")
            
            # Store failed query record
            try:
                failed_query = LegalQuery(
                    user_id=user_id,
                    query_text=query_text,
                    query_hash=LegalQuery.generate_query_hash(query_text),
                    status='failed',
                    error_message=str(e),
                    processing_time=(datetime.utcnow() - start_time).total_seconds()
                )
                db.session.add(failed_query)
                db.session.commit()
            except Exception as db_error:
                logger.error(f"Failed to store error record: {str(db_error)}")
            
            return {
                'response': "I encountered an error while processing your legal query. Please try again or contact support if the issue persists.",
                'confidence_score': 0.0,
                'source_documents': [],
                'legal_disclaimer': self._get_legal_disclaimer(),
                'error': str(e),
                'status': 'error'
            }
    
    async def _hybrid_retrieval(self, query_text: str, query_embedding: np.ndarray) -> List[Dict]:
        """
        Hybrid retrieval combining semantic and keyword search for higher accuracy
        """
        # Get all document chunks with embeddings
        chunks = db.session.query(DocumentChunk).filter(
            DocumentChunk.embedding_vector.isnot(None)
        ).join(LegalDocument).filter(
            LegalDocument.processing_status == 'completed'
        ).all()
        
        if not chunks:
            logger.warning("No processed document chunks found")
            return []
        
        # Calculate semantic similarity scores
        chunk_similarities = []
        for chunk in chunks:
            try:
                chunk_embedding = np.array(chunk.embedding_vector)
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    chunk_embedding.reshape(1, -1)
                )[0][0]
                
                # Keyword matching bonus
                keyword_bonus = self._calculate_keyword_bonus(query_text, chunk.content)
                
                # Combined score with weights
                combined_score = (similarity * 0.8) + (keyword_bonus * 0.2)
                
                chunk_similarities.append({
                    'chunk': chunk,
                    'document_title': chunk.document.title,
                    'document_filename': chunk.document.filename,
                    'similarity_score': similarity,
                    'keyword_bonus': keyword_bonus,
                    'combined_score': combined_score
                })
                
            except Exception as e:
                logger.warning(f"Error processing chunk {chunk.id}: {str(e)}")
                continue
        
        # Sort by combined score and filter by threshold
        chunk_similarities.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Filter by similarity threshold and take top-k
        relevant_chunks = [
            chunk for chunk in chunk_similarities 
            if chunk['similarity_score'] >= self.similarity_threshold
        ][:self.top_k]
        
        logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks from {len(chunks)} total chunks")
        
        return relevant_chunks
    
    def _calculate_keyword_bonus(self, query: str, content: str) -> float:
        """Calculate keyword matching bonus for hybrid retrieval"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        query_words = query_words - stop_words
        content_words = content_words - stop_words
        
        if not query_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(content_words))
        union = len(query_words.union(content_words))
        
        if union == 0:
            return 0.0
        
        jaccard_score = intersection / union
        
        # Bonus for exact phrase matches
        phrase_bonus = 0.0
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Check for exact phrase matches
        for i in range(len(query_words)):
            for j in range(i + 2, len(query_words) + 1):  # phrases of 2+ words
                phrase = ' '.join(list(query_words)[i:j])
                if phrase in content_lower:
                    phrase_bonus += 0.1
        
        return min(jaccard_score + phrase_bonus, 1.0)
    
    def _prepare_context(self, relevant_chunks: List[Dict]) -> str:
        """Prepare context from relevant chunks with smart truncation"""
        context_parts = []
        current_length = 0
        
        for chunk_data in relevant_chunks:
            chunk = chunk_data['chunk']
            document_title = chunk_data['document_title']
            
            # Format chunk with source information
            chunk_text = f"[Source: {document_title}]\n{chunk.content}\n"
            
            # Check if adding this chunk would exceed max context length
            if current_length + len(chunk_text) > self.max_context_length:
                # Truncate the chunk to fit
                remaining_space = self.max_context_length - current_length
                if remaining_space > 100:  # Only add if we have meaningful space
                    truncated_text = chunk_text[:remaining_space-3] + "..."
                    context_parts.append(truncated_text)
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "\n---\n".join(context_parts)
    
    async def _generate_legal_response(self, 
                                     query: str, 
                                     context: str, 
                                     relevant_chunks: List[Dict]) -> Tuple[str, float]:
        """Generate legal response using Ollama with structured prompting"""
        
        # Create specialized legal prompt
        prompt = f"""You are an expert HR legal consultant specializing in Indian employment law and HR compliance. 
Provide accurate, detailed legal guidance based ONLY on the provided legal documents.

CONTEXT FROM LEGAL DOCUMENTS:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Provide a comprehensive answer based ONLY on the information in the provided legal documents
2. Include specific legal provisions, sections, or case references when available
3. Structure your response clearly with headings if appropriate
4. If the legal documents don't contain sufficient information to answer the question, clearly state this
5. Include practical HR implementation guidance when relevant
6. Cite specific sources from the provided documents

IMPORTANT LEGAL GUIDELINES:
- Only reference information explicitly present in the provided legal documents
- Do not make assumptions or provide general legal advice not supported by the sources
- If information is incomplete, recommend consulting with qualified legal counsel
- Focus on Indian employment law and HR compliance context

Provide your response in the following format:

**Legal Analysis:**
[Your detailed legal analysis based on the provided documents]

**Key Legal Provisions:**
[List specific legal provisions or sections referenced]

**HR Implementation Guidance:**
[Practical steps for HR teams if applicable]

**Sources Referenced:**
[List the specific sources used in your analysis]

**Limitations:**
[Note any limitations in the available information or areas requiring further legal consultation]

Response:"""

        try:
            async with OllamaService() as ollama:
                response = await ollama.generate(
                    prompt=prompt,
                    temperature=0.2,  # Lower temperature for more consistent legal advice
                    max_tokens=2000
                )
            
            # Calculate confidence based on response quality and source coverage
            confidence = self._calculate_response_confidence(response, relevant_chunks, query)
            
            return response.strip(), confidence
            
        except Exception as e:
            logger.error(f"Failed to generate legal response: {str(e)}")
            return (
                "I apologize, but I encountered an error while generating a response to your legal query. "
                "Please try again or consult with qualified legal counsel for urgent matters.",
                0.0
            )
    
    def _calculate_response_confidence(self, 
                                     response: str, 
                                     relevant_chunks: List[Dict], 
                                     query: str) -> float:
        """Calculate confidence score for the generated response"""
        confidence_factors = []
        
        # Factor 1: Number of high-quality sources (0-40 points)
        high_quality_sources = len([c for c in relevant_chunks if c['similarity_score'] > 0.8])
        source_score = min(high_quality_sources * 10, 40)
        confidence_factors.append(source_score)
        
        # Factor 2: Response length and structure (0-20 points)
        response_length = len(response.split())
        if response_length > 100:
            length_score = 20
        elif response_length > 50:
            length_score = 15
        elif response_length > 20:
            length_score = 10
        else:
            length_score = 5
        confidence_factors.append(length_score)
        
        # Factor 3: Presence of structured elements (0-20 points)
        structure_indicators = ['**', 'Legal Analysis', 'Key Legal', 'Sources', 'Implementation']
        structure_score = sum(5 for indicator in structure_indicators if indicator in response)
        structure_score = min(structure_score, 20)
        confidence_factors.append(structure_score)
        
        # Factor 4: Coverage of query terms (0-20 points)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        query_words = query_words - stop_words
        
        if query_words:
            coverage = len(query_words.intersection(response_words)) / len(query_words)
            coverage_score = coverage * 20
        else:
            coverage_score = 10
        confidence_factors.append(coverage_score)
        
        # Normalize to 0-1 scale
        total_score = sum(confidence_factors)
        confidence = min(total_score / 100.0, 1.0)
        
        return round(confidence, 3)
    
    def _prepare_source_documents(self, relevant_chunks: List[Dict], max_sources: int) -> List[Dict]:
        """Prepare source document information for response"""
        # Group chunks by document
        documents = {}
        for chunk_data in relevant_chunks:
            chunk = chunk_data['chunk']
            doc_id = str(chunk.document.id)
            
            if doc_id not in documents:
                documents[doc_id] = {
                    'document_id': doc_id,
                    'title': chunk_data['document_title'],
                    'filename': chunk_data['document_filename'],
                    'document_type': chunk.document.document_type.value if chunk.document.document_type else 'other',
                    'chunks_referenced': 0,
                    'highest_similarity': 0.0,
                    'relevant_sections': []
                }
            
            documents[doc_id]['chunks_referenced'] += 1
            documents[doc_id]['highest_similarity'] = max(
                documents[doc_id]['highest_similarity'],
                chunk_data['similarity_score']
            )
            
            # Add relevant section info
            if chunk.doc_metadata and 'section' in str(chunk.doc_metadata):
                section_info = str(chunk.doc_metadata)
                if section_info not in documents[doc_id]['relevant_sections']:
                    documents[doc_id]['relevant_sections'].append(section_info)
        
        # Sort by relevance and limit to max_sources
        sorted_docs = sorted(
            documents.values(),
            key=lambda x: (x['chunks_referenced'], x['highest_similarity']),
            reverse=True
        )
        
        return sorted_docs[:max_sources]
    
    def _get_legal_disclaimer(self) -> str:
        """Get standard legal disclaimer"""
        return (
            "⚠️ LEGAL DISCLAIMER: This response is generated by AI based on legal documents and is for informational purposes only. "
            "It does not constitute legal advice and should not be relied upon as a substitute for consultation with qualified legal counsel. "
            "For specific legal matters, always consult with a licensed attorney familiar with current Indian employment law and your specific circumstances."
        )
    
    async def _store_query_record(self, **kwargs) -> LegalQuery:
        """Store query record in database"""
        try:
            query_record = LegalQuery(
                user_id=kwargs['user_id'],
                query_text=kwargs['query_text'],
                query_hash=kwargs['query_hash'],
                response=kwargs['response'],
                confidence_score=kwargs['confidence_score'],
                retrieved_chunks=[
                    {
                        'chunk_id': str(chunk['chunk'].id),
                        'similarity_score': chunk['similarity_score'],
                        'document_title': chunk['document_title']
                    }
                    for chunk in kwargs['relevant_chunks']
                ],
                source_documents=kwargs['source_documents'],
                total_context_length=len(kwargs.get('context', '')),
                processing_time=kwargs['processing_time'],
                embedding_time=kwargs['embedding_time'],
                retrieval_time=kwargs['retrieval_time'],
                generation_time=kwargs['generation_time'],
                status='completed'
            )
            
            db.session.add(query_record)
            db.session.commit()
            
            return query_record
            
        except Exception as e:
            logger.error(f"Failed to store query record: {str(e)}")
            db.session.rollback()
            raise
    
    async def _update_chunk_statistics(self, relevant_chunks: List[Dict]):
        """Update retrieval statistics for chunks"""
        try:
            for chunk_data in relevant_chunks:
                chunk = chunk_data['chunk']
                chunk.retrieval_count = (chunk.retrieval_count or 0) + 1
                chunk.last_retrieved_at = datetime.utcnow()
                
                # Update document query statistics
                document = chunk.document
                document.query_count = (document.query_count or 0) + 1
                document.last_queried_at = datetime.utcnow()
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update chunk statistics: {str(e)}")
            db.session.rollback()
    
    async def _get_cached_response(self, query_hash: str) -> Optional[Dict]:
        """Get cached response if available and not expired"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.cache_ttl)
            
            cached_query = LegalQuery.query.filter(
                LegalQuery.query_hash == query_hash,
                LegalQuery.created_at > cutoff_time,
                LegalQuery.status == 'completed'
            ).order_by(LegalQuery.created_at.desc()).first()
            
            if cached_query:
                return {
                    'response': cached_query.response,
                    'confidence_score': cached_query.confidence_score,
                    'source_documents': cached_query.source_documents,
                    'legal_disclaimer': self._get_legal_disclaimer(),
                    'retrieved_chunks': cached_query.retrieved_chunks,
                    'processing_time': cached_query.processing_time,
                    'query_id': str(cached_query.id),
                    'status': 'cached'
                }
            
        except Exception as e:
            logger.error(f"Error retrieving cached response: {str(e)}")
        
        return None
    
    async def _cache_response(self, query_hash: str, response: Dict):
        """Cache response for future use (this is handled by storing in database)"""
        # Response is automatically cached by storing in LegalQuery table
        pass
    
    async def get_knowledge_base_stats(self) -> Dict:
        """Get statistics about the legal knowledge base"""
        try:
            total_documents = LegalDocument.query.count()
            processed_documents = LegalDocument.query.filter(
                LegalDocument.processing_status == 'completed'
            ).count()
            total_chunks = DocumentChunk.query.count()
            total_queries = LegalQuery.query.count()
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_queries = LegalQuery.query.filter(
                LegalQuery.created_at > thirty_days_ago
            ).count()
            
            # Average confidence score
            avg_confidence = db.session.query(
                db.func.avg(LegalQuery.confidence_score)
            ).filter(
                LegalQuery.confidence_score.isnot(None)
            ).scalar() or 0.0
            
            # Top queried documents
            top_documents = db.session.query(
                LegalDocument.title,
                LegalDocument.query_count
            ).filter(
                LegalDocument.query_count > 0
            ).order_by(LegalDocument.query_count.desc()).limit(5).all()
            
            return {
                'total_documents': total_documents,
                'processed_documents': processed_documents,
                'total_chunks': total_chunks,
                'total_queries': total_queries,
                'recent_queries_30d': recent_queries,
                'average_confidence': round(avg_confidence, 3),
                'processing_rate': round(processed_documents / max(total_documents, 1), 3),
                'top_queried_documents': [
                    {'title': title, 'query_count': count}
                    for title, count in top_documents
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {str(e)}")
            return {
                'error': str(e),
                'total_documents': 0,
                'processed_documents': 0,
                'total_chunks': 0
            }
