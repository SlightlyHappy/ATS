# Frontend API Reference - HR Consultancy ATS

## Base URL
```
Production: https://your-railway-deployment.railway.app/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication
All API endpoints (except health checks and authentication) require JWT authentication. Include the JWT token in the Authorization header:

```http
Authorization: Bearer your-jwt-token-here
```

### Authentication Endpoints

#### User Registration
**POST** `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "username": "john_doe"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "credits_balance": 10
}
```

#### User Login
**POST** `/auth/login`

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "is_admin": false,
    "credits_balance": 25
  }
}
```

#### Token Refresh
**POST** `/auth/refresh`

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### User Logout
**POST** `/auth/logout`

Logout user and invalidate tokens.

**Authentication:** Required

### User Context
User information is automatically extracted from JWT tokens. No need to pass `user_id` in request bodies - the system determines the user from the authenticated token.

## Rate Limiting
- **Default**: 100 requests per hour
- **Resume upload**: 10 requests per minute
- **Analysis requests**: 5 requests per minute
- **Re-analysis**: 3 requests per minute
- **Authentication**: 10 requests per minute

---

## 1. Resume Endpoints

### Upload Resume
**POST** `/resumes`

Upload and process a resume file for text extraction.

**Content-Type:** `multipart/form-data`

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```javascript
FormData {
  file: File                    // Required: Resume file (PDF, DOC, DOCX, TXT)
  // user_id is automatically extracted from JWT token
  metadata: string              // Optional: JSON string with additional metadata
}
```

**Response (201):**
```json
{
  "message": "Resume uploaded successfully",
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "text_extracted",
  "metadata": {
    "filename": "john_doe_resume.pdf",
    "file_size": 1048576,
    "file_type": "pdf"
  }
}
```

**Possible Statuses:**
- `pending`: File uploaded, processing not started
- `text_extracted`: Text successfully extracted
- `failed`: Processing failed

**Error Responses:**
- `400`: No file provided, invalid file type
- `500`: Upload or processing failed

---

### Get Resume Details
**GET** `/resumes/{resume_id}`

Retrieve detailed information about a specific resume.

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "processed_resume.pdf",
  "original_filename": "john_doe_resume.pdf",
  "file_size": 1048576,
  "file_type": "pdf",
  "processing_status": "text_extracted",
  "batch_upload_id": null,
  "created_at": "2024-12-19T10:30:00Z",
  "processed_at": "2024-12-19T10:30:30Z",
  "analyses_count": 2,
  "structured_data": {
    "contact_info": {
      "name": "John Doe",
      "email": "john.doe@email.com",
      "phone": "+91-9876543210"
    },
    "sections": {
      "experience": "...",
      "education": "...",
      "skills": "..."
    }
  }
}
```

---

### List Resumes
**GET** `/resumes`

Get a paginated list of resumes with optional filtering.

**Query Parameters:**
- `user_id` (string): Filter by user ID
- `status` (string): Filter by processing status
- `page` (number): Page number (default: 1)
- `per_page` (number): Items per page (default: 20, max: 100)

**Response (200):**
```json
{
  "resumes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "processed_resume.pdf",
      "original_filename": "john_doe_resume.pdf",
      "file_size": 1048576,
      "file_type": "pdf",
      "processing_status": "text_extracted",
      "created_at": "2024-12-19T10:30:00Z",
      "analyses_count": 1
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Get Resume Text
**GET** `/resumes/{resume_id}/text`

Retrieve the extracted text content and structured data from a resume.

**Response (200):**
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "John Doe\nSoftware Engineer\n\nExperience:\n- Senior Developer at Tech Corp...",
  "extracted_at": "2024-12-19T10:30:30Z",
  "structured_data": {
    "contact_info": {...},
    "sections": {...}
  }
}
```

---

### Delete Resume
**DELETE** `/resumes/{resume_id}`

Delete a resume and all associated data including analyses.

**Response (200):**
```json
{
  "message": "Resume deleted successfully",
  "file_deleted": true
}
```

---

### Reprocess Resume
**POST** `/resumes/{resume_id}/reprocess`

Re-extract text from a resume file (useful if initial processing failed).

**Response (200):**
```json
{
  "message": "Resume reprocessed successfully",
  "status": "text_extracted"
}
```

---

## 2. Analysis Endpoints

### Trigger Resume Analysis
**POST** `/resumes/{resume_id}/analyze`

Start comprehensive AI analysis of a resume using all available agents.

**Request Body (optional):**
```json
{
  "context": {
    "job_description": "Looking for a senior software engineer...",
    "company_culture": "Fast-paced startup environment",
    "specific_requirements": ["Python", "AWS", "Team Leadership"]
  }
}
```

**Response (201):**
```json
{
  "message": "Analysis completed successfully",
  "analysis_id": "660e8400-e29b-41d4-a716-446655440001",
  "overall_score": 85.5,
  "status": "completed",
  "processing_time": 45.2,
  "summary": {
    "strengths": [
      "Strong technical skills in Python and cloud technologies",
      "Excellent leadership experience with proven track record"
    ],
    "weaknesses": [
      "Limited experience with specific industry regulations",
      "Could benefit from more advanced certifications"
    ],
    "recommendations": [
      "Pursue AWS certification for cloud expertise validation",
      "Gain experience in financial services compliance"
    ]
  }
}
```

---

### Get Analysis Results
**GET** `/analyses/{analysis_id}`

Retrieve complete analysis results with detailed agent breakdowns.

**Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "analysis_type": "full",
  "overall_score": 85.5,
  "scores_breakdown": {
    "technical_skills": {
      "score": 88,
      "confidence": 0.92,
      "weight": 0.3
    },
    "experience": {
      "score": 85,
      "confidence": 0.87,
      "weight": 0.3
    },
    "education": {
      "score": 82,
      "confidence": 0.89,
      "weight": 0.2
    },
    "soft_skills": {
      "score": 86,
      "confidence": 0.84,
      "weight": 0.2
    }
  },
  "strengths": [
    "Strong technical foundation in multiple technologies",
    "Excellent Indian market knowledge and compliance understanding"
  ],
  "weaknesses": [
    "Limited international exposure",
    "Could benefit from broader industry experience"
  ],
  "recommendations": [
    "Seek international assignment or global project exposure",
    "Consider cross-industry experience to broaden perspective"
  ],
  "processing_time": 45.2,
  "status": "completed",
  "created_at": "2024-12-19T11:00:00Z",
  "completed_at": "2024-12-19T11:00:45Z",
  "agent_results": {
    "technical_skills": {
      "industry_classification": {
        "primary_industry": "Information Technology",
        "secondary_industries": ["Finance", "Healthcare"],
        "industry_expertise_level": "Advanced"
      },
      "technical_skills": {
        "programming_languages": [
          {
            "name": "Python",
            "proficiency": "Advanced",
            "years_experience": 5,
            "industry_context": "Data Science",
            "indian_demand": "High"
          }
        ],
        "platforms_systems": [
          {
            "name": "AWS",
            "services": ["EC2", "S3", "Lambda"],
            "certification_level": "Associate"
          }
        ]
      },
      "skill_assessment": {
        "technical_depth_score": 85,
        "technical_breadth_score": 78,
        "indian_market_relevance": 92,
        "skill_currency": 88
      }
    },
    "experience": {
      "career_overview": {
        "total_experience": "8 years 6 months",
        "relevant_experience": "7 years 2 months",
        "primary_industry": "Information Technology",
        "industry_diversity": ["Technology", "Finance", "Healthcare"],
        "career_level": "Senior Professional"
      },
      "work_experience": [
        {
          "company": "Infosys Limited",
          "role": "Senior Software Engineer",
          "duration": "2 years 3 months",
          "company_type": "MNC",
          "industry": "IT Services",
          "achievements": [
            "Reduced system latency by 40% saving ₹2 crore annually",
            "Delivered 3 major projects on time and under budget"
          ],
          "impact_score": 88,
          "leadership_scope": "Team Lead"
        }
      ],
      "leadership_assessment": {
        "people_management": {
          "direct_reports": [3, 5, 8],
          "team_sizes_led": [5, 12, 20],
          "leadership_style": "Collaborative"
        }
      }
    },
    "education": {
      "education_overview": {
        "highest_qualification": "Master of Technology",
        "primary_field": "Computer Science Engineering",
        "education_level_score": 88,
        "institution_prestige_score": 92
      },
      "formal_education": [
        {
          "degree": "Bachelor of Technology",
          "field": "Computer Science",
          "institution": "IIT Bombay",
          "year": 2015,
          "grade": "8.5 CGPA",
          "indian_context": {
            "institution_tier": "Tier 1",
            "entrance_exam": "JEE Advanced"
          }
        }
      ]
    },
    "soft_skills": {
      "soft_skills_overview": {
        "overall_soft_skills_score": 84,
        "cultural_fit_score": 88,
        "interpersonal_effectiveness": 82,
        "leadership_potential": 86
      },
      "communication_skills": {
        "verbal_communication": {
          "clarity_of_expression": 85,
          "public_speaking": "Conference presentations",
          "multilingual_ability": ["Hindi", "English", "Tamil"]
        }
      },
      "indian_workplace_fit": {
        "hierarchical_navigation": {
          "respect_for_authority": "Shows appropriate deference",
          "chain_of_command": "Follows organizational structure",
          "score": 87
        },
        "cultural_adaptation": {
          "festival_awareness": "Respects religious and cultural celebrations",
          "regional_sensitivity": "Understands local customs",
          "score": 90
        }
      }
    }
  }
}
```

---

### List Resume Analyses
**GET** `/resumes/{resume_id}/analyses`

Get all analyses performed on a specific resume.

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `per_page` (number): Items per page (default: 10, max: 50)

**Response (200):**
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "analyses": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "analysis_type": "full",
      "overall_score": 85.5,
      "status": "completed",
      "created_at": "2024-12-19T11:00:00Z",
      "completed_at": "2024-12-19T11:00:45Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 3,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

### Re-analyze Resume
**POST** `/resumes/{resume_id}/reanalyze`

Re-run analysis with optional agent selection for focused analysis.

**Request Body (optional):**
```json
{
  "agent_types": ["technical_skills", "experience"],  // Optional: specific agents only
  "context": {
    "job_description": "Updated job requirements...",
    "focus_areas": ["cloud technologies", "leadership"]
  }
}
```

**Response (201):**
```json
{
  "message": "Re-analysis completed successfully",
  "analysis_id": "770e8400-e29b-41d4-a716-446655440002",
  "overall_score": 87.2,
  "status": "completed",
  "processing_time": 32.1
}
```

---

### Compare Analyses
**GET** `/analyses/{analysis_id1}/compare/{analysis_id2}`

Compare two analyses to show differences and improvements.

**Response (200):**
```json
{
  "comparison_summary": {
    "score_difference": 2.5,
    "improvement_areas": ["technical_skills", "soft_skills"],
    "regression_areas": [],
    "overall_trend": "positive"
  },
  "detailed_comparison": {
    "technical_skills": {
      "analysis_1_score": 85,
      "analysis_2_score": 88,
      "difference": 3,
      "key_changes": ["Added cloud certifications", "Improved framework knowledge"]
    }
  }
}
```

---

### Get Specific Agent Result
**GET** `/analyses/{analysis_id}/agent/{agent_name}`

Get detailed results from a specific agent.

**Agent Names:** `technical_skills`, `experience`, `education`, `soft_skills`

**Response (200):**
```json
{
  "analysis_id": "660e8400-e29b-41d4-a716-446655440001",
  "agent_name": "technical_skills",
  "result": {
    "industry_classification": {...},
    "technical_skills": {...},
    "skill_assessment": {...}
  },
  "agent_score": 88
}
```

---

### List All Analyses
**GET** `/analyses`

Get all analyses with filtering options.

**Query Parameters:**
- `resume_id` (string): Filter by resume ID
- `status` (string): Filter by analysis status
- `min_score` (number): Minimum overall score
- `max_score` (number): Maximum overall score
- `page` (number): Page number
- `per_page` (number): Items per page (max: 100)

---

## 3. Queue Management Endpoints

### Upload Single Resume to Queue
**POST** `/queue/upload`

Upload a resume for queued analysis processing.

**Content-Type:** `multipart/form-data`

**Request Body:**
```javascript
FormData {
  file: File        // Required: Resume file
  // user_id is automatically extracted from JWT token
}
```

**Response (201):**
```json
{
  "message": "Resume uploaded successfully",
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "queue_id": "880e8400-e29b-41d4-a716-446655440003",
  "queue_position": 5,
  "estimated_completion": "2024-12-19T12:30:00Z"
}
```

---

### Upload Batch Resumes
**POST** `/queue/upload/batch`

Upload multiple resumes as a batch (ZIP file or multiple individual files).

**Content-Type:** `multipart/form-data`

**Option 1 - ZIP File:**
```javascript
FormData {
  zip_file: File,         // ZIP containing multiple resume files
  user_id: string,        // Required: User UUID
  batch_name: string      // Optional: Custom batch name
}
```

**Option 2 - Multiple Files:**
```javascript
FormData {
  files: File[],          // Array of resume files
  user_id: string,        // Required: User UUID
  batch_name: string      // Optional: Custom batch name
}
```

**Response (201):**
```json
{
  "message": "Batch of 15 resumes uploaded successfully",
  "batch_id": "990e8400-e29b-41d4-a716-446655440004",
  "batch_name": "Marketing Team Candidates",
  "total_resumes": 15,
  "resume_ids": ["uuid1", "uuid2", "..."],
  "credits_required": 15
}
```

---

### Get Queue Status
**GET** `/queue/status`

Get overall queue status and statistics.

**Query Parameters:**
- `user_id` (string): Filter for specific user (optional)

**Response (200):**
```json
{
  "queue_statistics": {
    "total_pending": 25,
    "total_processing": 3,
    "average_wait_time": "15 minutes",
    "estimated_completion": "2024-12-19T13:00:00Z"
  },
  "user_statistics": {
    "pending_items": 5,
    "processing_items": 1,
    "completed_today": 8
  }
}
```

---

### Get User Queue Items
**GET** `/queue/user/{user_id}/queue`

Get queue items for a specific user.

**Query Parameters:**
- `status` (string): Filter by status (pending, processing, completed, failed)

**Response (200):**
```json
{
  "items": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "resume_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "pending",
      "priority": 1,
      "queue_position": 5,
      "estimated_completion_time": "2024-12-19T12:30:00Z",
      "created_at": "2024-12-19T11:45:00Z"
    }
  ]
}
```

---

### Get User Batches
**GET** `/queue/user/{user_id}/batches`

Get all batch uploads for a user.

**Response (200):**
```json
{
  "batches": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "batch_name": "Marketing Team Candidates",
      "total_resumes": 15,
      "processed_resumes": 12,
      "successful_analyses": 10,
      "failed_analyses": 2,
      "status": "processing",
      "credits_used": 12,
      "created_at": "2024-12-19T10:00:00Z"
    }
  ]
}
```

---

### Get Batch Status
**GET** `/queue/batch/{batch_id}/status`

Get detailed status of a specific batch.

**Query Parameters:**
- `user_id` (string): Required for authorization

**Response (200):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "batch_name": "Marketing Team Candidates",
  "total_resumes": 15,
  "processed_resumes": 12,
  "successful_analyses": 10,
  "failed_analyses": 2,
  "status": "processing",
  "credits_used": 12,
  "created_at": "2024-12-19T10:00:00Z",
  "completed_at": null
}
```

---

### Cancel Queue Item
**POST** `/queue/cancel/{queue_id}`

Cancel a pending queue item.

**Request Body:**
```json
{
  "user_id": "440e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200):**
```json
{
  "message": "Queue item cancelled successfully"
}
```

---

## 4. Credit Management Endpoints

### Get User Credits
**GET** `/queue/user/{user_id}/credits`

Get user's credit balance and transaction history.

**Response (200):**
```json
{
  "user_id": "440e8400-e29b-41d4-a716-446655440000",
  "credits_balance": 25,
  "total_credits_purchased": 100,
  "total_credits_used": 75,
  "is_admin": false,
  "recent_transactions": [
    {
      "id": "trans_001",
      "transaction_type": "debit",
      "amount": 1,
      "description": "Resume analysis",
      "balance_after": 25,
      "created_at": "2024-12-19T11:30:00Z"
    },
    {
      "id": "trans_002",
      "transaction_type": "credit",
      "amount": 50,
      "description": "Credit purchase",
      "balance_after": 26,
      "created_at": "2024-12-19T09:00:00Z"
    }
  ]
}
```

---

### Add User Credits
**POST** `/queue/user/{user_id}/credits/add`

Add credits to a user's account (admin only or payment processing).

**Request Body:**
```json
{
  "amount": 50,
  "description": "Credit purchase via payment gateway"
}
```

**Response (200):**
```json
{
  "message": "Added 50 credits successfully",
  "new_balance": 75
}
```

---

## 5. Admin Management Endpoints

### Get All Users
**GET** `/admin/users`

Get paginated list of all users with filtering and search (admin only).

**Authentication:** Required (Admin)

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `per_page` (number): Items per page (default: 20, max: 100)
- `search` (string): Search in email, username, or name
- `is_admin` (boolean): Filter by admin status
- `has_credits` (boolean): Filter by credit availability
- `created_after` (string): Filter by creation date (ISO format)
- `created_before` (string): Filter by creation date (ISO format)

**Response (200):**
```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "john_doe",
      "is_admin": false,
      "is_active": true,
      "credits_balance": 25,
      "total_resumes": 5,
      "total_analyses": 8,
      "created_at": "2024-12-19T10:00:00Z",
      "last_login": "2024-12-19T15:30:00Z",
      "admin_profile": null
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Get User Details
**GET** `/admin/users/{user_id}`

Get detailed information for a specific user (admin only).

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "john_doe",
  "is_admin": false,
  "is_active": true,
  "credits_balance": 25,
  "total_resumes": 5,
  "total_analyses": 8,
  "created_at": "2024-12-19T10:00:00Z",
  "last_login": "2024-12-19T15:30:00Z",
  "recent_activity": [
    {
      "action": "resume_upload",
      "timestamp": "2024-12-19T15:30:00Z",
      "details": "Uploaded resume: senior_dev.pdf"
    }
  ],
  "credit_transactions": [
    {
      "id": "trans_001",
      "transaction_type": "debit",
      "amount": 1,
      "description": "Resume analysis",
      "created_at": "2024-12-19T15:00:00Z"
    }
  ],
  "admin_profile": {
    "role": "Super Admin",
    "access_level": 100,
    "is_active": true,
    "login_count": 45,
    "actions_performed": 120,
    "failed_login_attempts": 0,
    "last_login_ip": "192.168.1.100",
    "created_at": "2024-12-01T10:00:00Z"
  }
}
```

---

### Modify User Credits
**POST** `/admin/users/{user_id}/credits`

Add or remove credits from a user's account (admin only).

**Request Body:**
```json
{
  "amount": 50,
  "operation": "add",
  "description": "Credit bonus for feedback"
}
```

**Response (200):**
```json
{
  "message": "Added 50 credits successfully",
  "previous_balance": 25,
  "new_balance": 75,
  "transaction_id": "trans_002"
}
```

---

### Toggle Admin Status
**POST** `/admin/users/{user_id}/admin-status`

Grant or revoke admin privileges for a user.

**Request Body:**
```json
{
  "make_admin": true,
  "role": "Admin",
  "access_level": 50
}
```

**Response (200):**
```json
{
  "message": "User granted admin privileges successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_admin": true
}
```

---

### Get System Configuration
**GET** `/admin/system/config`

Get all system configuration settings (admin only).

**Response (200):**
```json
{
  "configurations": [
    {
      "id": "config_001",
      "key": "max_concurrent_analyses",
      "value": 3,
      "category": "performance",
      "description": "Maximum number of concurrent analysis processes",
      "is_sensitive": false,
      "requires_restart": true,
      "created_at": "2024-12-01T10:00:00Z"
    }
  ]
}
```

---

### Update System Configuration
**POST** `/admin/system/config`

Update or create system configuration setting (admin only).

**Request Body:**
```json
{
  "key": "max_file_size_mb",
  "value": 100,
  "category": "upload",
  "description": "Maximum file size for uploads in MB",
  "is_sensitive": false,
  "requires_restart": false
}
```

---

### Get Admin Dashboard Analytics
**GET** `/admin/analytics/dashboard`

Get comprehensive analytics for admin dashboard.

**Response (200):**
```json
{
  "summary": {
    "total_users": 150,
    "new_users": 12,
    "active_users": 89,
    "total_resumes": 450,
    "completed_analyses": 380,
    "pending_analyses": 15,
    "total_credits_used": 2500,
    "avg_credits_per_user": 16.7
  },
  "daily_stats": [
    {
      "date": "2024-12-19",
      "new_users": 3,
      "uploads": 15,
      "analyses": 18,
      "credits_used": 25
    }
  ],
  "queue_health": {
    "status": "healthy",
    "average_wait_time": 45,
    "max_queue_length": 25,
    "processing_rate": 2.5
  },
  "generated_at": "2024-12-19T16:00:00Z"
}
```

---

### Get Audit Log
**GET** `/admin/audit-log`

Get audit trail of admin actions.

**Query Parameters:**
- `page` (number): Page number
- `per_page` (number): Items per page
- `action_type` (string): Filter by action type
- `date_from` (string): Start date filter
- `date_to` (string): End date filter

**Response (200):**
```json
{
  "actions": [
    {
      "id": "action_001",
      "admin_user_id": "admin_001",
      "action_type": "user_credit_modification",
      "description": "Added 50 credits to user john_doe",
      "target_resource": "user:550e8400-e29b-41d4-a716-446655440000",
      "metadata": {
        "previous_balance": 25,
        "amount_added": 50,
        "new_balance": 75
      },
      "ip_address": "192.168.1.100",
      "created_at": "2024-12-19T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Get Admin Notifications
**GET** `/admin/notifications`

Get admin notifications and alerts.

**Response (200):**
```json
{
  "notifications": [
    {
      "id": "notif_001",
      "title": "High Queue Volume",
      "message": "Queue has 25+ pending items, consider scaling",
      "type": "warning",
      "is_read": false,
      "created_at": "2024-12-19T15:00:00Z"
    }
  ],
  "unread_count": 3
}
```

---

### Mark Notification Read
**POST** `/admin/notifications/{notification_id}/read`

Mark a specific notification as read.

---

## 6. WebSocket & Real-time Endpoints

### Get System Statistics
**GET** `/websocket/stats`

Get real-time system statistics for dashboards.

**Authentication:** Optional (public stats)

**Response (200):**
```json
{
  "queue": {
    "pending": 15,
    "processing": 3,
    "completed_today": 45,
    "failed_today": 2
  },
  "users": {
    "total_users": 150,
    "active_today": 25,
    "admin_users": 5
  },
  "processing": {
    "total_resumes": 450,
    "total_analyses": 380,
    "analyses_today": 45,
    "avg_processing_time": 65.5
  },
  "websocket": {
    "connected_users": 12,
    "total_sessions": 15
  },
  "timestamp": "2024-12-19T16:00:00Z"
}
```

---

### Get Live Queue Data
**GET** `/websocket/queue/live`

Get live queue data for real-time dashboard updates.

**Response (200):**
```json
{
  "queue_items": [
    {
      "id": "queue_001",
      "resume_id": "resume_001",
      "user_id": "user_001",
      "status": "processing",
      "priority": 1,
      "created_at": "2024-12-19T15:45:00Z",
      "estimated_completion": "2024-12-19T16:00:00Z"
    }
  ],
  "statistics": {
    "average_wait_time": 180,
    "queue_length": 15,
    "processing_rate": 2.5
  }
}
```

---

### Get Hourly Analytics
**GET** `/websocket/analytics/hourly`

Get hourly analytics for the last 24 hours.

**Response (200):**
```json
{
  "hourly_data": [
    {
      "hour": "2024-12-19T15:00:00Z",
      "uploads": 5,
      "analyses_completed": 8,
      "new_users": 2,
      "credits_used": 12
    }
  ],
  "summary": {
    "total_uploads": 120,
    "total_analyses": 95,
    "peak_hour": "2024-12-19T14:00:00Z",
    "peak_uploads": 15
  }
}
```

---

### Send Test Broadcast
**POST** `/websocket/broadcast/test`

Send test broadcast message to connected clients (admin only).

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "message": "System maintenance in 10 minutes",
  "type": "maintenance",
  "level": "warning"
}
```

**Response (200):**
```json
{
  "message": "Broadcast sent successfully",
  "recipients": 25,
  "timestamp": "2024-12-19T16:00:00Z"
}
```

---

### Refresh Dashboard
**POST** `/websocket/dashboard/refresh`

Trigger dashboard data refresh for all connected admin users.

**Authentication:** Required (Admin)

---

## 7. Health Check Endpoints

### Simple Health Check
**GET** `/health/simple`

Basic health check for load balancers and monitoring.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-19T12:00:00Z",
  "message": "Service is running and database is accessible"
}
```

---

### Comprehensive Health Check
**GET** `/health`

Detailed health check including all services.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-19T12:00:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "ollama": {
      "status": "healthy",
      "message": "Ollama service accessible",
      "available_models": ["qwen2.5:7b"],
      "service_url": "http://ollama:11434"
    },
    "file_storage": {
      "status": "healthy",
      "message": "Upload directory accessible",
      "path": "/app/uploads"
    }
  }
}
```

---

### Database Health
**GET** `/health/database`

Database-specific health check.

---

### Ollama Service Health
**GET** `/health/ollama`

AI service health check with model availability.

---

### Agent Health
**GET** `/health/agents`

Test all AI agents functionality.

**Response (200):**
```json
{
  "status": "healthy",
  "healthy_agents": 4,
  "total_agents": 4,
  "agent_results": {
    "technical_skills": {
      "status": "healthy",
      "score": 85,
      "confidence": 0.92,
      "processing_time": 12.5
    },
    "experience": {
      "status": "healthy",
      "score": 82,
      "confidence": 0.87,
      "processing_time": 15.2
    },
    "education": {
      "status": "healthy",
      "score": 88,
      "confidence": 0.89,
      "processing_time": 10.1
    },
    "soft_skills": {
      "status": "healthy",
      "score": 84,
      "confidence": 0.84,
      "processing_time": 13.8
    }
  }
}
```

---

## Error Handling

### Error Response Format

All endpoints return errors in this standardized format:

```json
{
  "error": "Brief error description",
  "details": "Detailed error message (when available)",
  "code": "ERROR_CODE",
  "timestamp": "2024-12-19T12:00:00Z",
  "request_id": "req_12345"
}
```

### Authentication Errors

**401 Unauthorized:**
```json
{
  "error": "Authentication required",
  "details": "Valid JWT token required for this endpoint",
  "code": "AUTH_REQUIRED"
}
```

**403 Forbidden:**
```json
{
  "error": "Insufficient privileges",
  "details": "Admin access required for this operation",
  "code": "ADMIN_REQUIRED"
}
```

### Validation Errors

**400 Bad Request:**
```json
{
  "error": "Validation failed",
  "details": "Invalid request data",
  "code": "VALIDATION_ERROR",
  "validation_errors": [
    {
      "field": "email",
      "message": "Valid email address required"
    }
  ]
}
```

### Credit Errors

**402 Payment Required:**
```json
{
  "error": "Insufficient credits",
  "details": "1 credit required, current balance: 0",
  "code": "INSUFFICIENT_CREDITS",
  "required_credits": 1,
  "current_balance": 0
}
```

### Rate Limiting Errors

**429 Too Many Requests:**
```json
{
  "error": "Rate limit exceeded",
  "details": "Maximum 5 requests per minute exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

### Common HTTP Status Codes

- **200**: Success - Request completed successfully
- **201**: Created - Resource created successfully
- **400**: Bad Request - Invalid parameters, missing data, or validation errors
- **401**: Unauthorized - Authentication required or invalid token
- **402**: Payment Required - Insufficient credits for operation
- **403**: Forbidden - Admin privileges required
- **404**: Resource not found
- **429**: Rate limit exceeded
- **500**: Internal server error
- **503**: Service unavailable (health check failures or maintenance)

### Response Headers

All API responses include standard headers:
```http
Content-Type: application/json
X-Request-ID: req_12345
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```

### Security Headers

Production responses include security headers:
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## File Upload Requirements

### Supported File Types
- **PDF**: .pdf
- **Microsoft Word**: .doc, .docx
- **Text**: .txt

### File Size Limits
- Individual files: 50MB maximum
- ZIP archives: 50MB maximum

### File Naming
- Files are automatically renamed with UUID prefixes to avoid conflicts
- Original filenames are preserved in metadata

---

## Agent Analysis Structure

### Analysis Types
- **full**: Complete analysis with all 4 agents
- **technical**: Technical skills only
- **experience**: Experience analysis only
- **education**: Education analysis only
- **soft_skills**: Soft skills analysis only

### Agent-Specific Data Structures

#### Technical Skills Agent
```json
{
  "industry_classification": {
    "primary_industry": "Information Technology",
    "secondary_industries": ["Finance", "Healthcare"],
    "industry_expertise_level": "Advanced"
  },
  "technical_skills": {
    "programming_languages": [...],
    "software_tools": [...],
    "platforms_systems": [...],
    "cloud_platforms": [...]
  },
  "indian_market_skills": {
    "regulatory_knowledge": [...],
    "regional_languages": [...],
    "local_software": [...]
  },
  "skill_assessment": {
    "technical_depth_score": 85,
    "technical_breadth_score": 78,
    "indian_market_relevance": 92,
    "skill_currency": 88
  }
}
```

#### Experience Agent
```json
{
  "career_overview": {
    "total_experience": "8 years 6 months",
    "primary_industry": "Information Technology",
    "career_level": "Senior Professional"
  },
  "work_experience": [...],
  "leadership_assessment": {
    "people_management": {...},
    "project_leadership": {...}
  },
  "indian_market_fit": {
    "cultural_adaptability": {...},
    "market_understanding": {...}
  }
}
```

#### Education Agent
```json
{
  "education_overview": {
    "highest_qualification": "Master of Technology",
    "primary_field": "Computer Science Engineering",
    "education_level_score": 88
  },
  "formal_education": [...],
  "certifications": [...],
  "continuous_learning": {...}
}
```

#### Soft Skills Agent
```json
{
  "soft_skills_overview": {
    "overall_soft_skills_score": 84,
    "cultural_fit_score": 88,
    "interpersonal_effectiveness": 82
  },
  "communication_skills": {...},
  "leadership_skills": {...},
  "indian_workplace_fit": {...}
}
```

---

## Integration Notes

### CORS Configuration
The API supports requests from:
- `http://localhost:3000` (development - React/Next.js)
- `https://*.vercel.app` (Vercel deployments)
- `https://*.railway.app` (Railway deployments)
- Custom frontend URLs via `FRONTEND_URL` environment variable

### WebSocket Integration
Real-time features are available via WebSocket connection:

```javascript
// Connect to WebSocket
const socket = io('https://your-railway-app.railway.app');

// Authenticate
socket.emit('authenticate', {
    user_id: 'your-user-id',
    user_type: 'user' // or 'admin'
});

// Listen for real-time updates
socket.on('queue_item_update', (data) => {
    console.log('Queue update:', data);
});

socket.on('analysis_completed', (data) => {
    console.log('Analysis complete:', data);
});
```

### Frontend Framework Integration

#### React/Next.js Example
```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                try {
                    const response = await axios.post('/auth/refresh', {
                        refresh_token: refreshToken
                    });
                    localStorage.setItem('access_token', response.data.access_token);
                    return api.request(error.config);
                } catch (refreshError) {
                    // Redirect to login
                    window.location.href = '/login';
                }
            }
        }
        return Promise.reject(error);
    }
);
```

### Content Types
- **File uploads**: `multipart/form-data`
- **JSON requests**: `application/json`
- **Responses**: `application/json`

### Pagination
All list endpoints support pagination with consistent structure:
```json
{
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### Timestamps
- All timestamps are in ISO 8601 format: `2024-12-19T12:00:00Z`
- Times are in UTC

### UUID Format
All IDs use UUID v4 format: `550e8400-e29b-41d4-a716-446655440000`

---

## Development Guidelines

### Environment Setup
```bash
# Development environment
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=http://localhost:8000

# Production environment
REACT_APP_API_URL=https://your-railway-app.railway.app/api/v1
REACT_APP_WS_URL=https://your-railway-app.railway.app
```

### Best Practices

#### Error Handling
Always implement proper error handling for API calls:

```javascript
try {
    const response = await api.post('/resumes', formData);
    // Handle success
} catch (error) {
    if (error.response?.status === 402) {
        // Handle insufficient credits
        showCreditPurchaseModal();
    } else if (error.response?.status === 429) {
        // Handle rate limiting
        showRateLimitMessage(error.response.data.retry_after);
    } else {
        // Handle other errors
        showErrorMessage(error.response?.data?.error || 'An error occurred');
    }
}
```

#### File Upload Progress
For large file uploads, implement progress tracking:

```javascript
const uploadResume = async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post('/resumes', formData, {
        onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percentCompleted);
        }
    });
};
```

#### Real-time Updates
Integrate WebSocket for real-time features:

```javascript
useEffect(() => {
    const socket = io(process.env.REACT_APP_WS_URL);
    
    socket.emit('authenticate', {
        user_id: user.id,
        user_type: user.is_admin ? 'admin' : 'user'
    });
    
    socket.on('queue_item_update', (data) => {
        updateQueueStatus(data);
    });
    
    socket.on('analysis_completed', (data) => {
        showNotification('Analysis Complete!');
        refreshAnalyses();
    });
    
    return () => socket.disconnect();
}, [user]);
```

### Testing

#### API Testing
Use the health check endpoints to verify connectivity:

```javascript
// Test API connectivity
const testConnection = async () => {
    try {
        const response = await fetch('/api/v1/health/simple');
        const data = await response.json();
        console.log('API Status:', data.status);
    } catch (error) {
        console.error('API Connection Failed:', error);
    }
};
```

#### Authentication Testing
```javascript
// Test authentication flow
const testAuth = async () => {
    try {
        const loginResponse = await api.post('/auth/login', {
            email: 'test@example.com',
            password: 'password'
        });
        
        const token = loginResponse.data.access_token;
        
        // Test authenticated endpoint
        const userResponse = await api.get('/admin/users', {
            headers: { Authorization: `Bearer ${token}` }
        });
        
        console.log('Auth test passed');
    } catch (error) {
        console.error('Auth test failed:', error);
    }
};
```

---

## Support & Resources

### Documentation
- **API Reference**: This document
- **WebSocket Guide**: `/docs/WebSocket_Implementation_Guide.md`
- **Project Roadmap**: `/docs/PROJECT_ROADMAP.md`

### Health Monitoring
Monitor API health using the health check endpoints:
- **Simple**: `/api/v1/health/simple`
- **Detailed**: `/api/v1/health`
- **System Stats**: `/api/v1/websocket/stats`

### Contact
For technical support or API questions, refer to the system administrator or check the health endpoints for current system status.

---

*This API reference provides comprehensive information for frontend developers to integrate with the HR Consultancy ATS backend. The API is designed to support both traditional web applications and modern frontend frameworks like React and Next.js.*
