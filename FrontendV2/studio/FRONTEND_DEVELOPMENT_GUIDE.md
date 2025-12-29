# 🚀 HR ATS System - Complete Frontend Development Guide

## 📋 System Overview

This is a comprehensive B2B SaaS HR Applicant Tracking System with advanced AI-powered resume analysis, HR legal consultation, and intelligent credit management. The system features a sophisticated multi-tier architecture designed for enterprise scalability.

## 🏗️ System Architecture

### Core Technology Stack
- **Backend**: Flask-based Python API with Railway deployment (32GB RAM/32 CPU cores)
- **Database**: **Railway PostgreSQL (PRIMARY)** + Supabase PostgreSQL (backup) + SQLite (cache)
- **AI Engine**: 4-Agent AI system with premium routing (Ollama local + OpenAI/Anthropic premium)
- **Authentication**: Dual-layer auth system (JWT + database sessions)
- **Credit System**: B2B SaaS monetization with trial limits and premium tiers
- **Infrastructure**: Railway Pro deployment with connection pooling and circuit breakers

### Data Flow Architecture
```
User Upload → File Processing → AI Analysis → Database Storage → Frontend Display
     ↓              ↓               ↓              ↓              ↓
   PDF/DOCX    Text Extraction   4 AI Agents   PostgreSQL    React Dashboard
   Images      OCR Processing    + Legal RAG    + Supabase    + Admin Panel
```

## 🗄️ Railway PostgreSQL Database Architecture

### Database Priority System
1. **Railway PostgreSQL (PRIMARY)** - All production operations, high performance
2. **Supabase PostgreSQL (BACKUP)** - Authentication + backup sync
3. **SQLite (CACHE)** - Local performance optimization

### Connection Architecture
- **Connection Pool**: 5-20 threaded connections with circuit breaker
- **Health Monitoring**: Performance metrics and automatic failover
- **Optimization**: JSONB fields for AI analysis, comprehensive indexing

### Core Database Schema (Railway PostgreSQL)

#### Users & Authentication Tables
```sql
-- Core user table with INTEGER primary keys
users (
    id BIGINT PRIMARY KEY,          -- Railway uses integer IDs
    supabase_uuid UUID,             -- For backup sync mapping
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    access_type VARCHAR(50),        -- 'trial', 'full', 'enterprise'
    trial_resumes_analyzed BIGINT,
    created_at TIMESTAMP
)

-- User sessions for authentication
user_sessions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    session_token VARCHAR(255),
    expires_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
)
```

#### Resume Storage & Analysis
```sql
-- Resume storage with AI analysis
resumes (
    id BIGINT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    filename VARCHAR(255),
    file_hash VARCHAR(255),
    file_size INTEGER,
    file_type VARCHAR(50),
    
    -- AI Analysis Results (JSONB for performance)
    ai_analysis JSONB,              -- Complete 4-agent analysis
    technical_score INTEGER,
    experience_score INTEGER,
    cultural_fit_score INTEGER,
    legal_compliance JSONB,
    
    -- Processing status
    processing_status VARCHAR(20),  -- 'pending', 'processing', 'completed'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

#### Credit Management System
```sql
-- User credit tracking
user_credits (
    id BIGINT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    trial_credits INTEGER DEFAULT 100,
    premium_credits INTEGER DEFAULT 0,
    total_used INTEGER DEFAULT 0,
    is_trial_exhausted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Credit transaction history
credit_transactions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    transaction_type VARCHAR(20),   -- 'deduct', 'add', 'purchase'
    credit_type VARCHAR(20),        -- 'trial', 'premium'
    amount INTEGER,
    balance_after INTEGER,
    description TEXT,
    metadata JSONB,
    timestamp TIMESTAMP
)
```

### CRUD Operations Examples

#### Create Operations
```javascript
// Create new resume record
const createResume = async (resumeData) => {
    const response = await fetch('/api/upload', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: resumeData.filename,
            file_type: resumeData.type,
            file_size: resumeData.size
        })
    });
    return response.json();
};
```

#### Read Operations
```javascript
// Get user's resumes with pagination
const getUserResumes = async (page = 1, limit = 10) => {
    const response = await fetch(`/api/resumes?page=${page}&limit=${limit}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
};

// Get specific resume with AI analysis
const getResumeAnalysis = async (resumeId) => {
    const response = await fetch(`/api/resumes/${resumeId}/analysis`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
};
```

#### Update Operations
```javascript
// Update resume processing status
const updateResumeStatus = async (resumeId, status) => {
    const response = await fetch(`/api/admin/resumes/${resumeId}/status`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${adminToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ processing_status: status })
    });
    return response.json();
};
```

#### Delete Operations
```javascript
// Delete resume (soft delete)
const deleteResume = async (resumeId) => {
    const response = await fetch(`/api/resumes/${resumeId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
};
```

### Railway PostgreSQL Performance Features

#### Connection Pooling Implementation
```python
# Backend connection management (for context)
class RailwayPostgreSQL:
    def __init__(self, database_url):
        self.pool = ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            dsn=database_url
        )
        self.circuit_breaker = CircuitBreaker()
```

#### JSONB Query Examples for Frontend
```javascript
// Search resumes by AI analysis scores
const searchResumesByScore = async (minScore, skills) => {
    const response = await fetch('/api/resumes/search', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            min_technical_score: minScore,
            required_skills: skills,
            // Uses JSONB queries: ai_analysis->>'technical_score'::int >= minScore
        })
    });
    return response.json();
};
```

## 🎯 Target Users & User Journeys

### 1. **Landing Page Visitors (Prospects)**
**Goal**: Convert to trial users
**Journey**: 
- Land on marketing page → See value proposition → Sign up for free trial → Start using system

### 2. **Trial Users** 
**Goal**: Experience value, convert to paid
**Journey**:
- Login → Upload resumes → Get AI analysis → Use 100 free credits → Hit trial limits → Convert to paid

### 3. **Premium Users**
**Goal**: High-volume usage, retention
**Journey**:
- Login → Unlimited usage → Premium AI → Priority processing → Renewal

### 4. **Administrators**
**Goal**: System management, user oversight
**Journey**:
- Admin login → Dashboard overview → User management → System analytics → Credit management

## 🎨 UI/UX Design Requirements

### Landing Page Design
**Purpose**: SaaS business marketing and conversion

**Required Sections**:
1. **Hero Section**
   - Compelling headline: "AI-Powered Resume Analysis for Modern HR Teams"
   - Subheading: "Analyze resumes 10x faster with our 4-agent AI system"
   - CTA Button: "Start Free Trial - 100 Credits Free"
   - Demo video or screenshot carousel

2. **Features Showcase**
   - 4 AI Agents visualization
   - Real-time analysis demo
   - HR legal consultation highlight
   - Enterprise security badges

3. **Pricing Tiers**
   - **Free Trial**: 100 resume analyses + 50 legal queries
   - **Professional**: $99/month - 1000 credits + premium AI
   - **Enterprise**: Custom pricing - unlimited + dedicated support

4. **Trust Signals**
   - Customer testimonials
   - Security certifications
   - Uptime guarantees
   - GDPR/compliance badges

5. **Call-to-Action**
   - Free trial signup form
   - "No credit card required"
   - "Get results in 30 seconds"

### Dashboard Design Patterns

#### User Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: Logo | Credits: 85/100 | User Menu | Logout         │
├─────────────────────────────────────────────────────────────┤
│ SIDEBAR: Upload | Resumes | Legal | Analytics | Settings     │
├──────────────┬──────────────────────────────────────────────┤
│              │ MAIN CONTENT AREA                            │
│   SIDEBAR    │ - Quick Upload Dropzone                      │
│   MENU       │ - Recent Analyses (Cards)                    │
│              │ - Usage Analytics                            │
│              │ - Quick Legal Query Box                      │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

#### Admin Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│ ADMIN HEADER: System Status | Admin Menu | Logout           │
├─────────────────────────────────────────────────────────────┤
│ ADMIN SIDEBAR: Users | Analytics | Credits | System         │
├──────────────┬──────────────────────────────────────────────┤
│              │ ADMIN CONTENT                                │
│   ADMIN      │ - System Metrics Dashboard                   │
│   MENU       │ - User Management Table                      │
│              │ - Revenue Analytics                          │
│              │ - System Health Monitors                     │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

## 🔐 Authentication Flow

### User Authentication
1. **Registration**: Admin-only user creation (no public signup)
2. **Login Process**:
   ```
   POST /api/auth/user-login
   {
     "email": "user@company.com",
     "password": "password123"
   }
   
   Response:
   {
     "success": true,
     "token": "session_token_here",
     "user": {
       "user_id": 123,
       "email": "user@company.com",
       "name": "John Doe",
       "access_type": "trial",
       "is_admin": false,
       "trial_info": {
         "resume_limits": {"used": 15, "limit": 100},
         "legal_limits": {"used": 3, "limit": 50}
       }
     }
   }
   ```

### Admin Authentication
```
POST /api/auth/admin-login
{
  "username": "admin",
  "password": "admin_password"
}

Response:
{
  "success": true,
  "token": "admin_session_token",
  "user": {
    "user_id": 1,
    "username": "admin",
    "is_admin": true,
    "permissions": ["all"]
  }
}
```

## 🔥 Core API Endpoints (Railway PostgreSQL Optimized)

### Base URL: `https://hrtoolsbackend-production.up.railway.app`

> **Database Architecture**: All endpoints utilize Railway PostgreSQL as the primary database with connection pooling, circuit breakers, and automatic failover to Supabase backup. CRUD operations are optimized for Railway's 32GB RAM/32 CPU infrastructure.

### Authentication Endpoints (JWT + Database Sessions)
| Method | Endpoint | Purpose | Auth Required | Database Impact |
|--------|----------|---------|---------------|-----------------|
| POST | `/api/auth/user-login` | User login | No | **Railway**: Session creation |
| POST | `/api/auth/admin-login` | Admin login | No | **Railway**: Admin session |
| POST | `/api/auth/logout` | Logout (user/admin) | Yes | **Railway**: Session cleanup |
| GET | `/api/auth/me` | Get current user info | Yes | **Railway**: User lookup |
| GET | `/api/auth/session` | Validate session | Yes | **Railway**: Session validation |
| POST | `/api/auth/create-user` | Create user (admin only) | Admin | **Railway**: User creation + credit init |

### Resume Processing Endpoints (CRUD Optimized)
| Method | Endpoint | Purpose | Auth Required | Railway PostgreSQL Operations |
|--------|----------|---------|---------------|------------------------------|
| POST | `/api/upload` | Upload resume file | User | **CREATE**: Insert to `resumes` table with JSONB metadata |
| POST | `/api/analyze/<resume_id>` | Analyze specific resume | User | **UPDATE**: JSONB AI analysis results |
| POST | `/api/analyze/batch` | Batch analyze resumes | User | **BULK UPDATE**: Multiple JSONB analysis records |
| GET | `/api/resumes` | Get user's resumes | User | **READ**: Paginated SELECT with indexing |
| GET | `/api/resumes/<id>` | Get specific resume | User | **READ**: Single record with JSONB analysis |
| DELETE | `/api/resumes/<id>` | Delete resume | User | **DELETE**: Soft delete with status update |
| POST | `/api/resumes/search` | Search resumes by criteria | User | **READ**: JSONB queries with GIN indexes |

### HR Legal Endpoints (RAG + PostgreSQL)
| Method | Endpoint | Purpose | Auth Required | Database Operations |
|--------|----------|---------|---------------|-------------------|
| POST | `/api/hr-legal/query` | Legal consultation | User | **CREATE**: Store query + response in JSONB |
| GET | `/api/hr-legal/history` | Get legal query history | User | **READ**: User's legal queries |
| POST | `/api/admin/hr-legal/query` | Admin unlimited legal | Admin | **CREATE**: Admin query without credit deduction |

### Credit System Endpoints (B2B SaaS Integration)
| Method | Endpoint | Purpose | Auth Required | Railway PostgreSQL CRUD |
|--------|----------|---------|---------------|--------------------------|
| GET | `/api/credits/status` | Get user's credit status | User | **READ**: `user_credits` table lookup |
| GET | `/api/credits/health` | Credit system health | No | **READ**: System health metrics |
| POST | `/api/queue/add` | Add request to queue | User | **CREATE**: Queue entry with credit check |
| GET | `/api/queue/status/<id>` | Get queue status | User | **READ**: Queue status lookup |

### Admin User Management (Full CRUD)
| Method | Endpoint | Purpose | Auth Required | Database Operations |
|--------|----------|---------|---------------|-------------------|
| GET | `/api/admin/users` | List all users | Admin | **READ**: Paginated users with credit status |
| POST | `/api/admin/users` | Create new user | Admin | **CREATE**: User + credit initialization |
| GET | `/api/admin/users/<id>` | Get specific user | Admin | **READ**: User details + analytics |
| PUT | `/api/admin/users/<id>` | Update user | Admin | **UPDATE**: User information |
| DELETE | `/api/admin/users/<id>` | Delete user | Admin | **DELETE**: Cascade delete with cleanup |

### Admin Credit Management (Railway Optimized)
| Method | Endpoint | Purpose | Auth Required | PostgreSQL Operations |
|--------|----------|---------|---------------|----------------------|
| GET | `/api/admin/users/<id>/credits` | Get user credits | Admin | **READ**: Credit status with transactions |
| PUT | `/api/admin/users/<id>/credits` | Update user credits | Admin | **UPDATE**: Credit balance + transaction log |
| POST | `/api/admin/users/<id>/credits/reset` | Reset user credits | Admin | **UPDATE**: Reset to trial + audit log |
| POST | `/api/admin/users/<id>/credits/add` | Add premium credits | Admin | **CREATE**: Premium credit transaction |

### Admin Analytics & Intelligence
| Method | Endpoint | Purpose | Auth Required | Railway PostgreSQL Queries |
|--------|----------|---------|---------------|----------------------------|
| GET | `/api/admin/stats` | Dashboard statistics | Admin | **READ**: Aggregated metrics with caching |
| GET | `/api/admin/sales-intelligence` | Sales leads data | Admin | **READ**: Complex JSONB queries for lead scoring |
| GET | `/api/admin/hot-leads` | Qualified prospects | Admin | **READ**: ML-based prospect identification |
| GET | `/api/admin/conversion-predictions` | ML conversion data | Admin | **READ**: Predictive analytics from JSONB |
| GET | `/api/admin/advanced-analytics` | Business intelligence | Admin | **READ**: Complex aggregations with indexing |

### System Monitoring & Railway Integration
| Method | Endpoint | Purpose | Auth Required | Database Operations |
|--------|----------|---------|---------------|-------------------|
| GET | `/api/health` | Basic health check | No | **READ**: Basic connectivity test |
| GET | `/api/admin/system/health` | Detailed system health | Admin | **READ**: Full system diagnostics |
| GET | `/api/railway/performance` | Railway metrics | Admin | **READ**: Railway-specific performance data |
| GET | `/api/railway/memory` | Railway memory usage | Admin | **READ**: Memory utilization metrics |

### Payment & Subscription Endpoints
| Method | Endpoint | Purpose | Auth Required | Database Operations |
|--------|----------|---------|---------------|-------------------|
| POST | `/api/payments/create-order` | Create payment order | User | **CREATE**: RazorPay order in `payment_orders` |
| POST | `/api/payments/verify` | Verify payment | User | **UPDATE**: Payment status + credit addition |
| GET | `/api/payments/history` | Payment history | User | **READ**: User's payment transactions |

### Email Automation & Sales Intelligence
| Method | Endpoint | Purpose | Auth Required | Database Operations |
|--------|----------|---------|---------------|-------------------|
| POST | `/api/automation/trigger-email` | Trigger email sequence | Admin | **CREATE**: Email campaign entry |
| GET | `/api/automation/email-performance` | Email metrics | Admin | **READ**: Email campaign analytics |
| POST | `/api/admin/update-lead-status` | Update lead status | Admin | **UPDATE**: Sales intelligence data |

## 📊 Data Structures (Railway PostgreSQL Schema)

> **Database Context**: All data structures reflect Railway PostgreSQL schema with JSONB fields for AI analysis, integer primary keys, and optimized indexing.

### User Object (Railway `users` table)
```json
{
  "user_id": 123,                    // BIGINT PRIMARY KEY (Railway)
  "supabase_uuid": "uuid-for-sync",  // UUID for backup sync
  "email": "user@company.com",       // VARCHAR(255) UNIQUE
  "name": "John Doe",                // VARCHAR(255)
  "access_type": "trial",            // VARCHAR(50): "trial", "premium", "enterprise"
  "is_admin": false,                 // BOOLEAN
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T09:15:00Z",
  
  // Railway PostgreSQL specific fields
  "trial_resumes_analyzed": 15,      // BIGINT
  "trial_legal_queries": 3,          // BIGINT  
  "status": "active"                 // VARCHAR(50)
}
```

### Resume Analysis Result (Railway JSONB Storage)
```json
{
  "success": true,
  "resume_id": 456,                  // BIGINT PRIMARY KEY
  "user_id": 123,                    // BIGINT FOREIGN KEY
  "filename": "john_doe_resume.pdf",
  "file_hash": "sha256-hash",
  "file_size": 245760,
  "processing_status": "completed",  // Railway status tracking
  
  // AI Analysis stored as JSONB in Railway PostgreSQL
  "ai_analysis": {
    "overall_score": 85,             // INTEGER field for indexing
    "technical_score": 88,           // INTEGER field for indexing  
    "experience_score": 82,          // INTEGER field for indexing
    "cultural_score": 87,            // INTEGER field for indexing
    "legal_compliance": {            // JSONB field
      "bias_score": 95,
      "compliance_issues": [],
      "risk_level": "low"
    },
    
    // 4-Agent Analysis Results (stored in JSONB)
    "agent_insights": {
      "technical_agent": {
        "skills_identified": ["Python", "PostgreSQL", "AI/ML"],
        "experience_level": "senior",
        "technical_gaps": ["Kubernetes", "GraphQL"]
      },
      "experience_agent": {
        "career_progression": "positive",
        "leadership_potential": "moderate",
        "domain_expertise": ["fintech", "healthcare"]
      },
      "cultural_agent": {
        "communication_style": "collaborative",
        "team_fit": "high",
        "cultural_indicators": ["innovation", "growth-mindset"]
      },
      "legal_agent": {
        "bias_analysis": "passed",
        "privacy_compliance": "gdpr_compliant",
        "discrimination_risk": "none"
      }
    },
    
    "processing_metadata": {
      "processing_time": 1250,        // milliseconds
      "ai_provider": "ollama",        // "ollama", "openai", "anthropic"
      "processing_tier": "free_trial",
      "railway_connection_pool": "primary"
    }
  },
  
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:31:15Z"
}
```

### Credit Status Object (Railway `user_credits` table)
```json
{
  "user_id": 123,                    // BIGINT FOREIGN KEY
  "trial_credits": 85,               // INTEGER DEFAULT 100
  "premium_credits": 0,              // INTEGER DEFAULT 0
  "total_used": 15,                  // INTEGER DEFAULT 0
  "credits_remaining": 85,           // Calculated field
  "is_trial_exhausted": false,       // BOOLEAN DEFAULT FALSE
  "sales_contacted": false,          // BOOLEAN for B2B sales
  
  // Processing tier based on Railway credit logic
  "processing_tier": "free_trial",   // "free_trial", "queue_skip", "premium_instant"
  "can_process": true,
  
  // Railway PostgreSQL analytics (stored as JSONB)
  "usage_pattern": {
    "daily_usage": 5,
    "weekly_usage": 15,
    "peak_hours": [9, 10, 14, 15],
    "last_activity": "2024-01-20T09:15:00Z"
  },
  
  "lead_score": 75,                  // INTEGER for sales intelligence
  
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T09:15:00Z",
  "last_used": "2024-01-20T09:15:00Z"
}
```

### Credit Transaction Object (Railway `credit_transactions` table)
```json
{
  "id": 789,                         // BIGINT PRIMARY KEY
  "user_id": 123,                    // BIGINT FOREIGN KEY
  "transaction_type": "deduct",      // VARCHAR(20): "deduct", "add", "purchase", "refund"
  "credit_type": "trial",            // VARCHAR(20): "trial", "premium", "enterprise"
  "amount": 1,                       // INTEGER (credits consumed/added)
  "balance_after": 84,               // INTEGER (remaining balance)
  "description": "Resume analysis",   // TEXT description
  
  // Railway JSONB metadata
  "metadata": {
    "feature_used": "resume_analysis",
    "processing_tier": "free_trial",
    "railway_performance": {
      "connection_pool_id": "primary",
      "query_time_ms": 45
    }
  },
  
  "timestamp": "2024-01-20T09:15:00Z"
}
```

### HR Legal Query Result (Railway JSONB Storage)
```json
{
  "query_id": 321,                   // BIGINT PRIMARY KEY
  "user_id": 123,                    // BIGINT FOREIGN KEY
  "query_text": "What are the legal requirements for remote work policies?",
  "query_category": "compliance",     // VARCHAR: "general", "compliance", "hiring_law"
  
  // AI Response stored as JSONB in Railway
  "response_data": {
    "response_text": "Remote work policies must comply with...",
    "confidence_score": 0.92,
    "sources": [
      "Labor Standards Act 2020",
      "Remote Work Guidelines 2023"
    ],
    "ai_model_used": "legal_rag_system",
    "processing_time": 850
  },
  
  "user_rating": 5,                  // INTEGER 1-5 rating
  "created_at": "2024-01-20T11:00:00Z"
}
```

### Admin Dashboard Stats (Railway Optimized Queries)
```json
{
  "success": true,
  "cached": false,                   // Railway caching indicator
  "railway_performance": {
    "query_time_ms": 245,
    "connection_pool": "healthy",
    "active_connections": 12
  },
  
  "stats": {
    "users": {
      "total": 1250,                 // COUNT(*) from Railway users table
      "by_type": {
        "trial": 1100,               // WHERE access_type = 'trial'
        "premium": 120,              // WHERE access_type = 'premium'  
        "enterprise": 30             // WHERE access_type = 'enterprise'
      },
      "recent_signups": 45,          // Last 7 days
      "active_today": 128            // Users active in last 24h
    },
    
    "processing": {
      "total_resumes": 15000,        // COUNT(*) from resumes table
      "completed_analyses": 14750,   // WHERE processing_status = 'completed'
      "pending_queue": 12,           // WHERE processing_status = 'pending'
      "failed_analyses": 8           // WHERE processing_status = 'failed'
    },
    
    "credits": {
      "total_trial_used": 125000,    // SUM(total_used) WHERE trial_credits > 0
      "premium_transactions": 1250,   // COUNT(*) from credit_transactions
      "trial_exhausted_users": 150   // WHERE is_trial_exhausted = true
    },
    
    "database_health": {
      "railway_primary": {
        "status": "healthy",
        "connection_pool": "12/20",
        "avg_query_time_ms": 45
      },
      "supabase_backup": {
        "status": "synced",
        "last_sync": "2024-01-20T11:00:00Z"
      },
      "sqlite_cache": {
        "status": "active",
        "size_mb": 0.3
      }
    }
  },
  
  "timestamp": "2024-01-20T11:30:00Z"
}
```

### Sales Intelligence Data (Railway JSONB Analytics)
```json
{
  "qualified_leads": [
    {
      "user_id": 123,
      "email": "user@company.com",
      "lead_score": 85,               // Calculated from usage patterns
      "qualification_status": "hot",   // "new", "qualified", "hot", "contacted"
      "usage_insights": {
        "credits_used": 95,
        "feature_adoption": ["resume_analysis", "legal_queries"],
        "engagement_level": "high"
      },
      "predicted_conversion": 0.78,   // ML prediction score
      "recommended_action": "immediate_contact"
    }
  ],
  
  "pipeline_metrics": {
    "total_leads": 1250,
    "qualified_leads": 180,
    "hot_leads": 45,
    "conversion_rate": 0.15
  }
}
```

## 🚄 Railway PostgreSQL Implementation Considerations

### Frontend Optimization for Railway Database

#### Connection Pooling Awareness
```javascript
// Frontend should handle Railway's connection pool optimization
const apiRequest = async (endpoint, options = {}) => {
  // Include connection pool hint for Railway optimization
  const headers = {
    'Content-Type': 'application/json',
    'X-Railway-Pool-Hint': 'primary', // Help backend route optimally
    ...options.headers
  };
  
  try {
    const response = await fetch(endpoint, {
      ...options,
      headers,
      timeout: 30000 // Railway can handle longer queries
    });
    
    // Handle Railway-specific response headers
    const railwayPerf = response.headers.get('X-Railway-Performance');
    if (railwayPerf) {
      console.debug('Railway Performance:', JSON.parse(railwayPerf));
    }
    
    return response;
  } catch (error) {
    // Railway failover handling
    if (error.name === 'TimeoutError') {
      console.warn('Railway query timeout, may retry with backup');
    }
    throw error;
  }
};
```

#### JSONB Query Support
```javascript
// Frontend helpers for Railway PostgreSQL JSONB queries
const buildJSONBSearch = (criteria) => {
  return {
    // Use Railway's JSONB indexing for AI analysis searches
    ai_analysis_query: {
      technical_score_min: criteria.minTechnicalScore,
      skills_required: criteria.requiredSkills,
      experience_level: criteria.experienceLevel
    },
    
    // Railway supports complex JSONB path queries
    jsonb_path: `$.agent_insights.technical_agent.skills_identified[*] ? (@ like_regex "${criteria.skillPattern}")`
  };
};

// Example: Search resumes by AI analysis in Railway PostgreSQL
const searchResumesByAI = async (criteria) => {
  const searchQuery = buildJSONBSearch(criteria);
  
  const response = await apiRequest('/api/resumes/search', {
    method: 'POST',
    body: JSON.stringify({
      ...searchQuery,
      // Railway pagination optimization
      limit: 50,
      offset: criteria.page * 50,
      use_railway_indexes: true
    })
  });
  
  return response.json();
};
```

#### Real-time Data Updates
```javascript
// Railway PostgreSQL supports efficient real-time updates
const setupRailwayRealtime = (tableName, callback) => {
  // Use Server-Sent Events for Railway database changes
  const eventSource = new EventSource(`/api/railway/stream/${tableName}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Railway includes metadata about the change
    if (data.railway_metadata) {
      console.debug('Railway change:', data.railway_metadata);
    }
    
    callback(data);
  };
  
  // Railway connection health monitoring
  eventSource.onerror = (error) => {
    console.warn('Railway stream error, falling back to polling');
    // Implement polling fallback
  };
  
  return eventSource;
};
```

#### Performance Monitoring Integration
```javascript
// Frontend performance monitoring for Railway database
const RailwayPerformanceMonitor = {
  trackQuery: (queryName, startTime) => {
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    // Send performance data to Railway analytics
    fetch('/api/railway/performance-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query_name: queryName,
        duration_ms: duration,
        timestamp: new Date().toISOString(),
        client_info: {
          user_agent: navigator.userAgent,
          connection: navigator.connection?.effectiveType
        }
      })
    }).catch(err => console.debug('Performance logging failed:', err));
  },
  
  // Railway database health check from frontend
  checkHealth: async () => {
    const response = await fetch('/api/railway/health');
    const health = await response.json();
    
    return {
      primary_db: health.railway_primary,
      backup_sync: health.supabase_backup,
      performance: health.avg_query_time_ms
    };
  }
};
```

#### Error Handling for Railway Specifics
```javascript
// Railway-aware error handling
const handleRailwayError = (error, context) => {
  // Railway specific error codes
  const railwayErrors = {
    'RAILWAY_POOL_EXHAUSTED': 'High load detected, please try again',
    'RAILWAY_FAILOVER_ACTIVE': 'System switching to backup, please wait',
    'RAILWAY_MAINTENANCE': 'System maintenance in progress',
    'JSONB_QUERY_ERROR': 'Search query invalid, please refine criteria'
  };
  
  if (error.railway_error_code) {
    return {
      user_message: railwayErrors[error.railway_error_code] || 'Database error occurred',
      should_retry: ['RAILWAY_POOL_EXHAUSTED', 'RAILWAY_FAILOVER_ACTIVE'].includes(error.railway_error_code),
      retry_delay: error.railway_error_code === 'RAILWAY_POOL_EXHAUSTED' ? 5000 : 2000
    };
  }
  
  return { user_message: 'An error occurred', should_retry: false };
};
```

#### Data Pagination for Large Datasets
```javascript
// Railway PostgreSQL optimized pagination
const RailwayPagination = {
  // Use Railway's efficient OFFSET/LIMIT with total count optimization
  fetchPage: async (endpoint, page, pageSize = 50) => {
    const response = await apiRequest(`${endpoint}?page=${page}&limit=${pageSize}&include_total=true`);
    const data = await response.json();
    
    return {
      items: data.items,
      pagination: {
        current_page: page,
        page_size: pageSize,
        total_items: data.total_count,
        total_pages: Math.ceil(data.total_count / pageSize),
        has_next: data.has_next,
        railway_query_time: data.railway_performance?.query_time_ms
      }
    };
  }
};
```

### Railway PostgreSQL Best Practices for Frontend

#### 1. **Batch Operations**
- Use batch endpoints for multiple operations (reduce connection pool usage)
- Implement request queuing for high-volume operations
- Monitor Railway connection pool health

#### 2. **JSONB Field Utilization**
- Leverage Railway's JSONB indexing for AI analysis searches
- Use JSONB path queries for complex filtering
- Cache JSONB schema understanding in frontend

#### 3. **Real-time Features**
- Implement Server-Sent Events for Railway database changes
- Use Railway's connection pooling for WebSocket connections
- Handle Railway failover gracefully in real-time features

#### 4. **Performance Optimization**
- Include performance tracking for Railway query optimization
- Use Railway's 32GB RAM effectively with larger page sizes
- Monitor and display Railway performance metrics to users

## 🎨 Component Architecture

### Required React Components

#### 1. Landing Page Components
```jsx
// Landing page structure
<LandingPage>
  <HeroSection />
  <FeaturesShowcase />
  <PricingSection />
  <TestimonialsSection />
  <CTASection />
</LandingPage>
```

#### 2. User Dashboard Components
```jsx
// User dashboard structure
<UserDashboard>
  <DashboardHeader />
  <Sidebar />
  <MainContent>
    <UploadArea />
    <ResumeList />
    <AnalysisResults />
    <CreditCounter />
    <LegalQueryBox />
  </MainContent>
</UserDashboard>
```

#### 3. Admin Dashboard Components
```jsx
// Admin dashboard structure
<AdminDashboard>
  <AdminHeader />
  <AdminSidebar />
  <AdminContent>
    <SystemMetrics />
    <UserManagement />
    <RevenueAnalytics />
    <SystemHealth />
    <CreditManagement />
  </AdminContent>
</AdminDashboard>
```

### Key Component Props

#### UploadArea Component
```jsx
<UploadArea
  onFileUpload={handleFileUpload}
  acceptedTypes={['.pdf', '.docx', '.doc', '.png', '.jpg']}
  maxSize={10} // MB
  creditsRemaining={85}
  disabled={creditsRemaining === 0}
/>
```

#### AnalysisResults Component
```jsx
<AnalysisResults
  analysis={analysisData}
  showDetailedBreakdown={true}
  showRecommendations={true}
  allowExport={true}
/>
```

#### CreditCounter Component
```jsx
<CreditCounter
  creditsUsed={15}
  creditsTotal={100}
  showUpgradePrompt={creditsUsed > 75}
  upgradeUrl="/upgrade"
/>
```

## 🔄 State Management

### User State
```jsx
const userState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  credits: {
    trial_credits: 0,
    premium_credits: 0,
    total_used: 0,
    credits_remaining: 0
  },
  trial_info: {
    resume_limits: { used: 0, limit: 100 },
    legal_limits: { used: 0, limit: 50 }
  }
}
```

### Resume State
```jsx
const resumeState = {
  resumes: [],
  currentAnalysis: null,
  isAnalyzing: false,
  uploadProgress: 0,
  error: null
}
```

### Admin State
```jsx
const adminState = {
  users: [],
  systemStats: null,
  selectedUser: null,
  isLoading: false,
  filters: {
    userType: 'all',
    dateRange: '30days'
  }
}
```

## 🚨 Error Handling

### Error Types to Handle

1. **Authentication Errors**
   - Invalid credentials
   - Session expired
   - Insufficient permissions

2. **Credit System Errors**
   - Insufficient credits
   - Credit system unavailable
   - Payment required

3. **File Upload Errors**
   - File too large
   - Invalid file type
   - Upload failed

4. **Analysis Errors**
   - AI processing timeout
   - Analysis failed
   - Queue system busy

### Error Display Components
```jsx
<ErrorBoundary>
  <ErrorMessage type="warning" message="Low credits remaining" />
  <ErrorMessage type="error" message="Analysis failed" />
  <ErrorMessage type="info" message="Processing queued" />
</ErrorBoundary>
```

## 🎯 Key User Flows

### 1. Trial User Journey
```
Login → Dashboard → Upload Resume → View Analysis → 
Use Credits → Hit Limits → See Upgrade Prompt → Convert/Leave
```

### 2. Premium User Journey  
```
Login → Dashboard → Bulk Upload → Premium AI Analysis → 
Export Results → Continue Usage → Renewal
```

### 3. Admin User Journey
```
Admin Login → System Overview → User Management → 
Credit Adjustments → System Monitoring → Reports
```

## 💡 UX Best Practices

### Credit System UX
1. **Always visible credit counter** in header
2. **Progressive warnings** at 75%, 90%, 100% usage
3. **Clear upgrade paths** with benefit explanations
4. **Trial limits messaging** without being pushy
5. **Usage analytics** to show value received

### File Upload UX
1. **Drag & drop interface** with visual feedback
2. **Progress indicators** for upload and analysis
3. **File type validation** with helpful error messages  
4. **Batch upload support** for power users
5. **Preview functionality** before analysis

### Analysis Results UX
1. **Progressive disclosure** - summary first, details on demand
2. **Visual score indicators** with color coding
3. **Actionable recommendations** not just feedback
4. **Comparison features** for multiple candidates
5. **Export options** (PDF, CSV) for sharing

### Admin Dashboard UX
1. **Real-time metrics** with live updates
2. **Quick action buttons** for common tasks
3. **Advanced filtering** and search capabilities
4. **Bulk operations** for user management
5. **System health indicators** with alerts

## 🔧 Technical Implementation Notes

### Authentication Implementation
```jsx
// JWT token handling
const token = localStorage.getItem('auth_token');
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Session validation
useEffect(() => {
  validateSession();
}, []);
```

### File Upload Implementation
```jsx
const handleFileUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    
    const result = await response.json();
    if (result.success) {
      setUploadedFile(result.resume_id);
    }
  } catch (error) {
    setError('Upload failed');
  }
};
```

### Real-time Updates
```jsx
// WebSocket or polling for real-time updates
useEffect(() => {
  const interval = setInterval(() => {
    fetchCreditStatus();
    fetchSystemStats();
  }, 30000); // 30 seconds
  
  return () => clearInterval(interval);
}, []);
```

## 🎨 Styling Guidelines

### Color Scheme
- **Primary**: #2563eb (Blue) - CTAs, links, active states
- **Secondary**: #10b981 (Green) - Success, positive metrics
- **Warning**: #f59e0b (Orange) - Low credits, warnings
- **Error**: #ef4444 (Red) - Errors, critical alerts
- **Background**: #f8fafc (Light Gray) - Page backgrounds
- **Text**: #1f2937 (Dark Gray) - Primary text

### Typography
- **Headers**: Inter, sans-serif (Bold)
- **Body**: Inter, sans-serif (Regular)
- **Code**: Fira Code, monospace

### Component Styling
- **Cards**: Subtle shadows, rounded corners (8px)
- **Buttons**: Consistent padding, hover states
- **Forms**: Clear labels, validation states
- **Tables**: Zebra striping, sortable headers

## 🚀 Performance Optimization

### Frontend Optimization
1. **Code splitting** by route and component
2. **Lazy loading** for heavy components
3. **Image optimization** for landing page
4. **Bundle analysis** to minimize size
5. **Service worker** for offline capability

### API Optimization  
1. **Request batching** for multiple operations
2. **Response caching** for static data
3. **Debounced requests** for search/filters
4. **Error retry logic** with exponential backoff
5. **Loading states** for better UX

## 📱 Responsive Design

### Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: 1024px+

### Mobile Considerations
1. **Touch-friendly** button sizes (44px minimum)
2. **Simplified navigation** with hamburger menu
3. **Optimized file upload** for mobile devices
4. **Readable text** without zooming
5. **Fast loading** on slower connections

## 🔒 Security Considerations

### Frontend Security
1. **Input validation** on all forms
2. **XSS prevention** with proper escaping
3. **Secure token storage** (httpOnly cookies preferred)
4. **HTTPS enforcement** for all requests
5. **Content Security Policy** headers

### Data Protection
1. **Sensitive data handling** (no localStorage for tokens)
2. **File upload restrictions** (type, size validation)
3. **Rate limiting** on user actions
4. **Audit logging** for admin actions
5. **GDPR compliance** for user data

## 📈 Analytics & Monitoring

### User Analytics
- Page views and user journeys
- Feature usage patterns
- Conversion rates (trial → paid)
- Error rates and types
- Performance metrics

### Business Metrics
- Monthly/Weekly Active Users
- Credit consumption patterns
- Upgrade conversion rates
- Customer lifetime value
- System performance metrics

## 🚀 Deployment & DevOps

### Frontend Deployment
- **Platform**: Vercel (recommended) or Netlify
- **Build**: Next.js or Create React App
- **Environment**: Production, Staging, Development
- **Domain**: Connect to custom domain
- **SSL**: Automatic HTTPS

### Environment Variables
```env
REACT_APP_API_URL=https://hrtoolsbackend-production.up.railway.app
REACT_APP_ENVIRONMENT=production
REACT_APP_ANALYTICS_ID=your_analytics_id
```

## 🎯 Success Metrics

### User Experience Metrics
- **Time to first analysis**: < 60 seconds
- **Upload success rate**: > 98%
- **Analysis completion rate**: > 95%
- **User satisfaction score**: > 4.5/5

### Business Metrics
- **Trial-to-paid conversion**: > 15%
- **Monthly churn rate**: < 5%
- **Average session duration**: > 10 minutes
- **Feature adoption rate**: > 60%

## 🛠️ Development Workflow

### Getting Started
1. Clone the frontend repository
2. Install dependencies: `npm install`
3. Set up environment variables
4. Start development server: `npm start`
5. Connect to staging API for testing

### Testing Strategy
1. **Unit tests** for components and utilities
2. **Integration tests** for API interactions
3. **E2E tests** for critical user flows
4. **Performance tests** for key metrics
5. **Accessibility tests** for compliance

### Code Quality
- **ESLint** for code consistency
- **Prettier** for formatting
- **TypeScript** for type safety (recommended)
- **Husky** for pre-commit hooks
- **Code reviews** for all changes

---

## 🛠️ Comprehensive CRUD Operations Guide (Railway PostgreSQL)

### Complete Frontend Implementation Examples

#### Resume Management CRUD
```javascript
// Complete Resume CRUD Operations
class ResumeManager {
  constructor(apiBase, authToken) {
    this.apiBase = apiBase;
    this.authToken = authToken;
  }
  
  // CREATE: Upload and create new resume
  async createResume(file, metadata = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));
    
    const response = await fetch(`${this.apiBase}/api/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        // Don't set Content-Type for FormData
      },
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  // READ: Get paginated resumes with Railway optimization
  async getResumes(page = 1, limit = 10, filters = {}) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters
    });
    
    const response = await fetch(`${this.apiBase}/api/resumes?${params}`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'X-Railway-Optimize': 'pagination'
      }
    });
    
    const data = await response.json();
    
    return {
      resumes: data.resumes,
      pagination: data.pagination,
      railway_performance: data.railway_performance
    };
  }
  
  // READ: Get specific resume with AI analysis
  async getResumeById(resumeId) {
    const response = await fetch(`${this.apiBase}/api/resumes/${resumeId}`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'X-Railway-Include': 'ai_analysis'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Resume not found: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  // UPDATE: Trigger AI analysis for resume
  async analyzeResume(resumeId, analysisOptions = {}) {
    const response = await fetch(`${this.apiBase}/api/analyze/${resumeId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(analysisOptions)
    });
    
    return await response.json();
  }
  
  // DELETE: Remove resume
  async deleteResume(resumeId) {
    const response = await fetch(`${this.apiBase}/api/resumes/${resumeId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`Delete failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  // SEARCH: Complex JSONB queries on Railway
  async searchResumes(searchCriteria) {
    const response = await fetch(`${this.apiBase}/api/resumes/search`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json',
        'X-Railway-JSONB': 'optimized'
      },
      body: JSON.stringify({
        technical_score_min: searchCriteria.minTechnicalScore,
        skills: searchCriteria.requiredSkills,
        experience_years: searchCriteria.minExperience,
        // Railway JSONB path queries
        jsonb_filters: {
          'ai_analysis.agent_insights.technical_agent.experience_level': searchCriteria.level,
          'ai_analysis.legal_compliance.risk_level': 'low'
        }
      })
    });
    
    return await response.json();
  }
}
```

#### User Management CRUD (Admin)
```javascript
// Complete User Management CRUD
class AdminUserManager {
  constructor(apiBase, adminToken) {
    this.apiBase = apiBase;
    this.adminToken = adminToken;
  }
  
  // CREATE: Create new user
  async createUser(userData) {
    const response = await fetch(`${this.apiBase}/api/auth/create-user`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.adminToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: userData.email,
        name: userData.name,
        password: userData.password,
        access_type: userData.accessType || 'trial',
        trial_resume_limit: userData.trialResumeLimit || 100,
        trial_legal_limit: userData.trialLegalLimit || 50
      })
    });
    
    return await response.json();
  }
  
  // READ: Get all users with Railway pagination
  async getUsers(page = 1, limit = 50, filters = {}) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      include_credits: 'true',
      include_usage: 'true',
      ...filters
    });
    
    const response = await fetch(`${this.apiBase}/api/admin/users?${params}`, {
      headers: {
        'Authorization': `Bearer ${this.adminToken}`,
        'X-Railway-Admin': 'bulk-query'
      }
    });
    
    return await response.json();
  }
  
  // READ: Get specific user with complete profile
  async getUserById(userId) {
    const response = await fetch(`${this.apiBase}/api/admin/users/${userId}`, {
      headers: {
        'Authorization': `Bearer ${this.adminToken}`,
        'X-Railway-Include': 'credits,usage,analytics'
      }
    });
    
    return await response.json();
  }
  
  // UPDATE: Update user information
  async updateUser(userId, updates) {
    const response = await fetch(`${this.apiBase}/api/admin/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${this.adminToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });
    
    return await response.json();
  }
  
  // DELETE: Delete user (with cascade)
  async deleteUser(userId) {
    const response = await fetch(`${this.apiBase}/api/admin/users/${userId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.adminToken}`,
        'X-Railway-Cascade': 'true'
      }
    });
    
    return await response.json();
  }
}
```

#### Credit Management CRUD
```javascript
// Complete Credit Management System
class CreditManager {
  constructor(apiBase, authToken) {
    this.apiBase = apiBase;
    this.authToken = authToken;
  }
  
  // READ: Get current user's credit status
  async getCreditStatus() {
    const response = await fetch(`${this.apiBase}/api/credits/status`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'X-Railway-Real-time': 'true'
      }
    });
    
    return await response.json();
  }
  
  // READ: Get credit transaction history
  async getCreditHistory(page = 1, limit = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString()
    });
    
    const response = await fetch(`${this.apiBase}/api/credits/history?${params}`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });
    
    return await response.json();
  }
  
  // Admin CRUD operations for credits
  async getAdminUserCredits(userId) {
    const response = await fetch(`${this.apiBase}/api/admin/users/${userId}/credits`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });
    
    return await response.json();
  }
  
  // UPDATE: Admin add credits to user
  async addCreditsToUser(userId, credits, creditType = 'premium') {
    const response = await fetch(`${this.apiBase}/api/admin/users/${userId}/credits`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        credits: credits,
        credit_type: creditType,
        reason: 'admin_adjustment'
      })
    });
    
    return await response.json();
  }
  
  // UPDATE: Reset user credits to trial default
  async resetUserCredits(userId) {
    const response = await fetch(`${this.apiBase}/api/admin/users/${userId}/credits/reset`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });
    
    return await response.json();
  }
}
```

#### HR Legal Query CRUD
```javascript
// HR Legal Query Management
class LegalQueryManager {
  constructor(apiBase, authToken) {
    this.apiBase = apiBase;
    this.authToken = authToken;
  }
  
  // CREATE: Submit new legal query
  async submitLegalQuery(queryText, category = 'general') {
    const response = await fetch(`${this.apiBase}/api/hr-legal/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query_text: queryText,
        query_category: category
      })
    });
    
    return await response.json();
  }
  
  // READ: Get user's legal query history
  async getLegalQueryHistory(page = 1, limit = 10) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString()
    });
    
    const response = await fetch(`${this.apiBase}/api/hr-legal/history?${params}`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });
    
    return await response.json();
  }
  
  // READ: Get specific legal query with response
  async getLegalQueryById(queryId) {
    const response = await fetch(`${this.apiBase}/api/hr-legal/queries/${queryId}`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });
    
    return await response.json();
  }
  
  // UPDATE: Rate legal query response
  async rateLegalQuery(queryId, rating, feedback = '') {
    const response = await fetch(`${this.apiBase}/api/hr-legal/queries/${queryId}/rate`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        rating: rating,
        feedback: feedback
      })
    });
    
    return await response.json();
  }
}
```

#### Complete Integration Hook Example
```javascript
// React Hook for Railway PostgreSQL Integration
import { useState, useEffect, useCallback } from 'react';

const useRailwayData = (endpoint, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [railwayPerformance, setRailwayPerformance] = useState(null);
  
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const startTime = performance.now();
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${options.token}`,
          'X-Railway-Optimize': 'performance',
          'X-Railway-Cache': options.cache ? 'enabled' : 'disabled',
          ...options.headers
        },
        ...options
      });
      
      if (!response.ok) {
        throw new Error(`Railway request failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      const endTime = performance.now();
      
      // Track Railway performance
      const railwayPerf = response.headers.get('X-Railway-Performance');
      if (railwayPerf) {
        setRailwayPerformance({
          ...JSON.parse(railwayPerf),
          client_time_ms: endTime - startTime
        });
      }
      
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint, options]);
  
  useEffect(() => {
    if (options.autoFetch !== false) {
      fetchData();
    }
  }, [fetchData, options.autoFetch]);
  
  return {
    data,
    loading,
    error,
    railwayPerformance,
    refetch: fetchData
  };
};

// Usage example
const ResumeList = () => {
  const { data: resumes, loading, error, railwayPerformance } = useRailwayData('/api/resumes', {
    token: authToken,
    cache: true
  });
  
  if (loading) return <div>Loading resumes from Railway...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <div className="railway-performance">
        Query Time: {railwayPerformance?.query_time_ms}ms
      </div>
      {resumes?.map(resume => (
        <ResumeCard key={resume.id} resume={resume} />
      ))}
    </div>
  );
};
```

### Railway PostgreSQL CRUD Best Practices Summary

1. **Always include Railway-specific headers** for optimization
2. **Use batch operations** when possible to reduce connection pool usage
3. **Implement proper error handling** for Railway-specific scenarios
4. **Monitor and display performance metrics** from Railway responses
5. **Leverage JSONB fields** for complex AI analysis queries
6. **Use pagination** effectively with Railway's 32GB RAM advantage
7. **Implement real-time updates** using Server-Sent Events
8. **Handle failover scenarios** gracefully with backup systems

---

## 🎉 Conclusion

This HR ATS system is a sophisticated B2B SaaS platform with advanced AI capabilities and enterprise-grade features. The frontend should emphasize the value proposition, provide excellent user experience, and facilitate the trial-to-paid conversion journey.

**Key Success Factors:**
1. **Clear value demonstration** in the first 30 seconds
2. **Frictionless trial experience** with immediate value
3. **Transparent credit system** that doesn't feel restrictive
4. **Professional admin interface** for system management
5. **Mobile-responsive design** for modern users
6. **Railway PostgreSQL optimization** for high performance

The system handles heavy AI processing on the backend with Railway PostgreSQL as the primary database, so the frontend should focus on presenting results clearly and guiding users through their journey from trial to paid conversion.

**Priority Development Order:**
1. Landing page + trial signup
2. User dashboard + file upload  
3. Analysis results display
4. Credit management UI
5. Admin dashboard
6. Railway PostgreSQL integration optimization
7. Mobile optimization
8. Advanced features

This comprehensive guide provides everything needed to build a world-class frontend for this advanced HR ATS system. Focus on user value, clear information architecture, Railway database optimization, and smooth conversion flows to maximize the business impact.
