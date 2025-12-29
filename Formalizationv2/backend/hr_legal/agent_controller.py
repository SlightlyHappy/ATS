"""
Legal Agent Controller
=====================

Orchestrates intelligent decision-making for legal queries,
including query classification, multi-step reasoning, and response planning.
"""

import logging
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from .config import (
    AgenticRAGConfig, LegalQueryContext, LegalResponse,
    ResponseLength, ResponseStyle, DetailLevel
)

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """Types of query intents."""
    COMPLIANCE_CHECK = "compliance_check"
    POLICY_GUIDANCE = "policy_guidance"
    DOCUMENT_GENERATION = "document_generation"
    LEGAL_INTERPRETATION = "legal_interpretation"
    PROCEDURE_INQUIRY = "procedure_inquiry"
    GENERAL_QUESTION = "general_question"

class QueryComplexity(Enum):
    """Levels of query complexity."""
    SIMPLE = "simple"          # Direct factual question
    MODERATE = "moderate"      # Requires some analysis
    COMPLEX = "complex"        # Multi-step reasoning needed
    VERY_COMPLEX = "very_complex"  # Requires deep analysis

class LegalAgent:
    """Intelligent agent for legal query processing."""
    
    def __init__(self, rag_engine=None):
        """
        Initialize the legal agent.
        
        Args:
            rag_engine: The enhanced RAG engine instance
        """
        self.rag_engine = rag_engine
        
        # Query classification patterns
        self.intent_patterns = {
            QueryIntent.COMPLIANCE_CHECK: [
                r'(comply|compliance|compliant|violation|breach|legal)',
                r'(requirement|mandatory|obligatory|must|shall)',
                r'(audit|inspection|check|verify|validate)'
            ],
            QueryIntent.POLICY_GUIDANCE: [
                r'(policy|procedure|guideline|best practice)',
                r'(how to|what should|recommended|suggest)',
                r'(implement|establish|create|develop)'
            ],
            QueryIntent.DOCUMENT_GENERATION: [
                r'(generate|create|draft|template|format)',
                r'(contract|agreement|letter|notice|form)',
                r'(document|paperwork|filing)'
            ],
            QueryIntent.LEGAL_INTERPRETATION: [
                r'(interpret|meaning|define|explain|clarify)',
                r'(section|clause|provision|article|rule)',
                r'(legal|law|act|regulation|statute)'
            ],
            QueryIntent.PROCEDURE_INQUIRY: [
                r'(process|procedure|step|workflow|method)',
                r'(how do|what are the steps|walk through)',
                r'(timeline|deadline|timeframe)'
            ]
        }
        
        # Complexity indicators
        self.complexity_indicators = {
            'simple': [
                r'(yes|no|can I|is it|does)',
                r'(what is|define|meaning)',
                r'(when|where|who)'
            ],
            'moderate': [
                r'(how to|what should|explain)',
                r'(difference|compare|contrast)',
                r'(requirements|conditions)'
            ],
            'complex': [
                r'(analyze|evaluate|assess)',
                r'(multiple|various|different)',
                r'(consider|factor|aspect)'
            ],
            'very_complex': [
                r'(comprehensive|detailed|thorough)',
                r'(strategy|framework|system)',
                r'(implications|consequences|impact)'
            ]
        }
        
        # Memory for conversation context
        self.conversation_memory = {}
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_processing_time": 0.0,
            "intent_distribution": {intent.value: 0 for intent in QueryIntent},
            "complexity_distribution": {complexity.value: 0 for complexity in QueryComplexity}
        }
    
    def process_query(self, 
                     query: str, 
                     config: AgenticRAGConfig,
                     conversation_id: Optional[str] = None,
                     user_context: Optional[Dict[str, Any]] = None) -> LegalResponse:
        """
        Process a legal query with intelligent decision-making.
        
        Args:
            query: The user's legal question
            config: Configuration for response generation
            conversation_id: Optional conversation identifier
            user_context: Additional user context information
            
        Returns:
            Complete legal response
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # Create query context
            query_context = self._create_query_context(
                query, conversation_id, user_context
            )
            
            # Classify query intent and complexity
            intent = self._classify_intent(query)
            complexity = self._assess_complexity(query)
            
            # Update stats
            self.stats["intent_distribution"][intent.value] += 1
            self.stats["complexity_distribution"][complexity.value] += 1
            
            # Adapt configuration based on analysis
            adapted_config = self._adapt_configuration(config, intent, complexity)
            
            # Plan response strategy
            strategy = self._plan_response_strategy(query_context, intent, complexity)
            
            # Execute response generation
            if strategy.get("requires_multi_step", False):
                response = self._multi_step_reasoning(query_context, adapted_config, strategy)
            else:
                response = self._single_step_response(query_context, adapted_config, strategy)
            
            # Store conversation context if needed
            if conversation_id:
                self._store_conversation_context(conversation_id, query_context, response)
            
            # Update performance stats
            processing_time = time.time() - start_time
            self._update_performance_stats(True, processing_time)
            
            logger.info(f"Processed {intent.value} query with {complexity.value} complexity "
                       f"in {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_performance_stats(False, processing_time)
            logger.error(f"Query processing failed: {e}")
            raise
    
    def _create_query_context(self, 
                             query: str, 
                             conversation_id: Optional[str],
                             user_context: Optional[Dict[str, Any]]) -> LegalQueryContext:
        """Create comprehensive query context."""
        
        # Extract urgency indicators
        urgency = self._detect_urgency(query)
        
        # Determine user role from context
        user_role = "hr_professional"
        if user_context:
            user_role = user_context.get("role", "hr_professional")
        
        # Get previous context if available
        previous_context = None
        if conversation_id and conversation_id in self.conversation_memory:
            previous_context = self.conversation_memory[conversation_id]
        
        return LegalQueryContext(
            query=query,
            query_type="general",  # Will be updated after classification
            conversation_id=conversation_id,
            user_role=user_role,
            urgency=urgency,
            previous_context=previous_context
        )
    
    def _classify_intent(self, query: str) -> QueryIntent:
        """Classify the intent of the query."""
        query_lower = query.lower()
        
        # Score each intent based on pattern matches
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            intent_scores[intent] = score
        
        # Return intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent
        
        return QueryIntent.GENERAL_QUESTION
    
    def _assess_complexity(self, query: str) -> QueryComplexity:
        """Assess the complexity of the query."""
        query_lower = query.lower()
        
        # Count complexity indicators
        complexity_scores = {
            QueryComplexity.SIMPLE: 0,
            QueryComplexity.MODERATE: 0,
            QueryComplexity.COMPLEX: 0,
            QueryComplexity.VERY_COMPLEX: 0
        }
        
        # Score based on patterns
        for level, patterns in self.complexity_indicators.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                if level == 'simple':
                    complexity_scores[QueryComplexity.SIMPLE] += matches
                elif level == 'moderate':
                    complexity_scores[QueryComplexity.MODERATE] += matches
                elif level == 'complex':
                    complexity_scores[QueryComplexity.COMPLEX] += matches
                elif level == 'very_complex':
                    complexity_scores[QueryComplexity.VERY_COMPLEX] += matches
        
        # Additional complexity factors
        word_count = len(query.split())
        question_marks = query.count('?')
        
        # Adjust scores based on length and structure
        if word_count > 50:
            complexity_scores[QueryComplexity.COMPLEX] += 2
        if word_count > 100:
            complexity_scores[QueryComplexity.VERY_COMPLEX] += 2
        if question_marks > 1:
            complexity_scores[QueryComplexity.COMPLEX] += 1
        
        # Return highest scoring complexity
        best_complexity = max(complexity_scores, key=complexity_scores.get)
        return best_complexity if complexity_scores[best_complexity] > 0 else QueryComplexity.SIMPLE
    
    def _detect_urgency(self, query: str) -> str:
        """Detect urgency level from query."""
        query_lower = query.lower()
        
        urgent_patterns = [
            r'(urgent|immediately|asap|emergency|critical)',
            r'(deadline|due date|time sensitive|rush)',
            r'(now|today|this week)'
        ]
        
        high_patterns = [
            r'(soon|quickly|fast|priority)',
            r'(important|significant|serious)'
        ]
        
        for pattern in urgent_patterns:
            if re.search(pattern, query_lower):
                return "urgent"
        
        for pattern in high_patterns:
            if re.search(pattern, query_lower):
                return "high"
        
        return "normal"
    
    def _adapt_configuration(self, 
                           config: AgenticRAGConfig, 
                           intent: QueryIntent, 
                           complexity: QueryComplexity) -> AgenticRAGConfig:
        """Adapt configuration based on query analysis."""
        
        # Create a copy to avoid modifying original
        adapted_config = AgenticRAGConfig(
            response_length=config.response_length,
            custom_word_count=config.custom_word_count,
            max_tokens=config.max_tokens,
            response_style=config.response_style,
            detail_level=config.detail_level,
            audience_level=config.audience_level,
            include_citations=config.include_citations,
            include_confidence=config.include_confidence,
            show_reasoning_chain=config.show_reasoning_chain,
            include_follow_up_questions=config.include_follow_up_questions,
            include_case_examples=config.include_case_examples,
            structured_output=config.structured_output,
            include_metadata=config.include_metadata,
            retrieval_depth=config.retrieval_depth,
            similarity_threshold=config.similarity_threshold,
            cross_reference=config.cross_reference,
            jurisdiction_focus=config.jurisdiction_focus,
            enable_multi_step_reasoning=config.enable_multi_step_reasoning,
            quality_check=config.quality_check,
            response_validation=config.response_validation,
            auto_improve=config.auto_improve,
            timeout_seconds=config.timeout_seconds,
            enable_caching=config.enable_caching,
            cache_ttl_minutes=config.cache_ttl_minutes
        )
        
        # Adjust based on complexity
        if complexity == QueryComplexity.VERY_COMPLEX:
            adapted_config.response_length = ResponseLength.DETAILED
            adapted_config.detail_level = DetailLevel.COMPREHENSIVE
            adapted_config.show_reasoning_chain = True
            adapted_config.retrieval_depth = min(10, adapted_config.retrieval_depth * 2)
            adapted_config.enable_multi_step_reasoning = True
            
        elif complexity == QueryComplexity.COMPLEX:
            if adapted_config.response_length == ResponseLength.SHORT:
                adapted_config.response_length = ResponseLength.MEDIUM
            adapted_config.detail_level = DetailLevel.BALANCED
            adapted_config.enable_multi_step_reasoning = True
            
        elif complexity == QueryComplexity.SIMPLE:
            if adapted_config.response_length == ResponseLength.DETAILED:
                adapted_config.response_length = ResponseLength.MEDIUM
            adapted_config.detail_level = DetailLevel.BRIEF
            adapted_config.show_reasoning_chain = False
        
        # Adjust based on intent
        if intent == QueryIntent.LEGAL_INTERPRETATION:
            adapted_config.response_style = ResponseStyle.LEGAL
            adapted_config.include_citations = True
            
        elif intent == QueryIntent.COMPLIANCE_CHECK:
            adapted_config.structured_output = True
            adapted_config.include_case_examples = True
            
        elif intent == QueryIntent.DOCUMENT_GENERATION:
            adapted_config.response_style = ResponseStyle.PROFESSIONAL
            adapted_config.structured_output = True
        
        return adapted_config
    
    def _plan_response_strategy(self, 
                               query_context: LegalQueryContext, 
                               intent: QueryIntent, 
                               complexity: QueryComplexity) -> Dict[str, Any]:
        """Plan the response generation strategy."""
        
        strategy = {
            "requires_multi_step": False,
            "sub_queries": [],
            "retrieval_strategy": "standard",
            "response_structure": "standard"
        }
        
        # Determine if multi-step reasoning is needed
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            strategy["requires_multi_step"] = True
            strategy["sub_queries"] = self._decompose_query(query_context.query)
        
        # Adjust retrieval strategy based on intent
        if intent == QueryIntent.COMPLIANCE_CHECK:
            strategy["retrieval_strategy"] = "compliance_focused"
        elif intent == QueryIntent.POLICY_GUIDANCE:
            strategy["retrieval_strategy"] = "policy_focused"
        elif intent == QueryIntent.LEGAL_INTERPRETATION:
            strategy["retrieval_strategy"] = "legal_focused"
        
        # Set response structure
        if intent == QueryIntent.DOCUMENT_GENERATION:
            strategy["response_structure"] = "template_based"
        elif intent == QueryIntent.PROCEDURE_INQUIRY:
            strategy["response_structure"] = "step_by_step"
        
        return strategy
    
    def _decompose_query(self, query: str) -> List[str]:
        """Decompose complex query into sub-queries."""
        # Simple implementation - could be enhanced with AI
        sub_queries = []
        
        # Look for multiple questions
        questions = re.split(r'[.!?]\\s*(?=.*\\?)', query)
        if len(questions) > 1:
            sub_queries.extend([q.strip() + '?' for q in questions if q.strip()])
        
        # Look for "and" clauses
        and_parts = re.split(r'\\s+and\\s+', query, flags=re.IGNORECASE)
        if len(and_parts) > 1:
            for part in and_parts:
                if len(part.strip()) > 10:  # Meaningful sub-query
                    sub_queries.append(part.strip())
        
        return sub_queries[:3] if sub_queries else [query]  # Limit to 3 sub-queries
    
    def _single_step_response(self, 
                             query_context: LegalQueryContext, 
                             config: AgenticRAGConfig,
                             strategy: Dict[str, Any]) -> LegalResponse:
        """Generate response using single-step RAG."""
        if not self.rag_engine:
            raise ValueError("No RAG engine configured")
        
        return self.rag_engine.query(query_context, config)
    
    def _multi_step_reasoning(self, 
                             query_context: LegalQueryContext, 
                             config: AgenticRAGConfig,
                             strategy: Dict[str, Any]) -> LegalResponse:
        """Generate response using multi-step reasoning."""
        if not self.rag_engine:
            raise ValueError("No RAG engine configured")
        
        sub_queries = strategy.get("sub_queries", [query_context.query])
        sub_responses = []
        
        # Process each sub-query
        for sub_query in sub_queries:
            sub_context = LegalQueryContext(
                query=sub_query,
                query_type=query_context.query_type,
                conversation_id=query_context.conversation_id,
                user_role=query_context.user_role,
                urgency=query_context.urgency
            )
            
            try:
                sub_response = self.rag_engine.query(sub_context, config)
                sub_responses.append(sub_response)
            except Exception as e:
                logger.warning(f"Sub-query failed: {e}")
                continue
        
        # Combine responses intelligently
        return self._combine_sub_responses(query_context, sub_responses, config)
    
    def _combine_sub_responses(self, 
                              query_context: LegalQueryContext, 
                              sub_responses: List[LegalResponse],
                              config: AgenticRAGConfig) -> LegalResponse:
        """Combine multiple sub-responses into a coherent answer."""
        
        if not sub_responses:
            # Fallback to simple query
            return self._single_step_response(query_context, config, {})
        
        if len(sub_responses) == 1:
            return sub_responses[0]
        
        # Combine content
        combined_content = self._merge_response_content(sub_responses)
        
        # Merge metadata
        combined_metadata = self._merge_response_metadata(sub_responses)
        
        # Create combined response
        from .config import LegalResponse
        return LegalResponse(
            content=combined_content,
            metadata=combined_metadata,
            config_used=config,
            query_context=query_context,
            response_id=f"multi_{int(time.time())}",
            timestamp=sub_responses[0].timestamp
        )
    
    def _merge_response_content(self, responses: List[LegalResponse]) -> str:
        """Merge content from multiple responses."""
        sections = []
        
        for i, response in enumerate(responses):
            if i == 0:
                sections.append(response.content)
            else:
                # Add section header for subsequent responses
                sections.append(f"\\n\\nAdditional Considerations:\\n{response.content}")
        
        return "\\n".join(sections)
    
    def _merge_response_metadata(self, responses: List[LegalResponse]):
        """Merge metadata from multiple responses."""
        from .config import ResponseMetadata
        
        # Combine sources
        all_sources = []
        total_processing_time = 0
        confidence_scores = []
        
        for response in responses:
            all_sources.extend(response.metadata.sources_used)
            total_processing_time += response.metadata.processing_time
            confidence_scores.append(response.metadata.confidence_score)
        
        # Calculate average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return ResponseMetadata(
            confidence_score=avg_confidence,
            processing_time=total_processing_time,
            sources_used=list(set(all_sources)),  # Remove duplicates
            reasoning_steps=["Multi-step reasoning applied"],
            follow_up_suggestions=[],
            quality_score=avg_confidence,  # Simple approximation
            validation_passed=avg_confidence > 0.6
        )
    
    def _store_conversation_context(self, 
                                   conversation_id: str, 
                                   query_context: LegalQueryContext,
                                   response: LegalResponse):
        """Store conversation context for future reference."""
        self.conversation_memory[conversation_id] = {
            "last_query": query_context.query,
            "last_response_summary": response.content[:200] + "..." if len(response.content) > 200 else response.content,
            "timestamp": time.time(),
            "query_count": self.conversation_memory.get(conversation_id, {}).get("query_count", 0) + 1
        }
        
        # Limit memory size (keep only recent conversations)
        if len(self.conversation_memory) > 100:
            oldest_id = min(self.conversation_memory.keys(), 
                           key=lambda k: self.conversation_memory[k]["timestamp"])
            del self.conversation_memory[oldest_id]
    
    def _update_performance_stats(self, success: bool, processing_time: float):
        """Update agent performance statistics."""
        if success:
            self.stats["successful_responses"] += 1
        else:
            self.stats["failed_responses"] += 1
        
        # Update average processing time
        total_responses = self.stats["successful_responses"] + self.stats["failed_responses"]
        current_avg = self.stats["average_processing_time"]
        self.stats["average_processing_time"] = ((current_avg * (total_responses - 1)) + processing_time) / total_responses
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get comprehensive agent statistics."""
        total_responses = self.stats["successful_responses"] + self.stats["failed_responses"]
        success_rate = (self.stats["successful_responses"] / total_responses) if total_responses > 0 else 0.0
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "conversation_memory_size": len(self.conversation_memory)
        }
    
    def clear_conversation_memory(self):
        """Clear conversation memory."""
        self.conversation_memory.clear()
        logger.info("Conversation memory cleared")
