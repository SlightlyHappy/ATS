"""
Railway Database Schema for AI Resume Analysis System

This file documents the complete database schema that will be created
automatically upon Railway deployment.
"""

# =============================================================================
# USERS TABLE - User accounts and authentication
# =============================================================================
users_table = """
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    
    -- Credit system
    credits_balance INTEGER DEFAULT 10,
    total_credits_purchased INTEGER DEFAULT 0,
    total_credits_used INTEGER DEFAULT 0,
    last_credit_transaction TIMESTAMP,
    
    -- Subscription info
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_admin ON users(is_admin);
CREATE INDEX idx_users_credits ON users(credits_balance);
"""

# =============================================================================
# CREDIT_TRANSACTIONS TABLE - Credit transaction history
# =============================================================================
credit_transactions_table = """
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('credit', 'debit')),
    amount INTEGER NOT NULL,
    description VARCHAR(255),
    balance_after INTEGER NOT NULL,
    
    -- References to what caused this transaction
    resume_id UUID REFERENCES resumes(id),
    analysis_id UUID REFERENCES analyses(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for credit_transactions table
CREATE INDEX idx_credits_user_id ON credit_transactions(user_id);
CREATE INDEX idx_credits_created ON credit_transactions(created_at);
CREATE INDEX idx_credits_type ON credit_transactions(transaction_type);
"""

# =============================================================================
# BATCH_UPLOADS TABLE - Batch upload tracking
# =============================================================================
batch_uploads_table = """
CREATE TABLE batch_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    batch_name VARCHAR(255),
    total_resumes INTEGER NOT NULL,
    processed_resumes INTEGER DEFAULT 0,
    successful_analyses INTEGER DEFAULT 0,
    failed_analyses INTEGER DEFAULT 0,
    
    status VARCHAR(20) DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    credits_used INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes for batch_uploads table
CREATE INDEX idx_batch_user_id ON batch_uploads(user_id);
CREATE INDEX idx_batch_status ON batch_uploads(status);
CREATE INDEX idx_batch_created ON batch_uploads(created_at);
"""

# =============================================================================
# RESUMES TABLE - Resume files and metadata
# =============================================================================
resumes_table = """
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    batch_upload_id UUID REFERENCES batch_uploads(id),
    
    -- File information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    
    -- Extracted content (stored in database for quick access)
    raw_text TEXT,  -- Complete extracted text
    structured_data JSONB,  -- Parsed resume structure
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending' 
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Indexes for resumes table
CREATE INDEX idx_resumes_user_id ON resumes(user_id);
CREATE INDEX idx_resumes_status ON resumes(processing_status);
CREATE INDEX idx_resumes_batch ON resumes(batch_upload_id);
CREATE INDEX idx_resumes_created ON resumes(created_at);
CREATE INDEX idx_resumes_filename ON resumes(filename);

-- Full text search index for resume content
CREATE INDEX idx_resumes_text_search ON resumes USING gin(to_tsvector('english', raw_text));
"""

# =============================================================================
# ANALYSES TABLE - AI analysis results
# =============================================================================
analyses_table = """
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    
    -- Analysis metadata
    analysis_type VARCHAR(50) DEFAULT 'full',
    status VARCHAR(20) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    model_used VARCHAR(100),
    
    -- Overall results
    overall_score FLOAT,
    scores_breakdown JSONB,  -- Individual agent scores
    
    -- Individual agent results (stored as JSONB for flexibility)
    technical_skills_result JSONB,
    experience_result JSONB,
    education_result JSONB,
    soft_skills_result JSONB,
    
    -- Summary results
    strengths TEXT[],  -- Array of strength points
    weaknesses TEXT[], -- Array of weakness points
    recommendations TEXT[], -- Array of recommendations
    
    -- Indian market specific results
    indian_market_assessment JSONB,
    cultural_fit_score FLOAT,
    regulatory_knowledge_score FLOAT,
    
    -- Processing metadata
    processing_time FLOAT,  -- Time taken in seconds
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes for analyses table
CREATE INDEX idx_analyses_resume_id ON analyses(resume_id);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_score ON analyses(overall_score);
CREATE INDEX idx_analyses_created ON analyses(created_at);
CREATE INDEX idx_analyses_model ON analyses(model_used);

-- GIN index for JSONB fields
CREATE INDEX idx_analyses_scores_breakdown ON analyses USING gin(scores_breakdown);
CREATE INDEX idx_analyses_indian_assessment ON analyses USING gin(indian_market_assessment);
"""

# =============================================================================
# ANALYSIS_QUEUE TABLE - Queue management
# =============================================================================
analysis_queue_table = """
CREATE TABLE analysis_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES analyses(id),
    
    status VARCHAR(20) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 1,  -- Higher number = higher priority
    
    -- Queue metadata
    queue_position INTEGER,
    estimated_completion_time TIMESTAMP,
    
    -- Processing info
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for analysis_queue table
CREATE INDEX idx_queue_status ON analysis_queue(status);
CREATE INDEX idx_queue_priority ON analysis_queue(priority DESC, created_at);
CREATE INDEX idx_queue_user ON analysis_queue(user_id);
CREATE INDEX idx_queue_position ON analysis_queue(queue_position);
CREATE INDEX idx_queue_resume ON analysis_queue(resume_id);

-- Unique constraint to prevent duplicate queue entries
CREATE UNIQUE INDEX idx_queue_unique_resume ON analysis_queue(resume_id) 
    WHERE status IN ('pending', 'processing');
"""

# =============================================================================
# STORAGE ESTIMATES FOR RAILWAY
# =============================================================================
storage_estimates = """
STORAGE REQUIREMENTS ESTIMATE:

1. USERS TABLE:
   - ~1KB per user
   - 10,000 users = ~10MB

2. RESUMES TABLE:
   - File metadata: ~2KB per resume
   - Raw text: ~50KB per resume (average)
   - Structured data: ~10KB per resume
   - Total: ~62KB per resume
   - 100,000 resumes = ~6.2GB

3. ANALYSES TABLE:
   - Analysis results: ~100KB per analysis (comprehensive JSONB)
   - 100,000 analyses = ~10GB

4. QUEUE TABLES:
   - ~1KB per queue item
   - Temporary data, minimal storage

5. CREDIT TRANSACTIONS:
   - ~500 bytes per transaction
   - 1,000,000 transactions = ~500MB

TOTAL ESTIMATED DATABASE SIZE:
- For 100,000 resumes with analyses: ~16-17GB
- For 10,000 resumes with analyses: ~1.7GB

RAILWAY POSTGRESQL LIMITS:
- Hobby Plan: 1GB storage (suitable for ~5,000 resumes)
- Pro Plan: 8GB storage (suitable for ~45,000 resumes)
- Enterprise: Custom limits

FILE STORAGE (separate from database):
- Resume files stored in Railway's filesystem or external storage
- Average resume file: 500KB - 2MB
- 10,000 resumes ≈ 5-20GB file storage
"""

# =============================================================================
# PERFORMANCE OPTIMIZATION NOTES
# =============================================================================
performance_notes = """
PERFORMANCE OPTIMIZATIONS IMPLEMENTED:

1. INDEXING STRATEGY:
   - Primary keys (UUID) with btree indexes
   - Foreign key indexes for join performance
   - Composite indexes for common query patterns
   - GIN indexes for JSONB and full-text search

2. DATA TYPES:
   - UUID for primary keys (better than sequential IDs)
   - JSONB for flexible analysis results storage
   - TEXT arrays for lists (strengths, weaknesses)
   - Appropriate VARCHAR lengths for optimization

3. CONSTRAINTS:
   - CHECK constraints for data integrity
   - Foreign key constraints with CASCADE
   - Unique constraints to prevent duplicates

4. QUERY OPTIMIZATION:
   - Indexes on frequently queried columns
   - Composite indexes for multi-column queries
   - Partial indexes where appropriate

5. STORAGE OPTIMIZATION:
   - JSONB compression for large analysis results
   - Text arrays instead of separate tables for lists
   - Appropriate column sizing
"""
