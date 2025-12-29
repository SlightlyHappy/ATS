"""
Legal Knowledge Base Management
==============================

Manages loading, processing, and indexing of legal documents
from the HRLaw folder for RAG operations.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import time

logger = logging.getLogger(__name__)

class LegalKnowledgeBase:
    """Manages the legal document knowledge base."""
    
    def __init__(self, 
                 hrlaw_path: str = "../HRlaw",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the legal knowledge base.
        
        Args:
            hrlaw_path: Path to the HRLaw folder
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
        """
        self.hrlaw_path = Path(hrlaw_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Document sources
        self.book_parsing_path = self.hrlaw_path / "bookparsing" / "texts"
        self.books_path = self.hrlaw_path / "indian_law_rag" / "books"
        
        # Processing stats
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "processing_time": 0.0,
            "last_updated": None
        }
        
        self.processed_documents = []
        self.document_metadata = []
    
    def load_legal_documents(self) -> bool:
        """Load and process all legal documents."""
        try:
            start_time = time.time()
            logger.info("Starting to load legal documents...")
            
            # Load from bookparsing/texts
            if self.book_parsing_path.exists():
                self._load_from_bookparsing()
            
            # Load from indian_law_rag/books  
            if self.books_path.exists():
                self._load_from_books()
            
            # Process documents into chunks
            self._process_documents_into_chunks()
            
            # Update stats
            self.stats["processing_time"] = time.time() - start_time
            self.stats["last_updated"] = time.time()
            
            logger.info(f"Loaded {self.stats['total_documents']} documents, "
                       f"created {self.stats['total_chunks']} chunks in "
                       f"{self.stats['processing_time']:.2f} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load legal documents: {e}")
            return False
    
    def _load_from_bookparsing(self):
        """Load processed text files from bookparsing folder."""
        try:
            text_files = list(self.book_parsing_path.glob("*.txt"))
            logger.info(f"Found {len(text_files)} text files in bookparsing")
            
            for text_file in text_files:
                try:
                    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if content.strip():
                        doc_info = self._extract_document_info(text_file.name, content)
                        self.processed_documents.append(content)
                        self.document_metadata.append(doc_info)
                        self.stats["total_documents"] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to load {text_file}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error loading from bookparsing: {e}")
    
    def _load_from_books(self):
        """Load text files from indian_law_rag/books folder."""
        try:
            text_files = list(self.books_path.glob("*.txt"))
            logger.info(f"Found {len(text_files)} text files in books")
            
            for text_file in text_files:
                try:
                    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if content.strip():
                        doc_info = self._extract_document_info(text_file.name, content)
                        self.processed_documents.append(content)
                        self.document_metadata.append(doc_info)
                        self.stats["total_documents"] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to load {text_file}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error loading from books: {e}")
    
    def _extract_document_info(self, filename: str, content: str) -> Dict[str, Any]:
        """Extract metadata from document filename and content."""
        # Clean filename for better analysis
        clean_name = filename.replace('.txt', '').replace('_', ' ')
        
        # Determine document type based on filename
        doc_type = self._classify_document_type(clean_name)
        
        # Extract basic info
        word_count = len(content.split())
        char_count = len(content)
        
        # Try to extract title from content
        title = self._extract_title_from_content(content, clean_name)
        
        return {
            "filename": filename,
            "title": title,
            "document_type": doc_type,
            "word_count": word_count,
            "char_count": char_count,
            "source_folder": "bookparsing" if "bookparsing" in str(filename) else "books",
            "processed_at": time.time(),
            "content_hash": hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()
        }
    
    def _classify_document_type(self, filename: str) -> str:
        """Classify document type based on filename."""
        filename_lower = filename.lower()
        
        if any(term in filename_lower for term in ['labour act', 'labor act']):
            return "labour_act"
        elif 'minimum wage' in filename_lower:
            return "minimum_wage"
        elif 'industrial relation' in filename_lower:
            return "industrial_relations"
        elif any(term in filename_lower for term in ['handbook', 'guide']):
            return "handbook"
        elif 'law' in filename_lower:
            return "legal_text"
        elif any(term in filename_lower for term in ['textbook', 'education']):
            return "educational"
        else:
            return "general"
    
    def _extract_title_from_content(self, content: str, fallback_title: str) -> str:
        """Try to extract document title from content."""
        lines = content.split('\n')[:20]  # Check first 20 lines
        
        for line in lines:
            line = line.strip()
            if line and len(line) < 200:  # Reasonable title length
                # Look for title patterns
                if any(pattern in line.upper() for pattern in 
                      ['ACT', 'LAW', 'CODE', 'REGULATION', 'HANDBOOK', 'GUIDE']):
                    return line
        
        # Fallback to processed filename
        return fallback_title.title()
    
    def _process_documents_into_chunks(self):
        """Process documents into smaller chunks for better retrieval."""
        chunked_documents = []
        chunked_metadata = []
        
        for i, (doc, metadata) in enumerate(zip(self.processed_documents, self.document_metadata)):
            chunks = self._create_chunks(doc)
            
            for j, chunk in enumerate(chunks):
                if chunk.strip():  # Only add non-empty chunks
                    chunked_documents.append(chunk)
                    
                    # Create metadata for chunk
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "chunk_id": f"{i}_{j}",
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                        "chunk_word_count": len(chunk.split()),
                        "chunk_char_count": len(chunk)
                    })
                    chunked_metadata.append(chunk_metadata)
        
        # Replace original documents with chunks
        self.processed_documents = chunked_documents
        self.document_metadata = chunked_metadata
        self.stats["total_chunks"] = len(chunked_documents)
        
        logger.info(f"Created {len(chunked_documents)} chunks from {self.stats['total_documents']} documents")
    
    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            # Stop if we've reached the end
            if i + self.chunk_size >= len(words):
                break
        
        return chunks
    
    def get_documents_by_type(self, doc_type: str) -> List[Dict[str, Any]]:
        """Get all documents of a specific type."""
        results = []
        for doc, metadata in zip(self.processed_documents, self.document_metadata):
            if metadata.get("document_type") == doc_type:
                results.append({
                    "content": doc,
                    "metadata": metadata
                })
        return results
    
    def search_documents(self, 
                        query: str, 
                        doc_types: Optional[List[str]] = None,
                        source_folders: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search documents with optional filtering."""
        results = []
        query_lower = query.lower()
        
        for doc, metadata in zip(self.processed_documents, self.document_metadata):
            # Apply filters
            if doc_types and metadata.get("document_type") not in doc_types:
                continue
            if source_folders and metadata.get("source_folder") not in source_folders:
                continue
            
            # Simple text search
            if query_lower in doc.lower():
                results.append({
                    "content": doc,
                    "metadata": metadata,
                    "relevance_score": doc.lower().count(query_lower)
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    def get_document_types(self) -> Dict[str, int]:
        """Get count of documents by type."""
        type_counts = {}
        for metadata in self.document_metadata:
            doc_type = metadata.get("document_type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        return type_counts
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base statistics."""
        return {
            **self.stats,
            "document_types": self.get_document_types(),
            "average_chunk_size": sum(len(doc.split()) for doc in self.processed_documents) / len(self.processed_documents) if self.processed_documents else 0,
            "total_words": sum(len(doc.split()) for doc in self.processed_documents),
            "source_distribution": self._get_source_distribution()
        }
    
    def _get_source_distribution(self) -> Dict[str, int]:
        """Get distribution of documents by source folder."""
        source_counts = {}
        for metadata in self.document_metadata:
            source = metadata.get("source_folder", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        return source_counts
    
    def export_processed_documents(self, output_path: str) -> bool:
        """Export processed documents to JSON file."""
        try:
            export_data = {
                "metadata": self.get_knowledge_base_stats(),
                "documents": [
                    {
                        "content": doc,
                        "metadata": metadata
                    }
                    for doc, metadata in zip(self.processed_documents, self.document_metadata)
                ]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported {len(self.processed_documents)} documents to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export documents: {e}")
            return False
    
    def get_documents_and_metadata(self) -> tuple[List[str], List[Dict[str, Any]]]:
        """Get all processed documents and their metadata."""
        return self.processed_documents, self.document_metadata
