# 🎨 Frontend Engineer Guide and Roadmap

## 📖 Introduction
This document is a comprehensive guide for frontend engineers building the UI for the **HR Consultancy ATS** platform - a production-ready, AI-powered resume analysis system. It covers all backend endpoints, expected request/response formats, UI page designs, component suggestions, and a detailed project roadmap with checklists based on the complete backend implementation.

**Backend Status**: ✅ **100% Complete** - 85+ API endpoints across 13 functional modules with full authentication, real-time WebSocket communication, comprehensive credit system analytics, and Railway cloud deployment ready.

**🌐 Live Production URL**: https://determined-harmony-production.up.railway.app

**🔄 Recent Updates** (August 2025):
- ✅ Authentication middleware fully operational with proper error handling
- ✅ Credit transaction tracking with comprehensive admin analytics  
- ✅ WebSocket service compatibility fixes for flask-socketio versions
- ✅ Token refresh mechanism for seamless user experience
- ✅ All admin dashboard endpoints including credit analytics and monitoring alerts
- ✅ Database relationship fixes for admin profile management

---

## 🎯 Goals and Scope
1. **Landing Page**: Marketing landing, feature highlights, links to login/signup
2. **Authentication Flow**: JWT-based login, signup, password reset, role-based routes (user/admin)
3. **Main Application Dashboard**: 
   - Resume upload (single/batch) with real-time queue tracking via `/api/v1/queue/upload`
   - AI analysis results with 4-agent scoring system via `/api/v1/analyses`
   - Candidate pipeline management (Kanban/Table views) via `/api/v1/pipeline/candidates`
   - HR communication templates with AI generation via `/api/v1/communication/templates`
   - Legal consultation with RAG-based Q&A via `/api/legal/query`
   - Sales intelligence with lead scoring & ROI calculator via `/api/v1/sales`
   - Real-time monitoring & analytics dashboards via `/api/v1/monitoring`
4. **Admin Panel**: User management, credit transaction analytics, system configuration, comprehensive monitoring via `/api/v1/admin`
5. **Responsive Design**: Desktop and mobile-first layouts with accessibility
6. **Real-time Features**: WebSocket-powered notifications and live updates via `/api/v1/websocket`

---

## 🏗️ Technology Stack Recommendations
**Frontend Framework**:
- **React 18+ with TypeScript** (preferred for enterprise features)
- **Next.js 14+** (for SSR, API routes, and SEO optimization)
- Alternative: Vue 3 + Nuxt 3 with TypeScript

**State Management**:
- **Redux Toolkit** or **Zustand** for complex state
- **TanStack Query** for server state management
- Context API for simple global state

**UI & Styling**:
- **Tailwind CSS** + **Headless UI** (highly recommended)
- Alternative: **Material-UI v5** or **Ant Design v5**
- **Framer Motion** for animations

**Real-time & HTTP**:
- **Socket.io-client** for WebSocket connections to `wss://determined-harmony-production.up.railway.app`
- **Axios** with interceptors for HTTP requests to `https://determined-harmony-production.up.railway.app`
- **React Hook Form** for form management with validation

**Charts & Data Visualization**:
- **Recharts** (React-specific, recommended)
- **Chart.js** with react-chartjs-2
- **D3.js** for custom visualizations

**Development Tools**:
- **Vite** for blazing fast development
- **ESLint** + **Prettier** for code quality
- **Storybook** for component development

---

## 🔐 Authentication & Authorization

### Endpoints

| Action            | Method | URL                       | Request Body                                 | Response                                  |
|-------------------|--------|---------------------------|----------------------------------------------|-------------------------------------------|
| Sign Up           | POST   | `/api/v1/auth/register`   | `{ email, password, username?, first_name?, last_name? }` | `{ message, user_id, credits_balance }`   |
| Login             | POST   | `/api/v1/auth/login`      | `{ email, password }`                        | `{ access_token, refresh_token, user }`   |
| Refresh Token     | POST   | `/api/v1/auth/refresh`    | `{ refresh_token }`                          | `{ access_token }`                        |
| Logout            | POST   | `/api/v1/auth/logout`     | `{ }` with Authorization header              | `{ message }`                             |
| Get Current User  | GET    | `/api/v1/auth/me`         | Authorization: Bearer `token`                | `{ id, email, username, role, credits }`  |
| Forgot Password   | POST   | `/api/v1/auth/forgot-password` | `{ email }`                             | `{ message }`                             |
| Reset Password    | POST   | `/api/v1/auth/reset-password`  | `{ token, new_password }`               | `{ message }`                             |

### Authentication Response Structure
```typescript
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer";
  expires_in: number; // 86400 seconds (24 hours)
  user: {
    id: string;
    email: string;
    username: string;
    first_name?: string;
    last_name?: string;
    is_admin: boolean;
    credits_balance: number;
    created_at: string;
    last_login?: string;
    admin_profile?: {
      role: string;
      access_level: string;
      permissions: string[];
    };
  };
}
```

### Frontend Implementation Notes
- **Base URL**: Use `https://determined-harmony-production.up.railway.app` for production API calls
- **WebSocket URL**: Use `wss://determined-harmony-production.up.railway.app` for real-time connections
- **JWT Storage**: Use secure, HttpOnly cookies for production or sessionStorage for development
- **Token Refresh**: Implement automatic token refresh using axios interceptors (tokens expire in 24 hours)
- **Role-based Routing**: Protect admin routes with `is_admin` check from user object
- **Credit Balance**: Display user credits prominently, check before paid operations (resume analysis costs 1 credit, legal queries cost 2 credits)
- **Session Management**: Handle 401 responses with automatic logout/redirect to login page
- **Error Handling**: Implement global error boundaries and user-friendly error messages
- **Loading States**: Show loading indicators for all async operations
- **Real-time Updates**: Use WebSocket events for immediate UI updates (queue positions, analysis progress, system alerts)

### Security Features Implemented
- ✅ JWT token expiration (24 hours) with refresh tokens (30 days)
- ✅ Automatic token refresh with seamless user experience
- ✅ Failed login attempt tracking and rate limiting
- ✅ Password hashing with bcrypt
- ✅ User ownership verification for all data operations
- ✅ Admin privilege checking for sensitive operations
- ✅ Authentication middleware with proper error state management
- ✅ WebSocket authentication with token validation

---

## 🗂️ API Endpoints Overview

Below is a categorized list of backend endpoints with sample requests and responses.

### 1. Resume Upload & Analysis

**Upload Single Resume**
- **POST** `/api/v1/queue/upload`
- **Form Data**: `file` (PDF/DOC/DOCX), optional `filename`
- **Auth Required**: Yes
- **Credits Required**: 1
- **Response**: `{ message, resume_id, queue_id, queue_position, estimated_completion }`

**Upload Batch (ZIP)**
- **POST** `/api/v1/queue/upload/batch`
- **Form Data**: `file` (ZIP containing resumes)
- **Auth Required**: Yes
- **Credits Required**: Variable (based on file count)
- **Response**: `{ message, batch_id, total_files, estimated_completion }`

**Get Queue Status**
- **GET** `/api/v1/queue/status`
- **Response**: `{ total_in_queue, user_in_queue, estimated_wait_time }`

**Get Queue Stats**
- **GET** `/api/v1/queue/stats`
- **Response**: `{ processed_today, average_processing_time, queue_health }`

**Get Analysis Result**
- **GET** `/api/v1/resumes/{resumeId}/analyses`
- **Response**: `[{ analysis_id, status, overall_score, agent_results: {...}, created_at }]`

**Get Specific Analysis**
- **GET** `/api/v1/analyses/{analysisId}`
- **Response**: `{ analysis_id, resume_id, overall_score, agent_results, detailed_feedback }`

**Trigger Re-Analysis**
- **POST** `/api/v1/resumes/{resumeId}/reanalyze`
- **Credits Required**: 1
- **Response**: `{ success, analysis_id }`

**Get All Analyses (Admin)**
- **GET** `/api/v1/analyses`
- **Query**: `?page=1&per_page=20&status=completed`
- **Response**: `{ analyses: [...], pagination: {...} }`

**Compare Analyses**
- **GET** `/api/v1/analyses/{analysisId1}/compare/{analysisId2}`
- **Response**: `{ comparison, score_differences, recommendations }`

**Get Agent-Specific Results**
- **GET** `/api/v1/analyses/{analysisId}/agent/{agentName}`
- **Response**: `{ agent_name, score, detailed_analysis, recommendations }`

**List User Resumes**
- **GET** `/api/v1/resumes`
- **Query**: `?page=1&per_page=20&status=completed`
- **Response**: `{ resumes: [...], pagination: {...} }`

**Get Resume Details**
- **GET** `/api/v1/resumes/{resumeId}`
- **Response**: `{ id, filename, file_size, upload_date, processing_status, analyses_count }`

**Get Resume Text**
- **GET** `/api/v1/resumes/{resumeId}/text`
- **Response**: `{ resume_id, extracted_text, metadata }`

**Delete Resume**
- **DELETE** `/api/v1/resumes/{resumeId}`
- **Response**: `{ success, message }`

### 2. Candidate Pipeline Management

| Method | Endpoint                                    | Description                                      |
|--------|---------------------------------------------|--------------------------------------------------|
| GET    | `/api/v1/pipeline/candidates`               | List candidates (query: `page, per_page, stage, status, priority, search, sort_by`) |
| POST   | `/api/v1/pipeline/candidates`               | Create candidate: `{ first_name, last_name, email, position_title, resume_id?, ... }`|
| GET    | `/api/v1/pipeline/candidates/{id}`          | Get details with activity timeline               |
| PUT    | `/api/v1/pipeline/candidates/{id}`          | Update candidate info                            |
| DELETE | `/api/v1/pipeline/candidates/{id}`          | Remove candidate from pipeline                   |
| PUT    | `/api/v1/pipeline/candidates/{id}/stage`    | Move to new stage: `{ stage: 'phone_interview', notes? }` |
| POST   | `/api/v1/pipeline/candidates/{id}/notes`    | Add note: `{ content, note_type? }`              |
| GET    | `/api/v1/pipeline/candidates/{id}/timeline` | Get activity timeline                            |
| POST   | `/api/v1/pipeline/candidates/{id}/score`    | Update scoring: `{ overall_score, technical_score?, ... }` |
| GET    | `/api/v1/pipeline/analytics/overview`       | Pipeline overview analytics                      |
| GET    | `/api/v1/pipeline/analytics/conversion`     | Stage conversion analytics                       |
| GET    | `/api/v1/pipeline/analytics/performance`    | Hiring performance metrics                       |

### 3. HR Communication Templates

| Method | Endpoint                                                | Description                                  |
|--------|---------------------------------------------------------|----------------------------------------------|
| GET    | `/api/v1/communication/templates?category=&status=`    | List templates with filtering               |
| GET    | `/api/v1/communication/templates/{id}`                 | Get template details                        |
| POST   | `/api/v1/communication/templates/generate`             | Generate new: `{ category, candidate_id?, context?, compliance_level }`|
| POST   | `/api/v1/communication/templates/{id}/personalize`     | Personalize: `{ candidate_id, context }`     |
| PUT    | `/api/v1/communication/templates/{id}`                 | Update: `{ subject?, body?, status? }`        |
| DELETE | `/api/v1/communication/templates/{id}`                 | Archive template                             |
| GET    | `/api/v1/communication/categories`                     | Get available categories                     |
| GET    | `/api/v1/communication/compliance-rules`               | Get compliance guidelines                    |
| POST   | `/api/v1/communication/templates/{id}/validate`        | Validate compliance                          |

### 4. Legal RAG Consultation

| Method | Endpoint                           | Body                                  | Response                                     |
|--------|------------------------------------|---------------------------------------|----------------------------------------------|
| POST   | `/api/legal/query`                 | `{ query: 'How to comply...', max_sources?: 5, include_examples?: true }` | `{ answer, sources: [{ doc_title, chunk_text, similarity, page_number? }], query_id, confidence_score }` |
| POST   | `/api/legal/feedback`              | `{ query_id, rating: 1-5, feedback?: 'text' }`| `{ success, message }`                      |
| GET    | `/api/legal/history`               | Query: `?page=1&per_page=20`         | List past consultations with pagination     |
| GET    | `/api/legal/query/{queryId}`       | —                                     | Get specific query details                   |
| GET    | `/api/legal/documents`             | —                                     | List available legal documents              |
| GET    | `/api/legal/search`                | Query: `?q=search_term&limit=10`     | Search legal documents                       |

### 5. Sales Intelligence & ROI

| Method | Endpoint                                 | Description                                      |
|--------|------------------------------------------|--------------------------------------------------|
| GET    | `/api/v1/sales/leads?page=&score_min=&status=` | List leads with filtering                       |
| GET    | `/api/v1/sales/leads/{id}`               | Get lead details                                |
| POST   | `/api/v1/sales/leads/{id}/score/update` | Update lead score: `{ new_score, factors }`     |
| POST   | `/api/v1/sales/leads/{id}/qualify`      | Qualify lead: `{ qualification_notes }`         |
| GET    | `/api/v1/sales/leads/hot`               | Get high-priority leads                         |
| POST   | `/api/v1/sales/leads/score/batch-update`| Batch update scores                             |
| POST   | `/api/v1/sales/roi/calculate`           | `{ monthly_analyses, hourly_rate, time_saved_per_analysis?, platform_cost_per_analysis? }` | `{ roi_percentage, net_savings, payback_period_days, annual_savings }` |
| GET    | `/api/v1/sales/analytics/overview`      | Sales metrics summary                           |
| GET    | `/api/v1/sales/analytics/conversion`    | Lead conversion analytics                       |

### 6. Monitoring & Admin

#### Credit System Endpoints (Admin)
- **GET** `/api/v1/admin/credit-transactions` — List credit transactions
  - **Query Parameters**: `page`, `per_page`, `user_id`, `transaction_type`, `start_date`, `end_date`
  - **Response**: `{ transactions: [...], pagination: {...}, summary: {...} }`
- **GET** `/api/v1/admin/analytics/credits` — Credit system analytics
  - **Response**: `{ summary: {...}, daily_trends: [...], user_distribution: {...}, top_users: [...] }`

#### Monitoring Endpoints (Public & Admin)
- **GET** `/api/v1/monitoring/status` — Basic system status (public)
- **GET** `/api/v1/monitoring/metrics` — Basic system metrics (public)
- **GET** `/api/v1/monitoring/health` — Monitoring system health (public)
- **GET** `/api/v1/monitoring/dashboard` — Comprehensive dashboard (admin)
- **GET** `/api/v1/monitoring/performance/metrics` — Performance metrics (admin)
- **GET** `/api/v1/monitoring/performance/trends/{metric_type}` — Performance trends (admin)
- **GET** `/api/v1/monitoring/usage/insights` — User behavior insights (admin)
- **GET** `/api/v1/monitoring/usage/activity` — Recent user activity (admin)
- **GET** `/api/v1/monitoring/errors/dashboard` — Error tracking dashboard (admin)
- **GET** `/api/v1/monitoring/errors/list` — Paginated error list (admin)
- **GET** `/api/v1/monitoring/alerts` — System alerts (admin)
- **POST** `/api/v1/monitoring/alerts/{id}/acknowledge` — Acknowledge alert (admin)

#### Admin Panel Endpoints
- **GET** `/api/v1/admin/health` — Admin system health check
- **GET** `/api/v1/admin/users` — List all users with pagination
- **GET** `/api/v1/admin/users/{id}` — Get user details
- **POST** `/api/v1/admin/users/{id}/credits` — Adjust user credits
- **POST** `/api/v1/admin/users/{id}/admin-status` — Toggle admin status
- **GET** `/api/v1/admin/credit-transactions` — List all credit transactions with pagination
- **GET** `/api/v1/admin/analytics/credits` — Credit system analytics and insights
- **GET** `/api/v1/admin/system/config` — Get system configuration
- **POST** `/api/v1/admin/system/config` — Update system settings
- **GET** `/api/v1/admin/analytics/dashboard` — Admin analytics dashboard
- **GET** `/api/v1/admin/audit-log` — System audit logs
- **GET** `/api/v1/admin/notifications` — Admin notifications
- **GET** `/api/v1/admin/hr-templates/diagnose` — Diagnose HR template issues
- **POST** `/api/v1/admin/hr-templates/auto-fix` — Auto-fix HR template issues

#### WebSocket & Real-time Endpoints
- **GET** `/api/v1/websocket/stats` — WebSocket connection stats
- **GET** `/api/v1/websocket/queue/live` — Live queue updates
- **GET** `/api/v1/websocket/analytics/hourly` — Hourly analytics data
- **GET** `/api/v1/websocket/system/health` — Real-time system health
- **POST** `/api/v1/websocket/broadcast/test` — Test broadcast message
- **POST** `/api/v1/websocket/dashboard/refresh` — Trigger dashboard refresh

### 7. Health & Status Endpoints

| Method | Endpoint                    | Description                          |
|--------|-----------------------------|--------------------------------------|
| GET    | `/`                         | API information & available endpoints|
| GET    | `/api/v1/`                  | API v1 information                   |
| GET    | `/api/v1/health`            | Comprehensive health check           |
| GET    | `/api/v1/dashboard`         | Serve dashboard HTML                 |
| GET    | `/api/v1/admin-dashboard`   | Serve admin dashboard HTML           |


---

## 🖥️ UI Pages & Components

### 1. Landing Page
- Hero section: Title, key features, CTA to Login/Signup
- Feature highlights: Cards for AI Analysis, Pipeline, Templates, Legal, Sales, Monitoring
- Footer: Links to docs, support, privacy

### 2. Authentication Pages
- **Login**: Email, Password, Remember Me, Submit
- **Signup**: Name, Email, Password, Confirm
- **Forgot Password**: Request reset link
- **Reset Password**: New password form

### 3. Dashboard (User)

#### a. Resume Upload Section
- File upload drag & drop or browse
- Single vs Batch toggle
- On upload: call `/queue/upload` or `/upload/batch`
- Show notification on success: queue position

#### b. Analyses Table
- Columns: Resume Name, Status, Overall Score, Date, Actions (View details, Re-analyze, Delete)
- Data from `/resumes` and `/resumes/{id}/analyses`
- Row click opens detail modal with agent results

#### c. Candidate Pipeline
- Table or Kanban view of candidates
- Columns: Name, Stage, Priority, Score, Last Activity
- Inline actions: Advance Stage, Add Note, View Timeline

#### d. HR Templates
- List templates: category filter dropdown
- Actions: Generate New, Personalize, Archive
- Editor modal for subject/body

#### e. Legal Consultation
- Query input box, submit to `/legal/query`
- Display answer and sources list
- Feedback buttons (helpful/not helpful)
- History panel of past queries

#### f. Sales Intelligence
- Leads table: Company, Status, Score, Source, Actions
- ROI Calculator form: input fields, calculate button, display results chart
- Metrics dashboard: lead conversion funnel chart

#### g. Monitoring Dashboard
- Real-time charts: CPU, Memory, Queue length, API latency
- Health status cards: Database, AI service, Agents
- Admin actions: trigger health check

### 4. Admin Panel
- **User Management**: list, add, edit, deactivate users
- **System Config**: toggle feature flags, view environment variables
- **Audit Logs**: paginated list of actions with filters
- **Analytics**: global metrics and usage insights

---

## 🗓️ Project Roadmap & Checklist

**🎯 Current Status**: Backend implementation is 100% complete. Frontend development can now begin with full confidence that all API endpoints are operational and production-ready.

| Phase | Task | Completed | Notes |
|-------|------|-----------|-------|
| **Backend** | ✅ Authentication & JWT system | ✅ | Middleware operational, token refresh working |
|           | ✅ Credit transaction tracking | ✅ | Full admin analytics implemented |
|           | ✅ WebSocket service compatibility | ✅ | Flask-socketio version fixes applied |
|           | ✅ Admin management endpoints | ✅ | Credit analytics, monitoring alerts, user activity |
|           | ✅ Database relationship fixes | ✅ | Admin profile relationships working |
| **Phase 4** | Setup React/Vue project structure | ☐ | Create base layout & routing with Next.js/Nuxt |
|           | Implement Authentication UI | ☐ | `/login`, `/signup`, `/forgot-password` pages |
|           | Build Resume Upload module | ☐ | Drag & drop, progress tracking, batch support |
|           | Develop Analyses Table & Detail | ☐ | Agent results modal, comparison tools |
|           | Candidate Pipeline (Table/Kanban) | ☐ | Stage transitions, drag & drop, filtering |
|           | HR Templates UI | ☐ | Generate, personalize, compliance validation |
|           | Legal Consultation UI | ☐ | Query input, sources display, history |
|           | Sales Intelligence UI | ☐ | Leads table, ROI calculator, analytics |
|           | Monitoring Dashboard UI | ☐ | Real-time charts, health status, alerts |
|           | Admin Panel Frontend | ☐ | User mgmt, credit analytics, system config, audit logs |
| **Integration** | WebSocket & Notifications | ☐ | socket.io client, real-time updates |
|               | HTTP Client Setup | ☐ | Axios with interceptors, error handling |
|               | Authentication Integration | ☐ | JWT handling, auto-refresh, role guards |
|               | Charting library integration | ☐ | Recharts/Chart.js for analytics |
| **Polish**    | Responsive design & theming | ☐ | Mobile breakpoints, dark/light mode |
|               | Form validation & UX | ☐ | React Hook Form, loading states |
|               | Error boundaries & handling | ☐ | Global error handling, user feedback |
|               | Accessibility & internationalization | ☐ | ARIA labels, i18n support |
|               | Performance optimization | ☐ | Code splitting, lazy loading, caching |
|               | End-to-end testing | ☐ | Cypress tests for critical flows |
|               | Documentation & deployment | ☐ | README, environment setup, CI/CD |

---

## 📝 Data Models & Sample JSON

### Typescript Interfaces
```typescript
// Authentication Types
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer";
  expires_in: number; // 86400 seconds (24 hours)
  user: {
    id: string;
    email: string;
    username: string;
    first_name?: string;
    last_name?: string;
    is_admin: boolean;
    credits_balance: number;
    created_at: string;
    last_login?: string;
    admin_profile?: {
      role: string;
      access_level: string;
      permissions: string[];
    };
  };
}

interface RegisterRequest {
  email: string;
  password: string;
  username?: string;
  first_name?: string;
  last_name?: string;
}

// Resume Upload & Analysis
interface UploadResponse {
  message: string;
  resume_id: string;
  queue_id: string;
  queue_position: number;
  estimated_completion?: string;
}

interface BatchUploadResponse {
  message: string;
  batch_id: string;
  total_files: number;
  estimated_completion?: string;
  processed_files: number;
}

interface AnalysisResult {
  analysis_id: string;
  resume_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  overall_score: number;
  agent_results: {
    technical: { score: number; summary: string; detailed_feedback: string };
    experience: { score: number; summary: string; detailed_feedback: string };
    education: { score: number; summary: string; detailed_feedback: string };
    soft_skills: { score: number; summary: string; detailed_feedback: string };
  };
  processing_time?: number;
  created_at: string;
  completed_at?: string;
}

interface Resume {
  id: string;
  user_id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  upload_date: string;
  analyses_count: number;
}

// Candidate Pipeline
interface Candidate {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  position_title?: string;
  department?: string;
  resume_id?: string;
  status: 'active' | 'on_hold' | 'rejected' | 'hired' | 'withdrawn';
  current_stage: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  overall_score?: number;
  technical_score?: number;
  experience_score?: number;
  education_score?: number;
  soft_skills_score?: number;
  applied_at?: string;
  created_at: string;
  updated_at: string;
  last_activity?: string;
}

interface CandidateNote {
  id: string;
  candidate_id: string;
  content: string;
  note_type: 'general' | 'interview' | 'feedback' | 'internal';
  created_by: string;
  created_at: string;
}

interface PipelineStage {
  stage: string;
  display_name: string;
  order: number;
  is_final: boolean;
}

// HR Communication Templates
interface HRTemplate {
  id: string;
  user_id?: string;
  category: string;
  template_type: string;
  subject: string;
  body: string;
  compliance_level: 'basic' | 'standard' | 'strict';
  status: 'draft' | 'active' | 'archived';
  is_system_template: boolean;
  personalization_fields: string[];
  created_at: string;
  updated_at: string;
}

interface TemplateGenerationRequest {
  category: string;
  candidate_id?: string;
  context?: string;
  compliance_level: 'basic' | 'standard' | 'strict';
  include_legal_disclaimer?: boolean;
}

interface PersonalizationRequest {
  candidate_id: string;
  context?: string;
  custom_fields?: Record<string, string>;
}

// Legal RAG
interface LegalSource {
  doc_title: string;
  chunk_text: string;
  page_number?: number;
  similarity: number;
  section?: string;
}

interface LegalQueryRequest {
  query: string;
  max_sources?: number;
  include_examples?: boolean;
}

interface LegalResponse {
  answer: string;
  sources: LegalSource[];
  query_id: string;
  confidence_score: number;
  query_type: 'compliance' | 'procedure' | 'legal_definition' | 'case_study';
  processing_time: number;
}

interface LegalQueryHistory {
  id: string;
  user_id: string;
  query: string;
  answer: string;
  confidence_score: number;
  sources_count: number;
  rating?: number;
  feedback?: string;
  created_at: string;
}

// Sales Intelligence & ROI
interface SalesLead {
  id: string;
  company_name: string;
  contact_email: string;
  contact_name?: string;
  lead_score: number;
  status: 'new' | 'contacted' | 'qualified' | 'proposal' | 'closed_won' | 'closed_lost';
  source: string;
  estimated_value?: number;
  created_at: string;
  last_activity?: string;
}

interface ROIInput {
  monthly_analyses: number;
  hourly_rate: number;
  time_saved_per_analysis?: number;
  platform_cost_per_analysis?: number;
}

interface ROIResult {
  monthly_time_savings: number;
  monthly_cost_savings: number;
  platform_cost: number;
  net_savings: number;
  roi_percentage: number;
  payback_period_days: number;
  annual_savings: number;
  three_year_savings: number;
  break_even_point: string;
}

// Monitoring & Analytics
interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  timestamp: string;
  services: {
    database: { status: string; message: string; response_time?: number };
    ai_service: { status: string; message: string; models_loaded?: number };
    queue_system: { status: string; message: string; queue_length?: number };
    file_storage: { status: string; message: string; available_space?: string };
  };
  performance_metrics: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
  };
}

interface MonitoringMetrics {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  response_time_avg: number;
  requests_per_minute: number;
  error_rate: number;
  queue_length: number;
}

interface PerformanceTrend {
  timestamp: string;
  metric_name: string;
  value: number;
  status: 'normal' | 'warning' | 'critical';
}

// Admin Types
interface AdminUser {
  id: string;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  is_admin: boolean;
  credits_balance: number;
  total_analyses: number;
  total_uploads: number;
  last_login?: string;
  created_at: string;
  status: 'active' | 'suspended' | 'deleted';
}

interface CreditTransaction {
  id: string;
  user_id: string;
  transaction_type: 'spent' | 'purchased' | 'refunded' | 'bonus';
  amount: number;
  description: string;
  operation_type: string;
  created_at: string;
  user?: {
    id: string;
    email: string;
    username: string;
  };
}

interface CreditAnalytics {
  summary: {
    total_transactions: number;
    total_credits_spent: number;
    total_credits_purchased: number;
    net_credits: number;
    active_users: number;
    average_credits_per_user: number;
  };
  daily_trends: Array<{
    date: string;
    credits_spent: number;
    credits_purchased: number;
    transactions: number;
    active_users: number;
  }>;
  user_distribution: {
    high_usage: number;
    medium_usage: number;
    low_usage: number;
    inactive: number;
  };
  top_users: Array<{
    user_id: string;
    email: string;
    total_spent: number;
    total_purchased: number;
    balance: number;
    last_activity: string;
  }>;
}

interface AuditLog {
  id: string;
  user_id?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

// WebSocket Event Types
interface QueueUpdateEvent {
  queue_id: string;
  new_position: number;
  estimated_completion?: string;
}

interface AnalysisProgressEvent {
  resume_id: string;
  analysis_id: string;
  progress_percentage: number;
  current_agent: string;
}

interface AnalysisCompletedEvent {
  resume_id: string;
  analysis_id: string;
  overall_score: number;
  agent_results: AnalysisResult['agent_results'];
}

interface SystemHealthUpdateEvent {
  status: 'healthy' | 'warning' | 'critical';
  metrics: MonitoringMetrics;
  alert_level?: 'info' | 'warning' | 'critical';
}

// API Response Wrappers
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Error Types
interface ApiError {
  error: string;
  error_code?: string;
  details?: Record<string, any>;
  timestamp: string;
}

interface ValidationError {
  field: string;
  message: string;
  value?: any;
}
```

### Sample JSON Payloads

**Upload Single Resume Response**
```json
{
  "message": "Resume uploaded successfully",
  "resume_id": "res_789abc",
  "queue_id": "queue_123def",
  "queue_position": 2,
  "estimated_completion": "2025-08-06T15:45:00Z"
}
```

**Get Analysis Result Sample**
```json
[{
  "analysis_id": "anl_456ghi",
  "resume_id": "res_789abc",
  "status": "completed",
  "overall_score": 85,
  "agent_results": {
    "technical": { 
      "score": 20, 
      "summary": "Strong backend development skills with Python and Flask",
      "detailed_feedback": "Excellent experience with REST APIs, database design, and cloud deployment"
    },
    "experience": { 
      "score": 18, 
      "summary": "5 years progressive experience in fintech startups",
      "detailed_feedback": "Demonstrated growth from junior to senior developer with leadership experience"
    },
    "education": { 
      "score": 22, 
      "summary": "Computer Science degree with honors from tier-1 university",
      "detailed_feedback": "Strong academic foundation with relevant coursework in AI and data structures"
    },
    "soft_skills": { 
      "score": 25, 
      "summary": "Excellent communication and team collaboration skills",
      "detailed_feedback": "Evidence of mentoring, cross-functional collaboration, and client interaction"
    }
  },
  "processing_time": 45,
  "created_at": "2025-08-06T14:30:00Z",
  "completed_at": "2025-08-06T14:30:45Z"
}]
```

**Candidate List Sample**
```json
{
  "candidates": [
    {
      "id": "cand_001",
      "first_name": "Alice",
      "last_name": "Johnson",
      "email": "alice.johnson@example.com",
      "position_title": "Senior React Developer",
      "current_stage": "phone_interview",
      "priority": "high",
      "overall_score": 78,
      "status": "active",
      "applied_at": "2025-08-01T10:00:00Z",
      "created_at": "2025-08-01T10:00:00Z",
      "last_activity": "2025-08-05T16:30:00Z"
    }
  ],
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

**HR Template Generation Response**
```json
{
  "success": true,
  "template": {
    "id": "tpl_001xyz",
    "category": "phone_interview",
    "subject": "Phone Interview Invitation - Senior React Developer Position",
    "body": "Dear {{candidate_name}},\n\nThank you for your interest in the Senior React Developer position at {{company_name}}. Based on your impressive background in frontend development and your {{years_experience}} years of experience, we would like to schedule a phone interview.\n\nThe interview will cover:\n- Your experience with React, TypeScript, and modern frontend tooling\n- Discussion of your previous projects and achievements\n- Our company culture and the role expectations\n\nPlease let us know your availability for a 30-minute call in the coming week.\n\nBest regards,\n{{interviewer_name}}\n{{company_name}} Talent Acquisition Team",
    "compliance_level": "standard",
    "personalization_fields": ["candidate_name", "company_name", "years_experience", "interviewer_name"],
    "created_at": "2025-08-06T14:45:00Z"
  },
  "generation_metadata": {
    "processing_time": 3.2,
    "template_type": "ai_generated",
    "compliance_checks_passed": true
  }
}
```

**Legal RAG Query Response**
```json
{
  "answer": "According to Section 25 of the Industrial Relations Code, 2020, employers must provide a minimum of 30 days written notice for termination of employment for workmen. For officers and other employees, the notice period is typically governed by the employment contract, but should not be less than 30 days as per general practice. The notice period can be waived by payment in lieu of notice.",
  "sources": [
    { 
      "doc_title": "Industrial_Relations_Code_2020.txt", 
      "chunk_text": "Section 25(1): No employer shall terminate the services of a workman who has been in continuous service for not less than one year, except for reasonable cause and after giving to such workman not less than thirty days' notice in writing...",
      "similarity": 0.92,
      "page_number": 45,
      "section": "Section 25 - Termination of Service"
    },
    {
      "doc_title": "Employment_Contract_Guidelines.txt",
      "chunk_text": "Standard practice in Indian employment law requires a minimum notice period of 30 days for termination, which can be extended based on the seniority and role of the employee...",
      "similarity": 0.87,
      "section": "Notice Period Guidelines"
    }
  ],
  "query_id": "lgq_123abc",
  "confidence_score": 0.89,
  "query_type": "compliance",
  "processing_time": 2.1
}
```

**ROI Calculation Sample**
```json
{
  "monthly_time_savings": 200,
  "monthly_cost_savings": 4000,
  "platform_cost": 800,
  "net_savings": 3200,
  "roi_percentage": 400,
  "payback_period_days": 9,
  "annual_savings": 48000,
  "three_year_savings": 144000,
  "break_even_point": "9 days",
  "calculation_details": {
    "time_saved_per_analysis": 2.5,
    "hourly_rate": 20,
    "monthly_analyses": 80,
    "platform_cost_per_analysis": 10
  }
}
```

**Credit Transactions List Response**
```json
{
  "success": true,
  "transactions": [
    {
      "id": "ct_123abc",
      "user_id": "user_456def",
      "transaction_type": "spent",
      "amount": -1,
      "description": "Resume analysis",
      "operation_type": "resume_analysis",
      "created_at": "2025-08-06T14:30:00Z",
      "user": {
        "id": "user_456def",
        "email": "user@example.com",
        "username": "john_doe"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "has_next": true,
    "has_prev": false
  },
  "summary": {
    "total_credits_spent": 450,
    "total_credits_purchased": 500,
    "net_credits": 50
  }
}
```

**Credit Analytics Response**
```json
{
  "success": true,
  "summary": {
    "total_transactions": 1250,
    "total_credits_spent": 2800,
    "total_credits_purchased": 3500,
    "net_credits": 700,
    "active_users": 45,
    "average_credits_per_user": 62.2
  },
  "daily_trends": [
    {
      "date": "2025-08-06",
      "credits_spent": 85,
      "credits_purchased": 120,
      "transactions": 25,
      "active_users": 12
    }
  ],
  "user_distribution": {
    "high_usage": 8,
    "medium_usage": 15,
    "low_usage": 22,
    "inactive": 5
  },
  "top_users": [
    {
      "user_id": "user_123",
      "email": "topuser@company.com",
      "total_spent": 150,
      "total_purchased": 200,
      "balance": 50,
      "last_activity": "2025-08-06T15:30:00Z"
    }
  ]
}
```

**System Health Check Response**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-06T15:00:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "message": "PostgreSQL connection successful",
      "response_time": 15
    },
    "ai_service": {
      "status": "healthy", 
      "message": "All AI agents operational",
      "models_loaded": 4
    },
    "queue_system": {
      "status": "healthy",
      "message": "Queue processing normally",
      "queue_length": 3
    },
    "file_storage": {
      "status": "healthy",
      "message": "File storage accessible",
      "available_space": "85.2 GB"
    }
  },
  "performance_metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 34.5,
    "active_connections": 12
  }
}
```

**WebSocket Event Examples**
```json
// Analysis Progress Event
{
  "event": "analysis_progress",
  "data": {
    "resume_id": "res_789abc",
    "analysis_id": "anl_456ghi", 
    "progress_percentage": 65,
    "current_agent": "experience_agent",
    "estimated_completion": "2025-08-06T15:02:30Z"
  }
}

// Queue Position Update Event
{
  "event": "queue_position_update",
  "data": {
    "queue_id": "queue_123def",
    "new_position": 1,
    "estimated_completion": "2025-08-06T15:01:00Z"
  }
}

// Candidate Stage Change Event
{
  "event": "candidate_stage_changed",
  "data": {
    "candidate_id": "cand_001",
    "new_stage": "technical_assessment",
    "old_stage": "phone_interview",
    "user_id": "user_456",
    "changed_by": "admin_789",
    "timestamp": "2025-08-06T15:00:00Z"
  }
}
```

---

## 🔄 WebSocket Events & Real-time Features

### Connection Setup
```javascript
import io from 'socket.io-client';

const socket = io('https://determined-harmony-production.up.railway.app', {
  auth: {
    token: localStorage.getItem('access_token')
  },
  transports: ['websocket', 'polling'], // Fallback for Railway deployment
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000
});

// Connection event handlers
socket.on('connect', () => {
  console.log('Connected to WebSocket server');
  socket.emit('join_user_room', { userId: currentUser.id });
});

socket.on('disconnect', () => {
  console.log('Disconnected from WebSocket server');
});

socket.on('connect_error', (error) => {
  console.error('WebSocket connection error:', error);
  // Handle authentication errors
  if (error.message.includes('authentication')) {
    // Refresh token and retry
    refreshAuthToken();
  }
});

socket.on('reconnect', (attemptNumber) => {
  console.log(`Reconnected after ${attemptNumber} attempts`);
});
```

**⚠️ Important Notes**:
- The backend WebSocket service has been updated for compatibility across flask-socketio versions
- Connection errors are gracefully handled with fallback patterns
- Authentication tokens are validated on WebSocket connection
- Automatic reconnection is enabled for production reliability

### Events to Listen For
| Event Name | Payload | Description |
|------------|---------|-------------|
| `queue_position_update` | `{ queue_id, new_position, estimated_completion }` | Queue position changed |
| `analysis_started` | `{ resume_id, analysis_id, agent_status }` | Analysis began processing |
| `analysis_progress` | `{ resume_id, analysis_id, progress_percentage, current_agent }` | Analysis progress update |
| `analysis_completed` | `{ resume_id, analysis_id, overall_score, agent_results }` | Analysis finished successfully |
| `analysis_failed` | `{ resume_id, analysis_id, error, retry_available }` | Analysis failed with error |
| `batch_progress` | `{ batch_id, processed_count, total_count, current_file }` | Batch upload progress |
| `batch_completed` | `{ batch_id, total_processed, failed_count, summary }` | Batch processing completed |
| `candidate_stage_changed` | `{ candidate_id, new_stage, old_stage, user_id }` | Pipeline stage update |
| `candidate_score_updated` | `{ candidate_id, new_score, previous_score }` | Candidate scoring changed |
| `high_priority_alert` | `{ candidate_id, alert_type, message, priority_level }` | Top candidate alert |
| `template_generated` | `{ template_id, category, personalized_for }` | HR template generated |
| `legal_query_completed` | `{ query_id, confidence_score, sources_count }` | Legal RAG query processed |
| `system_health_update` | `{ status, metrics, alert_level }` | System health change |
| `credit_balance_updated` | `{ user_id, new_balance, transaction_type, credits_used }` | Credit balance change |
| `admin_notification` | `{ type, message, severity, requires_action }` | Admin-only notifications |
| `pipeline_analytics_update` | `{ hiring_metrics, conversion_rates, pipeline_health }` | Pipeline analytics refresh |

### Events to Emit
| Event Name | Payload | Description |
|------------|---------|-------------|
| `join_user_room` | `{ userId }` | Subscribe to user-specific events |
| `join_admin_room` | `{ }` | Subscribe to admin-only events (admin users only) |
| `join_pipeline_room` | `{ userId }` | Subscribe to pipeline updates |
| `request_queue_status` | `{ userId }` | Get current queue status |
| `request_system_stats` | `{ }` | Request real-time system statistics |
| `ping_health_check` | `{ timestamp }` | Health check ping |

### WebSocket Integration Example
```javascript
// Set up event listeners for resume analysis
const setupAnalysisListeners = (resumeId) => {
  // Listen for analysis start
  socket.on('analysis_started', (data) => {
    if (data.resume_id === resumeId) {
      updateAnalysisStatus('processing');
      showNotification('Analysis started', 'info');
    }
  });

  // Listen for progress updates
  socket.on('analysis_progress', (data) => {
    if (data.resume_id === resumeId) {
      updateProgressBar(data.progress_percentage);
      updateCurrentAgent(data.current_agent);
    }
  });

  // Listen for completion
  socket.on('analysis_completed', (data) => {
    if (data.resume_id === resumeId) {
      updateAnalysisResults(data);
      showNotification('Analysis completed!', 'success');
      refreshAnalysisTable();
    }
  });

  // Listen for failures
  socket.on('analysis_failed', (data) => {
    if (data.resume_id === resumeId) {
      showError(`Analysis failed: ${data.error}`);
      if (data.retry_available) {
        showRetryButton(resumeId);
      }
    }
  });
};

// Set up queue position tracking
const setupQueueListeners = () => {
  socket.on('queue_position_update', (data) => {
    updateQueuePosition(data.queue_id, data.new_position);
    updateEstimatedTime(data.estimated_completion);
  });
};

// Set up real-time dashboard updates
const setupDashboardListeners = () => {
  socket.on('system_health_update', (data) => {
    updateHealthStatus(data.status);
    updateSystemMetrics(data.metrics);
    if (data.alert_level === 'critical') {
      showCriticalAlert(data);
    }
  });

  socket.on('pipeline_analytics_update', (data) => {
    updatePipelineCharts(data.hiring_metrics);
    updateConversionRates(data.conversion_rates);
  });
};

// Clean up listeners when component unmounts
const cleanupSocketListeners = () => {
  socket.off('analysis_started');
  socket.off('analysis_progress');
  socket.off('analysis_completed');
  socket.off('analysis_failed');
  socket.off('queue_position_update');
  socket.off('system_health_update');
  socket.off('pipeline_analytics_update');
};
```

---

## 🔧 API Integration Guide

### Environment Configuration
```javascript
// Environment variables (.env)
VITE_API_BASE_URL=https://determined-harmony-production.up.railway.app
VITE_WS_URL=wss://determined-harmony-production.up.railway.app
VITE_APP_NAME=HR Consultancy ATS
VITE_APP_VERSION=1.3

// For development
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Axios Configuration
```javascript
// api/client.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://determined-harmony-production.up.railway.app';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

### API Service Classes
```javascript
// services/AuthService.js
import apiClient from '../api/client';

export class AuthService {
  static async login(email, password) {
    const response = await apiClient.post('/api/v1/auth/login', {
      email,
      password
    });
    
    const { access_token, refresh_token, user } = response.data;
    
    // Store tokens
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  }
  
  static async register(userData) {
    const response = await apiClient.post('/api/v1/auth/register', userData);
    return response.data;
  }
  
  static async getCurrentUser() {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  }
  
  static logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }
}

// services/ResumeService.js
import apiClient from '../api/client';

export class ResumeService {
  static async uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/api/v1/queue/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }
  
  static async uploadBatch(zipFile) {
    const formData = new FormData();
    formData.append('file', zipFile);
    
    const response = await apiClient.post('/api/v1/queue/upload/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }
  
  static async getResumes(page = 1, perPage = 20, status = null) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    if (status) params.append('status', status);
    
    const response = await apiClient.get(`/api/v1/resumes?${params}`);
    return response.data;
  }
  
  static async getAnalyses(resumeId) {
    const response = await apiClient.get(`/api/v1/resumes/${resumeId}/analyses`);
    return response.data;
  }
  
  static async reanalyzeResume(resumeId) {
    const response = await apiClient.post(`/api/v1/resumes/${resumeId}/reanalyze`);
    return response.data;
  }
  
  static async deleteResume(resumeId) {
    const response = await apiClient.delete(`/api/v1/resumes/${resumeId}`);
    return response.data;
  }
}

// services/CandidateService.js
import apiClient from '../api/client';

export class CandidateService {
  static async getCandidates(filters = {}) {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        params.append(key, value.toString());
      }
    });
    
    const response = await apiClient.get(`/api/v1/pipeline/candidates?${params}`);
    return response.data;
  }
  
  static async createCandidate(candidateData) {
    const response = await apiClient.post('/api/v1/pipeline/candidates', candidateData);
    return response.data;
  }
  
  static async updateCandidate(candidateId, updates) {
    const response = await apiClient.put(`/api/v1/pipeline/candidates/${candidateId}`, updates);
    return response.data;
  }
  
  static async moveToStage(candidateId, stage, notes = null) {
    const response = await apiClient.put(`/api/v1/pipeline/candidates/${candidateId}/stage`, {
      stage,
      notes
    });
    return response.data;
  }
  
  static async addNote(candidateId, content, noteType = 'general') {
    const response = await apiClient.post(`/api/v1/pipeline/candidates/${candidateId}/notes`, {
      content,
      note_type: noteType
    });
    return response.data;
  }
}

// services/LegalService.js
import apiClient from '../api/client';

export class LegalService {
  static async submitQuery(query, maxSources = 5, includeExamples = true) {
    const response = await apiClient.post('/api/legal/query', {
      query,
      max_sources: maxSources,
      include_examples: includeExamples
    });
    return response.data;
  }
  
  static async submitFeedback(queryId, rating, feedback = null) {
    const response = await apiClient.post('/api/legal/feedback', {
      query_id: queryId,
      rating,
      feedback
    });
    return response.data;
  }
  
  static async getQueryHistory(page = 1, perPage = 20) {
    const response = await apiClient.get(`/api/legal/history?page=${page}&per_page=${perPage}`);
    return response.data;
  }
}

// services/AdminService.js
import apiClient from '../api/client';

export class AdminService {
  static async getCreditTransactions(filters = {}) {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        params.append(key, value.toString());
      }
    });
    
    const response = await apiClient.get(`/api/v1/admin/credit-transactions?${params}`);
    return response.data;
  }
  
  static async getCreditAnalytics() {
    const response = await apiClient.get('/api/v1/admin/analytics/credits');
    return response.data;
  }
  
  static async getUsers(page = 1, perPage = 20, status = null) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    if (status) params.append('status', status);
    
    const response = await apiClient.get(`/api/v1/admin/users?${params}`);
    return response.data;
  }
  
  static async adjustUserCredits(userId, amount, description) {
    const response = await apiClient.post(`/api/v1/admin/users/${userId}/credits`, {
      amount,
      description
    });
    return response.data;
  }
  
  static async toggleAdminStatus(userId, isAdmin) {
    const response = await apiClient.post(`/api/v1/admin/users/${userId}/admin-status`, {
      is_admin: isAdmin
    });
    return response.data;
  }
  
  static async getSystemHealth() {
    const response = await apiClient.get('/api/v1/admin/health');
    return response.data;
  }
  
  static async getMonitoringAlerts(page = 1, perPage = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    const response = await apiClient.get(`/api/v1/monitoring/alerts?${params}`);
    return response.data;
  }
  
  static async acknowledgeAlert(alertId) {
    const response = await apiClient.post(`/api/v1/monitoring/alerts/${alertId}/acknowledge`);
    return response.data;
  }
  
  static async getUserActivity(page = 1, perPage = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    const response = await apiClient.get(`/api/v1/monitoring/usage/activity?${params}`);
    return response.data;
  }
}
```

### Error Handling Utilities
```javascript
// utils/errorHandler.js
export const handleApiError = (error, showNotification) => {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        showNotification(data.error || 'Invalid request', 'error');
        break;
      case 401:
        showNotification('Please log in to continue', 'error');
        // AuthService.logout() will be called by interceptor
        break;
      case 402:
        showNotification('Insufficient credits. Please top up your account.', 'warning');
        break;
      case 403:
        showNotification('You do not have permission to perform this action', 'error');
        break;
      case 404:
        showNotification('Resource not found', 'error');
        break;
      case 429:
        showNotification('Too many requests. Please try again later.', 'warning');
        break;
      case 500:
        showNotification('Server error. Please try again later.', 'error');
        break;
      default:
        showNotification(data.error || 'An unexpected error occurred', 'error');
    }
  } else if (error.request) {
    showNotification('Network error. Please check your connection.', 'error');
  } else {
    showNotification('An unexpected error occurred', 'error');
  }
};

// utils/validation.js
export const validateFile = (file, allowedTypes = ['pdf', 'doc', 'docx'], maxSizeMB = 10) => {
  const errors = [];
  
  if (!file) {
    errors.push('No file selected');
    return errors;
  }
  
  // Check file type
  const fileExtension = file.name.split('.').pop().toLowerCase();
  if (!allowedTypes.includes(fileExtension)) {
    errors.push(`File type .${fileExtension} not allowed. Allowed types: ${allowedTypes.join(', ')}`);
  }
  
  // Check file size
  const fileSizeMB = file.size / (1024 * 1024);
  if (fileSizeMB > maxSizeMB) {
    errors.push(`File size ${fileSizeMB.toFixed(1)}MB exceeds maximum of ${maxSizeMB}MB`);
  }
  
  return errors;
};
```

---

## 🎨 Detailed UI Components & Wireframes

### 1. Landing Page Layout
```
Header: [Logo] [Features] [Pricing] [Login] [Sign Up]
Hero Section:
  - H1: "AI-Powered Resume Analysis for HR Teams"
  - Subtitle: "Multi-agent AI system with Indian market optimization"
  - CTA Buttons: [Start Free Trial] [Watch Demo]
  - Hero Image: Dashboard screenshot

Features Grid (3x2):
  1. AI Resume Analysis - Icon + description
  2. Candidate Pipeline - Icon + description  
  3. HR Templates - Icon + description
  4. Legal Consultation - Icon + description
  5. Sales Intelligence - Icon + description
  6. Real-time Monitoring - Icon + description

Social Proof:
  - Customer logos
  - Testimonials carousel
  - Statistics: "10,000+ resumes analyzed"

Footer: [About] [Privacy] [Terms] [Support] [API Docs]
```

### 2. Authentication Flow Details

**Login Page (/login)**
```html
<div class="login-container">
  <div class="login-form">
    <h1>Welcome Back</h1>
    <form onSubmit={handleLogin}>
      <input type="email" placeholder="Email" required />
      <input type="password" placeholder="Password" required />
      <div class="form-options">
        <label><input type="checkbox" /> Remember me</label>
        <a href="/forgot-password">Forgot password?</a>
      </div>
      <button type="submit">Sign In</button>
    </form>
    <p>Don't have an account? <a href="/signup">Sign up</a></p>
  </div>
  <div class="login-illustration">
    <!-- AI/HR themed illustration -->
  </div>
</div>
```

**Signup Page (/signup)**
```html
<div class="signup-container">
  <form onSubmit={handleSignup}>
    <h1>Create Account</h1>
    <p>Get 10 free credits to start analyzing resumes</p>
    <input type="text" placeholder="Full Name" required />
    <input type="email" placeholder="Email" required />
    <input type="password" placeholder="Password" required />
    <input type="password" placeholder="Confirm Password" required />
    <label><input type="checkbox" required /> I agree to Terms & Privacy</label>
    <button type="submit">Create Account</button>
  </form>
</div>
```

### 3. Main Dashboard Layout (/dashboard)

**Sidebar Navigation**
```
[Logo]
Dashboard
Resume Analysis
  - Upload Resumes
  - Analysis Results
  - Batch Uploads
Candidate Pipeline
  - All Candidates
  - Pipeline View
  - Analytics
HR Communication
  - Templates
  - Generator
  - History
Legal Consultation
  - Ask Question
  - Query History
Sales Intelligence
  - Leads
  - ROI Calculator
  - Analytics
[Admin Only]
Admin Panel
  - Users
  - System Config
  - Monitoring
  - Logs
```

**Main Content Area Structure**
```html
<div class="dashboard-layout">
  <aside class="sidebar">
    <!-- Navigation menu -->
  </aside>
  <main class="main-content">
    <header class="page-header">
      <h1>{currentPageTitle}</h1>
      <div class="user-info">
        <span>Credits: {userCredits}</span>
        <div class="user-menu">
          <img src={userAvatar} />
          <dropdown>
            <item>Profile</item>
            <item>Settings</item>
            <item>Logout</item>
          </dropdown>
        </div>
      </div>
    </header>
    <div class="page-content">
      <!-- Dynamic content based on route -->
    </div>
  </main>
</div>
```

### 4. Resume Upload Component (/dashboard/upload)

**Upload Section UI**
```html
<div class="upload-section">
  <div class="upload-tabs">
    <button class={singleActive ? 'active' : ''}>Single Resume</button>
    <button class={batchActive ? 'active' : ''}>Batch Upload</button>
  </div>
  
  <!-- Single Upload -->
  <div class="single-upload" style={singleActive ? 'display:block' : 'display:none'}>
    <div class="dropzone" onDrop={handleSingleDrop} onDragOver={handleDragOver}>
      <input type="file" accept=".pdf,.doc,.docx" onChange={handleFileSelect} />
      <div class="dropzone-content">
        <icon>📄</icon>
        <p>Drag & drop a resume here, or <span class="browse-link">browse</span></p>
        <small>Supports PDF, DOC, DOCX (max 10MB)</small>
      </div>
    </div>
    <button onClick={handleSingleUpload} disabled={!selectedFile}>
      Analyze Resume (1 credit)
    </button>
  </div>
  
  <!-- Batch Upload -->
  <div class="batch-upload" style={batchActive ? 'display:block' : 'display:none'}>
    <div class="dropzone" onDrop={handleBatchDrop}>
      <input type="file" accept=".zip" onChange={handleZipSelect} />
      <div class="dropzone-content">
        <icon>📦</icon>
        <p>Drag & drop a ZIP file with resumes</p>
        <small>ZIP containing PDF/DOC/DOCX files</small>
      </div>
    </div>
    <div class="batch-info" style={zipFile ? 'display:block' : 'display:none'}>
      <p>Files detected: {filesCount}</p>
      <p>Credits required: {filesCount}</p>
      <p>Current balance: {userCredits}</p>
    </div>
    <button onClick={handleBatchUpload} disabled={!zipFile || filesCount > userCredits}>
      Analyze Batch ({filesCount} credits)
    </button>
  </div>
</div>
```

**Upload Handler Logic**
```javascript
const handleSingleUpload = async () => {
  const formData = new FormData();
  formData.append('file', selectedFile);
  
  try {
    const response = await axios.post('/api/v1/queue/upload', formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (response.data.message) {
      showNotification(`Resume uploaded! Queue position: ${response.data.queue_position}`);
      
      // Listen for WebSocket updates
      socket.on(`queue_position_update`, (data) => {
        if (data.queue_id === response.data.queue_id) {
          updateQueuePosition(data.new_position);
          updateEstimatedTime(data.estimated_completion);
        }
      });
      
      // Listen for analysis events
      socket.on('analysis_started', (data) => {
        if (data.resume_id === response.data.resume_id) {
          updateAnalysisStatus('processing');
          showProgressBar();
        }
      });
      
      socket.on('analysis_progress', (data) => {
        if (data.resume_id === response.data.resume_id) {
          updateProgress(data.progress_percentage);
          updateCurrentAgent(data.current_agent);
        }
      });
      
      socket.on('analysis_completed', (data) => {
        if (data.resume_id === response.data.resume_id) {
          hideProgressBar();
          showSuccessMessage('Analysis completed!');
          refreshAnalysisTable();
          // Navigate to results or update UI
          router.push('/dashboard/results');
        }
      });
    }
  } catch (error) {
    if (error.response?.status === 402) {
      showError('Insufficient credits. Please top up your account.');
      showTopUpModal();
    } else if (error.response?.status === 401) {
      showError('Please log in to upload resumes.');
      redirectToLogin();
    } else {
      showError('Upload failed: ' + (error.response?.data?.error || error.message));
    }
  }
};

const handleBatchUpload = async () => {
  const formData = new FormData();
  formData.append('file', zipFile);
  
  try {
    const response = await axios.post('/api/v1/queue/upload/batch', formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (response.data.message) {
      showNotification(`Batch uploaded! ${response.data.total_files} files queued for processing`);
      
      // Listen for batch progress updates
      socket.on('batch_progress', (data) => {
        if (data.batch_id === response.data.batch_id) {
          updateBatchProgress(data.processed_count, data.total_count);
          updateCurrentFile(data.current_file);
        }
      });
      
      socket.on('batch_completed', (data) => {
        if (data.batch_id === response.data.batch_id) {
          hideBatchProgress();
          showBatchSummary(data.total_processed, data.failed_count);
          refreshAnalysisTable();
        }
      });
    }
  } catch (error) {
    handleUploadError(error);
  }
};
```

### 5. Analysis Results Table (/dashboard/results)

**Table Component**
```html
<div class="results-section">
  <div class="table-controls">
    <input type="text" placeholder="Search resumes..." onChange={handleSearch} />
    <select onChange={handleStatusFilter}>
      <option value="">All Statuses</option>
      <option value="pending">Pending</option>
      <option value="processing">Processing</option>
      <option value="completed">Completed</option>
      <option value="failed">Failed</option>
    </select>
    <select onChange={handleSortBy}>
      <option value="createdAt">Date</option>
      <option value="overallScore">Score</option>
      <option value="status">Status</option>
    </select>
  </div>
  
  <table class="results-table">
    <thead>
      <tr>
        <th>Resume Name</th>
        <th>Status</th>
        <th>Overall Score</th>
        <th>Technical</th>
        <th>Experience</th>
        <th>Education</th>
        <th>Soft Skills</th>
        <th>Date</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {analyses.map(analysis => (
        <tr key={analysis.id} onClick={() => openDetailModal(analysis)}>
          <td>{analysis.resumeName}</td>
          <td>
            <span class={`status-badge ${analysis.status}`}>
              {analysis.status}
            </span>
          </td>
          <td>
            <div class="score-cell">
              <span class="score-number">{analysis.overallScore}</span>
              <div class="score-bar">
                <div class="score-fill" style={`width: ${analysis.overallScore}%`}></div>
              </div>
            </div>
          </td>
          <td>{analysis.agentResults.technical.score}</td>
          <td>{analysis.agentResults.experience.score}</td>
          <td>{analysis.agentResults.education.score}</td>
          <td>{analysis.agentResults.softSkills.score}</td>
          <td>{formatDate(analysis.createdAt)}</td>
          <td>
            <button onClick={e => { e.stopPropagation(); reanalyze(analysis.id); }}>
              🔄 Re-analyze
            </button>
            <button onClick={e => { e.stopPropagation(); deleteResume(analysis.id); }}>
              🗑️ Delete
            </button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
  
  <div class="pagination">
    <button disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>
      Previous
    </button>
    <span>Page {currentPage} of {totalPages}</span>
    <button disabled={currentPage === totalPages} onClick={() => setPage(currentPage + 1)}>
      Next
    </button>
  </div>
</div>
```

### 6. Analysis Detail Modal

**Modal Component**
```html
<div class="modal-overlay" onClick={closeModal}>
  <div class="analysis-modal" onClick={e => e.stopPropagation()}>
    <header class="modal-header">
      <h2>{analysis.resumeName}</h2>
      <button class="close-btn" onClick={closeModal}>×</button>
    </header>
    
    <div class="modal-content">
      <div class="score-summary">
        <div class="overall-score">
          <h3>Overall Score</h3>
          <div class="score-circle">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" stroke="#e6e6e6" strokeWidth="10" fill="none" />
              <circle cx="50" cy="50" r="45" stroke="#4CAF50" strokeWidth="10" 
                      fill="none" strokeDasharray={`${analysis.overallScore * 2.83} 283`} />
            </svg>
            <span class="score-text">{analysis.overallScore}</span>
          </div>
        </div>
        
        <div class="agent-scores">
          <div class="agent-score">
            <h4>Technical Skills</h4>
            <div class="score-bar">
              <div class="fill" style={`width: ${analysis.agentResults.technical.score * 4}%`}></div>
            </div>
            <span>{analysis.agentResults.technical.score}/25</span>
            <p>{analysis.agentResults.technical.summary}</p>
          </div>
          
          <div class="agent-score">
            <h4>Experience</h4>
            <div class="score-bar">
              <div class="fill" style={`width: ${analysis.agentResults.experience.score * 4}%`}></div>
            </div>
            <span>{analysis.agentResults.experience.score}/25</span>
            <p>{analysis.agentResults.experience.summary}</p>
          </div>
          
          <div class="agent-score">
            <h4>Education</h4>
            <div class="score-bar">
              <div class="fill" style={`width: ${analysis.agentResults.education.score * 4}%`}></div>
            </div>
            <span>{analysis.agentResults.education.score}/25</span>
            <p>{analysis.agentResults.education.summary}</p>
          </div>
          
          <div class="agent-score">
            <h4>Soft Skills</h4>
            <div class="score-bar">
              <div class="fill" style={`width: ${analysis.agentResults.softSkills.score * 4}%`}></div>
            </div>
            <span>{analysis.agentResults.softSkills.score}/25</span>
            <p>{analysis.agentResults.softSkills.summary}</p>
          </div>
        </div>
      </div>
      
      <div class="modal-actions">
        <button onClick={() => convertToCandidate(analysis)}>
          👤 Convert to Candidate
        </button>
        <button onClick={() => generateTemplate(analysis)}>
          📄 Generate HR Template
        </button>
        <button onClick={() => reanalyze(analysis.id)}>
          🔄 Re-analyze
        </button>
      </div>
    </div>
  </div>
</div>
```

### 7. Candidate Pipeline (/dashboard/candidates)

**Pipeline Table View**
```html
<div class="candidates-section">
  <div class="candidates-header">
    <h2>Candidate Pipeline</h2>
    <div class="view-toggles">
      <button class={tableView ? 'active' : ''} onClick={() => setTableView(true)}>
        📋 Table View
      </button>
      <button class={!tableView ? 'active' : ''} onClick={() => setTableView(false)}>
        📊 Kanban View
      </button>
    </div>
    <button class="add-candidate-btn" onClick={openAddCandidateModal}>
      + Add Candidate
    </button>
  </div>
  
  <!-- Filters -->
  <div class="candidates-filters">
    <input type="text" placeholder="Search candidates..." onChange={handleSearch} />
    <select onChange={handleStageFilter}>
      <option value="">All Stages</option>
      <option value="applied">Applied</option>
      <option value="screening">Screening</option>
      <option value="phone_interview">Phone Interview</option>
      <option value="technical_assessment">Technical Assessment</option>
      <option value="on_site_interview">On-site Interview</option>
      <option value="final_interview">Final Interview</option>
      <option value="offer_made">Offer Made</option>
    </select>
    <select onChange={handlePriorityFilter}>
      <option value="">All Priorities</option>
      <option value="urgent">Urgent</option>
      <option value="high">High</option>
      <option value="medium">Medium</option>
      <option value="low">Low</option>
    </select>
  </div>
  
  <!-- Table View -->
  <div class="candidates-table" style={tableView ? 'display:block' : 'display:none'}>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Stage</th>
          <th>Priority</th>
          <th>Score</th>
          <th>Last Activity</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {candidates.map(candidate => (
          <tr key={candidate.id}>
            <td>
              <div class="candidate-name">
                <img src={candidate.avatar} class="candidate-avatar" />
                <span>{candidate.name}</span>
              </div>
            </td>
            <td>{candidate.email}</td>
            <td>
              <span class={`stage-badge ${candidate.stage}`}>
                {formatStage(candidate.stage)}
              </span>
            </td>
            <td>
              <span class={`priority-badge ${candidate.priority}`}>
                {candidate.priority}
              </span>
            </td>
            <td>
              <div class="score-display">
                <span>{candidate.overallScore}</span>
                <div class="mini-score-bar">
                  <div style={`width: ${candidate.overallScore}%`}></div>
                </div>
              </div>
            </td>
            <td>{formatDate(candidate.lastActivity)}</td>
            <td>
              <div class="action-buttons">
                <button onClick={() => advanceStage(candidate.id)}>
                  ⏭️ Advance
                </button>
                <button onClick={() => addNote(candidate.id)}>
                  📝 Note
                </button>
                <button onClick={() => viewTimeline(candidate.id)}>
                  📅 Timeline
                </button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
  
  <!-- Kanban View -->
  <div class="candidates-kanban" style={!tableView ? 'display:block' : 'display:none'}>
    {stages.map(stage => (
      <div key={stage} class="kanban-column">
        <h3 class="column-header">
          {formatStage(stage)}
          <span class="count">({getCandidatesByStage(stage).length})</span>
        </h3>
        <div class="kanban-cards" 
             onDrop={e => handleDrop(e, stage)} 
             onDragOver={handleDragOver}>
          {getCandidatesByStage(stage).map(candidate => (
            <div key={candidate.id} 
                 class="candidate-card" 
                 draggable
                 onDragStart={e => handleDragStart(e, candidate)}>
              <div class="card-header">
                <span class="candidate-name">{candidate.name}</span>
                <span class={`priority-dot ${candidate.priority}`}></span>
              </div>
              <div class="card-body">
                <p class="candidate-email">{candidate.email}</p>
                <div class="score-info">
                  <span>Score: {candidate.overallScore}</span>
                </div>
              </div>
              <div class="card-actions">
                <button onClick={() => addNote(candidate.id)}>📝</button>
                <button onClick={() => viewTimeline(candidate.id)}>📅</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
</div>
```

### 8. HR Templates (/dashboard/templates)

**Template Generator Interface**
```html
<div class="templates-section">
  <div class="templates-header">
    <h2>HR Communication Templates</h2>
    <button class="generate-btn" onClick={openGenerateModal}>
      ✨ Generate New Template
    </button>
  </div>
  
  <!-- Template Categories -->
  <div class="template-categories">
    <button class={selectedCategory === 'all' ? 'active' : ''} 
            onClick={() => setSelectedCategory('all')}>
      All Templates
    </button>
    <button class={selectedCategory === 'screening' ? 'active' : ''} 
            onClick={() => setSelectedCategory('screening')}>
      Screening
    </button>
    <button class={selectedCategory === 'phone_interview' ? 'active' : ''} 
            onClick={() => setSelectedCategory('phone_interview')}>
      Phone Interview
    </button>
    <button class={selectedCategory === 'offer' ? 'active' : ''} 
            onClick={() => setSelectedCategory('offer')}>
      Job Offers
    </button>
    <button class={selectedCategory === 'rejection' ? 'active' : ''} 
            onClick={() => setSelectedCategory('rejection')}>
      Rejection
    </button>
    <button class={selectedCategory === 'onboarding' ? 'active' : ''} 
            onClick={() => setSelectedCategory('onboarding')}>
      Onboarding
    </button>
  </div>
  
  <!-- Templates Grid -->
  <div class="templates-grid">
    {filteredTemplates.map(template => (
      <div key={template.id} class="template-card">
        <div class="template-header">
          <h3>{template.subject}</h3>
          <div class="template-meta">
            <span class={`category-badge ${template.category}`}>
              {formatCategory(template.category)}
            </span>
            <span class={`compliance-badge ${template.complianceLevel}`}>
              {template.complianceLevel}
            </span>
          </div>
        </div>
        <div class="template-preview">
          <p>{template.body.substring(0, 150)}...</p>
        </div>
        <div class="template-actions">
          <button onClick={() => personalizeTemplate(template.id)}>
            🎯 Personalize
          </button>
          <button onClick={() => editTemplate(template.id)}>
            ✏️ Edit
          </button>
          <button onClick={() => previewTemplate(template.id)}>
            👁️ Preview
          </button>
          <button onClick={() => archiveTemplate(template.id)}>
            🗄️ Archive
          </button>
        </div>
        <div class="template-footer">
          <small>Created: {formatDate(template.createdAt)}</small>
          <small>Status: {template.status}</small>
        </div>
      </div>
    ))}
  </div>
</div>

<!-- Generate Template Modal -->
<div class="modal-overlay" style={showGenerateModal ? 'display:flex' : 'display:none'}>
  <div class="generate-modal">
    <h2>Generate HR Template</h2>
    <form onSubmit={handleGenerateTemplate}>
      <div class="form-group">
        <label>Template Category</label>
        <select name="category" required>
          <option value="">Select category...</option>
          <option value="screening">Screening</option>
          <option value="phone_interview">Phone Interview</option>
          <option value="technical_interview">Technical Interview</option>
          <option value="offer">Job Offer</option>
          <option value="rejection">Rejection</option>
          <option value="onboarding">Onboarding</option>
        </select>
      </div>
      
      <div class="form-group">
        <label>Candidate (Optional)</label>
        <select name="candidateId">
          <option value="">Generic template</option>
          {candidates.map(candidate => (
            <option value={candidate.id}>{candidate.name}</option>
          ))}
        </select>
      </div>
      
      <div class="form-group">
        <label>Additional Context</label>
        <textarea name="context" 
                  placeholder="e.g., Senior React Developer position, immediate start required..."></textarea>
      </div>
      
      <div class="form-group">
        <label>Compliance Level</label>
        <select name="complianceLevel" required>
          <option value="basic">Basic</option>
          <option value="standard">Standard</option>
          <option value="strict">Strict (Legal Review)</option>
        </select>
      </div>
      
      <div class="modal-actions">
        <button type="button" onClick={closeGenerateModal}>Cancel</button>
        <button type="submit">Generate Template</button>
      </div>
    </form>
  </div>
</div>
```

### 9. Legal Consultation (/dashboard/legal)

**Legal Query Interface**
```html
<div class="legal-section">
  <div class="legal-header">
    <h2>HR Legal Consultation</h2>
    <p>Ask questions about Indian employment law and HR compliance</p>
  </div>
  
  <div class="legal-layout">
    <!-- Query Panel -->
    <div class="query-panel">
      <div class="query-form">
        <textarea 
          placeholder="Ask your HR legal question here... e.g., 'What are the notice period requirements for termination in India?'"
          value={queryText}
          onChange={e => setQueryText(e.target.value)}
          rows="4"
        ></textarea>
        
        <div class="query-options">
          <label>
            <input type="checkbox" checked={includeExample} onChange={e => setIncludeExample(e.target.checked)} />
            Include practical examples
          </label>
          <label>
            Max sources: 
            <select value={maxSources} onChange={e => setMaxSources(e.target.value)}>
              <option value="3">3</option>
              <option value="5">5</option>
              <option value="10">10</option>
            </select>
          </label>
        </div>
        
        <button 
          onClick={submitQuery} 
          disabled={!queryText.trim() || isLoading}
          class="submit-query-btn"
        >
          {isLoading ? 'Analyzing...' : 'Get Legal Advice'}
        </button>
      </div>
      
      <!-- Query History -->
      <div class="query-history">
        <h3>Recent Queries</h3>
        <div class="history-list">
          {queryHistory.map(query => (
            <div key={query.id} class="history-item" onClick={() => loadQuery(query)}>
              <div class="history-question">{query.question.substring(0, 80)}...</div>
              <div class="history-date">{formatDate(query.createdAt)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
    
    <!-- Results Panel -->
    <div class="results-panel">
      {currentResponse && (
        <div class="legal-response">
          <div class="response-header">
            <h3>Legal Analysis</h3>
            <div class="response-meta">
              <span>Sources: {currentResponse.sources.length}</span>
              <span>Query ID: {currentResponse.queryId}</span>
            </div>
          </div>
          
          <div class="response-content">
            <div class="answer-section">
              <h4>Answer</h4>
              <div class="answer-text">{currentResponse.answer}</div>
            </div>
            
            <div class="sources-section">
              <h4>Legal Sources</h4>
              <div class="sources-list">
                {currentResponse.sources.map((source, index) => (
                  <div key={index} class="source-item">
                    <div class="source-header">
                      <span class="source-title">{source.docTitle}</span>
                      <span class="similarity-score">{Math.round(source.similarity * 100)}% match</span>
                    </div>
                    <div class="source-content">{source.chunkText}</div>
                    {source.pageNumber && (
                      <div class="source-page">Page {source.pageNumber}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <div class="response-actions">
            <div class="feedback-section">
              <span>Was this helpful?</span>
              <button onClick={() => submitFeedback('helpful')}>👍 Yes</button>
              <button onClick={() => submitFeedback('not_helpful')}>👎 No</button>
              <button onClick={() => submitFeedback('needs_clarification')}>❓ Needs clarification</button>
            </div>
            <button onClick={exportResponse} class="export-btn">📄 Export to PDF</button>
          </div>
        </div>
      )}
      
      {isLoading && (
        <div class="loading-state">
          <div class="loading-spinner"></div>
          <p>Analyzing legal documents...</p>
        </div>
      )}
      
      {!currentResponse && !isLoading && (
        <div class="empty-state">
          <div class="empty-icon">⚖️</div>
          <h3>Ask Your First Legal Question</h3>
          <p>Get instant answers to HR compliance and employment law questions based on Indian legal documents.</p>
        </div>
      )}
    </div>
  </div>
</div>
```
