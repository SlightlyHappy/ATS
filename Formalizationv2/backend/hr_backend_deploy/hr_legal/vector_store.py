"""
Legal Vector Store Management
============================

Manages vector databases for legal documents with efficient retrieval
and similarity search capabilities.
"""

import os
import json
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import hashlib
import time

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Install with: pip install faiss-cpu")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("SentenceTransformers not available. Install with: pip install sentence-transformers")

class LegalVectorStore:
    """Manages vector database for legal documents."""
    
    def __init__(self, 
                 vector_db_path: str = None,
                 embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
                 index_type: str = "flat"):
        """
        Initialize the vector store with dynamic path detection for Railway.
        
        Args:
            vector_db_path: Path to store vector database files
            embedding_model: Name of the sentence transformer model
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
        """
        # Dynamic path detection for Railway deployment
        if vector_db_path:
            self.vector_db_path = Path(vector_db_path)
        elif os.path.exists("/app"):
            # Railway deployment path
            self.vector_db_path = Path("/app/hr_legal/vector_db")
        else:
            # Local development path
            self.vector_db_path = Path("hr_legal/vector_db")
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model_name = embedding_model
        self.index_type = index_type
        
        # Initialize components
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.is_loaded = False
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "average_query_time": 0.0,
            "cache_hits": 0,
            "index_size": 0
        }
        
        # Query cache for performance
        self.query_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("SentenceTransformers not available")
            
        try:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _initialize_faiss_index(self, dimension: int):
        """Initialize FAISS index based on specified type."""
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not available")
            
        if self.index_type == "flat":
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        elif self.index_type == "ivf":
            quantizer = faiss.IndexFlatIP(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)  # 100 clusters
        elif self.index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(dimension, 32)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
            
        logger.info(f"Initialized {self.index_type} FAISS index with dimension {dimension}")
    
    def load_or_create_index(self) -> bool:
        """Load existing index or create new one."""
        try:
            # Try to load existing index
            if self._load_existing_index():
                logger.info("Loaded existing vector index")
                self.is_loaded = True
                return True
            else:
                logger.info("No existing index found, will create new one when documents are added")
                self._initialize_embedding_model()
                return True
                
        except Exception as e:
            logger.error(f"Failed to load/create index: {e}")
            return False
    
    def _load_existing_index(self) -> bool:
        """Load existing FAISS index and metadata."""
        index_path = self.vector_db_path / "index.faiss"
        docs_path = self.vector_db_path / "documents.pkl"
        metadata_path = self.vector_db_path / "metadata.json"
        
        if not all(path.exists() for path in [index_path, docs_path, metadata_path]):
            return False
            
        try:
            # Load FAISS index
            if FAISS_AVAILABLE:
                self.index = faiss.read_index(str(index_path))
            
            # Load documents
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
            
            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_info = json.load(f)
                self.metadata = metadata_info.get('documents', [])
                self.embedding_model_name = metadata_info.get('embedding_model', self.embedding_model_name)
            
            # Initialize embedding model
            self._initialize_embedding_model()
            
            # Update stats
            self.stats["index_size"] = len(self.documents)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading existing index: {e}")
            return False
    
    def add_documents(self, documents: List[str], metadata: List[Dict[str, Any]] = None) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
            
        Returns:
            bool: Success status
        """
        try:
            if not self.embedding_model:
                self._initialize_embedding_model()
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} documents")
            embeddings = self.embedding_model.encode(documents, show_progress_bar=True)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Initialize index if not exists
            if self.index is None:
                self._initialize_faiss_index(embeddings.shape[1])
                if self.index_type == "ivf":
                    # Train IVF index
                    self.index.train(embeddings.astype(np.float32))
            
            # Add to index
            if FAISS_AVAILABLE:
                self.index.add(embeddings.astype(np.float32))
            
            # Store documents and metadata
            self.documents.extend(documents)
            if metadata:
                self.metadata.extend(metadata)
            else:
                self.metadata.extend([{"index": i + len(self.metadata)} for i in range(len(documents))])
            
            # Update stats
            self.stats["index_size"] = len(self.documents)
            
            logger.info(f"Successfully added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def search(self, 
               query: str, 
               k: int = 5, 
               similarity_threshold: float = 0.7,
               use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            similarity_threshold: Minimum similarity score
            use_cache: Whether to use query cache
            
        Returns:
            List of search results with documents and scores
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # Check cache
            if use_cache:
                cache_key = hashlib.md5(f"{query}_{k}_{similarity_threshold}".encode()).hexdigest()
                if cache_key in self.query_cache:
                    cache_entry = self.query_cache[cache_key]
                    if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                        self.stats["cache_hits"] += 1
                        return cache_entry['results']
            
            # Generate query embedding
            if not self.embedding_model:
                self._initialize_embedding_model()
                
            query_embedding = self.embedding_model.encode([query])
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # Search in index
            if FAISS_AVAILABLE and self.index:
                scores, indices = self.index.search(query_embedding.astype(np.float32), k)
                scores = scores[0]  # Get first (and only) query result
                indices = indices[0]
            else:
                # Fallback to manual similarity calculation
                if not self.documents:
                    return []
                    
                doc_embeddings = self.embedding_model.encode(self.documents)
                doc_embeddings = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
                
                similarities = np.dot(query_embedding, doc_embeddings.T)[0]
                top_indices = np.argsort(similarities)[::-1][:k]
                scores = similarities[top_indices]
                indices = top_indices
            
            # Filter by similarity threshold and prepare results
            results = []
            for i, (score, idx) in enumerate(zip(scores, indices)):
                if score >= similarity_threshold and 0 <= idx < len(self.documents):
                    result = {
                        "document": self.documents[idx],
                        "score": float(score),
                        "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
                        "rank": i + 1
                    }
                    results.append(result)
            
            # Cache results
            if use_cache:
                self.query_cache[cache_key] = {
                    'results': results,
                    'timestamp': time.time()
                }
            
            # Update performance stats
            query_time = time.time() - start_time
            total_time = self.stats["average_query_time"] * (self.stats["total_queries"] - 1)
            self.stats["average_query_time"] = (total_time + query_time) / self.stats["total_queries"]
            
            logger.debug(f"Search completed in {query_time:.3f}s, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def save_index(self) -> bool:
        """Save the current index and metadata to disk."""
        try:
            if not self.documents:
                logger.warning("No documents to save")
                return False
            
            # Save FAISS index
            if FAISS_AVAILABLE and self.index:
                index_path = self.vector_db_path / "index.faiss"
                faiss.write_index(self.index, str(index_path))
            
            # Save documents
            docs_path = self.vector_db_path / "documents.pkl"
            with open(docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            # Save metadata
            metadata_path = self.vector_db_path / "metadata.json"
            metadata_info = {
                "embedding_model": self.embedding_model_name,
                "index_type": self.index_type,
                "document_count": len(self.documents),
                "created_at": time.time(),
                "documents": self.metadata
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved vector store with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            **self.stats,
            "cache_size": len(self.query_cache),
            "embedding_model": self.embedding_model_name,
            "index_type": self.index_type,
            "is_loaded": self.is_loaded
        }
    
    def clear_cache(self):
        """Clear the query cache."""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def rebuild_index(self) -> bool:
        """Rebuild the entire index from scratch."""
        try:
            if not self.documents:
                logger.warning("No documents to rebuild index")
                return False
            
            # Reset index
            self.index = None
            
            # Re-add all documents
            documents = self.documents.copy()
            metadata = self.metadata.copy()
            
            self.documents = []
            self.metadata = []
            
            return self.add_documents(documents, metadata)
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            return False
