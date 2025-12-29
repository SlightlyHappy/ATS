# 🧠 TECHNICAL ARCHITECTURE BLUEPRINT
# World-Class Agentic HR System on Railway

## 🏗️ **SYSTEM ARCHITECTURE**

### **Railway Resource Allocation (8GB RAM, 8 CPU)**
```
Ollama Process:     4-5GB RAM, 4-6 CPU cores
Flask Application: 2-3GB RAM, 2 CPU cores  
FAISS Vector Store: 500MB RAM, ephemeral storage
File Processing:    200MB RAM, /tmp storage
System Overhead:    300MB RAM, monitoring/logging
```

### **Multi-Stage Dockerfile Architecture**
```dockerfile
# Stage 1: Builder (Downloads & Preparation)
- Download Ollama binary and qwen2.5:7b model
- Clone HR legal document repository
- Build FAISS vector indexes from legal documents
- Prepare sentence-transformer embedding models
- Create optimized runtime environment

# Stage 2: Runtime (Production Deployment)
- Copy models and indexes from builder stage
- Install minimal production dependencies
- Configure Railway-specific optimizations
- Set up health checks and monitoring
```

## 🤖 **4-AGENT AGENTIC SYSTEM ARCHITECTURE**

### **Agent Workflow Pipeline**
```python
class AgenticResumeAnalyzer:
    def __init__(self):
        self.technical_agent = TechnicalSkillsAgent()
        self.experience_agent = ExperienceEvaluatorAgent()
        self.cultural_agent = CulturalFitAgent()
        self.legal_agent = LegalComplianceAgent()
        
    async def analyze_resume(self, resume_text, job_requirements):
        # Sequential processing with shared context
        context = ResumeAnalysisContext(resume_text, job_requirements)
        
        # Agent 1: Technical Skills Analysis
        technical_analysis = await self.technical_agent.analyze(context)
        context.add_insight("technical", technical_analysis)
        
        # Agent 2: Experience Evaluation
        experience_analysis = await self.experience_agent.analyze(context)
        context.add_insight("experience", experience_analysis)
        
        # Agent 3: Cultural Fit Assessment
        cultural_analysis = await self.cultural_agent.analyze(context)
        context.add_insight("cultural", cultural_analysis)
        
        # Agent 4: Legal Compliance Check
        legal_analysis = await self.legal_agent.analyze(context)
        context.add_insight("legal", legal_analysis)
        
        # Consensus Building
        final_assessment = await self.build_consensus(context)
        return final_assessment
```

### **Individual Agent Specifications**

#### **Technical Skills Agent**
```python
class TechnicalSkillsAgent:
    def __init__(self):
        self.tools = [
            WebSearchTool(),           # Verify skill relevance
            TechnicalDatabaseTool(),   # Check certifications
            SkillTrendAnalyzer()       # Industry skill demand
        ]
        
    async def analyze(self, context):
        return {
            "programming_languages": [],
            "frameworks_tools": [],
            "certifications": [],
            "technical_projects": [],
            "skill_proficiency_scores": {},
            "industry_relevance": {},
            "learning_trajectory": "",
            "technical_recommendations": []
        }
```

#### **Experience Evaluator Agent**
```python
class ExperienceEvaluatorAgent:
    def __init__(self):
        self.tools = [
            CompanyVerificationTool(), # Validate work history
            IndustryAnalyzer(),        # Industry context
            CareerProgressionTool()    # Growth analysis
        ]
        
    async def analyze(self, context):
        return {
            "work_history": [],
            "career_progression": "",
            "achievement_analysis": [],
            "responsibility_growth": {},
            "industry_experience": {},
            "leadership_indicators": [],
            "experience_gaps": [],
            "experience_recommendations": []
        }
```

#### **Cultural Fit Agent**
```python
class CulturalFitAgent:
    def __init__(self):
        self.tools = [
            CommunicationAnalyzer(),   # Language analysis
            PersonalityInsights(),     # Soft skills detection
            TeamworkIndicators()       # Collaboration signs
        ]
        
    async def analyze(self, context):
        return {
            "communication_style": "",
            "soft_skills": [],
            "leadership_potential": {},
            "teamwork_indicators": [],
            "adaptability_signs": [],
            "cultural_alignment": {},
            "personality_insights": {},
            "fit_recommendations": []
        }
```

#### **Legal Compliance Agent**
```python
class LegalComplianceAgent:
    def __init__(self):
        self.tools = [
            BiasDetectionTool(),       # Unconscious bias detection
            LegalDatabaseTool(),       # Indian labor law compliance
            FairnessAnalyzer()         # Equal opportunity assessment
        ]
        
    async def analyze(self, context):
        return {
            "bias_detection": {},
            "legal_compliance": {},
            "fairness_assessment": {},
            "discrimination_risks": [],
            "compliance_recommendations": [],
            "legal_documentation": {},
            "audit_trail": {},
            "risk_mitigation": []
        }
```

## 🗄️ **DATA ARCHITECTURE**

### **Supabase Schema Integration (Existing Tables)**
```sql
-- DO NOT RECREATE - These tables already exist
user_profiles (
    user_id UUID PRIMARY KEY,
    email VARCHAR,
    full_name VARCHAR,
    access_type VARCHAR, -- 'trial', 'full', 'admin'
    trial_resumes_analyzed INTEGER DEFAULT 0,
    trial_limit INTEGER DEFAULT 100,
    encrypted_data BYTEA, -- AES-256 encrypted user data
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

resumes (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(user_id),
    filename VARCHAR,
    processed_content TEXT, -- Compressed resume text
    ai_analysis JSONB, -- 4-agent analysis results
    encrypted_file BYTEA, -- AES-256 encrypted original file
    processing_status VARCHAR, -- 'pending', 'processing', 'completed', 'failed'
    agent_insights JSONB, -- Individual agent outputs
    consensus_score FLOAT, -- Final scoring from all agents
    legal_compliance JSONB, -- Legal compliance assessment
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

user_activity (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(user_id),
    action VARCHAR, -- 'upload', 'analysis', 'legal_query', etc.
    details JSONB, -- Encrypted activity details
    encrypted_payload BYTEA, -- AES-256 encrypted sensitive data
    timestamp TIMESTAMP,
    ip_address INET,
    user_agent TEXT
)

hr_legal_queries (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(user_id),
    query_text TEXT,
    query_context JSONB, -- Query type, urgency, etc.
    response_data JSONB, -- AI-generated legal response
    encrypted_content BYTEA, -- AES-256 encrypted sensitive content
    confidence_score FLOAT,
    sources JSONB, -- Legal document sources
    created_at TIMESTAMP
)

system_config (
    key VARCHAR PRIMARY KEY,
    value JSONB,
    encrypted_value BYTEA, -- For sensitive configurations
    description TEXT,
    updated_by UUID,
    updated_at TIMESTAMP
)

admin_users (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(user_id),
    admin_level VARCHAR, -- 'super_admin', 'admin', 'moderator'
    permissions JSONB,
    encrypted_credentials BYTEA,
    created_at TIMESTAMP,
    last_login TIMESTAMP
)
```

### **Encryption & Compression Strategy**
```python
class DataSecurityManager:
    def __init__(self):
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        self.compression_level = 9  # Maximum compression
        
    def encrypt_and_compress(self, data):
        # 1. JSON serialize if needed
        json_data = json.dumps(data) if not isinstance(data, str) else data
        
        # 2. Compress with LZ4 for speed or GZIP for size
        compressed = lz4.compress(json_data.encode('utf-8'))
        
        # 3. Encrypt with AES-256-GCM
        cipher = AES.new(self.encryption_key, AES.MODE_GCM)
        encrypted_data, tag = cipher.encrypt_and_digest(compressed)
        
        # 4. Return encrypted binary blob for PostgreSQL
        return cipher.nonce + tag + encrypted_data
    
    def decrypt_and_decompress(self, encrypted_blob):
        # Reverse the process
        nonce = encrypted_blob[:16]
        tag = encrypted_blob[16:32]
        encrypted_data = encrypted_blob[32:]
        
        cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=nonce)
        compressed = cipher.decrypt_and_verify(encrypted_data, tag)
        
        decompressed = lz4.decompress(compressed)
        return json.loads(decompressed.decode('utf-8'))
```

## 🌐 **API ARCHITECTURE**

### **High-Performance Flask Application**
```python
from flask import Flask
from flask_cors import CORS
import asyncio
import logging

class HighPerformanceFlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_cors()
        self.setup_middleware()
        self.setup_routes()
        self.setup_error_handlers()
        
    def setup_cors(self):
        CORS(self.app, 
             origins=["https://hrtool-sable.vercel.app"],
             supports_credentials=True,
             allow_headers=['Content-Type', 'Authorization'],
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    def setup_middleware(self):
        @self.app.before_request
        def before_request():
            # Authentication middleware
            # Rate limiting middleware
            # Security headers middleware
            # Performance monitoring
            pass
    
    def setup_routes(self):
        # Register all route blueprints
        from api.auth import auth_bp
        from api.resumes import resumes_bp
        from api.legal import legal_bp
        from api.admin import admin_bp
        
        self.app.register_blueprint(auth_bp, url_prefix='/api/auth')
        self.app.register_blueprint(resumes_bp, url_prefix='/api')
        self.app.register_blueprint(legal_bp, url_prefix='/api/hr-legal')
        self.app.register_blueprint(admin_bp, url_prefix='/api/admin')
```

### **Real-Time Processing Updates**
```python
class RealTimeUpdateManager:
    def __init__(self):
        self.websocket_connections = {}
        
    async def send_processing_update(self, user_id, stage, data):
        update = {
            "type": "processing_update",
            "stage": stage,  # 'technical_agent', 'experience_agent', etc.
            "progress": data.get('progress', 0),
            "status": data.get('status', 'processing'),
            "agent_insights": data.get('insights', {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id in self.websocket_connections:
            await self.websocket_connections[user_id].send(json.dumps(update))
```

## 🔧 **AI PROVIDER MANAGEMENT**

### **Dynamic Provider Switching**
```python
class AIProviderManager:
    def __init__(self):
        self.providers = {
            'ollama': OllamaProvider(),
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider()
        }
        self.admin_settings = SystemConfigManager()
        
    async def get_provider_for_user(self, user_id):
        # Check admin override
        admin_override = await self.admin_settings.get('ai_provider_override')
        if admin_override:
            return self.providers[admin_override]
        
        # Check user preference
        user_preference = await self.get_user_preference(user_id)
        if user_preference and user_preference in self.providers:
            return self.providers[user_preference]
        
        # Default to Ollama
        return self.providers['ollama']
    
    async def get_best_provider_for_task(self, task_type, complexity):
        # Route different tasks to optimal providers
        if task_type == 'legal_analysis' and complexity == 'high':
            return self.providers['anthropic']  # Better for legal reasoning
        elif task_type == 'technical_analysis':
            return self.providers['ollama']     # Fast and local
        else:
            return self.providers['openai']     # Balanced performance
```

## 📊 **ADMIN CONTROL SYSTEM**

### **Comprehensive Admin Dashboard**
```python
class AdminDashboard:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.config_manager = SystemConfigManager()
        
    async def get_system_metrics(self):
        return {
            "performance": {
                "avg_processing_time": await self.get_avg_processing_time(),
                "active_users": await self.get_active_users_count(),
                "api_requests_per_minute": await self.get_api_rate(),
                "railway_resource_usage": await self.get_railway_metrics(),
                "supabase_connection_health": await self.check_supabase_health()
            },
            "costs": {
                "ai_api_usage": await self.get_ai_api_costs(),
                "supabase_usage": await self.get_supabase_costs(),
                "railway_usage": await self.get_railway_costs()
            },
            "quality": {
                "ai_analysis_accuracy": await self.get_accuracy_metrics(),
                "user_satisfaction": await self.get_satisfaction_scores(),
                "error_rates": await self.get_error_rates()
            }
        }
    
    async def update_system_config(self, config_key, value):
        # Dynamic system configuration
        await self.config_manager.update_encrypted(config_key, value)
        await self.broadcast_config_change(config_key, value)
```

## 🚀 **RAILWAY OPTIMIZATION STRATEGIES**

### **Performance Optimizations**
```python
# Connection Pooling
SUPABASE_CONNECTION_POOL = 15  # Optimal for 8GB RAM
OLLAMA_CONCURRENT_REQUESTS = 4  # Match CPU cores

# Memory Management
MAX_RESUME_CACHE_SIZE = 100     # Keep processed resumes in memory
FAISS_INDEX_CACHE = True        # Cache vector indexes
EMBEDDING_MODEL_CACHE = True    # Keep models loaded

# Processing Optimizations
ASYNC_FILE_PROCESSING = True    # Non-blocking file operations
BATCH_AGENT_ANALYSIS = True     # Process multiple resumes together
STREAMING_RESPONSES = True      # Stream large responses
```

### **Railway-Specific Configuration**
```python
# Railway PORT detection
PORT = int(os.environ.get('PORT', 8000))

# Railway health checks
@app.route('/api/health')
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "railway": {
            "memory_usage": get_memory_usage(),
            "cpu_usage": get_cpu_usage(),
            "disk_usage": get_disk_usage()
        },
        "services": {
            "ollama": check_ollama_health(),
            "supabase": check_supabase_health(),
            "faiss": check_faiss_health()
        }
    }
```

## 🛡️ **SECURITY ARCHITECTURE**

### **Multi-Layer Security**
```python
class SecurityManager:
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.auth_manager = AuthenticationManager()
        self.encryption_manager = EncryptionManager()
        
    async def validate_request(self, request):
        # 1. Rate limiting
        if not await self.rate_limiter.check(request.remote_addr):
            raise RateLimitExceeded()
        
        # 2. Authentication
        user = await self.auth_manager.validate_token(request.headers.get('Authorization'))
        if not user:
            raise UnauthorizedAccess()
        
        # 3. Input validation
        if not self.validate_input(request.json):
            raise InvalidInput()
        
        # 4. Permission check
        if not await self.check_permissions(user, request.endpoint):
            raise InsufficientPermissions()
        
        return user
```

**This technical blueprint provides complete architectural guidance for building the world-class agentic HR system on Railway with optimal performance, security, and scalability.**
