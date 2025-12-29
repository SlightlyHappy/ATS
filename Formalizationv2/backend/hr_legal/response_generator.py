"""
Response Generator with Configurable Output
==========================================

Generates customized legal responses based on user preferences
and query context with quality validation.
"""

import logging
import time
import re
from typing import Dict, Any, List, Optional
from .config import (
    AgenticRAGConfig, LegalQueryContext, LegalResponse, 
    ResponseMetadata, ResponseLength, ResponseStyle, DetailLevel
)

logger = logging.getLogger(__name__)

class ResponseController:
    """Controls response generation with customizable parameters."""
    
    def __init__(self, ai_provider=None):
        """
        Initialize response controller.
        
        Args:
            ai_provider: AI provider instance for text generation
        """
        self.ai_provider = ai_provider
        
        # Response length mapping (target word counts)
        self.length_targets = {
            ResponseLength.SHORT: (50, 150),
            ResponseLength.MEDIUM: (150, 400),
            ResponseLength.LONG: (400, 800),
            ResponseLength.DETAILED: (800, 1500)
        }
        
        # Style-specific prompt modifications with enhanced legal prompts
        self.style_prompts = {
            ResponseStyle.PROFESSIONAL: """
            Provide a professional, business-appropriate response that:
            - Uses formal business language
            - Includes clear recommendations
            - Maintains objective tone
            - Focuses on practical applications
            """,
            ResponseStyle.LEGAL: """
            Provide a formal legal response that:
            - Uses proper legal terminology and citations
            - Follows legal analysis structure (Issue, Rule, Application, Conclusion)
            - References relevant statutes, regulations, and case law
            - Includes appropriate legal disclaimers
            - Maintains formal legal writing style
            """,
            ResponseStyle.CASUAL: """
            Provide a conversational, easy-to-understand response that:
            - Uses plain language and avoids jargon
            - Explains complex concepts simply
            - Uses examples and analogies
            - Maintains friendly but informative tone
            """,
            ResponseStyle.TECHNICAL: """
            Provide a detailed technical response that:
            - Includes specific procedures and step-by-step guidance
            - References exact sections and subsections
            - Provides implementation details
            - Uses precise technical terminology
            """,
            ResponseStyle.EDUCATIONAL: """
            Provide an educational response that:
            - Explains the reasoning behind legal principles
            - Includes background context and history
            - Uses examples to illustrate concepts
            - Builds understanding progressively
            - Includes learning objectives and key takeaways
            """
        }
        
        # Enhanced quality validation patterns
        self.quality_patterns = {
            "has_structure": r"(\n\n|\n\s*[-•*]\s|\n\s*\d+\.|\n#{1,3}\s)",
            "has_citations": r"(section|act|clause|rule|regulation|article|subsection|chapter)",
            "balanced_length": lambda text, target: abs(len(text.split()) - target) / target < 0.3,
            "coherent_sentences": r"[.!?]\s+[A-Z]",
            "legal_terminology": r"(shall|pursuant|compliance|regulation|statutory|provision|jurisdiction|precedent)",
            "has_examples": r"(for example|for instance|such as|including|e\.g\.|i\.e\.)",
            "actionable_advice": r"(should|must|recommend|suggest|advise|consider|ensure)",
            "proper_disclaimers": r"(disclaimer|consult|professional|advice|attorney|lawyer)",
            "logical_flow": r"(therefore|however|moreover|furthermore|in addition|consequently)",
            "risk_assessment": r"(risk|liability|potential|may result|could lead|compliance)"
        }
    
    def generate_response(self, 
                         query_context: LegalQueryContext, 
                         retrieved_docs: List[Dict[str, Any]], 
                         config: AgenticRAGConfig) -> LegalResponse:
        """
        Generate a customized legal response.
        
        Args:
            query_context: Context information for the query
            retrieved_docs: Documents retrieved from vector search
            config: Configuration for response generation
            
        Returns:
            Complete legal response with metadata
        """
        start_time = time.time()
        
        try:
            # Build context from retrieved documents
            context = self._build_context(retrieved_docs, config)
            
            # Create prompt based on configuration
            prompt = self._create_prompt(query_context, context, config)
            
            # Generate response using AI provider
            raw_response = self._generate_with_ai(prompt, config)
            
            # Post-process and validate response
            processed_response = self._post_process_response(raw_response, config)
            
            # Create response metadata
            metadata = self._create_metadata(
                processed_response, retrieved_docs, config, 
                time.time() - start_time
            )
            
            # Create complete response object
            response = LegalResponse(
                content=processed_response,
                metadata=metadata,
                config_used=config,
                query_context=query_context,
                response_id=self._generate_response_id(),
                timestamp=self._get_timestamp()
            )
            
            logger.info(f"Generated response in {metadata.processing_time:.2f}s "
                       f"with confidence {metadata.confidence_score:.2f}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            # Return error response
            return self._create_error_response(query_context, config, str(e))
    
    def _build_context(self, retrieved_docs: List[Dict[str, Any]], config: AgenticRAGConfig) -> str:
        """Build context string from retrieved documents."""
        if not retrieved_docs:
            return "No relevant legal documents found."
        
        context_parts = []
        max_docs = min(config.retrieval_depth, len(retrieved_docs))
        
        for i, doc in enumerate(retrieved_docs[:max_docs]):
            if doc.get('score', 0) >= config.similarity_threshold:
                doc_text = doc.get('document', '')
                metadata = doc.get('metadata', {})
                
                # Add document with source information if requested
                if config.include_metadata:
                    source = metadata.get('title', metadata.get('filename', f'Document {i+1}'))
                    context_parts.append(f"Source: {source}\\n{doc_text}")
                else:
                    context_parts.append(doc_text)
        
        return "\\n\\n".join(context_parts)
    
    def _create_prompt(self, 
                      query_context: LegalQueryContext, 
                      context: str, 
                      config: AgenticRAGConfig) -> str:
        """Create AI prompt based on configuration."""
        
        # Base prompt structure
        prompt_parts = [
            "You are an expert Indian labor law specialist providing HR guidance.",
            "",
            f"User Role: {query_context.user_role}",
            f"Query Type: {query_context.query_type}",
            f"Urgency: {query_context.urgency}",
            ""
        ]
        
        # Add style-specific instructions
        style_instruction = self.style_prompts.get(config.response_style, "")
        if style_instruction:
            prompt_parts.append(style_instruction)
            prompt_parts.append("")
        
        # Add length instructions
        if config.response_length != ResponseLength.CUSTOM:
            min_words, max_words = self.length_targets[config.response_length]
            prompt_parts.append(f"Response length: {min_words}-{max_words} words.")
        elif config.custom_word_count:
            prompt_parts.append(f"Response length: approximately {config.custom_word_count} words.")
        
        # Add detail level instructions
        detail_instructions = {
            DetailLevel.BRIEF: "Provide a concise, direct answer focusing on key points only.",
            DetailLevel.BALANCED: "Provide a balanced response with key information and relevant details.",
            DetailLevel.COMPREHENSIVE: "Provide a comprehensive response with detailed explanations, examples, and context."
        }
        
        detail_instruction = detail_instructions.get(config.detail_level, "")
        if detail_instruction:
            prompt_parts.append(detail_instruction)
        
        # Add audience level instructions
        audience_instructions = {
            "beginner": "Explain concepts clearly without assuming prior legal knowledge.",
            "intermediate": "Assume basic HR knowledge but explain legal complexities.",
            "expert": "Use appropriate legal terminology and assume professional expertise."
        }
        
        audience_instruction = audience_instructions.get(config.audience_level.value, "")
        if audience_instruction:
            prompt_parts.append(audience_instruction)
        
        prompt_parts.extend([
            "",
            "Additional Requirements:",
        ])
        
        # Add content requirements
        if config.include_citations:
            prompt_parts.append("- Include relevant legal citations and references")
        if config.include_case_examples and config.detail_level != DetailLevel.BRIEF:
            prompt_parts.append("- Include practical examples where relevant")
        if config.structured_output:
            prompt_parts.append("- Structure your response with clear headings and bullet points")
        if config.show_reasoning_chain:
            prompt_parts.append("- Show step-by-step legal reasoning")
        if config.include_follow_up_questions:
            prompt_parts.append("- Suggest relevant follow-up questions at the end")
        
        # Add context and query
        prompt_parts.extend([
            "",
            "Legal Context:",
            context,
            "",
            f"Question: {query_context.query}",
            "",
            "Response:"
        ])
        
        return "\\n".join(prompt_parts)
    
    def _generate_with_ai(self, prompt: str, config: AgenticRAGConfig) -> str:
        """Generate response using AI provider."""
        if not self.ai_provider:
            raise ValueError("No AI provider configured")
        
        try:
            # Generate response using multi-provider AI interface
            # Note: The multi-provider AI system only supports prompt and format_json parameters
            result = self.ai_provider.generate_response(prompt, format_json=False)
            
            if isinstance(result, dict):
                return result.get('response', str(result))
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            raise
    
    def _post_process_response(self, response: str, config: AgenticRAGConfig) -> str:
        """Post-process and validate the generated response."""
        # Clean up response
        response = response.strip()
        
        # Remove any JSON artifacts if present
        if response.startswith('{') and response.endswith('}'):
            try:
                import json
                parsed = json.loads(response)
                response = parsed.get('response', response)
            except:
                pass
        
        # Apply length adjustments if needed
        if config.response_length == ResponseLength.CUSTOM and config.custom_word_count:
            response = self._adjust_response_length(response, config.custom_word_count)
        
        # Add structure if requested and missing
        if config.structured_output and not self._has_structure(response):
            response = self._add_structure(response)
        
        # Validate and improve if auto-improve is enabled
        if config.auto_improve:
            response = self._improve_response(response, config)
        
        return response
    
    def _adjust_response_length(self, response: str, target_words: int) -> str:
        """Adjust response length to meet target word count."""
        current_words = len(response.split())
        
        if abs(current_words - target_words) / target_words < 0.2:
            return response  # Close enough
        
        if current_words > target_words * 1.3:
            # Too long - truncate intelligently
            sentences = response.split('. ')
            target_sentences = int(len(sentences) * (target_words / current_words))
            return '. '.join(sentences[:target_sentences]) + '.'
        
        elif current_words < target_words * 0.7:
            # Too short - add note about expansion
            response += "\\n\\nNote: For more detailed information on this topic, please ask specific follow-up questions."
        
        return response
    
    def _has_structure(self, text: str) -> bool:
        """Check if text has proper structure."""
        return bool(re.search(self.quality_patterns["has_structure"], text))
    
    def _add_structure(self, response: str) -> str:
        """Add basic structure to response."""
        sentences = response.split('. ')
        if len(sentences) > 3:
            # Group sentences into paragraphs
            structured = []
            for i in range(0, len(sentences), 2):
                paragraph = '. '.join(sentences[i:i+2])
                if paragraph:
                    structured.append(paragraph + '.')
            return '\\n\\n'.join(structured)
        return response
    
    def _improve_response(self, response: str, config: AgenticRAGConfig) -> str:
        """Apply automatic improvements to response."""
        # Add legal terminology if missing (for legal style)
        if (config.response_style == ResponseStyle.LEGAL and 
            not re.search(self.quality_patterns["legal_terminology"], response.lower())):
            response = response.replace("must", "shall").replace("rule", "regulation")
        
        return response
    
    def _create_metadata(self, 
                        response: str, 
                        retrieved_docs: List[Dict[str, Any]], 
                        config: AgenticRAGConfig,
                        processing_time: float) -> ResponseMetadata:
        """Create response metadata with quality scores."""
        
        # Calculate confidence score based on retrieval quality
        confidence = self._calculate_confidence(retrieved_docs, response)
        
        # Calculate quality score
        quality = self._calculate_quality_score(response, config)
        
        # Extract sources
        sources = [doc.get('metadata', {}).get('title', 'Unknown') 
                  for doc in retrieved_docs[:5]]
        
        # Generate follow-up suggestions if enabled
        follow_ups = []
        if config.include_follow_up_questions:
            follow_ups = self._generate_follow_up_questions(response)
        
        return ResponseMetadata(
            confidence_score=confidence,
            processing_time=processing_time,
            sources_used=sources,
            reasoning_steps=[],  # Would be populated if reasoning chain is enabled
            follow_up_suggestions=follow_ups,
            quality_score=quality,
            validation_passed=quality > 0.6,
            improvement_suggestions=self._generate_improvement_suggestions(response, config)
        )
    
    def _calculate_confidence(self, retrieved_docs: List[Dict[str, Any]], response: str) -> float:
        """Calculate confidence score based on retrieval and response quality."""
        if not retrieved_docs:
            return 0.3
        
        # Average similarity score of retrieved documents
        avg_similarity = sum(doc.get('score', 0) for doc in retrieved_docs) / len(retrieved_docs)
        
        # Response coherence (simple heuristic)
        word_count = len(response.split())
        sentence_count = len(re.findall(r'[.!?]+', response))
        coherence = min(1.0, word_count / max(1, sentence_count * 10))
        
        # Combine factors
        confidence = (avg_similarity * 0.6 + coherence * 0.4)
        return min(1.0, max(0.0, confidence))
    
    def _calculate_quality_score(self, response: str, config: AgenticRAGConfig) -> float:
        """Calculate quality score based on various criteria."""
        scores = []
        
        # Structure check
        if self._has_structure(response):
            scores.append(0.8)
        else:
            scores.append(0.4)
        
        # Length appropriateness
        word_count = len(response.split())
        if config.response_length != ResponseLength.CUSTOM:
            min_words, max_words = self.length_targets[config.response_length]
            length_score = 1.0 if min_words <= word_count <= max_words else 0.6
        else:
            length_score = 0.8  # Assume reasonable for custom
        scores.append(length_score)
        
        # Legal terminology (for legal style)
        if config.response_style == ResponseStyle.LEGAL:
            has_legal_terms = bool(re.search(self.quality_patterns["legal_terminology"], response.lower()))
            scores.append(0.9 if has_legal_terms else 0.5)
        
        # Coherence (sentence structure)
        coherent = bool(re.search(self.quality_patterns["coherent_sentences"], response))
        scores.append(0.8 if coherent else 0.6)
        
        return sum(scores) / len(scores)
    
    def _generate_follow_up_questions(self, response: str) -> List[str]:
        """Generate relevant follow-up questions."""
        # Simple implementation - could be enhanced with AI
        generic_questions = [
            "What are the specific compliance requirements for this?",
            "Are there any recent updates to these regulations?",
            "What documentation is required for this process?",
            "What are the penalties for non-compliance?"
        ]
        
        # Return 2-3 relevant questions
        return generic_questions[:3]
    
    def _generate_improvement_suggestions(self, response: str, config: AgenticRAGConfig) -> List[str]:
        """Generate suggestions for improving the response."""
        suggestions = []
        
        if not self._has_structure(response) and config.structured_output:
            suggestions.append("Add clear headings and bullet points for better readability")
        
        if config.include_citations and not re.search(self.quality_patterns["has_citations"], response.lower()):
            suggestions.append("Include more specific legal citations and references")
        
        if len(response.split()) < 50:
            suggestions.append("Provide more detailed explanation and examples")
        
        return suggestions
    
    def _generate_response_id(self) -> str:
        """Generate unique response ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _create_error_response(self, 
                              query_context: LegalQueryContext, 
                              config: AgenticRAGConfig, 
                              error_msg: str) -> LegalResponse:
        """Create error response when generation fails."""
        return LegalResponse(
            content=f"I apologize, but I encountered an error while processing your legal query: {error_msg}. Please try again or rephrase your question.",
            metadata=ResponseMetadata(
                confidence_score=0.0,
                processing_time=0.0,
                validation_passed=False,
                improvement_suggestions=["Try rephrasing the question", "Check system status"]
            ),
            config_used=config,
            query_context=query_context,
            response_id=self._generate_response_id(),
            timestamp=self._get_timestamp()
        )
