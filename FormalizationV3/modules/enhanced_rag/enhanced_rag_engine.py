"""
Enhanced RAG Engine - Railway Compatible
=======================================

Advanced RAG engine with intelligent AI routing, caching, and enhanced performance.
Built for dynamic initialization on Railway platform.
"""

import logging
import time
import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
import faiss

logger = logging.getLogger(__name__)

class EnhancedRAGEngine:
    """Enhanced RAG engine with agentic capabilities and intelligent AI routing."""
    
    def __init__(self, 
                 ai_provider=None,
                 legal_documents_path: str = "legal_documents",
                 vector_db_path: str = "vector_db",
                 auto_initialize: bool = True,
                 enable_smart_routing: bool = True):
        """
        Initialize the enhanced RAG engine for Railway deployment.
        
        Args:
            ai_provider: AI provider instance for text generation
            legal_documents_path: Path to legal documents directory
            vector_db_path: Path for vector database storage
            auto_initialize: Whether to automatically initialize components
            enable_smart_routing: Whether to enable intelligent AI provider routing
        """
        self.ai_provider = ai_provider
        self.legal_documents_path = legal_documents_path
        self.vector_db_path = vector_db_path
        self.enable_smart_routing = enable_smart_routing
        
        # Initialize components with Railway-compatible paths
        self.vector_store = None
        self.documents = []
        self.embeddings_cache = {}
        
        # Initialize multi-provider AI if smart routing is enabled
        self.multi_ai_processor = None
        if enable_smart_routing:
            try:
                from ..enhanced_ai.multi_provider_ai import MultiProviderAI
                self.multi_ai_processor = MultiProviderAI()
                logger.info("Smart AI routing enabled")
            except ImportError:
                logger.warning("Multi-provider AI not available, using single provider")
                self.enable_smart_routing = False
        
        # System state
        self.is_initialized = False
        self.initialization_error = None
        
        # Enhanced performance tracking
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_query_time": 0.0,
            "cache_hits": 0,
            "vector_searches": 0,
            "ai_provider_switches": 0,
            "fallback_requests": 0,
            "query_complexity_distribution": {
                "simple": 0,
                "medium": 0,
                "complex": 0
            }
        }
        
        # Response caching
        self.response_cache = {}
        self.cache_ttl = 1800  # 30 minutes
        
        # Auto-initialize if requested
        if auto_initialize:
            self.initialize()
    
    def initialize(self) -> bool:
        """Initialize the RAG engine and load knowledge base for Railway."""
        try:
            logger.info("Initializing Enhanced RAG Engine for Railway...")
            start_time = time.time()
            
            # Initialize FAISS vector store
            if not self._initialize_vector_store():
                logger.warning("FAISS initialization failed, continuing with basic functionality")
            
            # Load legal documents
            if not self._load_legal_documents():
                logger.warning("No legal documents found, RAG functionality will be limited")
            
            # Build vector index if documents are available
            if self.documents and self.vector_store:
                logger.info("Building FAISS index from legal documents...")
                if not self._build_vector_index():
                    logger.warning("Failed to build vector index")
            
            # Verify AI provider
            if not self.ai_provider:
                logger.warning("No AI provider configured - responses will be limited")
            
            initialization_time = time.time() - start_time
            logger.info(f"Enhanced RAG engine initialized successfully in {initialization_time:.2f}s")
            logger.info(f"Loaded {len(self.documents)} document chunks")
            
            self.is_initialized = True
            self.initialization_error = None
            return True
            
        except Exception as e:
            error_msg = f"Enhanced RAG engine initialization failed: {e}"
            logger.error(error_msg)
            self.initialization_error = str(e)
            self.is_initialized = False
            return False
    
    def _initialize_vector_store(self) -> bool:
        """Initialize FAISS vector store with Railway compatibility."""
        try:
            import faiss
            import numpy as np
            
            # Create vector store with Railway-compatible setup
            self.embedding_dimension = 384  # sentence-transformers/all-MiniLM-L6-v2
            self.vector_index = faiss.IndexFlatIP(self.embedding_dimension)
            self.document_metadata = []
            
            logger.info("FAISS vector store initialized")
            return True
            
        except ImportError:
            logger.error("FAISS not available - install with: pip install faiss-cpu")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            return False
    
    def _load_legal_documents(self) -> bool:
        """Load legal documents from the legal_documents directory."""
        try:
            documents_path = Path(self.legal_documents_path)
            if not documents_path.exists():
                logger.warning(f"Legal documents path not found: {self.legal_documents_path}")
                return False
            
            self.documents = []
            document_count = 0
            
            # Load all .txt files from legal_documents directory
            for doc_file in documents_path.glob("*.txt"):
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if content.strip():
                        # Split document into chunks for better retrieval
                        chunks = self._split_document(content, doc_file.name)
                        self.documents.extend(chunks)
                        document_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to load document {doc_file}: {e}")
            
            logger.info(f"Loaded {len(self.documents)} chunks from {document_count} legal documents")
            return len(self.documents) > 0
            
        except Exception as e:
            logger.error(f"Failed to load legal documents: {e}")
            return False
    
    def _split_document(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Split document into manageable chunks for vector indexing."""
        chunks = []
        
        # Simple chunking strategy - split by paragraphs and keep reasonable size
        paragraphs = content.split('\n\n')
        current_chunk = ""
        chunk_id = 0
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > 1000:  # Max chunk size
                if current_chunk.strip():
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': {
                            'source': filename,
                            'chunk_id': chunk_id,
                            'type': 'legal_document'
                        }
                    })
                    chunk_id += 1
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': {
                    'source': filename,
                    'chunk_id': chunk_id,
                    'type': 'legal_document'
                }
            })
        
        return chunks
    
    def _build_vector_index(self) -> bool:
        """Build FAISS vector index from loaded documents."""
        try:
            if not self.documents:
                return False
            
            # Initialize sentence transformer for embeddings
            from sentence_transformers import SentenceTransformer
            
            # Use a lightweight model suitable for Railway
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Generate embeddings for all document chunks
            texts = [doc['content'] for doc in self.documents]
            embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
            
            # Add embeddings to FAISS index
            import numpy as np
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)
            
            # Add to index
            self.vector_index.add(embeddings_array)
            
            # Store metadata
            self.document_metadata = [doc['metadata'] for doc in self.documents]
            
            logger.info(f"Built FAISS index with {len(texts)} document chunks")
            return True
            
        except ImportError:
            logger.error("sentence-transformers not available - install with: pip install sentence-transformers")
            return False
        except Exception as e:
            logger.error(f"Failed to build vector index: {e}")
            return False
    
    def query(self, 
              query_text: str,
              max_results: int = 5,
              similarity_threshold: float = 0.7,
              enable_caching: bool = True) -> Dict[str, Any]:
        """
        Process a legal query using the enhanced RAG engine.
        
        Args:
            query_text: The legal query to process
            max_results: Maximum number of results to retrieve
            similarity_threshold: Minimum similarity threshold for results
            enable_caching: Whether to use response caching
            
        Returns:
            Complete response with content, metadata, and source documents
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # Check initialization
            if not self.is_initialized:
                if not self.initialize():
                    raise Exception(f"RAG engine not initialized: {self.initialization_error}")
            
            # Validate inputs
            if not query_text.strip():
                raise ValueError("Empty query provided")
            
            logger.info(f"Processing enhanced query: {query_text[:100]}...")
            
            # Check cache first
            cache_key = self._get_cache_key(query_text, max_results, similarity_threshold)
            if enable_caching and cache_key in self.response_cache:
                cache_entry = self.response_cache[cache_key]
                if self._is_cache_valid(cache_entry):
                    self.stats["cache_hits"] += 1
                    logger.info("Cache hit - returning cached response")
                    return cache_entry['response']
                else:
                    del self.response_cache[cache_key]
            
            # Analyze query complexity for AI routing
            query_complexity = self._analyze_query_complexity(query_text)
            self.stats["query_complexity_distribution"][query_complexity] += 1
            
            # Step 1: Retrieve relevant documents
            retrieved_docs = self._retrieve_documents(query_text, max_results, similarity_threshold)
            self.stats["vector_searches"] += 1
            
            # Step 2: Select optimal AI provider if smart routing is enabled
            if self.enable_smart_routing and self.multi_ai_processor:
                self._select_optimal_ai_provider(query_complexity)
            
            # Step 3: Generate enhanced response
            response = self._generate_enhanced_response(query_text, retrieved_docs, query_complexity)
            
            # Cache response
            if enable_caching:
                self.response_cache[cache_key] = {
                    'response': response,
                    'timestamp': time.time(),
                    'complexity': query_complexity
                }
            
            # Update performance stats
            query_time = time.time() - start_time
            self._update_query_stats(True, query_time)
            
            logger.info(f"Enhanced query processed successfully in {query_time:.2f}s "
                       f"(confidence: {response.get('confidence_score', 0.0):.2f}, "
                       f"complexity: {query_complexity})")
            
            return response
            
        except Exception as e:
            query_time = time.time() - start_time
            self._update_query_stats(False, query_time)
            logger.error(f"Enhanced query processing failed: {e}")
            
            # Try fallback if smart routing is enabled
            if self.enable_smart_routing and self.multi_ai_processor:
                try:
                    logger.info("Attempting fallback with different AI provider...")
                    self.stats["fallback_requests"] += 1
                    fallback_response = self._generate_fallback_response(query_text, str(e))
                    return fallback_response
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
            
            # Return error response
            return self._create_error_response(query_text, str(e))
    
    def _analyze_query_complexity(self, query: str) -> str:
        """Analyze query complexity for AI provider selection."""
        if self.enable_smart_routing and self.multi_ai_processor:
            # Use multi-provider AI analysis if available
            return self.multi_ai_processor.analyze_query_complexity(query)
        else:
            # Simple fallback complexity analysis
            word_count = len(query.split())
            legal_keywords = ['section', 'act', 'clause', 'regulation', 'compliance', 'legal', 'law']
            keyword_count = sum(1 for word in query.lower().split() if word in legal_keywords)
            
            if word_count > 200 or keyword_count > 5:
                return 'complex'
            elif word_count > 50 or keyword_count > 2:
                return 'medium'
            else:
                return 'simple'
    
    def _select_optimal_ai_provider(self, query_complexity: str):
        """Select optimal AI provider based on query complexity."""
        if not self.multi_ai_processor:
            return
        
        try:
            best_provider = self.multi_ai_processor.get_best_provider_for_complexity(query_complexity)
            if best_provider and best_provider != self.multi_ai_processor.current_provider_name:
                self.multi_ai_processor.switch_provider(best_provider)
                self.stats["ai_provider_switches"] += 1
                logger.info(f"Switched to optimal AI provider: {best_provider}")
                
        except Exception as e:
            logger.warning(f"Failed to select optimal AI provider: {e}")
    
    def _retrieve_documents(self, query_text: str, max_results: int, similarity_threshold: float) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using FAISS vector search."""
        try:
            if not hasattr(self, 'vector_index') or not self.documents:
                logger.warning("Vector index not available, returning empty results")
                return []
            
            # Generate query embedding
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            query_embedding = model.encode([query_text])
            
            # Normalize query embedding
            import faiss
            import numpy as np
            query_embedding = np.array(query_embedding).astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Search vector index
            scores, indices = self.vector_index.search(query_embedding, max_results * 2)  # Get more to filter
            
            # Filter by similarity threshold and format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents) and score >= similarity_threshold:
                    results.append({
                        'content': self.documents[idx]['content'],
                        'metadata': self.documents[idx]['metadata'],
                        'similarity_score': float(score)
                    })
            
            # Limit to max_results
            results = results[:max_results]
            
            logger.debug(f"Retrieved {len(results)} relevant documents")
            return results
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []
    
    def _generate_enhanced_response(self, query_text: str, retrieved_docs: List[Dict[str, Any]], query_complexity: str) -> Dict[str, Any]:
        """Generate enhanced response using retrieved context and AI provider."""
        try:
            # Determine which AI provider to use
            if self.enable_smart_routing and self.multi_ai_processor:
                ai_provider = self.multi_ai_processor
            else:
                ai_provider = self.ai_provider
            
            if not ai_provider:
                # Fallback to basic response without AI
                return self._generate_basic_response(query_text, retrieved_docs)
            
            # Prepare context from retrieved documents
            context = self._prepare_context(retrieved_docs)
            
            # Create enhanced prompt
            prompt = self._create_enhanced_prompt(query_text, context, query_complexity)
            
            # Generate response using AI provider
            if hasattr(ai_provider, 'generate_with_config'):
                # Use enhanced multi-provider AI
                ai_response = ai_provider.generate_with_config(
                    prompt, 
                    format_json=True,
                    max_tokens=1000,
                    temperature=0.7
                )
            else:
                # Use basic AI provider
                ai_response = ai_provider.generate_text(prompt)
            
            # Parse and enhance response
            if isinstance(ai_response, dict):
                content = ai_response.get('content', ai_response.get('response', ''))
                confidence = ai_response.get('confidence_score', 0.8)
            else:
                content = str(ai_response)
                confidence = 0.7
            
            # Create comprehensive response
            response = {
                'content': content,
                'confidence_score': confidence,
                'source_documents': retrieved_docs,
                'query_complexity': query_complexity,
                'processing_metadata': {
                    'ai_provider': str(type(ai_provider).__name__),
                    'documents_used': len(retrieved_docs),
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Enhanced response generation failed: {e}")
            return self._generate_basic_response(query_text, retrieved_docs)
    
    def _prepare_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Prepare context string from retrieved documents."""
        if not retrieved_docs:
            return "No relevant legal documents found."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs[:3]):  # Limit to top 3 for context length
            source = doc['metadata'].get('source', 'Unknown')
            content = doc['content'][:500]  # Limit content length
            context_parts.append(f"Document {i+1} (from {source}):\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _create_enhanced_prompt(self, query_text: str, context: str, query_complexity: str) -> str:
        """Create enhanced prompt for AI generation."""
        complexity_instructions = {
            'simple': "Provide a clear and concise answer.",
            'medium': "Provide a comprehensive answer with relevant details and examples.",
            'complex': "Provide a detailed analysis with multiple perspectives, legal precedents, and practical implications."
        }
        
        instruction = complexity_instructions.get(query_complexity, "Provide a helpful answer.")
        
        prompt = f"""
You are an expert HR legal consultant. Based on the provided legal documents and your expertise, please answer the following query.

Query: {query_text}

Relevant Legal Context:
{context}

Instructions: {instruction}

Please format your response as JSON with the following structure:
{{
    "content": "Your detailed answer here",
    "confidence_score": 0.8,
    "key_legal_points": ["point1", "point2"],
    "recommendations": ["recommendation1", "recommendation2"]
}}

Ensure your answer is accurate, professional, and includes appropriate legal disclaimers when necessary.
"""
        return prompt
    
    def _generate_basic_response(self, query_text: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate basic response when AI provider is not available."""
        if retrieved_docs:
            content = f"Based on the available legal documents, here are relevant excerpts for your query '{query_text}':\n\n"
            for i, doc in enumerate(retrieved_docs[:2]):
                content += f"{i+1}. From {doc['metadata'].get('source', 'Legal Document')}:\n"
                content += f"{doc['content'][:300]}...\n\n"
            content += "For specific legal advice, please consult with a qualified legal professional."
        else:
            content = f"I couldn't find specific legal documents related to your query '{query_text}'. Please consult with a qualified legal professional for accurate guidance."
        
        return {
            'content': content,
            'confidence_score': 0.5,
            'source_documents': retrieved_docs,
            'query_complexity': 'unknown',
            'processing_metadata': {
                'ai_provider': 'basic_fallback',
                'documents_used': len(retrieved_docs),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    
    def _generate_fallback_response(self, query_text: str, original_error: str) -> Dict[str, Any]:
        """Generate response using fallback AI providers."""
        if not self.multi_ai_processor:
            raise Exception("No fallback available")
        
        try:
            fallback_prompt = f"""
            Legal Query: {query_text}
            
            Please provide a helpful legal response. If specific legal documents 
            are not available, provide general guidance and recommend consulting 
            with legal professionals.
            
            Format as JSON with 'content' and 'confidence_score' fields.
            """
            
            fallback_result = self.multi_ai_processor.generate_with_fallback(
                fallback_prompt, format_json=True, max_retries=3
            )
            
            # Create response from fallback result
            content = fallback_result.get('content', fallback_result.get('response', 'Unable to process query'))
            confidence = fallback_result.get('confidence_score', 0.5)
            
            return {
                'content': content,
                'confidence_score': confidence,
                'source_documents': [],
                'query_complexity': 'fallback',
                'processing_metadata': {
                    'ai_provider': 'fallback_provider',
                    'documents_used': 0,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'original_error': original_error
                }
            }
            
        except Exception as e:
            raise Exception(f"Fallback generation failed: {e}")
    
    def _create_error_response(self, query_text: str, error_msg: str) -> Dict[str, Any]:
        """Create error response when processing fails."""
        error_content = (
            f"I apologize, but I encountered an error while processing your legal query. "
            f"Error: {error_msg}\n\n"
            f"Please try:\n"
            f"• Rephrasing your question\n"
            f"• Being more specific about your requirements\n"
            f"• Checking if the system is properly configured\n"
            f"• Contacting support if the issue persists"
        )
        
        return {
            'content': error_content,
            'confidence_score': 0.0,
            'source_documents': [],
            'query_complexity': 'error',
            'processing_metadata': {
                'ai_provider': 'error_handler',
                'documents_used': 0,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'error': error_msg
            }
        }
    
    def _get_cache_key(self, query: str, max_results: int, similarity_threshold: float) -> str:
        """Generate cache key for response caching."""
        content = f"{query}_{max_results}_{similarity_threshold}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        return (time.time() - cache_entry['timestamp']) < self.cache_ttl
    
    def _update_query_stats(self, success: bool, query_time: float):
        """Update query performance statistics."""
        if success:
            self.stats["successful_queries"] += 1
        else:
            self.stats["failed_queries"] += 1
        
        # Update average query time
        total_queries = self.stats["successful_queries"] + self.stats["failed_queries"]
        current_avg = self.stats["average_query_time"]
        self.stats["average_query_time"] = ((current_avg * (total_queries - 1)) + query_time) / total_queries
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "is_initialized": self.is_initialized,
            "initialization_error": self.initialization_error,
            "ai_provider_available": self.ai_provider is not None,
            "multi_provider_available": self.multi_ai_processor is not None,
            "documents_loaded": len(self.documents),
            "vector_index_ready": hasattr(self, 'vector_index'),
            "engine_stats": self.stats,
            "cache_stats": {
                "cache_size": len(self.response_cache),
                "cache_ttl_seconds": self.cache_ttl,
                "cache_hit_rate": self.stats["cache_hits"] / max(self.stats["total_queries"], 1)
            },
            "system_info": {
                "legal_documents_path": self.legal_documents_path,
                "vector_db_path": self.vector_db_path,
                "smart_routing_enabled": self.enable_smart_routing
            }
        }
    
    def clear_cache(self):
        """Clear all caches."""
        self.response_cache.clear()
        self.embeddings_cache.clear()
        
        if self.multi_ai_processor:
            try:
                self.multi_ai_processor.clear_cache()
            except:
                pass
        
        logger.info("All caches cleared")
    
    def add_ai_provider(self, provider_type: str, model: str, api_key: str = None, **kwargs):
        """Add AI provider to the multi-provider system."""
        if not self.enable_smart_routing:
            logger.warning("Smart routing not enabled")
            return False
        
        if not self.multi_ai_processor:
            try:
                from ..enhanced_ai.multi_provider_ai import MultiProviderAI
                self.multi_ai_processor = MultiProviderAI()
            except ImportError:
                logger.error("Multi-provider AI not available")
                return False
        
        try:
            return self.multi_ai_processor.add_provider(provider_type, model, api_key, **kwargs)
        except Exception as e:
            logger.error(f"Failed to add AI provider: {e}")
            return False
