"""
Enhanced HR Legal RAG (Retrieval Augmented Generation) System
Provides intelligent legal guidance for HR processes using FAISS vector database
Integration from Salvage backend with comprehensive legal knowledge base
"""

import logging
import json
import os
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import hashlib

# Safe imports with fallback handling
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    np = None
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class HRLegalRAGSystem:
    """Enhanced HR Legal RAG System with FAISS vector database and advanced legal analysis"""
    
    def __init__(self):
        """Initialize enhanced HR Legal RAG system with lazy loading for production"""
        self.vector_db = None
        self.embeddings_model = None
        self.legal_documents = []
        self.document_metadata = []
        self.query_cache = {}
        self.response_quality_threshold = 0.7
        
        # Production memory optimization flags
        self._model_loaded = False
        self._vector_db_loaded = False
        self._initialization_lock = asyncio.Lock() if hasattr(asyncio, 'Lock') else None
        
        # Railway deployment compatibility
        self.is_production = os.getenv('RAILWAY_ENVIRONMENT') == 'production'
        self.data_dir = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '.')
        
        # Enhanced file paths with Railway compatibility
        self.index_file = os.path.join(self.data_dir, "hr_legal_faiss.index")
        self.metadata_file = os.path.join(self.data_dir, "hr_legal_metadata.pkl")
        self.embeddings_file = os.path.join(self.data_dir, "hr_legal_embeddings.pkl")
        self.cache_file = os.path.join(self.data_dir, "query_cache.pkl")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Legal domain categories
        self.legal_categories = {
            "employment_law": ["hiring", "termination", "contracts", "workplace rights"],
            "labor_relations": ["unions", "collective bargaining", "strikes", "negotiations"],
            "discrimination": ["bias", "equal opportunity", "harassment", "accommodation"],
            "compensation": ["wages", "overtime", "benefits", "minimum wage"],
            "workplace_safety": ["osha", "safety regulations", "workplace injuries"],
            "privacy": ["employee privacy", "data protection", "surveillance"],
            "compliance": ["regulatory compliance", "audits", "reporting"]
        }
        
        # Initialize components with production safety - LAZY LOADING
        self.fallback_mode = not (FAISS_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE)
        if self.fallback_mode:
            logger.warning("FAISS or sentence-transformers not available, using enhanced fallback mode")
        
        # Production readiness check
        if self.is_production and self.fallback_mode:
            logger.warning("Production deployment detected with missing ML dependencies - fallback mode active")
        
        # Initialize only fallback system immediately - defer heavy loading
        logger.info("Initializing RAG system with lazy loading for production optimization")
        self.legal_knowledge_base = self._get_comprehensive_legal_knowledge()
        
        # Load query cache immediately (lightweight)
        self._load_query_cache()
        
        logger.info("RAG system initialized in lazy-loading mode")
        
    def _initialize_system(self):
        """DEPRECATED: Replaced by lazy loading for production optimization"""
        logger.warning("_initialize_system called - using lazy loading instead")
        pass
        
    async def _ensure_models_loaded(self):
        """Ensure models are loaded on-demand with memory optimization"""
        if self._model_loaded and self._vector_db_loaded:
            return True
            
        if self.fallback_mode:
            logger.info("Models loading skipped - fallback mode active")
            return False
            
        try:
            # Use lock to prevent concurrent loading in multiple threads
            if self._initialization_lock:
                async with self._initialization_lock:
                    return await self._load_models_safely()
            else:
                return await self._load_models_safely()
                
        except Exception as e:
            logger.error(f"Failed to load models on-demand: {e}")
            self.fallback_mode = True
            return False
            
    async def _load_models_safely(self):
        """Load models with memory monitoring and error handling"""
        if self._model_loaded and self._vector_db_loaded:
            return True
            
        try:
            logger.info("Loading ML models on-demand...")
            
            # Initialize sentence transformer model with Railway optimization
            if not self._model_loaded:
                model_name = os.getenv('SENTENCE_TRANSFORMER_MODEL', 'all-MiniLM-L6-v2')
                cache_folder = os.path.join(self.data_dir, 'model_cache')
                os.makedirs(cache_folder, exist_ok=True)
                
                logger.info(f"Loading sentence transformer model: {model_name}")
                
                # Load with timeout to prevent hanging
                def load_model():
                    return SentenceTransformer(model_name, cache_folder=cache_folder)
                
                self.embeddings_model = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, load_model),
                    timeout=300.0  # 5 minute timeout for model loading
                )
                
                self._model_loaded = True
                logger.info("✅ Sentence transformer model loaded successfully")
            
            # Load or create vector database
            if not self._vector_db_loaded:
                logger.info("Loading vector database...")
                await self._load_or_create_enhanced_vector_db_async()
                self._vector_db_loaded = True
                logger.info("✅ Vector database loaded successfully")
            
            # Load comprehensive legal knowledge base
            logger.info("Loading legal knowledge base...")
            self._load_comprehensive_legal_knowledge_base()
            logger.info("✅ Legal knowledge base loaded successfully")
            
            return True
            
        except asyncio.TimeoutError:
            logger.error("Model loading timed out - switching to fallback mode")
            self.fallback_mode = True
            return False
        except Exception as e:
            logger.error(f"Failed to load models safely: {e}")
            self.fallback_mode = True
            return False
    
    def _initialize_fallback_system(self):
        """Initialize enhanced fallback system for when FAISS is unavailable"""
        if not hasattr(self, 'legal_knowledge_base'):
            self.legal_knowledge_base = self._get_comprehensive_legal_knowledge()
        logger.info("Enhanced fallback legal system initialized")
            
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        return FAISS_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE
        
    async def _load_or_create_enhanced_vector_db_async(self):
        """Load existing enhanced vector database or create new comprehensive one - async version"""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
                # Load existing database asynchronously
                def load_existing_db():
                    vector_db = faiss.read_index(self.index_file)
                    with open(self.metadata_file, 'rb') as f:
                        metadata = pickle.load(f)
                    return vector_db, metadata
                
                self.vector_db, self.document_metadata = await asyncio.get_event_loop().run_in_executor(
                    None, load_existing_db
                )
                    
                logger.info(f"Loaded enhanced vector database with {len(self.document_metadata)} documents")
            else:
                # Create comprehensive new database
                await self._create_comprehensive_vector_db_async()
                
        except Exception as e:
            logger.error(f"Error loading enhanced vector database: {e}")
            await self._create_comprehensive_vector_db_async()
            
    def _load_or_create_enhanced_vector_db(self):
        """Synchronous wrapper for backward compatibility"""
        logger.warning("Using synchronous vector DB load - consider using async version")
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
                # Load existing database
                self.vector_db = faiss.read_index(self.index_file)
                
                with open(self.metadata_file, 'rb') as f:
                    self.document_metadata = pickle.load(f)
                    
                logger.info(f"Loaded enhanced vector database with {len(self.document_metadata)} documents")
            else:
                # Create comprehensive new database
                self._create_comprehensive_vector_db()
                
        except Exception as e:
            logger.error(f"Error loading enhanced vector database: {e}")
            self._create_comprehensive_vector_db()
            
    async def _create_comprehensive_vector_db_async(self):
        """Create comprehensive vector database with extensive HR legal documents - async version"""
        try:
            # Load comprehensive legal documents
            legal_documents = self._get_comprehensive_legal_knowledge()
            
            if not legal_documents:
                logger.warning("No legal documents found, creating basic database")
                return
            
            # Create embeddings for all documents asynchronously
            all_texts = []
            all_metadata = []
            
            for category, documents in legal_documents.items():
                for doc_id, doc_data in documents.items():
                    # Split document into chunks for better retrieval
                    chunks = self._split_document_into_chunks(doc_data["content"], chunk_size=500)
                    
                    for i, chunk in enumerate(chunks):
                        all_texts.append(chunk)
                        all_metadata.append({
                            "category": category,
                            "document_id": doc_id,
                            "chunk_id": i,
                            "title": doc_data["title"],
                            "source": doc_data.get("source", "Internal"),
                            "relevance_keywords": doc_data.get("keywords", []),
                            "content_preview": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                            "content": chunk
                        })
            
            if not all_texts:
                logger.warning("No text content found for vector database")
                return
            
            # Generate embeddings asynchronously
            logger.info(f"Generating embeddings for {len(all_texts)} document chunks...")
            
            def generate_embeddings():
                return self.embeddings_model.encode(all_texts)
            
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, generate_embeddings
            )
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.vector_db = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.vector_db.add(embeddings)
            
            # Store metadata
            self.document_metadata = all_metadata
            
            # Save to disk asynchronously
            def save_db():
                faiss.write_index(self.vector_db, self.index_file)
                with open(self.metadata_file, 'wb') as f:
                    pickle.dump(self.document_metadata, f)
            
            await asyncio.get_event_loop().run_in_executor(None, save_db)
            
            logger.info(f"Enhanced vector database created with {len(all_texts)} chunks from legal documents")
            
        except Exception as e:
            logger.error(f"Error creating comprehensive vector database: {e}")
            self.fallback_mode = True
    
    def _create_comprehensive_vector_db(self):
        """Synchronous wrapper for backward compatibility"""
        logger.warning("Using synchronous vector DB creation - consider using async version")
        try:
            # Load comprehensive legal documents
            legal_documents = self._get_comprehensive_legal_knowledge()
            
            if not legal_documents:
                logger.warning("No legal documents found, creating basic database")
                return
            
            # Create embeddings for all documents
            all_texts = []
            all_metadata = []
            
            for category, documents in legal_documents.items():
                for doc_id, doc_data in documents.items():
                    # Split document into chunks for better retrieval
                    chunks = self._split_document_into_chunks(doc_data["content"], chunk_size=500)
                    
                    for i, chunk in enumerate(chunks):
                        all_texts.append(chunk)
                        all_metadata.append({
                            "category": category,
                            "document_id": doc_id,
                            "chunk_id": i,
                            "title": doc_data["title"],
                            "source": doc_data.get("source", "Internal"),
                            "relevance_keywords": doc_data.get("keywords", []),
                            "content_preview": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                            "content": chunk
                        })
            
            if not all_texts:
                logger.warning("No text content found for vector database")
                return
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(all_texts)} document chunks...")
            embeddings = self.embeddings_model.encode(all_texts)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.vector_db = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.vector_db.add(embeddings)
            
            # Store metadata
            self.document_metadata = all_metadata
            
            # Save to disk
            faiss.write_index(self.vector_db, self.index_file)
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.document_metadata, f)
            
            logger.info(f"Enhanced vector database created with {len(all_texts)} chunks from legal documents")
            
        except Exception as e:
            logger.error(f"Error creating comprehensive vector database: {e}")
            self.fallback_mode = True
    
    def _load_comprehensive_legal_knowledge_base(self):
        """Load comprehensive legal knowledge base with file system integration"""
        try:
            # Load legal documents from legal_documents folder if available
            legal_docs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'legal_documents')
            
            if os.path.exists(legal_docs_path):
                logger.info(f"Loading legal documents from: {legal_docs_path}")
                
                for filename in os.listdir(legal_docs_path):
                    if filename.endswith('.txt'):
                        try:
                            filepath = os.path.join(legal_docs_path, filename)
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            # Create document metadata
                            doc_data = {
                                "id": f"legal_doc_{filename.replace('.txt', '')}",
                                "title": filename.replace('.txt', '').replace('_', ' ').title(),
                                "content": content,
                                "category": "legal_reference",
                                "source": filename,
                                "last_updated": datetime.now().strftime("%Y-%m-%d")
                            }
                            
                            self.legal_documents.append(doc_data)
                            logger.info(f"Loaded legal document: {doc_data['title']}")
                            
                        except Exception as e:
                            logger.error(f"Error loading {filename}: {e}")
                            
                logger.info(f"Loaded {len(self.legal_documents)} legal documents from filesystem")
            else:
                logger.info("Legal documents folder not found, using embedded knowledge base")
        except Exception as e:
            logger.error(f"Error loading legal knowledge base: {e}")
    
    def _split_document_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split document into overlapping chunks for better retrieval"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within reasonable range
                sentence_ends = ['. ', '? ', '! ', '\n\n']
                best_break = end
                
                for i in range(max(0, end - 100), min(len(text), end + 100)):
                    for ending in sentence_ends:
                        if i + len(ending) <= len(text) and text[i:i+len(ending)] == ending:
                            best_break = i + len(ending)
                            break
                    if best_break != end:
                        break
                
                end = best_break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
        return chunks
    
    def _get_comprehensive_legal_knowledge(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive HR legal knowledge base with Indian Labour Law focus"""
        return {
            "employment_law": {
                "hiring_practices": {
                    "title": "Indian Labour Law - Hiring Practices",
                    "content": """
                    Indian Labour Law Compliance for Hiring:
                    
                    1. Equal Employment Opportunity: All hiring must comply with Constitution Article 16 ensuring equality of opportunity in employment.
                    
                    2. Non-Discrimination: Employers cannot discriminate based on religion, race, caste, sex, place of birth (Article 15).
                    
                    3. Age Requirements: Minimum age for employment is 14 years under Child Labour (Prohibition and Regulation) Act, 1986.
                    
                    4. Documentation: Proper documentation required including Form I under Contract Labour Act, ESI and PF registration.
                    
                    5. Background Verification: Employers may conduct background checks but must respect privacy rights under IT Act, 2000.
                    
                    6. Offer Letters: Should clearly mention terms of employment, salary, probation period, and termination clauses.
                    
                    7. Medical Examination: Can be conducted if job-related and non-discriminatory.
                    
                    8. Probation Period: Generally 6 months, but can vary by company policy and role requirements.
                    
                    9. Notice Period: Standard notice periods range from 1-3 months depending on role and company policy.
                    
                    10. Salary Structure: Must comply with minimum wage requirements and equal pay provisions.
                    """,
                    "keywords": ["hiring", "recruitment", "employment", "discrimination", "compliance"],
                    "source": "Indian Labour Laws"
                },
                
                "termination_practices": {
                    "title": "Employee Termination - Legal Requirements",
                    "content": """
                    Legal Requirements for Employee Termination in India:
                    
                    1. Industrial Disputes Act: Applies to establishments with 100+ workers, requires government permission for termination.
                    
                    2. Notice Requirements: Proper notice period must be given or payment in lieu of notice.
                    
                    3. Due Process: Show cause notice, opportunity to explain, and proper documentation required.
                    
                    4. Severance Pay: Compensation as per company policy and legal requirements.
                    
                    5. Terminal Benefits: Final settlement including salary, leave encashment, PF, and gratuity.
                    
                    6. Non-Compete Clauses: Must be reasonable in duration, geography, and scope.
                    
                    7. Documentation: Proper records of performance issues, disciplinary actions required.
                    
                    8. Constructive Dismissal: Avoid creating hostile work environment leading to resignation.
                    
                    9. Wrongful Termination: Ensure termination is not discriminatory or retaliatory.
                    
                    10. Exit Procedures: Proper handover, return of company property, and final clearances.
                    """,
                    "keywords": ["termination", "dismissal", "severance", "notice period", "due process"],
                    "source": "Industrial Disputes Act"
                }
            },
            
            "labor_relations": {
                "union_relations": {
                    "title": "Trade Union Relations and Collective Bargaining",
                    "content": """
                    Trade Union Relations in Indian Labour Law:
                    
                    1. Trade Union Act 1926: Provides for registration and regulation of trade unions.
                    
                    2. Right to Association: Workers have fundamental right to form and join trade unions (Article 19).
                    
                    3. Recognition: Trade unions representing 51% of workers get recognition for collective bargaining.
                    
                    4. Collective Bargaining: Negotiations between employer and recognized trade union representatives.
                    
                    5. Industrial Relations Code 2020: New framework for industrial relations and dispute resolution.
                    
                    6. Strikes and Lockouts: Regulated under Industrial Disputes Act with specific notice requirements.
                    
                    7. Works Committees: Mandatory for establishments with 100+ workers to promote good relations.
                    
                    8. Grievance Procedures: Established mechanisms for resolving workplace disputes.
                    
                    9. Standing Orders: Written rules and regulations for conduct and conditions of employment.
                    
                    10. Tripartite Consultations: Government, employers, and workers' representatives participation.
                    """,
                    "keywords": ["trade union", "collective bargaining", "strikes", "industrial relations"],
                    "source": "Trade Union Act 1926"
                }
            },
            
            "discrimination": {
                "workplace_harassment": {
                    "title": "Prevention of Sexual Harassment at Workplace",
                    "content": """
                    Sexual Harassment Prevention under POSH Act 2013:
                    
                    1. POSH Act 2013: Prevention of Sexual Harassment of Women at Workplace Act.
                    
                    2. Internal Committee: Mandatory for organizations with 10+ employees.
                    
                    3. Definition: Includes unwelcome physical contact, demands, sexually colored remarks.
                    
                    4. Complaint Procedure: Written complaint within 3 months, investigation within 90 days.
                    
                    5. Interim Relief: Can include transfer of complainant or respondent during investigation.
                    
                    6. Penalties: Can include warning, censure, withholding promotion, termination.
                    
                    7. Annual Report filing: Mandatory submission to District Officer.
                    
                    8. Third Party Harassment: Act covers harassment by clients, customers, vendors.
                    
                    9. Confidentiality: Strict confidentiality requirements during investigation.
                    
                    10. Training Programs: Regular awareness and training programs required.
                    """,
                    "keywords": ["sexual harassment", "POSH", "discrimination", "workplace safety"],
                    "source": "POSH Act 2013"
                }
            },
            
            "compensation": {
                "minimum_wages": {
                    "title": "Minimum Wages and Payment Regulations",
                    "content": """
                    Minimum Wages Act 1948 and Payment Regulations:
                    
                    1. Minimum Wages Act: Ensures minimum rate of wages in scheduled employments.
                    
                    2. State Notifications: Each state notifies minimum wages for different categories.
                    
                    3. Revision: Wages revised every 5 years with intermediate reviews every 2 years.
                    
                    4. Payment of Wages Act: Regulates payment of wages to workers.
                    
                    5. Wage Period: Monthly wages paid by 7th of following month, weekly by 3rd day.
                    
                    6. Deductions: Limited deductions allowed under specific circumstances.
                    
                    7. Equal Pay: Equal remuneration for equal work regardless of gender.
                    
                    8. Overtime: Time and half for work beyond 8 hours daily or 48 hours weekly.
                    
                    9. Bonus: Payment of Bonus Act provides for annual bonus based on profits.
                    
                    10. PF and ESI: Mandatory contributions for social security schemes.
                    """,
                    "keywords": ["minimum wages", "payment", "overtime", "bonus", "deductions"],
                    "source": "Minimum Wages Act 1948"
                }
            },
            
            "workplace_safety": {
                "occupational_safety": {
                    "title": "Occupational Safety and Health Requirements",
                    "content": """
                    Occupational Safety and Health Code 2020:
                    
                    1. OSH Code 2020: Consolidates 13 labour laws related to safety and health.
                    
                    2. Employer Duties: Provide safe working environment, safety training, protective equipment.
                    
                    3. Risk Assessment: Regular assessment and mitigation of workplace hazards.
                    
                    4. Safety Committees: Mandatory for establishments with 250+ workers.
                    
                    5. Accident Reporting: Immediate reporting of accidents to authorities.
                    
                    6. Medical Examinations: Pre-employment and periodic health check-ups.
                    
                    7. Working Hours: Maximum 48 hours per week with provisions for overtime.
                    
                    8. Women's Safety: Special provisions for women workers' safety and health.
                    
                    9. Contract Workers: Equal safety standards for contract and regular employees.
                    
                    10. Penalties: Fines and imprisonment for non-compliance with safety regulations.
                    """,
                    "keywords": ["occupational safety", "workplace health", "OSH code", "safety training"],
                    "source": "Occupational Safety and Health Code 2020"
                }
            }
        }
    
    def _load_query_cache(self):
        """Load query cache from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    self.query_cache = pickle.load(f)
                logger.info(f"Loaded query cache with {len(self.query_cache)} entries")
            else:
                self.query_cache = {}
        except Exception as e:
            logger.error(f"Error loading query cache: {e}")
            self.query_cache = {}
    
    def _get_sample_legal_documents(self) -> List[Dict[str, Any]]:
        """Get sample legal documents for basic operation"""
        return [
            {
                "id": "hr_legal_001",
                "title": "Employee Hiring Guidelines - India",
                "content": """
                Indian Labour Law Guidelines for Employee Hiring:
                
                1. Equal Opportunity: Must provide equal employment opportunities regardless of caste, religion, gender.
                
                2. Age Requirements: Minimum employment age is 14 years under Child Labour Act.
                
                3. Documentation: Proper verification of identity and address documents required.
                
                4. Background Checks: Permissible but must respect privacy rights under IT Act 2000.
                
                5. Medical Examination: Can be conducted if job-related and non-discriminatory.
                
                6. Probation Period: Standard probation period is 6 months but can vary.
                
                7. Contract Terms: Clear mention of salary, working hours, leave policy required.
                
                8. PF and ESI: Mandatory registration for eligible employees.
                """,
                "category": "hiring_law",
                "jurisdiction": "India",
                "last_updated": "2024-01-01"
            },
            {
                "id": "hr_legal_002", 
                "title": "Employment Termination Laws - India",
                "content": """
                Employment Termination under Indian Labour Law:
                
                1. Industrial Disputes Act, 1947: Governs termination in industrial establishments with 100+ workers.
                
                2. Notice Period: Minimum 30 days notice or pay in lieu required for termination.
                
                3. Retrenchment Compensation: Under Section 25F, workers with 240+ days service entitled to compensation.
                
                4. Valid Grounds: Termination must be for valid reasons - misconduct, poor performance, redundancy, or business closure.
                
                5. Due Process: Proper disciplinary procedures must be followed including show cause notice and inquiry.
                
                6. Gratuity Payment: Employees with 5+ years service entitled to gratuity under Payment of Gratuity Act, 1972.
                
                7. Final Settlement: All dues including salary, bonus, leave encashment must be cleared within prescribed timelines.
                
                8. Wrongful Termination: Can lead to reinstatement orders and back wages by labour courts.
                """,
                "category": "termination_law",
                "jurisdiction": "India", 
                "last_updated": "2024-01-01"
            },
            {
                "id": "hr_legal_003",
                "title": "Workplace Harassment - Prevention and Compliance",
                "content": """
                Sexual Harassment Prevention under Sexual Harassment of Women at Workplace Act, 2013:
                
                1. Internal Committee (IC): Mandatory for organizations with 10+ employees.
                
                2. Committee Composition: Presiding officer (senior woman employee), 2 employees, 1 external NGO member.
                
                3. Policy Requirements: Written policy on sexual harassment prevention and complaint mechanism.
                
                4. Training: Regular awareness programs for employees and committee members.
                
                5. Complaint Process: Confidential complaint mechanism with time-bound inquiry (90 days).
                
                6. Interim Relief: Protection and support to complainant during inquiry process.
                
                7. Annual Report: Mandatory filing of annual report to District Officer.
                
                8. Penalties: Non-compliance can result in penalties up to Rs. 50,000 and cancellation of licenses.
                
                9. Safe Working Environment: Employer duty to provide safe and secure working environment.
                """,
                "category": "workplace_safety",
                "jurisdiction": "India",
                "last_updated": "2024-01-01"
            },
            {
                "id": "hr_legal_004",
                "title": "Employee Data Protection and Privacy",
                "content": """
                Employee Data Protection under IT Act, 2000 and Digital Personal Data Protection Act, 2023:
                
                1. Consent Requirements: Explicit consent required for processing personal data of employees.
                
                2. Data Minimization: Collect only necessary data for employment purposes.
                
                3. Purpose Limitation: Use data only for specified, legitimate purposes.
                
                4. Access Controls: Implement appropriate security measures to protect employee data.
                
                5. Retention Limits: Data should not be retained longer than necessary for business purposes.
                
                6. Employee Rights: Right to access, correct, and delete personal data (subject to legal requirements).
                
                7. Third Party Sharing: Explicit consent required before sharing with third parties.
                
                8. Breach Notification: Mandatory reporting of data breaches to authorities and affected individuals.
                
                9. Cross-border Transfer: Special provisions for transferring employee data outside India.
                """,
                "category": "data_protection", 
                "jurisdiction": "India",
                "last_updated": "2024-01-01"
            },
            {
                "id": "hr_legal_005",
                "title": "Wage and Hour Laws - Compliance",
                "content": """
                Indian Wage and Hour Law Compliance:
                
                1. Minimum Wages Act, 1948: Employers must pay at least minimum wages notified by government.
                
                2. Payment of Wages Act, 1936: Wages must be paid within 7 days for establishments with <1000 employees.
                
                3. Working Hours: Maximum 48 hours per week and 9 hours per day under Factories Act.
                
                4. Overtime: Overtime rates (double time) for work beyond 8 hours/day or 48 hours/week.
                
                5. Weekly Off: At least one day off in every week mandatory.
                
                6. Annual Leave: Minimum 12 days annual leave with wages after 240 days of work.
                
                7. Festival Holidays: Compensation for work on national holidays.
                
                8. Equal Pay: Equal pay for equal work regardless of gender (Equal Remuneration Act, 1976).
                
                9. Wage Deductions: Limited deductions allowed only as per statutory provisions.
                """,
                "category": "wage_hour_law",
                "jurisdiction": "India",
                "last_updated": "2024-01-01"
            }
        ]
        
    async def query_legal_knowledge(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Query the legal knowledge base using RAG with production optimizations and lazy loading"""
        try:
            # Input validation
            if not query or not query.strip():
                return self._get_empty_response("Empty query provided")
            
            query = query.strip()
            if len(query) > 1000:  # Prevent extremely long queries
                query = query[:1000]
                logger.warning("Query truncated to 1000 characters")
            
            # Check query cache first
            query_hash = hashlib.md5(query.encode()).hexdigest()
            if query_hash in self.query_cache:
                cached_response = self.query_cache[query_hash]
                logger.info("Returning cached response for query")
                return cached_response
            
            # Ensure models are loaded on-demand
            models_loaded = await self._ensure_models_loaded()
            
            if self.fallback_mode or not models_loaded:
                response = self._get_fallback_response(query)
            else:
                # Generate query embedding with timeout
                try:
                    query_embedding = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, 
                            lambda: self.embeddings_model.encode([query])
                        ),
                        timeout=30.0  # 30 second timeout
                    )
                    faiss.normalize_L2(query_embedding)
                except asyncio.TimeoutError:
                    logger.error("Query embedding generation timed out")
                    return self._get_fallback_response(query)
                
                # Search vector database
                similarities, indices = self.vector_db.search(query_embedding.astype(np.float32), top_k)
                
                # Get relevant documents with improved filtering
                relevant_docs = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.document_metadata) and similarities[0][i] > 0.15:  # Slightly higher threshold
                        doc = self.document_metadata[idx].copy()
                        doc['relevance_score'] = float(similarities[0][i])
                        relevant_docs.append(doc)
                        
                # Generate response using relevant documents
                response_data = await self._generate_legal_response(query, relevant_docs)
                
                response = {
                    "query": query,
                    "response": response_data,
                    "relevant_documents": relevant_docs,
                    "timestamp": datetime.utcnow().isoformat(),
                    "method": "rag_vector_search",
                    "system_status": "operational",
                    "lazy_loading": True,
                    "models_loaded": models_loaded
                }
            
            # Cache the response with size limit
            if len(self.query_cache) < 1000:  # Limit cache size
                self.query_cache[query_hash] = response
            
            # Save cache periodically
            if len(self.query_cache) % 10 == 0:
                asyncio.create_task(self._save_cache_async())
            
            return response
            
        except Exception as e:
            logger.error(f"Legal knowledge query error: {e}")
            return self._get_fallback_response(query)
            
    def _get_empty_response(self, message: str) -> Dict[str, Any]:
        """Return response for empty or invalid queries"""
        return {
            "query": "",
            "response": {
                "legal_analysis": message,
                "relevant_laws": [],
                "recommendations": ["Please provide a specific legal question or concern"],
                "risk_level": "Low",
                "compliance_steps": [],
                "sources": [],
                "confidence_score": 0.0
            },
            "relevant_documents": [],
            "timestamp": datetime.utcnow().isoformat(),
            "method": "validation_error",
            "system_status": "operational"
        }
            
    async def _save_cache_async(self):
        """Save cache asynchronously to prevent blocking"""
        try:
            def save_cache():
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.query_cache, f)
            
            await asyncio.get_event_loop().run_in_executor(None, save_cache)
            logger.debug("Query cache saved successfully")
        except Exception as e:
            logger.error(f"Error saving query cache asynchronously: {e}")
            
    async def _generate_legal_response(self, query: str, relevant_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate legal response using relevant documents"""
        try:
            if not relevant_docs:
                return {
                    "legal_analysis": "No relevant legal documents found for this query.",
                    "relevant_laws": [],
                    "recommendations": ["Consult with legal professional for specific guidance"],
                    "risk_level": "Medium",
                    "compliance_steps": [],
                    "sources": [],
                    "confidence_score": 0.1
                }
            
            # Combine relevant document content
            context_parts = []
            for doc in relevant_docs[:3]:  # Use top 3 most relevant documents
                content = doc.get('content', doc.get('content_preview', ''))
                if content:
                    context_parts.append(f"Source: {doc.get('title', 'Unknown')}\n{content}")
            
            context = "\n\n".join(context_parts)
            
            # Create response based on context
            response = {
                "legal_analysis": self._analyze_legal_context(query, context),
                "relevant_laws": self._extract_relevant_laws(context),
                "recommendations": self._generate_recommendations(query, context),
                "risk_level": self._assess_risk_level(query, context),
                "compliance_steps": self._get_compliance_steps(query, context),
                "sources": [doc.get('title', 'Unknown') for doc in relevant_docs],
                "confidence_score": min(sum(doc.get('relevance_score', 0) for doc in relevant_docs) / len(relevant_docs), 1.0) if relevant_docs else 0.1
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating legal response: {e}")
            return {
                "legal_analysis": "Unable to generate legal analysis due to processing error",
                "relevant_laws": [],
                "recommendations": ["Consult with legal professional"],
                "risk_level": "Medium", 
                "compliance_steps": [],
                "sources": [],
                "confidence_score": 0.1
            }
            
    def _analyze_legal_context(self, query: str, context: str) -> str:
        """Analyze legal context based on query and retrieved documents"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ['hire', 'hiring', 'recruitment', 'selection']):
            return "Based on Indian labour law, hiring practices must comply with equal opportunity and non-discrimination principles. Proper documentation and background verification procedures should be followed."
            
        elif any(term in query_lower for term in ['terminate', 'termination', 'fire', 'dismiss']):
            return "Employment termination in India requires compliance with Industrial Disputes Act and proper due process. Notice period, compensation, and valid grounds are essential requirements."
            
        elif any(term in query_lower for term in ['harassment', 'sexual harassment', 'workplace safety']):
            return "Sexual Harassment of Women at Workplace Act, 2013 mandates establishment of Internal Committee and implementation of prevention policies for organizations with 10+ employees."
            
        elif any(term in query_lower for term in ['data', 'privacy', 'personal information']):
            return "Employee data protection requires compliance with IT Act, 2000 and Digital Personal Data Protection Act, 2023. Explicit consent and security measures are mandatory."
            
        elif any(term in query_lower for term in ['wage', 'salary', 'overtime', 'working hours']):
            return "Wage and hour compliance involves adherence to Minimum Wages Act, Payment of Wages Act, and prescribed working hour limits with proper overtime compensation."
            
        else:
            return "This query pertains to HR legal compliance under Indian labour laws. Please refer to specific acts and regulations for detailed requirements."
            
    def _extract_relevant_laws(self, context: str) -> List[str]:
        """Extract relevant laws from context"""
        laws = []
        context_lower = context.lower()
        
        law_patterns = [
            ("Industrial Disputes Act, 1947", "industrial disputes act"),
            ("Sexual Harassment of Women at Workplace Act, 2013", "sexual harassment"),
            ("Minimum Wages Act, 1948", "minimum wages act"),
            ("Payment of Wages Act, 1936", "payment of wages act"),
            ("Child Labour (Prohibition and Regulation) Act, 1986", "child labour"),
            ("Equal Remuneration Act, 1976", "equal remuneration act"),
            ("IT Act, 2000", "it act"),
            ("Digital Personal Data Protection Act, 2023", "digital personal data protection"),
            ("Payment of Gratuity Act, 1972", "gratuity act"),
            ("Constitution of India Article 15", "article 15"),
            ("Constitution of India Article 16", "article 16")
        ]
        
        for law_name, pattern in law_patterns:
            if pattern in context_lower:
                laws.append(law_name)
                
        return laws
        
    def _generate_recommendations(self, query: str, context: str) -> List[str]:
        """Generate practical recommendations"""
        query_lower = query.lower()
        recommendations = []
        
        if 'hire' in query_lower or 'recruitment' in query_lower:
            recommendations.extend([
                "Ensure equal opportunity compliance in job postings",
                "Conduct non-discriminatory background verification",
                "Prepare clear offer letters with terms and conditions",
                "Maintain proper documentation for audit trails"
            ])
            
        elif 'terminate' in query_lower or 'dismissal' in query_lower:
            recommendations.extend([
                "Follow proper disciplinary procedures with show cause notice",
                "Provide adequate notice period or pay in lieu",
                "Calculate and pay all statutory dues including gratuity",
                "Maintain detailed records of termination process"
            ])
            
        elif 'harassment' in query_lower:
            recommendations.extend([
                "Establish Internal Committee with required composition",
                "Implement written anti-harassment policy",
                "Conduct regular awareness training programs",
                "File mandatory annual reports to District Officer"
            ])
            
        else:
            recommendations.extend([
                "Consult with qualified labour law attorney",
                "Review current policies for compliance gaps",
                "Maintain detailed documentation for legal protection",
                "Stay updated with latest regulatory changes"
            ])
            
        return recommendations
        
    def _assess_risk_level(self, query: str, context: str) -> str:
        """Assess risk level based on query and context"""
        query_lower = query.lower()
        
        high_risk_terms = ['terminate', 'harassment', 'discrimination', 'violation', 'penalty']
        medium_risk_terms = ['hire', 'data', 'privacy', 'wage', 'overtime']
        
        if any(term in query_lower for term in high_risk_terms):
            return "High"
        elif any(term in query_lower for term in medium_risk_terms):
            return "Medium"
        else:
            return "Low"
            
    def _get_compliance_steps(self, query: str, context: str) -> List[str]:
        """Get step-by-step compliance guidance"""
        query_lower = query.lower()
        
        if 'hire' in query_lower:
            return [
                "1. Create job description with essential requirements only",
                "2. Post job openings on equal opportunity basis",
                "3. Conduct fair and consistent interview process",
                "4. Perform lawful background verification",
                "5. Issue formal offer letter with clear terms",
                "6. Complete joining formalities and documentation"
            ]
            
        elif 'terminate' in query_lower:
            return [
                "1. Document performance issues and provide improvement opportunities",
                "2. Issue show cause notice if misconduct involved",
                "3. Conduct fair inquiry with proper representation",
                "4. Provide adequate notice period as per law",
                "5. Calculate final settlement including all statutory dues",
                "6. Issue experience certificate and complete exit formalities"
            ]
            
        elif 'harassment' in query_lower:
            return [
                "1. Form Internal Committee with required composition",
                "2. Draft and implement anti-harassment policy",
                "3. Display policy prominently in workplace",
                "4. Conduct regular awareness training",
                "5. Establish confidential complaint mechanism",
                "6. File annual compliance report to authorities"
            ]
            
        else:
            return [
                "1. Identify specific legal requirements applicable",
                "2. Review current practices for compliance gaps",
                "3. Develop implementation plan with timelines",
                "4. Train relevant personnel on procedures",
                "5. Monitor compliance and maintain records",
                "6. Seek legal counsel for complex matters"
            ]
            
    def _get_fallback_response(self, query: str) -> Dict[str, Any]:
        """Fallback response when RAG system unavailable - Railway optimized"""
        deployment_info = ""
        if self.is_production:
            deployment_info = " System running in production mode with limited ML capabilities."
        
        return {
            "query": query,
            "response": {
                "legal_analysis": f"Legal analysis unavailable - RAG system not operational.{deployment_info} Please consult with qualified legal professional for specific guidance.",
                "relevant_laws": ["Indian Labour Laws", "Constitution of India", "Industrial Disputes Act"],
                "recommendations": [
                    "Consult with qualified labour law attorney",
                    "Review latest government notifications and amendments",
                    "Maintain comprehensive compliance documentation",
                    "Seek professional legal advice for specific cases",
                    "Stay updated with ministry of labour notifications"
                ],
                "risk_level": "Medium",
                "compliance_steps": [
                    "Identify applicable legal requirements for your organization",
                    "Consult with experienced legal professionals",
                    "Implement recommended compliance practices",
                    "Establish regular monitoring and review processes",
                    "Maintain audit trails for all HR decisions"
                ],
                "sources": ["General HR Legal Guidelines", "Indian Labour Law Framework"],
                "confidence_score": 0.1
            },
            "relevant_documents": [],
            "timestamp": datetime.utcnow().isoformat(),
            "method": "fallback_response",
            "system_status": "fallback",
            "note": f"RAG system unavailable - using enhanced fallback mode. Production: {self.is_production}"
        }
        
    def add_legal_document(self, document: Dict[str, Any]) -> bool:
        """Add new legal document to the knowledge base"""
        try:
            if self.fallback_mode:
                logger.warning("Cannot add document - RAG system in fallback mode")
                return False
                
            # Generate embedding for new document
            embedding = self.embeddings_model.encode([document['content']])
            
            # Add to vector database
            self.vector_db.add(embedding.astype(np.float32))
            
            # Add metadata
            self.document_metadata.append(document)
            
            # Save updated database
            faiss.write_index(self.vector_db, self.index_file)
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.document_metadata, f)
                
            logger.info(f"Added new legal document: {document.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding legal document: {e}")
            return False
            
    def health_check(self) -> Dict[str, Any]:
        """Check RAG system health with production monitoring and lazy loading status"""
        try:
            # Basic system checks
            basic_status = {
                "system_status": "operational" if not self.fallback_mode else "fallback",
                "lazy_loading_enabled": True,
                "models_loaded": self._model_loaded,
                "vector_db_loaded": self._vector_db_loaded,
                "vector_db_available": self.vector_db is not None,
                "embeddings_model_available": self.embeddings_model is not None,
                "documents_indexed": len(self.document_metadata),
                "cache_size": len(self.query_cache),
                "is_production": self.is_production,
                "data_directory": self.data_dir,
                "dependencies": {
                    "faiss": faiss is not None,
                    "sentence_transformers": SentenceTransformer is not None,
                    "numpy": np is not None
                }
            }
            
            # Production-specific health checks
            if self.is_production:
                basic_status.update({
                    "railway_environment": os.getenv('RAILWAY_ENVIRONMENT'),
                    "volume_mount": os.getenv('RAILWAY_VOLUME_MOUNT_PATH'),
                    "disk_usage": self._check_disk_usage(),
                    "model_files_exist": {
                        "index": os.path.exists(self.index_file),
                        "metadata": os.path.exists(self.metadata_file),
                        "cache": os.path.exists(self.cache_file)
                    }
                })
                
            # Performance metrics
            if not self.fallback_mode and self.vector_db:
                try:
                    basic_status["vector_db_size"] = self.vector_db.ntotal
                    basic_status["embedding_dimension"] = self.vector_db.d if hasattr(self.vector_db, 'd') else "unknown"
                except:
                    pass
                    
            return basic_status
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "system_status": "error",
                "error": str(e),
                "is_production": self.is_production,
                "fallback_available": True,
                "lazy_loading_enabled": True
            }
            
    def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage for Railway deployment"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.data_dir)
            return {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2), 
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Disk usage check failed: {e}")
            return {"error": "Unable to check disk usage"}
        
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        categories = {}
        for doc in self.document_metadata:
            category = doc.get('category', 'uncategorized')
            categories[category] = categories.get(category, 0) + 1
            
        return {
            "total_documents": len(self.document_metadata),
            "categories": categories,
            "last_updated": max([doc.get('last_updated', '2024-01-01') for doc in self.document_metadata]) if self.document_metadata else None,
            "system_mode": "vector_search" if not self.fallback_mode else "fallback"
        }

# Global RAG system instance
_global_rag_system = None

def get_rag_system():
    """Get global RAG system instance"""
    global _global_rag_system
    if _global_rag_system is None:
        _global_rag_system = HRLegalRAGSystem()
    return _global_rag_system

# Convenience functions
async def query_hr_legal(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Query HR legal knowledge base"""
    rag_system = get_rag_system()
    return await rag_system.query_legal_knowledge(query, top_k)

def add_legal_document(document: Dict[str, Any]) -> bool:
    """Add legal document to knowledge base"""
    rag_system = get_rag_system()
    return rag_system.add_legal_document(document)

def get_rag_health() -> Dict[str, Any]:
    """Get RAG system health status"""
    rag_system = get_rag_system()
    return rag_system.health_check()
