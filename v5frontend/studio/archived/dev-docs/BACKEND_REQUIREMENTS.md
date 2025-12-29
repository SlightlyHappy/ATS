# Required Backend Endpoints for Secure Candidate System

## 🔐 Authentication Endpoints

### POST /api/auth/candidate/login
**Purpose**: Authenticate candidate with email + device fingerprint
**Request**:
```json
{
  "email": "candidate@example.com",
  "device_info": {
    "fingerprint": "abc123",
    "userAgent": "...",
    "timezone": "UTC",
    "platform": "Win32"
  },
  "timestamp": "2025-08-18T10:00:00Z"
}
```
**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "refresh_abc123...",
  "user": {
    "id": "user_123",
    "email": "candidate@example.com",
    "resume_status": "completed",
    "chat_count": 5,
    "premium_access": false
  }
}
```

### POST /api/auth/refresh
**Purpose**: Refresh expired JWT tokens
**Request**:
```json
{
  "refresh_token": "refresh_abc123..."
}
```

### POST /api/auth/logout
**Purpose**: Invalidate user session
**Headers**: `Authorization: Bearer <token>`

## 📊 Candidate-Specific Endpoints

### GET /api/candidates/profile
**Purpose**: Get candidate profile and progress
**Headers**: `Authorization: Bearer <token>`
**Response**:
```json
{
  "id": "candidate_123",
  "email": "candidate@example.com",
  "resume_status": "completed",
  "resume_analysis": {
    "technical_score": 85,
    "experience_score": 92,
    "overall_score": 88,
    "skills": ["Python", "React", "AWS"],
    "recommendations": ["Learn Docker", "Get AWS certification"]
  },
  "chat_count": 7,
  "premium_access": false,
  "premium_expires_at": null,
  "created_at": "2025-08-18T10:00:00Z",
  "last_login": "2025-08-18T15:30:00Z"
}
```

### PUT /api/candidates/profile
**Purpose**: Update candidate profile (chat count, premium status)
**Headers**: `Authorization: Bearer <token>`

### GET /api/candidates/stats
**Purpose**: Get candidate ranking and stats
**Headers**: `Authorization: Bearer <token>`
**Response**:
```json
{
  "rank_percentile": 87,
  "peer_comparison": {
    "same_industry": 82,
    "same_experience": 90,
    "same_skills": [75, 80, 85, 70]
  },
  "growth_opportunities": [
    "Develop cloud computing skills",
    "Gain project management experience"
  ],
  "trending_skills": ["Python", "React", "AWS", "Docker"]
}
```

## 💬 Enhanced Chat Endpoints

### POST /api/chat/candidate
**Purpose**: AI chat with candidate context
**Headers**: `Authorization: Bearer <token>`
**Request**:
```json
{
  "message": "What skills should I learn next?",
  "conversation_id": "conv_123"
}
```
**Response**:
```json
{
  "response": "Based on your profile...",
  "suggestions": [
    "Tell me about cloud computing",
    "How can I improve my resume?"
  ],
  "context": {
    "user_skills": ["Python", "React"],
    "recommendations": ["Docker", "AWS"]
  }
}
```

## 💳 Payment Endpoints

### POST /api/payments/create-order
**Purpose**: Create Razorpay payment order
**Headers**: `Authorization: Bearer <token>`
**Request**:
```json
{
  "amount": 7000,
  "currency": "INR",
  "plan": "premium_3_days"
}
```

### POST /api/payments/verify
**Purpose**: Verify Razorpay payment
**Headers**: `Authorization: Bearer <token>`
**Request**:
```json
{
  "razorpay_payment_id": "pay_123",
  "razorpay_order_id": "order_123",
  "razorpay_signature": "signature_123"
}
```

## 📧 Email Notification Endpoints

### POST /api/notifications/resume-completed
**Purpose**: Internal endpoint to notify when resume analysis is done
**Headers**: `X-API-Key: <internal-api-key>`
**Request**:
```json
{
  "candidate_email": "candidate@example.com",
  "analysis_results": {...}
}
```

## 🔒 Security Headers Required

### All API Calls Should Include:
- `Authorization: Bearer <jwt-token>`
- `X-Request-ID: <unique-request-id>`
- `X-Client-Version: 1.0.0`
- `X-Timestamp: <request-timestamp>`
- `X-Signature: <hmac-signature>` (for critical operations)

## 🛡️ Security Features Needed

### 1. Rate Limiting
- 100 requests/hour per authenticated user
- 10 requests/minute for chat endpoints
- 5 requests/hour for file uploads

### 2. Request Validation
- JWT token validation on all protected endpoints
- Device fingerprint verification for sensitive operations
- Request signature verification for file uploads and payments

### 3. Audit Logging
- Log all authentication attempts
- Track file uploads and chat interactions
- Monitor premium upgrade transactions

### 4. Abuse Prevention
- Device fingerprint tracking
- IP-based rate limiting
- Suspicious activity detection
