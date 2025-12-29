"""
Enhanced RAG Engine
==================

Main RAG engine that orchestrates vector retrieval, AI generation,
and response customization for legal queries with intelligent AI routing.
"""

import logging
import time
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from .config import AgenticRAGConfig, LegalQueryContext, LegalResponse
from .vector_store import LegalVectorStore
from .legal_knowledge import LegalKnowledgeBase
from .response_generator import ResponseController
from .agent_controller import LegalAgent

logger = logging.getLogger(__name__)

class EnhancedRAGEngine:
    """Enhanced RAG engine with agentic capabilities and intelligent AI routing."""
    
    def __init__(self, 
                 ai_provider=None,
                 vector_db_path: str = "hr_legal/vector_db",
                 hrlaw_path: str = "../HRlaw",
                 auto_initialize: bool = True,
                 enable_smart_routing: bool = True):
        """
        Initialize the enhanced RAG engine.
        
        Args:
            ai_provider: AI provider instance for text generation
            vector_db_path: Path for vector database storage
            hrlaw_path: Path to HRLaw folder with legal documents
            auto_initialize: Whether to automatically initialize components
            enable_smart_routing: Whether to enable intelligent AI provider routing
        """
        self.ai_provider = ai_provider
        self.vector_db_path = vector_db_path
        self.hrlaw_path = hrlaw_path
        self.enable_smart_routing = enable_smart_routing
        
        # Initialize components
        self.vector_store = LegalVectorStore(vector_db_path)
        self.knowledge_base = LegalKnowledgeBase(hrlaw_path)
        self.response_controller = ResponseController(ai_provider)
        self.agent = LegalAgent(self)
        
        # Initialize multi-provider AI if smart routing is enabled
        self.multi_ai_processor = None
        if enable_smart_routing:
            try:
                from ..multi_provider_ai import EnhancedMultiProviderAI
                self.multi_ai_processor = EnhancedMultiProviderAI()
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
        """Initialize the RAG engine and load knowledge base."""
        try:
            logger.info("Initializing Enhanced RAG Engine...")
            start_time = time.time()
            
            # Check if HRLaw path exists
            if not Path(self.hrlaw_path).exists():
                logger.warning(f"HRLaw path not found: {self.hrlaw_path}")
                logger.info("RAG engine will work with limited functionality")
                self.is_initialized = True
                return True
            
            # Load legal documents
            logger.info("Loading legal knowledge base...")
            if not self.knowledge_base.load_legal_documents():
                raise Exception("Failed to load legal documents")
            
            # Initialize or load vector store
            logger.info("Initializing vector store...")
            if not self.vector_store.load_or_create_index():
                raise Exception("Failed to initialize vector store")
            
            # Check if we need to build the vector index
            if not self.vector_store.is_loaded or len(self.vector_store.documents) == 0:
                logger.info("Building vector index from legal documents...")
                documents, metadata = self.knowledge_base.get_documents_and_metadata()
                
                if documents:
                    if not self.vector_store.add_documents(documents, metadata):
                        raise Exception("Failed to add documents to vector store")
                    
                    # Save the index
                    if not self.vector_store.save_index():
                        logger.warning("Failed to save vector index")
                else:
                    logger.warning("No documents found to index")
            
            # Verify AI provider
            if not self.ai_provider:
                logger.warning("No AI provider configured - responses will be limited")
            
            initialization_time = time.time() - start_time
            logger.info(f"RAG engine initialized successfully in {initialization_time:.2f}s")
            logger.info(f"Loaded {len(self.vector_store.documents)} document chunks")
            
            self.is_initialized = True
            self.initialization_error = None
            return True
            
        except Exception as e:
            error_msg = f"RAG engine initialization failed: {e}"
            logger.error(error_msg)
            self.initialization_error = str(e)
            self.is_initialized = False
            return False
    
    def query(self, 
              query_context: LegalQueryContext, 
              config: AgenticRAGConfig) -> LegalResponse:
        """
        Process a legal query using the RAG engine with intelligent AI routing.
        
        Args:
            query_context: Context information for the query
            config: Configuration for response generation
            
        Returns:
            Complete legal response
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # Check initialization
            if not self.is_initialized:
                if not self.initialize():
                    raise Exception(f"RAG engine not initialized: {self.initialization_error}")
            
            # Validate inputs
            if not query_context.query.strip():
                raise ValueError("Empty query provided")
            
            logger.info(f"Processing query: {query_context.query[:100]}...")
            
            # Check cache first
            cache_key = self._get_cache_key(query_context.query, config)
            if config.enable_caching and cache_key in self.response_cache:
                cache_entry = self.response_cache[cache_key]
                if self._is_cache_valid(cache_entry):
                    self.stats["cache_hits"] += 1
                    logger.info("Cache hit - returning cached response")
                    return cache_entry['response']
                else:
                    del self.response_cache[cache_key]
            
            # Analyze query complexity for AI routing
            query_complexity = self._analyze_query_complexity(query_context.query)
            self.stats["query_complexity_distribution"][query_complexity] += 1
            
            # Step 1: Retrieve relevant documents
            retrieved_docs = self._retrieve_documents(query_context.query, config)
            self.stats["vector_searches"] += 1
            
            # Step 2: Select optimal AI provider if smart routing is enabled
            if self.enable_smart_routing and self.multi_ai_processor:
                self._select_optimal_ai_provider(query_complexity, config)
            
            # Step 3: Generate response using retrieved context
            response = self._generate_enhanced_response(
                query_context, retrieved_docs, config, query_complexity
            )
            
            # Step 4: Post-process and validate
            if config.response_validation:
                response = self._validate_response(response, config)
            
            # Cache response
            if config.enable_caching:
                self.response_cache[cache_key] = {
                    'response': response,
                    'timestamp': time.time(),
                    'complexity': query_complexity
                }
            
            # Update performance stats
            query_time = time.time() - start_time
            self._update_query_stats(True, query_time)
            
            logger.info(f"Query processed successfully in {query_time:.2f}s "
                       f"(confidence: {response.metadata.confidence_score:.2f}, "
                       f"complexity: {query_complexity})")
            
            return response
            
        except Exception as e:
            query_time = time.time() - start_time
            self._update_query_stats(False, query_time)
            logger.error(f"Query processing failed: {e}")
            
            # Try fallback if smart routing is enabled
            if self.enable_smart_routing and self.multi_ai_processor:
                try:
                    logger.info("Attempting fallback with different AI provider...")
                    self.stats["fallback_requests"] += 1
                    fallback_response = self._generate_fallback_response(query_context, config, str(e))
                    return fallback_response
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
            
            # Return error response
            return self._create_error_response(query_context, config, str(e))
    
    def _analyze_query_complexity(self, query: str) -> str:
        """Analyze query complexity for AI provider selection."""
        if self.enable_smart_routing and self.multi_ai_processor:
            return self.multi_ai_processor.analyze_query_complexity(query)
        else:
            # Simple fallback complexity analysis
            word_count = len(query.split())
            if word_count > 200:
                return 'complex'
            elif word_count > 50:
                return 'medium'
            else:
                return 'simple'
    
    def _select_optimal_ai_provider(self, query_complexity: str, config: AgenticRAGConfig):
        """Select optimal AI provider based on query complexity and config."""
        if not self.multi_ai_processor:
            return
        
        # Determine priority based on config
        if hasattr(config, 'ai_priority'):
            priority = config.ai_priority
        else:
            priority = 'balanced'  # Default priority
        
        try:
            best_provider = self.multi_ai_processor.get_best_provider(query_complexity, priority)
            current_provider_name = str(type(self.multi_ai_processor.current_provider).__name__) if self.multi_ai_processor.current_provider else None
            
            if best_provider not in str(current_provider_name or ''):
                self.multi_ai_processor.current_provider = self.multi_ai_processor.providers[best_provider]
                self.stats["ai_provider_switches"] += 1
                logger.info(f"Switched to optimal AI provider: {best_provider}")
                
                # Update response controller's AI provider
                if self.response_controller:
                    self.response_controller.ai_provider = self.multi_ai_processor
                    
        except Exception as e:
            logger.warning(f"Failed to select optimal AI provider: {e}")
    
    def _generate_enhanced_response(self, 
                                  query_context: LegalQueryContext,
                                  retrieved_docs: List[Dict[str, Any]],
                                  config: AgenticRAGConfig,
                                  query_complexity: str) -> LegalResponse:
        """Generate response with enhanced AI capabilities."""
        
        # Use multi-provider AI if available, otherwise fall back to single provider
        if self.enable_smart_routing and self.multi_ai_processor:
            # Set response controller to use multi-provider AI
            original_provider = self.response_controller.ai_provider
            self.response_controller.ai_provider = self.multi_ai_processor
            
            try:
                response = self.response_controller.generate_response(
                    query_context, retrieved_docs, config
                )
                return response
            except Exception as e:
                logger.warning(f"Multi-provider AI failed, falling back: {e}")
                # Restore original provider and try again
                self.response_controller.ai_provider = original_provider
                return self.response_controller.generate_response(
                    query_context, retrieved_docs, config
                )
        else:
            return self.response_controller.generate_response(
                query_context, retrieved_docs, config
            )
    
    def _generate_fallback_response(self, 
                                  query_context: LegalQueryContext,
                                  config: AgenticRAGConfig,
                                  original_error: str) -> LegalResponse:
        """Generate response using fallback AI providers."""
        if not self.multi_ai_processor:
            raise Exception("No fallback available")
        
        try:
            # Try with fallback mechanism
            fallback_prompt = f"""
            Legal Query: {query_context.query}
            
            Please provide a helpful legal response. If specific legal documents 
            are not available, provide general guidance and recommend consulting 
            with legal professionals.
            
            Format as JSON with 'content' and 'confidence_score' fields.
            """
            
            fallback_result = self.multi_ai_processor.generate_with_fallback(
                fallback_prompt, format_json=True, max_retries=3
            )
            
            # Create response from fallback result
            from .config import ResponseMetadata
            
            content = fallback_result.get('content', fallback_result.get('response', 'Unable to process query'))
            confidence = fallback_result.get('confidence_score', 0.5)
            
            return LegalResponse(
                content=content,
                metadata=ResponseMetadata(
                    confidence_score=confidence,
                    processing_time=0.0,
                    validation_passed=True,
                    improvement_suggestions=["Response generated using fallback AI provider"]
                ),
                config_used=config,
                query_context=query_context,
                response_id=f"fallback_{int(time.time())}",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
        except Exception as e:
            raise Exception(f"Fallback generation failed: {e}")
    
    def _get_cache_key(self, query: str, config: AgenticRAGConfig) -> str:
        """Generate cache key for response caching."""
        import hashlib
        # Include relevant config parameters in cache key
        config_str = f"{config.retrieval_depth}_{config.similarity_threshold}_{config.jurisdiction_focus}"
        content = f"{query}_{config_str}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        return (time.time() - cache_entry['timestamp']) < self.cache_ttl
    
    def _retrieve_documents(self, 
                           query: str, 
                           config: AgenticRAGConfig) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using vector search."""
        try:
            # Perform vector search
            results = self.vector_store.search(
                query=query,
                k=config.retrieval_depth,
                similarity_threshold=config.similarity_threshold,
                use_cache=config.enable_caching
            )
            
            # Apply cross-referencing if enabled
            if config.cross_reference and results:
                results = self._apply_cross_referencing(results, query)
            
            # Filter by jurisdiction if specified
            if config.jurisdiction_focus != "both":
                results = self._filter_by_jurisdiction(results, config.jurisdiction_focus)
            
            logger.debug(f"Retrieved {len(results)} relevant documents")
            return results
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []
    
    def _apply_cross_referencing(self, 
                                results: List[Dict[str, Any]], 
                                query: str) -> List[Dict[str, Any]]:
        """Apply cross-referencing to find related documents."""
        # Simple implementation - could be enhanced
        cross_referenced = results.copy()
        
        # Look for related terms in top results
        if results:
            top_result = results[0]
            doc_content = top_result.get('document', '')
            
            # Extract key terms for additional search
            import re
            legal_terms = re.findall(r'(section|act|clause|rule|regulation)\\s+\\w+', 
                                   doc_content.lower())
            
            # Perform additional searches for each term
            for term in legal_terms[:3]:  # Limit to avoid too many searches
                additional_results = self.vector_store.search(
                    query=term,
                    k=2,
                    similarity_threshold=0.6
                )
                
                # Add unique results
                for result in additional_results:
                    if not any(r.get('document') == result.get('document') 
                             for r in cross_referenced):
                        cross_referenced.append(result)
        
        return cross_referenced
    
    def _filter_by_jurisdiction(self, 
                               results: List[Dict[str, Any]], 
                               jurisdiction: str) -> List[Dict[str, Any]]:
        """Filter results by jurisdiction (central vs state laws)."""
        if jurisdiction == "both":
            return results
        
        filtered = []
        for result in results:
            metadata = result.get('metadata', {})
            doc_title = metadata.get('title', '').lower()
            
            # Simple heuristic for jurisdiction detection
            if jurisdiction == "central":
                if any(term in doc_title for term in ['central', 'national', 'india', 'code']):
                    filtered.append(result)
                elif not any(term in doc_title for term in ['state', 'local', 'municipal']):
                    filtered.append(result)  # Default to central if unclear
            elif jurisdiction == "state":
                if any(term in doc_title for term in ['state', 'local', 'municipal']):
                    filtered.append(result)
        
        return filtered if filtered else results  # Return original if none match
    
    def _validate_response(self, 
                          response: LegalResponse, 
                          config: AgenticRAGConfig) -> LegalResponse:
        """Validate and potentially improve the response."""
        
        # Check minimum quality threshold
        if response.metadata.quality_score < 0.5:
            logger.warning(f"Low quality response detected: {response.metadata.quality_score}")
            
            # Add improvement note
            response.content += "\\n\\n*Note: This response may require additional verification. " \
                              "Please consult with legal professionals for critical decisions.*"
            
            response.metadata.improvement_suggestions.append(
                "Consider requesting more specific information or consulting legal experts"
            )
        
        # Validate response length against configuration
        word_count = len(response.content.split())
        if config.custom_word_count:
            target = config.custom_word_count
            if abs(word_count - target) / target > 0.5:
                response.metadata.improvement_suggestions.append(
                    f"Response length ({word_count} words) differs significantly from target ({target} words)"
                )
        
        return response
    
    def _create_error_response(self, 
                              query_context: LegalQueryContext, 
                              config: AgenticRAGConfig, 
                              error_msg: str) -> LegalResponse:
        """Create error response when processing fails."""
        from .config import ResponseMetadata
        
        error_content = (
            f"I apologize, but I encountered an error while processing your legal query. "
            f"Error: {error_msg}\\n\\n"
            f"Please try:\\n"
            f"• Rephrasing your question\\n"
            f"• Being more specific about your requirements\\n"
            f"• Checking if the system is properly configured\\n"
            f"• Contacting support if the issue persists"
        )
        
        return LegalResponse(
            content=error_content,
            metadata=ResponseMetadata(
                confidence_score=0.0,
                processing_time=0.0,
                validation_passed=False,
                improvement_suggestions=["Rephrase query", "Check system status"]
            ),
            config_used=config,
            query_context=query_context,
            response_id=f"error_{int(time.time())}",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
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
    
    def add_documents(self, 
                     documents: List[str], 
                     metadata: List[Dict[str, Any]] = None) -> bool:
        """Add new documents to the knowledge base."""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return False
            
            success = self.vector_store.add_documents(documents, metadata)
            if success:
                # Save updated index
                self.vector_store.save_index()
                logger.info(f"Added {len(documents)} new documents to knowledge base")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def rebuild_index(self) -> bool:
        """Rebuild the entire vector index."""
        try:
            logger.info("Rebuilding vector index...")
            
            # Reload knowledge base
            if not self.knowledge_base.load_legal_documents():
                raise Exception("Failed to reload legal documents")
            
            # Rebuild vector store
            if not self.vector_store.rebuild_index():
                raise Exception("Failed to rebuild vector index")
            
            # Re-add documents
            documents, metadata = self.knowledge_base.get_documents_and_metadata()
            if documents:
                if not self.vector_store.add_documents(documents, metadata):
                    raise Exception("Failed to re-add documents")
                
                # Save rebuilt index
                self.vector_store.save_index()
            
            logger.info("Vector index rebuilt successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        vector_stats = self.vector_store.get_stats() if self.vector_store else {}
        knowledge_stats = self.knowledge_base.get_knowledge_base_stats() if self.knowledge_base else {}
        agent_stats = self.agent.get_agent_stats() if self.agent else {}
        
        return {
            "is_initialized": self.is_initialized,
            "initialization_error": self.initialization_error,
            "ai_provider_available": self.ai_provider is not None,
            "vector_store": vector_stats,
            "knowledge_base": knowledge_stats,
            "agent": agent_stats,
            "engine_stats": self.stats,
            "system_info": {
                "vector_db_path": self.vector_db_path,
                "hrlaw_path": self.hrlaw_path,
                "total_documents": len(self.vector_store.documents) if self.vector_store else 0
            }
        }
    
    def clear_cache(self):
        """Clear all caches (legacy method - use clear_all_caches for enhanced clearing)."""
        self.clear_all_caches()
    
    def export_knowledge_base(self, output_path: str) -> bool:
        """Export the current knowledge base."""
        try:
            return self.knowledge_base.export_processed_documents(output_path)
        except Exception as e:
            logger.error(f"Failed to export knowledge base: {e}")
            return False
    
    def set_ai_provider(self, ai_provider):
        """Update the AI provider."""
        self.ai_provider = ai_provider
        if self.response_controller:
            self.response_controller.ai_provider = ai_provider
        logger.info("AI provider updated")
    
    def setup_multi_provider_ai(self, provider_configs: List[Dict[str, str]]):
        """Setup multiple AI providers for intelligent routing."""
        if not self.enable_smart_routing:
            logger.warning("Smart routing not enabled")
            return False
        
        if not self.multi_ai_processor:
            try:
                from ..multi_provider_ai import EnhancedMultiProviderAI
                self.multi_ai_processor = EnhancedMultiProviderAI()
            except ImportError:
                logger.error("Multi-provider AI not available")
                return False
        
        try:
            self.multi_ai_processor.set_multiple_providers(provider_configs)
            logger.info(f"Configured {len(provider_configs)} AI providers")
            return True
        except Exception as e:
            logger.error(f"Failed to setup multi-provider AI: {e}")
            return False
    
    def add_ai_provider(self, provider_type: str, model: str, api_key: str = None, **kwargs):
        """Add a single AI provider to the multi-provider system."""
        if not self.enable_smart_routing or not self.multi_ai_processor:
            logger.warning("Smart routing not available")
            return False
        
        try:
            self.multi_ai_processor.set_provider(provider_type, model, api_key, **kwargs)
            logger.info(f"Added AI provider: {provider_type} - {model}")
            return True
        except Exception as e:
            logger.error(f"Failed to add AI provider: {e}")
            return False
    
    def get_ai_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all AI providers."""
        if self.multi_ai_processor:
            return self.multi_ai_processor.get_provider_stats()
        elif self.ai_provider:
            return {"single_provider": "Active"}
        else:
            return {"no_providers": "No AI providers configured"}
    
    def clear_all_caches(self):
        """Clear all caches including AI provider caches."""
        # Clear RAG engine caches
        self.response_cache.clear()
        if self.vector_store:
            self.vector_store.clear_cache()
        if self.agent:
            self.agent.clear_conversation_memory()
        
        # Clear AI provider caches
        if self.multi_ai_processor:
            self.multi_ai_processor.clear_cache()
        
        logger.info("All caches cleared including AI provider caches")
    
    def enable_smart_ai_routing(self, enable: bool = True):
        """Enable or disable smart AI routing."""
        if enable and not self.multi_ai_processor:
            try:
                from ..multi_provider_ai import EnhancedMultiProviderAI
                self.multi_ai_processor = EnhancedMultiProviderAI()
                self.enable_smart_routing = True
                logger.info("Smart AI routing enabled")
            except ImportError:
                logger.error("Cannot enable smart routing - multi-provider AI not available")
                return False
        elif not enable:
            self.enable_smart_routing = False
            logger.info("Smart AI routing disabled")
        
        return True
    
    def get_enhanced_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including AI provider information."""
        base_status = self.get_system_status()
        
        # Add AI provider information
        base_status["ai_providers"] = {
            "smart_routing_enabled": self.enable_smart_routing,
            "multi_provider_available": self.multi_ai_processor is not None,
            "provider_stats": self.get_ai_provider_stats()
        }
        
        # Add enhanced performance metrics
        base_status["enhanced_stats"] = {
            "cache_performance": {
                "cache_size": len(self.response_cache),
                "cache_ttl_seconds": self.cache_ttl,
                "cache_hit_rate": self.stats["cache_hits"] / max(self.stats["total_queries"], 1)
            },
            "ai_routing_stats": {
                "provider_switches": self.stats["ai_provider_switches"],
                "fallback_requests": self.stats["fallback_requests"],
                "complexity_distribution": self.stats["query_complexity_distribution"]
            }
        }
        
        return base_status
