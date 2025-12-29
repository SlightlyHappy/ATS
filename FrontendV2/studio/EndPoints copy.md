# 🚀 HR ATS Backend API Documentation
## The Complete Frontend Engineer's Guide to Backend Architecture

*Version 3.1 - Railway Production Deployment*  
*Last Updated: July 30, 2025*

---

## 📋 Table of Contents

1. [🏗️ Architecture Overview](#architecture-overview)
2. [🗄️ Database Architecture](#database-architecture)
3. [🤖 AI Analysis System](#ai-analysis-system)
4. [💰 Credit & Payment System](#credit-payment-system)
5. [🔐 Authentication System](#authentication-system)
6. [📊 Queue Management](#queue-management)
7. [🌐 API Endpoints](#api-endpoints)
8. [🎯 Error Handling](#error-handling)
9. [🚀 Deployment Architecture](#deployment-architecture)

---

## 🏗️ Architecture Overview

### Core Technology Stack
- **Backend Framework**: Flask (Python)
- **Primary Database**: Railway PostgreSQL (Production)
- **Backup Database**: Supabase PostgreSQL (Auto-sync enabled) 
- **AI Processing**: 4-Agent Agentic System
- **Authentication**: Supabase Auth + Custom JWT
- **Payment**: RazorPay Integration
- **Deployment**: Railway (Primary) + Supabase (Backup)

### System Architecture
```
Frontend (React) → API Gateway → Authentication → Credit Check → AI Processing → Railway PostgreSQL
                                      ↓                                               ↓
                              Queue Management ← Payment System              Supabase Backup
```

### Key Components
1. **HRATSApplication**: Main Flask application orchestrator
2. **AgenticResumeProcessor**: 4-Agent AI analysis system
3. **RailwayPostgreSQL**: Primary database operations with connection pooling
4. **SupabaseClient**: Backup database operations and user management
5. **CreditManager**: B2B monetization and usage tracking
6. **QueueManager**: Concurrent request handling
7. **PaymentManager**: RazorPay integration for premium features
8. **BackupSyncManager**: Automatic Railway ↔ Supabase synchronization

---

## 🗄️ Database Architecture

### Primary Database: PostgreSQL on Railway

**🚨 CONFIRMED**: The primary database is **PostgreSQL on Railway** with **Supabase as backup/sync**.

#### Architecture Details:
- **Primary Database**: Railway PostgreSQL (DATABASE_URL environment variable)
- **Backup Database**: Supabase PostgreSQL (automatic sync enabled)  
- **Default Configuration**: `PRIMARY_DB=railway` (configurable via environment)
- **Connection**: Railway internal URL for production, public URL for development
- **Connection Pool**: 5-20 connections optimized for Railway resource limits
- **Backup Sync**: Automatic bi-directional sync between Railway ↔ Supabase

#### Core Tables Schema

**1. user_profiles** - User Management
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    full_name TEXT,
    email TEXT UNIQUE NOT NULL,
    company_name TEXT,
    job_title TEXT,
    access_type TEXT DEFAULT 'trial', -- 'trial', 'full', 'enterprise'
    is_admin BOOLEAN DEFAULT false,
    trial_usage INTEGER DEFAULT 0,
    trial_limit INTEGER DEFAULT 100,
    subscription_status TEXT DEFAULT 'trial',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**2. resumes** - Resume Storage & AI Analysis
```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    raw_text TEXT, -- Extracted text for search
    
    -- AI Analysis Scores (0-100 range)
    overall_score INTEGER DEFAULT 0,
    technical_score INTEGER DEFAULT 0,
    experience_score INTEGER DEFAULT 0,
    education_score INTEGER DEFAULT 0,
    role_fit_score INTEGER DEFAULT 0,
    
    -- AI Analysis Details
    ai_feedback TEXT,
    ai_model_used TEXT,
    ai_processing_time INTEGER, -- milliseconds
    
    -- Extracted Information
    candidate_name TEXT,
    candidate_email TEXT,
    skills TEXT[],
    job_titles TEXT[],
    companies TEXT[],
    programming_languages TEXT[],
    certifications TEXT[],
    
    -- Comprehensive AI Analysis Result Storage
    analysis_result JSONB, -- Complete 4-agent analysis
    
    processing_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**3. user_credits** - B2B Credit System
```sql
CREATE TABLE user_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    trial_credits INTEGER DEFAULT 100,
    premium_credits INTEGER DEFAULT 0,
    total_used INTEGER DEFAULT 0,
    is_trial_exhausted BOOLEAN DEFAULT FALSE,
    processing_tier TEXT DEFAULT 'free_trial',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**4. payment_transactions** - Payment Tracking
```sql
CREATE TABLE payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    payment_provider VARCHAR(20) DEFAULT 'razorpay',
    razorpay_payment_id TEXT,
    amount INTEGER NOT NULL, -- Paisa (INR * 100)
    credits_added INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**5. hr_legal_queries** - Legal AI System
```sql
CREATE TABLE hr_legal_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    query_text TEXT NOT NULL,
    query_category TEXT DEFAULT 'general',
    response_text TEXT,
    confidence_score DECIMAL(5,2),
    sources JSONB DEFAULT '[]',
    ai_model_used TEXT,
    processing_time INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Railway PostgreSQL (Primary Production Database)
- **Status**: Primary production database on Railway
- **Configuration**: Optimized connection pooling (5-20 connections)
- **Performance**: Circuit breaker protection, health monitoring
- **Schema**: Complete production schema with all tables
- **URL**: Uses Railway internal network for optimal performance

### Supabase PostgreSQL (Backup & Development)
- **Status**: Backup database with automatic sync from Railway
- **Usage**: Development environment, backup operations
- **Sync**: Bi-directional sync every 2 hours (configurable)
- **Authentication**: Integrated with Supabase Auth system
- **Row Level Security**: Enabled for user data isolation

---

## 🤖 AI Analysis System

### 4-Agent Agentic Architecture

The backend uses a sophisticated 4-agent system for resume analysis:

#### Agent 1: Technical Skills Evaluator
- **Purpose**: Analyzes technical competencies
- **Output**: Technical skills score (0-100)
- **Processing**: Keyword matching, skill validation, experience correlation

#### Agent 2: Experience Assessor  
- **Purpose**: Evaluates professional experience
- **Output**: Experience relevance score (0-100)
- **Processing**: Career progression analysis, role alignment

#### Agent 3: Cultural Fit Analyzer
- **Purpose**: Assesses organizational compatibility
- **Output**: Cultural fit score (0-100)
- **Processing**: Communication style, team collaboration indicators

#### Agent 4: Legal Compliance Checker
- **Purpose**: Ensures hiring law compliance
- **Output**: Legal compliance score (0-100)
- **Processing**: Bias detection, privacy compliance, regulatory adherence

### AI Processing Flow
```python
# Simplified AI Processing Pipeline
class AgenticResumeProcessor:
    async def analyze_resume(self, resume_text: str, job_requirements: Dict) -> Dict:
        # 1. Premium Routing Check
        processing_tier = self.determine_processing_tier(user_id)
        
        # 2. Enhanced Multi-Agent Analysis
        if processing_tier in ["premium_instant", "queue_skip"]:
            result = await self.premium_router.route_premium_analysis()
        else:
            result = await self.enhanced_agentic_analysis()
        
        # 3. 4-Agent Consensus Building
        agent_results = [
            technical_agent.analyze(resume_data),
            experience_agent.analyze(resume_data), 
            cultural_agent.analyze(resume_data),
            legal_agent.analyze(resume_data)
        ]
        
        # 4. Weighted Scoring & Realistic Calibration
        final_score = self.calculate_weighted_consensus(agent_results)
        
        return {
            "overall_score": final_score,
            "individual_scores": agent_scores,
            "analysis_summary": detailed_feedback,
            "recommendations": hiring_recommendations,
            "red_flags": compliance_issues,
            "processing_metadata": ai_metadata
        }
```

### AI Analysis Result Structure
```json
{
    "overall_score": 78.5,
    "individual_scores": {
        "technical_skills": 85.0,
        "experience": 72.0,
        "cultural_fit": 80.0,
        "legal_compliance": 95.0
    },
    "analysis_summary": {
        "strengths": ["Strong Python skills", "5+ years experience"],
        "weaknesses": ["Limited team leadership", "No cloud experience"],
        "recommendations": ["Consider for senior developer role"]
    },
    "red_flags": [],
    "processing_metadata": {
        "analysis_timestamp": "2025-07-30T10:15:30Z",
        "ai_model_used": "enhanced_agentic_v3.1",
        "processing_time_ms": 2150,
        "agentic_analysis": true,
        "realistic_scoring_applied": true
    }
}
```

---

## 💰 Credit & Payment System

### B2B SaaS Monetization Model

#### Credit System Overview
- **Trial Credits**: 100 free credits per new user
- **Premium Credits**: Purchased credits for enhanced processing
- **Credit Consumption**: 1 credit per resume analysis, 5 credits per batch, 1 credit per legal query

#### Processing Tiers
```python
class ProcessingTier(Enum):
    FREE_TRIAL = "free_trial"           # Basic processing with queue
    QUEUE_SKIP = "queue_skip"           # ₹40 - Skip queue once
    PREMIUM_INSTANT = "premium_instant"  # Premium credits - instant processing
    ENTERPRISE = "enterprise"           # Unlimited processing
    CONTACT_SALES = "contact_sales"     # Trial exhausted
```

#### Payment Packages (RazorPay)
```python
PAYMENT_PACKAGES = {
    PaymentType.QUEUE_SKIP: {
        "amount": 4000,  # ₹40
        "credits": 0,    # Immediate processing privilege
        "description": "Skip queue and get instant processing"
    },
    PaymentType.CREDIT_PACKAGE_10: {
        "amount": 30000,  # ₹300
        "credits": 10,
        "description": "10 premium credits for enhanced AI processing"
    },
    PaymentType.CREDIT_PACKAGE_25: {
        "amount": 65000,  # ₹650
        "credits": 25,
        "description": "25 premium credits with better value"
    }
}
```

#### Credit Management Flow
```python
class CreditManager:
    def deduct_credits(self, user_id: int, amount: int = 1, 
                      feature_used: str = "resume_analysis") -> bool:
        # Atomic credit deduction with audit trail
        # Triggers sales intelligence updates
        # Handles trial exhaustion gracefully
        
    def add_premium_credits(self, user_id: int, credits: int, 
                           payment_id: str) -> bool:
        # Secure credit addition post-payment verification
        # Updates processing tier automatically
        # Logs payment behavior for sales intelligence
```

---

## 🔐 Authentication System

### Multi-Layer Security Architecture

#### 1. Supabase Authentication
- **Primary Auth**: Supabase Auth with JWT tokens
- **Social Login**: Google, GitHub integration ready
- **Session Management**: Secure token refresh mechanism

#### 2. Custom Authentication Middleware
```python
class AuthMiddleware:
    def require_auth(self, f):
        # JWT token validation
        # User session verification
        # Rate limiting protection
        
    def require_admin(self, f):
        # Admin privilege verification
        # Enhanced security for admin operations
```

#### 3. Row Level Security (RLS)
- **Supabase RLS**: Database-level access control
- **User Data Isolation**: Users can only access their own data
- **Admin Override**: Admins can access all data for management

### Authentication Flow
```
1. User Login → Supabase Auth → JWT Token
2. API Request → Token Validation → User Context
3. Database Query → RLS Enforcement → Filtered Results
```

---

## 📊 Queue Management

### Concurrent Request Handling

#### Queue System Architecture
```python
class BasicRequestQueue:
    def __init__(self, max_concurrent: int = 10):
        self.processing_queue = PriorityQueue()
        self.background_workers = ThreadPoolExecutor(max_workers=10)
        
    def add_request(self, user_id: str, request_type: str, 
                   data: Dict, processing_tier: ProcessingTier):
        # Priority-based queue insertion
        # Concurrent processing with worker threads
        # Real-time status tracking
```

#### Processing Priorities
1. **Enterprise Users**: Immediate processing
2. **Premium Credits**: High priority queue
3. **Queue Skip Payment**: Skip to front
4. **Trial Users**: Standard queue

#### Queue Status Management
```python
class QueueStatus(Enum):
    IDLE = "idle"
    NORMAL = "normal" 
    BUSY = "busy"
    OVERLOADED = "overloaded"
```

---

## 🌐 API Endpoints

### Core Resume Processing Endpoints

#### **POST /api/upload**
Upload and process resume files with automatic AI analysis
```json
{
  "files": [File],
  "job_requirements": {
    "title": "Senior Python Developer",
    "required_skills": ["Python", "Django", "AWS"],
    "experience_level": "Senior"
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": [{
    "resume_id": "uuid",
    "filename": "resume.pdf",
    "processing_status": "completed",
    "ai_processing": true
  }],
  "processed_count": 1,
  "successful_uploads": 1
}
```

#### **POST /api/analyze/{resume_id}**
Analyze specific resume with 4-agent system
```json
{
  "job_requirements": {
    "title": "Python Developer",
    "required_skills": ["Python", "Flask", "PostgreSQL"],
    "department": "Engineering"
  }
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "overall_score": 78.5,
    "individual_scores": {
      "technical_skills": 85.0,
      "experience": 72.0,
      "cultural_fit": 80.0,
      "legal_compliance": 95.0
    },
    "processing_metadata": {
      "analysis_type": "enhanced_agentic",
      "processing_tier": "premium_instant"
    }
  }
}
```

#### **POST /api/analyze/batch**
Analyze multiple resumes with comparative ranking
```json
{
  "resumes": [
    {"id": "resume_1", "text": "resume content..."},
    {"id": "resume_2", "text": "resume content..."}
  ],
  "job_requirements": {
    "title": "Software Engineer",
    "required_skills": ["JavaScript", "React", "Node.js"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "batch_analysis": {
    "total_resumes": 2,
    "results": [
      {
        "overall_score": 85.2,
        "batch_position": 1,
        "processing_status": "completed"
      }
    ],
    "scoring_calibrated": true,
    "concurrent_processing": true
  }
}
```

### User Management Endpoints

#### **GET /api/resumes**
Get all resumes for current user
```json
{
  "success": true,
  "resumes": [
    {
      "id": "uuid",
      "filename": "resume.pdf",
      "upload_date": "2025-07-30T10:15:30Z",
      "overall_score": 78.5,
      "processing_status": "completed"
    }
  ]
}
```

#### **DELETE /api/resumes/{resume_id}**
Delete specific resume
```json
{
  "success": true,
  "message": "Resume deleted successfully"
}
```

### Credit Management Endpoints

#### **GET /api/credits/status**
Get current user's credit status
```json
{
  "success": true,
  "credit_status": {
    "trial_credits": 75,
    "premium_credits": 10,
    "total_used": 25,
    "processing_tier": "premium_instant",
    "can_process": true
  }
}
```

### Payment Endpoints

#### **POST /api/payment/create-order**
Create RazorPay payment order
```json
{
  "payment_type": "credit_package_10",
  "return_url": "https://app.example.com/payment-success"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "order_razorpay_id",
  "amount": 30000,
  "currency": "INR",
  "razorpay_key": "rzp_test_key"
}
```

#### **POST /api/payment/verify**
Verify payment and add credits
```json
{
  "payment_id": "pay_razorpay_id",
  "order_id": "order_razorpay_id", 
  "signature": "razorpay_signature"
}
```

**Response:**
```json
{
  "success": true,
  "credits_added": 10,
  "processing_tier": "premium_instant",
  "message": "Payment verified and credits added"
}
```

### HR Legal System Endpoints

#### **POST /api/hr-legal/query**
HR Legal consultation with AI
```json
{
  "query_text": "What are the legal requirements for background verification in India?",
  "query_category": "compliance"
}
```

**Response:**
```json
{
  "success": true,
  "legal_response": {
    "legal_analysis": "Detailed legal analysis...",
    "relevant_laws": ["Industrial Relations Code 2020"],
    "recommendations": ["Practical recommendations..."],
    "risk_level": "Low",
    "confidence_score": 0.95
  }
}
```

### Admin Endpoints

#### **GET /api/admin/stats**
Admin dashboard statistics
```json
{
  "success": true,
  "admin_stats": {
    "total_users": 1250,
    "active_users_today": 89,
    "total_resumes_processed": 5420,
    "revenue_this_month": 125000,
    "system_health": "healthy"
  }
}
```

#### **GET /api/admin/users**
Get all users for admin management
```json
{
  "success": true,
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "access_type": "trial",
      "trial_usage": 25,
      "created_at": "2025-07-30T10:15:30Z"
    }
  ]
}
```

### System Health Endpoints

#### **GET /health**
System health check
```json
{
  "status": "healthy",
  "version": "3.1.0-production",
  "services": {
    "supabase": {"status": "healthy"},
    "ai_analyzer": {"status": "healthy"},
    "payment_system": {"status": "healthy"}
  },
  "memory": {
    "used_percent": 65.2,
    "optimization": "lazy_loading_enabled"
  }
}
```

#### **GET /api/system/status**
Comprehensive system status
```json
{
  "success": true,
  "system_status": {
    "basic_health": {
      "supabase": {"status": "healthy"},
      "ai_basic": {"status": "healthy"}
    },
    "enhanced_ai_status": {
      "agentic_system": "operational",
      "4_agent_analysis": "ready"
    }
  }
}
```

---

## 🎯 Error Handling

### Standardized Error Responses
```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": "Additional technical details",
  "error_id": "uuid-for-tracking"
}
```

### Common Error Codes
- **`insufficient_credits`**: User has no credits remaining
- **`payment_required`**: Premium feature requires payment
- **`queue_busy`**: System busy, request queued
- **`analysis_failed`**: AI analysis encountered error
- **`authentication_required`**: Valid login required
- **`file_too_large`**: Upload exceeds size limit
- **`unsupported_format`**: File format not supported

### Error Handling Best Practices
1. **Graceful Degradation**: System continues operating with reduced functionality
2. **User-Friendly Messages**: Technical errors translated to user language
3. **Retry Mechanisms**: Automatic retry for transient failures
4. **Audit Logging**: All errors logged for debugging and improvement

---

## 🚀 Deployment Architecture

### Railway Production Environment

#### Environment Configuration
```bash
# Essential Environment Variables - RAILWAY PRODUCTION
DATABASE_URL=postgresql://user:pass@host:port/db                    # Railway PostgreSQL (Primary)
DATABASE_PUBLIC_URL=postgresql://user:pass@public:port/db           # Railway PostgreSQL (Public)
SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co              # Supabase (Backup)
SUPABASE_KEY=your_supabase_anon_key                                 # Supabase Auth
PRIMARY_DB=railway                                                  # Primary database routing
BACKUP_SYNC_ENABLED=true                                           # Enable Railway → Supabase sync
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
FLASK_ENV=production
```

#### Railway Optimization Features
- **Memory Optimization**: Lazy loading of AI components
- **Connection Pooling**: 5-20 PostgreSQL connections with circuit breaker
- **Background Processing**: Non-blocking request handling with queue management
- **Health Monitoring**: Automated health checks and connection recovery
- **Database Routing**: Smart routing between Railway (primary) and Supabase (backup)
- **Backup Sync**: Automatic bi-directional synchronization every 2 hours

#### Performance Monitoring
- **Memory Usage**: Real-time monitoring with alerts
- **Request Latency**: API response time tracking
- **Error Rates**: System reliability metrics
- **Credit Usage**: Business metrics and forecasting

### Backup Systems
- **Database Backup**: Automated Railway PostgreSQL → Supabase sync (every 2 hours)
- **Failover**: Automatic fallback to Supabase if Railway unavailable
- **File Storage**: Redundant resume storage across both databases
- **Configuration Backup**: Environment variable and schema backup
- **Recovery**: One-click restore from Supabase to Railway

---

## 📚 Integration Examples

### Frontend Integration Example (React)
```javascript
// Resume Upload with Progress Tracking
const uploadResume = async (file, jobRequirements) => {
  const formData = new FormData();
  formData.append('files', file);
  formData.append('job_requirements', JSON.stringify(jobRequirements));

  const response = await fetch('/api/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`
    },
    body: formData
  });

  const result = await response.json();
  
  if (result.success) {
    // Handle successful upload
    console.log('Resume uploaded:', result.results[0]);
  } else {
    // Handle errors gracefully
    handleUploadError(result.error);
  }
};

// Credit Status Management
const checkCredits = async () => {
  const response = await fetch('/api/credits/status', {
    headers: { 'Authorization': `Bearer ${authToken}` }
  });
  
  const credits = await response.json();
  
  if (credits.credit_status.can_process) {
    // User can proceed with analysis
    enableAnalysisFeatures();
  } else {
    // Show payment options
    showPaymentModal(credits.credit_status);
  }
};
```

### Payment Integration Example
```javascript
// RazorPay Integration
const initiatePayment = async (paymentType) => {
  // 1. Create order
  const orderResponse = await fetch('/api/payment/create-order', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({ payment_type: paymentType })
  });

  const order = await orderResponse.json();

  // 2. Open RazorPay
  const options = {
    key: order.razorpay_key,
    amount: order.amount,
    currency: 'INR',
    order_id: order.order_id,
    handler: async (response) => {
      // 3. Verify payment
      const verifyResponse = await fetch('/api/payment/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          payment_id: response.razorpay_payment_id,
          order_id: response.razorpay_order_id,
          signature: response.razorpay_signature
        })
      });

      const result = await verifyResponse.json();
      if (result.success) {
        // Credits added successfully
        updateCreditDisplay(result.credits_added);
      }
    }
  };

  const razorpay = new Razorpay(options);
  razorpay.open();
};
```

---

## 🔧 Development Notes

### Database Migrations
When adding new features, follow this pattern:
1. Update Supabase schema first
2. Deploy Railway schema changes
3. Update backend models
4. Add API endpoints
5. Update frontend integration

### Testing Endpoints
Use the provided test scripts:
```bash
# Test credit system
python TestScripts/test_phase1_credit_system.py

# Test payment flow
python TestScripts/test_payment_integration.py

# Health check
curl https://your-railway-app.railway.app/health
```

### Performance Optimization
- **Lazy Loading**: AI components load on-demand
- **Caching**: Frequently accessed data cached
- **Connection Pooling**: Database connections optimized
- **Background Processing**: Heavy operations queued

---

## 📞 Support & Questions

For any questions about backend integration:

1. **Architecture Questions**: Check this documentation first
2. **API Issues**: Review error codes and responses
3. **Payment Integration**: Refer to RazorPay documentation
4. **Database Schema**: Check Supabase dashboard
5. **Performance Issues**: Monitor Railway metrics

---

**Happy Coding! 🚀**

*This documentation is maintained by the backend team. Last updated: July 30, 2025*