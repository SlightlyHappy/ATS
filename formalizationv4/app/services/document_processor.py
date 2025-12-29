"""
Document Processing Service for Legal RAG System
Handles text extraction, chunking, and embedding generation
"""
import os
import glob
import logging
import asyncio
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import nltk
from sentence_transformers import SentenceTransformer
import tiktoken

from app import db
from app.models.legal import LegalDocument, DocumentChunk, KnowledgeBaseUpdate, DocumentType, ProcessingStatus
from app.config import Config

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles legal document processing for RAG system"""
    
    def __init__(self):
        self.embedding_model = None
        self.tokenizer = None
        self.chunk_size = Config.RAG_CHUNK_SIZE
        self.chunk_overlap = Config.RAG_CHUNK_OVERLAP
        self.legal_docs_path = Config.LEGAL_DOCS_PATH
        
        # Download required NLTK data if not present
        self._ensure_nltk_data()
    
    def _ensure_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab', quiet=True)
    
    async def initialize_models(self):
        """Initialize embedding model and tokenizer"""
        try:
            logger.info("🔧 Starting document processor initialization...")
            logger.info(f"📊 Target embedding model: {Config.LEGAL_EMBEDDING_MODEL}")
            logger.info(f"📏 Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}")
            
            # Initialize embedding model with progress tracking
            logger.info("📥 Loading SentenceTransformer model...")
            logger.info("⏳ This may take several minutes on first run (downloading model)...")
            logger.info("🌐 Checking internet connectivity for model download...")
            
            try:
                # Add timeout and better error handling
                import signal
                import functools
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Model initialization timed out")
                
                # Set timeout for model loading (10 minutes)
                if hasattr(signal, 'SIGALRM'):  # Unix systems
                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(600)  # 10 minutes timeout
                
                logger.info("🚀 Starting SentenceTransformer initialization...")
                self.embedding_model = SentenceTransformer(Config.LEGAL_EMBEDDING_MODEL)
                
                if hasattr(signal, 'SIGALRM'):  # Unix systems
                    signal.alarm(0)  # Cancel timeout
                    signal.signal(signal.SIGALRM, old_handler)
                    
                logger.info("✅ SentenceTransformer model loaded successfully")
                
                # Test the model
                logger.info("🧪 Testing embedding model...")
                test_text = "This is a test sentence for the embedding model."
                test_embedding = self.embedding_model.encode([test_text])
                logger.info(f"✅ Model test successful - embedding shape: {test_embedding.shape}")
                
            except TimeoutError:
                logger.error("❌ Model initialization timed out after 10 minutes")
                logger.error("🌐 This usually indicates network connectivity issues")
                raise
            except Exception as model_error:
                logger.error(f"❌ Failed to load embedding model: {str(model_error)}")
                logger.error(f"📋 Model error type: {type(model_error).__name__}")
                import traceback
                logger.error(f"📋 Model traceback: {traceback.format_exc()}")
                raise
            
            # Initialize tokenizer for chunk size calculation
            logger.info("🔧 Initializing tokenizer...")
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
                logger.info("✅ Tiktoken tokenizer initialized")
            except Exception as tokenizer_error:
                logger.warning(f"⚠️  Could not initialize tiktoken: {str(tokenizer_error)}")
                logger.warning("🔄 Falling back to character-based chunking")
                self.tokenizer = None
            
            logger.info("🎉 Document processor initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize document processor: {str(e)}")
            logger.error(f"📋 Error type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            raise
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from .txt file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                    return content
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, try with error handling
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            logger.warning(f"Had to use error replacement for {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove special characters that might interfere with processing
        # But keep legal document formatting
        text = text.replace('\x00', '')  # Remove null bytes
        text = text.replace('\ufeff', '')  # Remove BOM
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def _create_chunks(self, text: str, filename: str) -> List[Dict]:
        """Split text into chunks with metadata"""
        chunks = []
        
        # Use NLTK sentence tokenization for better legal text chunking
        try:
            sentences = nltk.sent_tokenize(text)
        except Exception:
            # Fallback to simple sentence splitting
            sentences = text.split('. ')
        
        current_chunk = ""
        current_word_count = 0
        chunk_index = 0
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Calculate sentence length
            if self.tokenizer:
                sentence_tokens = len(self.tokenizer.encode(sentence))
                chunk_tokens = len(self.tokenizer.encode(current_chunk))
                
                # Check if adding this sentence would exceed chunk size
                if chunk_tokens + sentence_tokens > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunks.append(self._create_chunk_dict(
                        current_chunk, chunk_index, filename, current_word_count
                    ))
                    
                    # Start new chunk with overlap
                    overlap_sentences = self._get_overlap_sentences(sentences, i, filename)
                    current_chunk = overlap_sentences + " " + sentence
                    current_word_count = len(current_chunk.split())
                    chunk_index += 1
                else:
                    # Add sentence to current chunk
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
                    current_word_count = len(current_chunk.split())
            else:
                # Character-based chunking fallback
                if len(current_chunk) + len(sentence) > self.chunk_size * 4 and current_chunk:  # Approximate
                    chunks.append(self._create_chunk_dict(
                        current_chunk, chunk_index, filename, current_word_count
                    ))
                    current_chunk = sentence
                    current_word_count = len(current_chunk.split())
                    chunk_index += 1
                else:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
                    current_word_count = len(current_chunk.split())
        
        # Add final chunk if it exists
        if current_chunk.strip():
            chunks.append(self._create_chunk_dict(
                current_chunk, chunk_index, filename, current_word_count
            ))
        
        return chunks
    
    def _get_overlap_sentences(self, sentences: List[str], current_index: int, filename: str) -> str:
        """Get overlap sentences for context continuity"""
        overlap_tokens = self.chunk_overlap
        overlap_sentences = []
        
        # Go backwards from current sentence to get overlap
        for i in range(current_index - 1, -1, -1):
            sentence = sentences[i].strip()
            if not sentence:
                continue
            
            if self.tokenizer:
                sentence_tokens = len(self.tokenizer.encode(sentence))
                current_overlap_tokens = len(self.tokenizer.encode(" ".join(overlap_sentences)))
                
                if current_overlap_tokens + sentence_tokens <= overlap_tokens:
                    overlap_sentences.insert(0, sentence)
                else:
                    break
            else:
                # Character-based overlap fallback
                if len(" ".join(overlap_sentences)) + len(sentence) <= overlap_tokens * 4:
                    overlap_sentences.insert(0, sentence)
                else:
                    break
        
        return " ".join(overlap_sentences)
    
    def _create_chunk_dict(self, content: str, index: int, filename: str, word_count: int) -> Dict:
        """Create chunk dictionary with metadata"""
        return {
            'content': content.strip(),
            'chunk_index': index,
            'content_hash': DocumentChunk.generate_content_hash(content.strip()),
            'metadata': {
                'source_file': filename,
                'chunk_index': index,
                'word_count': word_count,
                'character_count': len(content),
                'created_at': datetime.utcnow().isoformat()
            },
            'word_count': word_count,
            'character_count': len(content)
        }
    
    async def _generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for text chunks"""
        if not self.embedding_model:
            await self.initialize_models()
        
        # Extract content for batch embedding generation
        contents = [chunk['content'] for chunk in chunks]
        
        try:
            # Generate embeddings in batch for efficiency
            embeddings = self.embedding_model.encode(
                contents,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Add embeddings to chunks
            for i, chunk in enumerate(chunks):
                chunk['embedding_vector'] = embeddings[i].tolist()
                chunk['embedding_model'] = Config.LEGAL_EMBEDDING_MODEL
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    async def process_single_document(self, file_path: str, update_id: Optional[str] = None) -> Tuple[bool, str]:
        """Process a single legal document"""
        filename = os.path.basename(file_path)
        
        try:
            logger.info(f"Processing document: {filename}")
            
            # Extract and clean text
            raw_text = self._extract_text_from_file(file_path)
            cleaned_text = self._clean_text(raw_text)
            
            if not cleaned_text.strip():
                return False, f"Document {filename} is empty after cleaning"
            
            # Generate content hash
            content_hash = LegalDocument.generate_content_hash(cleaned_text)
            file_size = os.path.getsize(file_path)
            
            # Check if document already exists and is up to date
            existing_doc = LegalDocument.query.filter_by(filename=filename).first()
            if existing_doc and existing_doc.content_hash == content_hash:
                logger.info(f"Document {filename} already up to date")
                return True, f"Document {filename} already processed"
            
            # Create or update document record
            if existing_doc:
                document = existing_doc
                document.processing_status = ProcessingStatus.PROCESSING
                document.processing_started_at = datetime.utcnow()
                
                # Delete existing chunks
                DocumentChunk.query.filter_by(document_id=document.id).delete()
            else:
                document = LegalDocument(
                    filename=filename,
                    title=self._extract_title(cleaned_text, filename),
                    document_type=self._classify_document_type(filename, cleaned_text),
                    content_hash=content_hash,
                    file_size=file_size,
                    processing_status=ProcessingStatus.PROCESSING,
                    processing_started_at=datetime.utcnow()
                )
                db.session.add(document)
                db.session.flush()  # Get the ID
            
            # Create text chunks
            chunks = self._create_chunks(cleaned_text, filename)
            
            # Generate embeddings
            chunks_with_embeddings = await self._generate_embeddings(chunks)
            
            # Store chunks in database
            for chunk_data in chunks_with_embeddings:
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_data['chunk_index'],
                    content=chunk_data['content'],
                    content_hash=chunk_data['content_hash'],
                    embedding_vector=chunk_data['embedding_vector'],
                    embedding_model=chunk_data['embedding_model'],
                    doc_metadata=chunk_data['metadata'],
                    word_count=chunk_data['word_count'],
                    character_count=chunk_data['character_count']
                )
                db.session.add(chunk)
            
            # Update document status
            document.total_chunks = len(chunks_with_embeddings)
            document.processing_status = ProcessingStatus.COMPLETED
            document.processing_completed_at = datetime.utcnow()
            document.processing_error = None
            
            db.session.commit()
            
            logger.info(f"Successfully processed {filename}: {len(chunks_with_embeddings)} chunks created")
            return True, f"Processed {filename} with {len(chunks_with_embeddings)} chunks"
            
        except Exception as e:
            logger.error(f"Failed to process document {filename}: {str(e)}")
            
            # Update document status on failure
            if 'document' in locals():
                document.processing_status = ProcessingStatus.FAILED
                document.processing_error = str(e)
                document.processing_completed_at = datetime.utcnow()
                db.session.commit()
            
            return False, f"Failed to process {filename}: {str(e)}"
    
    def _extract_title(self, text: str, filename: str) -> str:
        """Extract or generate document title"""
        lines = text.split('\n')
        
        # Look for title in first few lines
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                # This could be a title
                if not line.lower().startswith(('page', 'chapter', 'section')):
                    return line
        
        # Fallback to filename without extension
        return Path(filename).stem.replace('_', ' ').replace('-', ' ').title()
    
    def _classify_document_type(self, filename: str, content: str) -> DocumentType:
        """Classify document type based on filename and content"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Check filename for clues
        if any(word in filename_lower for word in ['textbook', 'book', 'manual', 'guide']):
            return DocumentType.TEXTBOOK
        elif any(word in filename_lower for word in ['code', 'act', 'law', 'statute']):
            return DocumentType.LEGAL_CODE
        elif any(word in filename_lower for word in ['case', 'judgment', 'ruling']):
            return DocumentType.CASE_LAW
        elif any(word in filename_lower for word in ['regulation', 'rule', 'circular']):
            return DocumentType.REGULATION
        elif any(word in filename_lower for word in ['policy', 'guidelines']):
            return DocumentType.POLICY
        
        # Check content for clues
        if any(phrase in content_lower for phrase in ['supreme court', 'high court', 'vs.', 'judgment']):
            return DocumentType.CASE_LAW
        elif any(phrase in content_lower for phrase in ['section', 'subsection', 'chapter']):
            return DocumentType.LEGAL_CODE
        elif 'regulation' in content_lower or 'rule' in content_lower:
            return DocumentType.REGULATION
        
        return DocumentType.OTHER
    
    async def process_all_documents(self, update_type: str = 'full_rebuild', trigger: str = 'manual') -> Dict:
        """Process all documents in the legal documents folder"""
        logger.info(f"🚀 Starting document processing: type={update_type}, trigger={trigger}")
        
        update_record = KnowledgeBaseUpdate(
            update_type=update_type,
            trigger=trigger,
            status='processing',
            started_at=datetime.utcnow()
        )
        db.session.add(update_record)
        db.session.commit()
        logger.info(f"📝 Created update record with ID: {update_record.id}")
        
        try:
            # Ensure models are initialized
            logger.info("🔧 Checking model initialization...")
            if not self.embedding_model:
                logger.info("🤖 Models not initialized, initializing now...")
                await self.initialize_models()
            else:
                logger.info("✅ Models already initialized")
            
            # Find all .txt files
            logger.info(f"📁 Scanning for .txt files in: {self.legal_docs_path}")
            txt_files = glob.glob(os.path.join(self.legal_docs_path, "*.txt"))
            
            if not txt_files:
                logger.warning(f"⚠️  No .txt files found in {self.legal_docs_path}")
                update_record.status = 'completed'
                update_record.completed_at = datetime.utcnow()
                update_record.error_message = "No .txt files found"
                db.session.commit()
                return {'status': 'completed', 'message': 'No files to process'}
            
            logger.info(f"📚 Found {len(txt_files)} documents to process:")
            for i, file_path in enumerate(txt_files, 1):
                logger.info(f"  {i}. {os.path.basename(file_path)}")
            
            processed_count = 0
            failed_count = 0
            total_chunks = 0
            
            for i, file_path in enumerate(txt_files, 1):
                try:
                    filename = os.path.basename(file_path)
                    logger.info(f"📄 Processing document {i}/{len(txt_files)}: {filename}")
                    
                    success, message = await self.process_single_document(file_path, str(update_record.id))
                    
                    if success:
                        processed_count += 1
                        # Count chunks for this document
                        doc = LegalDocument.query.filter_by(filename=filename).first()
                        if doc:
                            total_chunks += doc.total_chunks
                            logger.info(f"  ✅ Success: {doc.total_chunks} chunks created")
                        else:
                            logger.info(f"  ✅ Success: Document processed")
                    else:
                        failed_count += 1
                        logger.error(f"  ❌ Failed: {message}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"  💥 Exception processing {filename}: {str(e)}")
                    import traceback
                    logger.error(f"     Traceback: {traceback.format_exc()}")
            
            # Update completion record
            logger.info(f"📊 Processing summary: {processed_count} successful, {failed_count} failed")
            update_record.documents_processed = processed_count
            update_record.chunks_created = total_chunks
            update_record.status = 'completed' if failed_count == 0 else 'partial_failure'
            update_record.completed_at = datetime.utcnow()
            update_record.processing_time = (update_record.completed_at - update_record.started_at).total_seconds()
            
            # Update total statistics
            update_record.total_documents = LegalDocument.query.count()
            update_record.total_chunks = DocumentChunk.query.count()
            
            if failed_count > 0:
                update_record.error_message = f"{failed_count} documents failed to process"
            
            db.session.commit()
            
            result = {
                'status': 'completed' if failed_count == 0 else 'partial_failure',
                'processed': processed_count,
                'failed': failed_count,
                'total_chunks': total_chunks,
                'processing_time': update_record.processing_time
            }
            
            logger.info(f"Document processing completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            update_record.status = 'failed'
            update_record.error_message = str(e)
            update_record.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    async def check_for_updates(self) -> Dict:
        """Check for new or updated documents"""
        if not os.path.exists(self.legal_docs_path):
            return {'new_files': [], 'updated_files': []}
        
        txt_files = glob.glob(os.path.join(self.legal_docs_path, "*.txt"))
        new_files = []
        updated_files = []
        
        for file_path in txt_files:
            filename = os.path.basename(file_path)
            existing_doc = LegalDocument.query.filter_by(filename=filename).first()
            
            if not existing_doc:
                new_files.append(file_path)
            else:
                # Check if file has been modified
                try:
                    current_text = self._extract_text_from_file(file_path)
                    current_text = self._clean_text(current_text)
                    current_hash = LegalDocument.generate_content_hash(current_text)
                    
                    if current_hash != existing_doc.content_hash:
                        updated_files.append(file_path)
                        
                except Exception as e:
                    logger.error(f"Error checking file {file_path}: {str(e)}")
        
        return {
            'new_files': new_files,
            'updated_files': updated_files,
            'total_files': len(txt_files)
        }
