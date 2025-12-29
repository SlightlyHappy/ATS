# 🚀 HR Resume Analysis API Integration Guide

Complete API documentation for frontend applications (Vercel, React, Next.js, etc.) to integrate with the Railway-deployed HR Resume Analysis backend.

## 📋 Table of Contents
- [Base Configuration](#base-configuration)
- [Authentication](#authentication)
- [Resume Management](#resume-management)
- [AI Analysis](#ai-analysis)
- [Legal RAG System](#legal-rag-system)
- [Candidate Portal](#candidate-portal)
- [Admin Dashboard](#admin-dashboard)
- [Real-time Updates (Polling-based)](#real-time-updates-polling-based)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## 🔧 Base Configuration

### Railway Backend URL
```javascript
const API_BASE_URL = "https://your-railway-app.railway.app";
// Replace with your actual Railway deployment URL
```

### Headers Setup
```javascript
const defaultHeaders = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

const authHeaders = (token) => ({
  ...defaultHeaders,
  'Authorization': `Bearer ${token}`
});
```

---

## 🔐 Authentication

### 1. Admin Login
**Endpoint:** `POST /api/auth/login`  
**Auth Required:** ❌ No

**Request:**
```json
{
  "email": "admin@bearsystems.co.in",
  "password": "your_admin_password"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**JavaScript Example:**
```javascript
const login = async (email, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: defaultHeaders,
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem('auth_token', data.access_token);
      return data;
    } else {
      throw new Error(data.detail || 'Login failed');
    }
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};
```

### 2. Token Refresh
**Endpoint:** `POST /api/auth/refresh`  
**Auth Required:** ✅ Yes (Bearer Token)

**Response:**
```json
{
  "access_token": "new_jwt_token_here",
  "token_type": "bearer"
}
```

### 3. User Registration (NEW)
**Endpoint:** `POST /api/auth/register`  
**Auth Required:** ❌ No

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "job_title": "HR Manager",
  "department": "Human Resources",
  "phone": "+1234567890",
  "bio": "HR professional with 5 years experience"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 📄 Resume Management

### 1. Upload Resume
**Endpoint:** `POST /api/upload`  
**Auth Required:** ✅ Yes  
**Content-Type:** `multipart/form-data`

> **📦 ZIP File Handling Recommendation:**  
> **For better performance and user experience, it's recommended that frontend applications handle ZIP file extraction client-side and upload each resume file individually.** This approach provides:
> - Better progress tracking per file
> - Individual error handling per resume
> - Faster processing (parallel uploads)
> - More granular user feedback
> 
> See the [Batch Upload Example](#batch-upload-example) below for implementation details.

**Request (FormData):**
```javascript
const uploadResume = async (file, token, candidateName = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (candidateName) {
    formData.append('candidate_name', candidateName);
  }
  
  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
      // Don't set Content-Type for FormData - browser sets it automatically
    },
    body: formData
  });
  
  return await response.json();
};
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Resume uploaded, indexed, and queued for AI analysis",
  "resume_id": 123,
  "task_id": "celery-task-uuid-here",
  "filename": "john_doe_resume.pdf",
  "text_length": 2456,
  "queue_priority": 1,
  "estimated_analysis_time": "1-3 minutes",
  "progress_url": "/api/jobs/progress/celery-task-uuid-here",
  "rag_indexed": true,
  "status_check": "Use task_id to check analysis progress"
}
```

### 📦 Batch Upload Example (Recommended for ZIP Files)

**Frontend ZIP Handling with JSZip:**
```javascript
// npm install jszip
import JSZip from 'jszip';

const handleZipUpload = async (zipFile, token, onProgress) => {
  try {
    const zip = new JSZip();
    const zipContent = await zip.loadAsync(zipFile);
    
    const resumeFiles = [];
    const supportedExtensions = ['.pdf', '.docx', '.doc', '.txt'];
    
    // Extract individual files from ZIP
    for (const [filename, file] of Object.entries(zipContent.files)) {
      if (!file.dir && supportedExtensions.some(ext => filename.toLowerCase().endsWith(ext))) {
        const blob = await file.async('blob');
        resumeFiles.push({
          filename: filename,
          file: new File([blob], filename, { type: blob.type })
        });
      }
    }
    
    console.log(`Found ${resumeFiles.length} resume files in ZIP`);
    
    // Upload files individually with progress tracking
    const uploadResults = [];
    const totalFiles = resumeFiles.length;
    
    for (let i = 0; i < resumeFiles.length; i++) {
      const { filename, file } = resumeFiles[i];
      
      try {
        onProgress && onProgress({
          current: i + 1,
          total: totalFiles,
          filename: filename,
          status: 'uploading'
        });
        
        const result = await uploadResume(file, token);
        uploadResults.push({ filename, success: true, result });
        
        onProgress && onProgress({
          current: i + 1,
          total: totalFiles,
          filename: filename,
          status: 'completed'
        });
        
        // Small delay to prevent overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 100));
        
      } catch (error) {
        console.error(`Failed to upload ${filename}:`, error);
        uploadResults.push({ filename, success: false, error: error.message });
        
        onProgress && onProgress({
          current: i + 1,
          total: totalFiles,
          filename: filename,
          status: 'error',
          error: error.message
        });
      }
    }
    
    return {
      totalFiles,
      successful: uploadResults.filter(r => r.success).length,
      failed: uploadResults.filter(r => !r.success).length,
      results: uploadResults
    };
    
  } catch (error) {
    console.error('ZIP processing error:', error);
    throw new Error(`Failed to process ZIP file: ${error.message}`);
  }
};

// Usage in React component
const ZipUploadComponent = () => {
  const [uploadProgress, setUploadProgress] = useState(null);
  const { token } = useHRApi();
  
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    
    if (file.name.toLowerCase().endsWith('.zip')) {
      // Handle ZIP file
      const results = await handleZipUpload(file, token, setUploadProgress);
      console.log('Batch upload results:', results);
    } else {
      // Handle single file
      const result = await uploadResume(file, token);
      console.log('Single upload result:', result);
    }
  };
  
  return (
    <div>
      <input type="file" accept=".pdf,.docx,.doc,.txt,.zip" onChange={handleFileSelect} />
      
      {uploadProgress && (
        <div className="upload-progress">
          <div>Uploading: {uploadProgress.filename}</div>
          <div>Progress: {uploadProgress.current}/{uploadProgress.total}</div>
          <div>Status: {uploadProgress.status}</div>
          {uploadProgress.error && <div className="error">Error: {uploadProgress.error}</div>}
        </div>
      )}
    </div>
  );
};
```

**Benefits of Frontend ZIP Extraction:**
- ✅ **Better UX**: Individual file progress tracking
- ✅ **Error Handling**: Per-file error reporting  
- ✅ **Performance**: Parallel processing potential
- ✅ **Reliability**: Failed files don't affect others
- ✅ **Feedback**: Real-time progress updates
```

### 2. Get All Resumes
**Endpoint:** `GET /api/resumes`  
**Auth Required:** ✅ Yes

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Items per page (default: 100, max: 100)
- Admin users can see all resumes; regular users see only their own

**Request:**
```javascript
const getResumes = async (token, params = {}) => {
  const queryString = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}/api/resumes?${queryString}`;
  
  const response = await fetch(url, {
    headers: authHeaders(token)
  });
  
  return await response.json();
};

// Usage examples:
// getResumes(token)
// getResumes(token, { skip: 10, limit: 50 })
```

**Response:**
```json
{
  "resumes": [
    {
      "id": 123,
      "original_filename": "John Doe - Software Engineer.pdf",
      "candidate_name": "John Doe",
      "uploaded_at": "2025-08-18T14:30:00Z",
      "is_analyzed": true,
      "analysis_score": 87.5,
      "text_length": 2456
    }
  ],
  "total": 1
}
```

### 3. Get Single Resume
**Endpoint:** `GET /api/resumes/{resume_id}`  
**Auth Required:** ✅ Yes

**Response:**
```json
{
  "id": 123,
  "filename": "John Doe - Software Engineer.pdf",
  "candidate_name": "John Doe",
  "uploaded_at": "2025-08-18T14:30:00Z",
  "is_processed": true,
  "is_analyzed": true,
  "analysis_score": 87.5,
  "text_length": 2456,
  "analysis_results": {
    "final_score": 87.5,
    "agent_results": {
      "technical": {
        "score": 85,
        "insights": ["Strong Python and React skills", "5+ years experience"],
        "extracted_data": {
          "skills": ["Python", "React", "PostgreSQL"],
          "years_experience": 5.5
        }
      },
      "experience": {
        "score": 90,
        "insights": ["Excellent project diversity", "Leadership experience"]
      }
    }
  }
}
```

### 4. Delete Resume
**Endpoint:** `DELETE /api/resumes/{resume_id}` (Available through Admin API)
**Auth Required:** ✅ Yes (Admin only)

**Response:**
```json
{
  "message": "Resume deleted successfully",
  "deleted_id": 123
}
```

---

## 🤖 AI Analysis

### 1. Trigger Manual Analysis
**Endpoint:** `POST /api/analyze/{resume_id}`  
**Auth Required:** ✅ Yes

**Request:**
```json
{
  "force_reanalyze": false
}
```

**Response:**
```json
{
  "message": "Analysis queued successfully",
  "task_id": "celery-task-uuid-here",
  "resume_id": 123
}
```

### 2. Get Analysis Status  
**Endpoint:** `GET /api/jobs/status/{task_id}`  
**Auth Required:** ✅ Yes

**Response (In Progress):**
```json
{
  "job_id": "celery-task-uuid-here",
  "status": "processing",
  "progress_percentage": 65,
  "current_stage": "ai_analysis",
  "total_files": 1,
  "completed_files": 0,
  "failed_files": 0,
  "started_at": "2025-08-18T14:30:00Z"
}
```

**Response (Completed):**
```json
{
  "job_id": "celery-task-uuid-here",
  "status": "completed",
  "progress_percentage": 100,
  "total_files": 1,
  "completed_files": 1,
  "failed_files": 0,
  "completed_at": "2025-08-18T14:35:00Z",
  "processing_time_seconds": 245,
  "resume_jobs": [
    {
      "resume_id": 123,
      "status": "completed",
      "analysis_score": 87.5,
      "skills_count": 12
    }
  ]
}
```

### 3. Batch Analysis
**Endpoint:** `POST /api/bulk_upload` (Batch upload with analysis)
**Auth Required:** ✅ Yes (Admin only)

**Request:**
```json
{
  "files": ["file1.pdf", "file2.docx"]
}
```

**Response:**
```json
{
  "message": "Batch upload queued",
  "job_id": "batch-uuid-here",
  "total_files": 2
}
```

### 4. Get Enterprise Analytics (NEW)
**Endpoint:** `GET /api/resume/{resume_id}/enterprise-analytics`  
**Auth Required:** ✅ Yes

**Response:**
```json
{
  "success": true,
  "resume_id": 123,
  "candidate_name": "John Doe",
  "candidate_analytics": {
    "metrics": {
      "technical_depth_score": 85.2,
      "leadership_potential_score": 78.5,
      "innovation_indicator": 82.1,
      "communication_excellence": 88.3,
      "market_readiness_index": 90.1,
      "role_category": "full_stack_developer",
      "experience_band": "senior"
    },
    "skill_proficiency_map": {
      "python": {
        "proficiency_level": 4,
        "market_demand_score": 95,
        "years_experience": 5.5
      }
    }
  },
  "peer_group_analytics": {
    "role_category": "full_stack_developer",
    "experience_band": "senior",
    "overall_percentile": 78.5,
    "technical_percentile": 82.1
  },
  "generated_at": "2025-08-18T14:30:00.000Z"
}
```

---

## 🏛️ Legal RAG System

The Legal RAG (Retrieval-Augmented Generation) system provides comprehensive legal document search, compliance guidance, and employment law analysis for HR professionals.

### 1. Legal Query (Comprehensive Legal Analysis)
**Endpoint:** `POST /api/legal/query`  
**Auth Required:** ✅ Yes

**Request:**
```json
{
  "question": "What are the notice period requirements for employee termination in India?",
  "query_type": "compliance_check",
  "document_types": ["act", "regulation"],
  "categories": ["employment", "termination"],
  "jurisdiction": "India",
  "max_results": 5,
  "min_relevance_score": 0.3,
  "include_citations": true,
  "include_full_text": false
}
```

**Available Query Types:**
- `compliance_check` - Compliance requirements and obligations
- `employee_rights` - Employee rights and protections
- `policy_guidance` - Policy implementation guidance  
- `legal_interpretation` - Legal text interpretation
- `penalty_assessment` - Penalties and consequences
- `documentation_requirements` - Required documentation

**Available Document Types:**
- `act` - Legal acts and statutes
- `case_law` - Court decisions and precedents
- `regulation` - Government regulations
- `handbook` - Official handbooks
- `circular` - Government circulars
- `notification` - Official notifications
- `rules` - Rules and procedures
- `amendment` - Legal amendments

**Available Categories:**
- `employment` - Employment law
- `wages` - Wage and salary regulations
- `safety` - Workplace safety
- `compliance` - General compliance
- `termination` - Employment termination
- `leave` - Leave policies
- `provident_fund` - PF regulations
- `gratuity` - Gratuity provisions
- `bonus` - Bonus regulations
- `industrial_relations` - Industrial relations
- `trade_unions` - Trade union matters

**Response (Success):**
```json
{
  "success": true,
  "query": "What are the notice period requirements for employee termination in India?",
  "query_type": "compliance_check",
  "legal_analysis": {
    "direct_answer": "Under the Industrial Disputes Act, 1947, employees must be given one month's notice or pay in lieu thereof for termination.",
    "legal_interpretation": "The notice period varies based on the nature of employment and applicable labor laws...",
    "compliance_summary": "Employers must comply with notice period requirements under multiple acts including Industrial Disputes Act and specific state labor laws.",
    "risk_assessment": "Medium",
    "compliance_recommendations": [
      "Ensure notice period complies with Industrial Disputes Act requirements",
      "Check applicable state-specific labor laws",
      "Maintain proper termination documentation"
    ],
    "required_actions": [
      "Provide written notice to employee",
      "Update employee records",
      "Calculate final settlement including notice pay"
    ],
    "documentation_needed": [
      "Termination notice letter",
      "Employee acknowledgment",
      "Final settlement calculation"
    ],
    "applicable_laws": [
      "Industrial Disputes Act, 1947",
      "Shops and Establishments Act (State-specific)",
      "Employment Contract Terms"
    ],
    "relevant_sections": [
      "Section 25F of Industrial Disputes Act",
      "Section 25N for notice requirements"
    ],
    "search_results": [
      {
        "document_id": 123,
        "chunk_id": 456,
        "title": "Industrial Disputes Act, 1947",
        "document_type": "act",
        "category": "employment",
        "jurisdiction": "India",
        "matched_content": "Every workman whose services are terminated shall be entitled to notice of not less than one month...",
        "content_preview": "Section 25F outlines the conditions precedent to retrenchment...",
        "section_reference": "Section 25F",
        "legal_citation": "Industrial Disputes Act, 1947, Section 25F",
        "relevance_score": 0.95,
        "keywords_matched": ["notice", "termination", "employee"]
      }
    ],
    "total_results_found": 3,
    "confidence_score": 0.92,
    "analysis_completeness": 0.88,
    "processing_time_ms": 1250,
    "sources_consulted": 5
  },
  "processing_time": 1.25,
  "user": "hr@company.com"
}
```

### 2. Legal Semantic Search
**Endpoint:** `POST /api/legal/search`  
**Auth Required:** ✅ Yes

**Request:**
```json
{
  "query": "employee grievance handling procedures",
  "document_types": ["handbook", "act"],
  "categories": ["employment", "industrial_relations"],
  "jurisdiction": "India",
  "top_k": 10,
  "min_score": 0.3,
  "include_content": true
}
```

**Response:**
```json
{
  "success": true,
  "query": "employee grievance handling procedures",
  "total_results": 8,
  "results": [
    {
      "document_id": 789,
      "chunk_id": 101,
      "title": "Labour Industrial Relations Code",
      "document_type": "act",
      "category": "industrial_relations",
      "jurisdiction": "India",
      "matched_content": "Every establishment employing 20 or more workers shall constitute a grievance redressal committee...",
      "content_preview": "The grievance redressal committee shall consist of equal number of representatives...",
      "section_reference": "Chapter IV, Section 43",
      "legal_citation": "Industrial Relations Code, 2020, Section 43",
      "relevance_score": 0.89,
      "legal_keywords": ["grievance", "redressal", "committee"],
      "hr_relevance_keywords": ["employee", "complaint", "resolution"],
      "compliance_level": "Mandatory",
      "penalty_mentioned": false
    }
  ],
  "filters_applied": {
    "document_types": ["handbook", "act"],
    "categories": ["employment", "industrial_relations"],
    "jurisdiction": "India"
  },
  "search_type": "semantic_similarity"
}
```

### 3. List Legal Documents
**Endpoint:** `GET /api/legal/documents`  
**Auth Required:** ✅ Yes

**Query Parameters:**
- `document_type` (DocumentType): Filter by document type
- `category` (LegalCategory): Filter by legal category
- `jurisdiction` (string): Filter by jurisdiction
- `processing_status` (ProcessingStatus): Filter by status
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (1-100, default: 20)

**Response:**
```json
{
  "documents": [
    {
      "id": 123,
      "filename": "Industrial_Disputes_Act_1947.pdf",
      "original_filename": "Industrial_Disputes_Act_1947.pdf",
      "title": "Industrial Disputes Act, 1947",
      "document_type": "act",
      "category": "employment",
      "jurisdiction": "India",
      "authority": "Government of India",
      "act_number": "Act No. 14 of 1947",
      "processing_status": "indexed",
      "is_processed": true,
      "is_indexed": true,
      "rag_indexed": true,
      "chunk_count": 245,
      "embedding_count": 245,
      "sections_count": 38,
      "query_count": 1247,
      "content_quality_score": 0.94,
      "legal_completeness_score": 0.96,
      "relevance_score": 0.92,
      "file_size": 2048576,
      "text_length": 125000,
      "language": "en",
      "created_at": "2025-08-18T10:00:00Z",
      "updated_at": "2025-08-18T14:30:00Z",
      "uploaded_at": "2025-08-18T10:00:00Z",
      "processed_at": "2025-08-18T10:15:00Z",
      "last_accessed": "2025-08-20T09:30:00Z"
    }
  ],
  "total_count": 156,
  "filtered_count": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 8
}
```

### 4. Get Single Legal Document
**Endpoint:** `GET /api/legal/documents/{document_id}`  
**Auth Required:** ✅ Yes

**Response:** *(Same structure as individual document above)*

### 5. Upload Legal Document
**Endpoint:** `POST /api/legal/documents/upload`  
**Auth Required:** ✅ Yes (Admin)  
**Content-Type:** `multipart/form-data`

**Request (FormData):**
```javascript
const uploadLegalDocument = async (file, metadata, token) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', metadata.title);
  formData.append('document_type', metadata.document_type);
  formData.append('category', metadata.category);
  formData.append('jurisdiction', metadata.jurisdiction);
  formData.append('authority', metadata.authority);
  formData.append('act_number', metadata.act_number);
  
  const response = await fetch(`${API_BASE_URL}/api/legal/documents/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  return await response.json();
};
```

### 6. Legal System Analytics
**Endpoint:** `GET /api/legal/analytics`  
**Auth Required:** ✅ Yes (Admin)

**Response:**
```json
{
  "total_documents": 156,
  "documents_by_type": {
    "act": 45,
    "regulation": 32,
    "handbook": 28,
    "case_law": 24,
    "circular": 15,
    "notification": 12
  },
  "documents_by_category": {
    "employment": 48,
    "wages": 25,
    "safety": 22,
    "compliance": 20,
    "termination": 18,
    "industrial_relations": 15,
    "leave": 8
  },
  "documents_by_jurisdiction": {
    "India": 145,
    "Karnataka": 6,
    "Maharashtra": 3,
    "Delhi": 2
  },
  "processed_documents": 150,
  "indexed_documents": 148,
  "total_chunks": 15648,
  "total_embeddings": 15648,
  "total_queries": 8756,
  "queries_last_30_days": 1247,
  "most_queried_categories": [
    {"category": "employment", "query_count": 2156},
    {"category": "wages", "query_count": 1578},
    {"category": "termination", "query_count": 1234}
  ],
  "average_response_time_ms": 850.5,
  "average_content_quality": 0.91,
  "average_relevance_score": 0.85,
  "user_satisfaction_rating": 4.2
}
```

### 7. Legal System Status
**Endpoint:** `GET /api/legal/status`  
**Auth Required:** ✅ Yes

**Response:**
```json
{
  "system_ready": true,
  "documents_indexed": 148,
  "last_index_update": "2025-08-20T08:00:00Z",
  "embedding_service_status": "healthy",
  "vector_store_status": "connected",
  "average_query_time_ms": 850.5,
  "cache_hit_rate": 0.65,
  "storage_used_mb": 2048.5,
  "embedding_dimension": 1536,
  "max_supported_documents": 10000,
  "database_connection": true,
  "vector_store_connection": true,
  "embedding_model_loaded": true
}
```

### 8. Bulk Document Processing
**Endpoint:** `POST /api/legal/bulk/process`  
**Auth Required:** ✅ Yes (Admin)

**Request:**
```json
{
  "directory_path": "/legal_documents/new_batch",
  "document_type": "regulation",
  "category": "employment",
  "jurisdiction": "India",
  "auto_categorize": true
}
```

### 9. Helper Endpoints

**Get Legal Categories:**
- **Endpoint:** `GET /api/legal/categories`
- **Response:** `[{"value": "employment", "label": "Employment"}, ...]`

**Get Document Types:**
- **Endpoint:** `GET /api/legal/document-types`  
- **Response:** `[{"value": "act", "label": "Act"}, ...]`

**Get Query Types:**
- **Endpoint:** `GET /api/legal/query-types`
- **Response:** `[{"value": "compliance_check", "label": "Compliance Check"}, ...]`

---

## 👥 Candidate Portal

Complete candidate-facing system with authentication, resume upload, and AI-powered career advice.

### 1. Candidate Authentication
**Endpoint:** `POST /api/auth/candidate/login`  
**Auth Required:** ❌ No

**Request:**
```json
{
  "email": "candidate@example.com",
  "device_info": {
    "user_agent": "Mozilla/5.0...",
    "screen_resolution": "1920x1080",
    "timezone": "Asia/Kolkata",
    "language": "en-US"
  }
}
```

**Headers Required:**
```javascript
{
  'X-Request-ID': 'unique-request-id',
  'X-Timestamp': '2025-08-20T10:30:00Z',
  'X-Signature': 'optional-security-signature'
}
```

**Response:**
```json
{
  "access_token": "candidate-jwt-token-here",
  "token_type": "bearer",
  "session_id": "session-uuid-here",
  "expires_in": 3600,
  "candidate_profile": {
    "email": "candidate@example.com",
    "session_count": 1,
    "last_login": "2025-08-20T10:30:00Z"
  }
}
```

### 2. Candidate Token Refresh
**Endpoint:** `POST /api/auth/candidate/refresh`  
**Auth Required:** ✅ Yes (Candidate Token)

**Response:**
```json
{
  "access_token": "new-candidate-jwt-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 3. Candidate Logout
**Endpoint:** `POST /api/auth/candidate/logout`  
**Auth Required:** ✅ Yes (Candidate Token)

**Response:**
```json
{
  "message": "Successfully logged out",
  "session_terminated": true
}
```

### 4. Candidate Profile
**Endpoint:** `GET /api/candidates/profile`  
**Auth Required:** ✅ Yes (Candidate Token)

**Response:**
```json
{
  "email": "candidate@example.com",
  "session_id": "session-uuid-here",
  "total_sessions": 3,
  "resume_uploaded": true,
  "resume_analysis_status": "completed",
  "analysis_score": 87.5,
  "last_activity": "2025-08-20T10:30:00Z",
  "created_at": "2025-08-18T14:30:00Z"
}
```

### 5. Candidate Resume Upload
**Endpoint:** `POST /api/candidates/upload-resume`  
**Auth Required:** ✅ Yes (Candidate Token)  
**Content-Type:** `multipart/form-data`

**Request:**
```javascript
const uploadCandidateResume = async (file, token) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/api/candidates/upload-resume`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  return await response.json();
};
```

**Response:**
```json
{
  "message": "Resume uploaded successfully. Analysis will begin shortly.",
  "resume_id": "resume-uuid-here",
  "status": "uploaded",
  "analysis_queued": true,
  "estimated_processing_time": "2-5 minutes"
}
```

### 6. Candidate Chat/Career Advice
**Endpoint:** `POST /api/candidates/chat`  
**Auth Required:** ✅ Yes (Candidate Token)

**Request:**
```json
{
  "message": "What skills should I improve to become a senior developer?",
  "conversation_id": "optional-conversation-uuid"
}
```

**Response:**
```json
{
  "response": "Based on your resume analysis, I recommend focusing on these key areas: 1) Advanced system design and architecture patterns...",
  "conversation_id": "conversation-uuid",
  "suggestions": [
    "Learn microservices architecture",
    "Gain experience with cloud platforms (AWS/Azure)",
    "Practice system design interviews"
  ],
  "personalized": true,
  "based_on_resume_analysis": true
}
```

### 7. Payment Integration (Razorpay)

**Create Payment Order:**
**Endpoint:** `POST /api/candidates/create-payment-order`

**Verify Payment:**
**Endpoint:** `POST /api/candidates/verify-payment`

**Payment Status:**
**Endpoint:** `GET /api/candidates/payment-status`

---

## 📊 Admin Dashboard

### 1. Get Dashboard Statistics
**Endpoint:** `GET /api/admin/dashboard`  
**Auth Required:** ✅ Yes (Admin)

**Response:**
```json
{
  "success": true,
  "dashboard": {
    "overview": {
      "total_recruiters": 12,
      "active_sessions": 5,
      "total_payments": 1247,
      "conversion_rate": 15.2
    },
    "recent_activity": {
      "candidate_sessions": [
        {
          "session_id": "session-123",
          "candidate_name": "John Doe",
          "created_at": "2025-08-18T14:30:00Z",
          "status": "completed"
        }
      ],
      "payments": [
        {
          "payment_id": "pay-456",
          "amount": 99.99,
          "recruiter_email": "hr@company.com",
          "created_at": "2025-08-18T13:00:00Z"
        }
      ],
      "recruiters": [
        {
          "id": 789,
          "email": "recruiter@company.com",
          "company_name": "Tech Corp",
          "created_at": "2025-08-17T10:00:00Z"
        }
      ]
    },
    "alerts": [
      {
        "type": "warning",
        "message": "Conversion rate below target (15.2% < 20%)"
      }
    ]
  }
}
```

### 2. System Health Check
**Endpoint:** `GET /api/admin/health`  
**Auth Required:** ✅ Yes (Admin)

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "database_status": "connected",
  "timestamp": "2025-08-18T14:30:00Z"
}
```

### 3. Retry Failed Analysis (Available through reanalyze endpoints)
**Endpoint:** `POST /api/resume/{resume_id}/reanalyze`  
**Auth Required:** ✅ Yes

**Response:**
```json
{
  "message": "Analysis queued successfully",
  "task_id": "retry-task-uuid-here",
  "resume_id": 456
}
```

---

## 🔄 Real-time Updates (Polling-based)

Since WebSocket endpoints are not currently implemented, use polling for real-time updates:

### Job Progress Polling
```javascript
const pollJobStatus = async (jobId, token) => {
  const poll = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs/status/${jobId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      
      if (data.status === 'completed' || data.status === 'failed') {
        return data; // Stop polling
      }
      
      // Continue polling every 2 seconds
      setTimeout(() => poll(), 2000);
      return data;
      
    } catch (error) {
      console.error('Polling error:', error);
      return null;
    }
  };
  
  return poll();
};
```

### Real-time Dashboard Updates
```javascript
const pollDashboard = async (token, onUpdate) => {
  const pollDashboard = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      onUpdate(data);
      
      // Update every 30 seconds
      setTimeout(() => pollDashboard(), 30000);
      
    } catch (error) {
      console.error('Dashboard polling error:', error);
    }
  };
  
  pollDashboard();
};
```

---

## ⚠️ Error Handling

### Standard Error Response Format
```json
{
  "error": true,
  "error_type": "validation_error",
  "message": "Invalid file format",
  "details": {
    "field": "file",
    "allowed_formats": [".pdf", ".docx", ".doc", ".txt"]
  },
  "timestamp": "2025-08-18T14:30:00Z",
  "request_id": "req-uuid-here"
}
```

### Common Error Codes
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `413` - Payload Too Large (file size exceeded)
- `422` - Unprocessable Entity (business logic error)
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

### JavaScript Error Handling Pattern
```javascript
const handleApiResponse = async (response) => {
  const data = await response.json();
  
  if (!response.ok) {
    if (response.status === 401) {
      // Token expired - redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
      return;
    }
    
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  
  return data;
};
```

---

## 🚦 Rate Limiting

### Limits per Authentication Level
- **Unauthenticated**: 10 requests/minute
- **Authenticated User**: 100 requests/minute  
- **Admin User**: 500 requests/minute

### Rate Limit Headers
```javascript
// Check remaining requests
const checkRateLimit = (response) => {
  const remaining = response.headers.get('X-RateLimit-Remaining');
  const resetTime = response.headers.get('X-RateLimit-Reset');
  
  if (remaining && parseInt(remaining) < 5) {
    console.warn(`Rate limit warning: ${remaining} requests remaining`);
  }
};
```

---

## 🔧 Complete React Integration Example

```jsx
// hooks/useHRApi.js
import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export const useHRApi = () => {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    const expires = localStorage.getItem('token_expires');
    
    if (storedToken && expires && Date.now() < parseInt(expires)) {
      setToken(storedToken);
    }
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setToken(data.access_token);
        localStorage.setItem('auth_token', data.access_token);
        return data;
      } else {
        throw new Error(data.detail);
      }
    } finally {
      setLoading(false);
    }
  };

  const uploadResume = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    
    return await response.json();
  };

  const getResumes = async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`${API_BASE_URL}/api/resumes?${queryString}`, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return await response.json();
  };

  const getLegalQuery = async (question, queryType = 'compliance_check', filters = {}) => {
    const response = await fetch(`${API_BASE_URL}/api/legal/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question,
        query_type: queryType,
        ...filters
      })
    });
    
    return await response.json();
  };

  const candidateLogin = async (email, deviceInfo) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/candidate/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': `req-${Date.now()}`,
        'X-Timestamp': new Date().toISOString()
      },
      body: JSON.stringify({ email, device_info: deviceInfo })
    });
    
    return await response.json();
  };

  return {
    token,
    loading,
    login,
    uploadResume,
    getResumes,
    getLegalQuery,
    candidateLogin,
    isAuthenticated: !!token
  };
};
```

---

## 🚀 Getting Started Checklist

1. **✅ Setup Environment Variables**
   ```env
   NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
   ```

2. **✅ Install Dependencies**
   ```bash
   npm install axios  # Optional: for enhanced HTTP client
   ```

3. **✅ Implement Authentication**
   - Create login form
   - Store JWT token securely
   - Handle token refresh

4. **✅ Build Upload Interface**
   - File drop zone
   - Progress indicators
   - Real-time status updates

5. **✅ Create Dashboard**
   - Resume list with pagination
   - Analysis results display
   - Search and filtering

6. **✅ Add Real-time Features**
   - WebSocket connection
   - Progress notifications
   - Live status updates

---

## 📞 Support & Documentation

- **Backend Repository**: [hrtv6backend](https://github.com/SlightlyHappy/hrtv6backend)
- **API Version**: v1.76 (AI-Enhanced Enterprise Analytics)
- **Last Updated**: August 18, 2025
- **Railway Deployment**: Production Ready ✅
- **New Features**: AI-Enhanced Enterprise Metrics, 3-Tier Analysis System

### 🆕 Recent Updates (v1.76)
- ✅ **AI-Enhanced Metrics**: Leadership, innovation, and communication analysis
- ✅ **Enterprise Analytics**: CHRO-level comprehensive candidate assessment  
- ✅ **3-Tier AI System**: HuggingFace → Ollama → Rules fallback
- ✅ **Peer Comparison**: Role-based candidate benchmarking
- ✅ **Market Intelligence**: Skill demand and salary impact analysis

For additional support or feature requests, please check the GitHub repository or contact the development team.
