# HR ATS SaaS Frontend Architecture and Page Specification

This document outlines the proposed frontend structure, pages, routes, layout patterns, and key UI components for a production-ready SaaS application. It covers:

- Project structure and organization
- Routing and navigation
- Landing, Authentication, Admin and User sections
- Detailed page wireframes and component responsibilities
- Styling and UX considerations

---

## 1. Project Structure

```
/frontend                # Root of React/Vue/Svelte app
├── public              # Static assets (index.html, favicon, etc.)
└── src
    ├── assets          # Images, icons, fonts, styles
    ├── components      # Reusable UI components (Buttons, Modals, Cards)
    ├── layouts         # Layout wrappers (MainLayout, AuthLayout, AdminLayout)
    ├── pages           # Top-level pages
    │   ├── Landing
    │   ├── Auth
    │   │   ├── Login.jsx
    │   │   └── Signup.jsx
    │   ├── Admin
    │   │   ├── Dashboard.jsx
    │   │   ├── Resumes.jsx
    │   │   ├── Users.jsx
    │   │   └── Settings.jsx
    │   └── User
    │       ├── Profile.jsx
    │       ├── MyResumes.jsx
    │       └── SubmitResume.jsx
    ├── services        # API calls (resumeService, authService)
    ├── store           # State management (Redux/Vuex/Zustand)
    ├── utils           # Helpers (date formatting, validation)
    ├── App.jsx         # Application root and router setup
    └── index.jsx       # Entry point
```

## 2. Routing and Navigation

- `/` → **Landing Page** (public marketing site)
- `/login` → **Login** (AuthLayout)
- `/signup` → **Signup** (AuthLayout)
- `/admin` → **Admin Dashboard** (AdminLayout)
  - `/admin/resumes` → Resume management and AI analysis view
  - `/admin/users` → User management and subscription overview
  - `/admin/settings` → System configuration
- `/user` → **User Home** (MainLayout)
  - `/user/profile` → Profile and subscription status
  - `/user/my-resumes` → View and manage own resumes & analysis
  - `/user/submit` → Upload and submit new resume for AI analysis

Protected routes require JWT in localStorage; unauthorized users redirect to `/login`.

## 3. Landing Page

**Route:** `/`
**Layout:** Landing Layout (header + footer)

### Sections
1. **Hero** with headline, sub-headline, call-to-action (Sign Up)
2. **USP Features** cards: AI analysis, RAG legal assistant, analytics dashboard
3. **How It Works**: 3-step workflow graphic
4. **Pricing**: Tiered plans comparison table
5. **Testimonials**: Customer quotes
6. **Footer**: Links to Privacy, Terms, Contact

**Styling:** Bold hero background, brand colors, minimal iconography, responsive grid.

## 4. Authentication Pages

**Routes:** `/login`, `/signup`
**Layout:** AuthLayout (centered card)

### Login Page
- Email and password fields
- "Forgot password?" link
- Social login buttons (optional)
- Validation errors inline

### Signup Page
- Name, email, password, confirm fields
- Terms & Conditions checkbox
- Validation and password strength meter

## 5. Admin Section

**Layout:** AdminLayout (sidebar + top nav)

**Admin UI Structure**
- Sidebar
  • Links: Dashboard, Resumes, Users, Settings, Activity Log, Usage Stats
  • Icons and collapsed/expanded states
- Top Navigation Bar
  • Breadcrumbs or page title
  • Global search input
  • Notifications bell with badge count
  • Profile dropdown (avatar → Profile, Change Password, Logout)
- Main Content Area
  • Responsive container for page components
  • Consistent padding/margins and background
  • Dark/light theme support

### 5.1 Admin Dashboard
**Route:** `/admin`

**Dashboard UI Components**
- Responsive grid layout: 2–3 columns of cards on desktop, single-column on mobile
- StatCard: large number, metric label, optional icon, hover tooltip
- ChartCard: container with title, legend, tooltip-enabled chart (LineChart, BarChart, PieChart)
- Refresh Button: icon button top-right of grid
- Loading indicator overlay while fetching data

**Admin Dashboard Capabilities**
- Fetch and display data from `GET /api/admin/dashboard-stats`.
  • Expects response `{ success, stats: { users, database, system } }`.
  • `stats.users` includes trial and limit metrics (total_analyzed, at_resume_limit, at_legal_limit).
  • `stats.database` contains connection counts and basic DB health metrics.
  • `stats.system` holds `timestamp` and `admin_user` for last update and current session.
- Render summary cards, charts, and tables:
  • Trial user usage vs. limits.
  • Database performance stats (connections, query times).
  • Recent system health info with refresh timestamp.
- Provide a manual "Refresh Stats" control to re-fetch and update dashboard data.

### 5.2 Resume Management
**Route:** `/admin/resumes`

**Resume Management UI Components**
- FilterBar: horizontal form with dropdowns, date pickers, slider, search input
- ResumeTable: table with sortable headers, tailwind-styled rows, alternating backgrounds
- Pagination Controls: page numbers, Prev/Next buttons below table
- DetailDrawer: slide-in panel with header, summary section, JSON viewer, action toolbar
- UploadModal: centered modal with file input, user selector, submit/cancel buttons

**Resume Management Capabilities**
- List resumes via `GET /api/admin/resumes` with query parameters (`status`, `min_score`, `max_score`, `start_date`, `end_date`, `query`, `page`, `page_size`).
  • Response includes `{ success, resumes: [...], pagination: { page, limit, total, pages }, timestamp }`.
- Build table with sortable columns (`upload_date`, `overall_score`) and client-side sorting.
- Use `pagination` metadata to implement page controls (Prev/Next, page numbers).
- Filter panel binds to query params and refreshes results on change.
- On row click, open detail drawer showing:
  • Download link from `file_url`.
  • AI analysis summary (`analysis_result.overall_assessment`).
  • Agent-specific insights (`analysis_result.agent_insights`).
  • Full JSON `analysis_result` in collapsible code viewer.
- Action buttons:
  • Re-run analysis: `POST /api/admin/analyze/<resume_id>` → shows success message and `job_id`.
  • Batch analyze: `POST /api/admin/analyze/batch` with `resume_ids` → display list of queued jobs.
  • Upload resume: form posts multipart data to `POST /api/admin/resumes/upload`, integrates file picker and optional `user_id`.
  • Delete resume: `DELETE /api/admin/resumes/<resume_id>` with confirmation dialog.

**API Endpoints**
- `GET /api/admin/resumes`
  • Auth: admin cookie or `Authorization: Bearer <token>`
  • Query params: `status`, `min_score`, `max_score`, `start_date`, `end_date`, `query`, `page`, `page_size`
  • Response: `{ success, resumes: [ { id, user_id, filename, upload_date, processing_status, overall_score, analysis_result, file_url } ], total_count }`

- `GET /api/admin/resumes/analytics`
  • Auth: admin
  • Response: `{ success, stats: { avg_scores, counts_by_status, top_skills, recent_uploads_count } }`

- `POST /api/admin/resumes/upload`
  • Auth: admin
  • Body: multipart/form-data with `file` and optional `user_id`
  • Response: `{ success, resume: { id, filename, upload_date, status: 'pending' } }`

- `DELETE /api/admin/resumes/<resume_id>`
  • Auth: admin
  • Response: `{ success, message }`

- `POST /api/admin/analyze/<resume_id>`
  • Auth: admin
  • Response: `{ success, message: 'Analysis queued', job_id }`

- `POST /api/admin/analyze/batch`
  • Auth: admin
  • Body: `{ resume_ids: [id1, id2, ...] }`
  • Response: `{ success, queued: [ { resume_id, job_id } ] }`

**Components**
- `ResumeTable` (handles paging, filtering, search)
- `ResumeDetailDrawer` (displays full analysis)
- `FilterBar` (status, score, date pickers)
- `SearchBar` (text input)
- `ActionButtons` (rerun, archive, delete)

### 5.3 User Management
**Route:** `/admin/users`

**User Management UI Components**
- SearchBar & AccessTypeSelect: inline inputs above table
- UserTable: columns for avatar+name, email, role badge, trial status, action icons
- Action Icons: Edit (pencil), Delete (trash), Reset (refresh), Credits (dollar)
- UserModal: form modal for Create/Edit with validation, Save/Cancel buttons

**User Management Capabilities**
- Fetch user list `GET /api/admin/users` supporting `page`, `limit`, `search`, `access_type` filters.
  • Response `{ success, users, pagination, filters }` drives list view and filter state.
- Implement search box and access-type selector bound to query params.
- Pagination controls using returned `pagination` data.
- Create user form posts JSON to `POST /api/admin/users` with `{ email, name, password, access_type, trial_resume_limit, trial_legal_limit }`. On success, display new `user` object.
- Edit user: open modal/form, send `PUT /api/admin/users/<user_id>` with updated fields; update table row on success.
- Delete (deactivate) user: `DELETE /api/admin/users/<user_id>`; mark or remove from list.
- Reset trial limits: `POST /api/admin/users/<user_id>/reset-trial`; on success, refresh row counters.
- View user credits: `GET /api/admin/users/<user_id>/credits`; display credit balance in detail panel.

## 6. User Section

**Layout:** MainLayout (top nav + optional sidebar)

**User UI Structure**
- Top Navigation: page title, notifications, profile menu
- Content Container: centered card or panel with consistent padding

### 6.1 Profile
**Route:** `/user/profile`

**Profile UI Components**
- ProfileCard: display avatar, name, email, plan badge
- EditForm: inputs for name/email, Save/Cancel buttons, inline validation
- ChangePasswordSection: collapsed panel with old/new password fields and submit button

- Display name, email, subscription plan, usage
- Edit profile form
- Change password

### 6.2 My Resumes
**Route:** `/user/my-resumes`

**My Resumes UI Components**
- ResumeTable (similar to admin but limited to own data)
- DetailDrawer: same as admin resume detail
- DeleteButton: inline icon/button with confirmation dialog

- Table of user’s own resumes
- Columns: filename, upload date, status, overall score
- Click to view analysis (similar to admin detail)

### 6.3 Submit Resume
**Route:** `/user/submit`

**SubmitResume UI Components**
- FileUploader: drag-and-drop zone or browse button
- JobDescriptionTextarea: optional multiline input
- SubmitButton: primary button disabled until file selected
- ProgressIndicator: display upload/progress status

- Upload file (PDF/DOCX)
- Optional job description textarea
- Submit button triggers background AI processing
- After submit, redirect to My Resumes

**User Panel Capabilities**

**Profile Capabilities**
- Fetch current user metadata: `GET /api/auth/me` → `{ success, user: { user_id, email, name, access_type, is_trial, trial_info } }`.
- Change password: `POST /api/auth/change-password` with `{ old_password, new_password }` → `{ success, message }` or `{ error }`.
- Logout: `POST /api/auth/logout` → `{ success, message }`.

**My Resumes Capabilities**
- List own resumes: `GET /api/user/my-resumes` (to be implemented) → `{ success, resumes: [...], pagination, timestamp }`.
- Table view with columns (filename, upload_date, status, overall_score).
- Click to view analysis details (same as admin detail drawer).
- Delete own resume: `DELETE /api/admin/resumes/<resume_id>` (requires authorization) → `{ success, message, resume_id }`.

**Submit Resume Capabilities**
- Upload new resume: `POST /api/admin/resumes/upload` with multipart/form-data (`file`, optional `job_description`) → `{ success, resume: { id, filename, upload_date, status } }`.
- Optional job description passed in request body for AI context.
- After upload, automatically redirect/user to My Resumes and poll status.

**Payment Capabilities**
- View available packages: `GET /api/payment/packages` → `{ success, packages: [...], currency, message }`.
- Create order: `POST /api/payment/create-order` with `{ payment_type }` → returns `{ success, order_id, amount, ... }`.
- Verify payment: `POST /api/payment/verify` with `{ razorpay_order_id, razorpay_payment_id, razorpay_signature }` → `{ success, credits_added, processing_tier, order_id }`.

**Monitoring & Support**
- (Optional) Health check: `GET /api/monitoring/health` → `{ status, health }` for on-demand support or troubleshooting.

## 7. UI Style & Design System

- **Colors**: Primary (brand), Secondary (accent), Neutrals (gray scale)
- **Typography**: Choose web-safe font family, scale for H1–H4, body, captions
- **Spacing**: 8px base unit, consistent margins/padding
- **Components**: Buttons, Inputs, Modals, Tables, Cards
- **Responsiveness**: Mobile first, collapse sidebar on small screens
- **Theming**: Light/dark toggle (optional)

## 8. API Integration

- Use standardized `api/` service modules
- **AuthService**: login, signup, token refresh
- **ResumeService**: list, get detail, upload, rerun analysis
- **UserService**: get/update profile
- **AdminService**: admin-only endpoints (users, settings)

Use Axios or Fetch with interceptors for auth header injection and error handling.

### 8.1 Available REST API Endpoints

**Authentication (`/api/auth`)**
- POST `/api/auth/admin-login` – Admin login
- POST `/api/auth/user-login` – User login
- POST `/api/auth/create-user` – Create new user (admin only)
- GET  `/api/auth/session` – Get active session info
- POST `/api/auth/logout` – Logout current session
- GET  `/api/auth/me` – Get current user metadata
- POST `/api/auth/change-password` – Change user password
- GET  `/api/auth/health` – Check auth service health

**Admin (`/api/admin`)**
- GET    `/api/admin/dashboard-stats` – Summary stats for dashboard
- GET    `/api/admin/users` – List all users
- POST   `/api/admin/users` – Create a new user
- PUT    `/api/admin/users/<user_id>` – Update user details
- DELETE `/api/admin/users/<user_id>` – Delete a user
- POST   `/api/admin/users/<user_id>/reset-trial` – Reset trial limits
- GET    `/api/admin/users/<user_id>/credits` – Get user credit balance

- GET    `/api/admin/resumes` – List all resumes
- GET    `/api/admin/resumes/analytics` – Analytics summary for resumes
- POST   `/api/admin/resumes/upload` – Upload a new resume file
- DELETE `/api/admin/resumes/<resume_id>` – Delete a resume
- POST   `/api/admin/analyze/<resume_id>` – Trigger AI analysis for one resume
- POST   `/api/admin/analyze/batch` – Trigger batch AI analysis

- GET    `/api/admin/legal-queries` – List all legal compliance queries
- POST   `/api/admin/hr-legal/query` – Submit a new legal query
- DELETE `/api/admin/legal-queries/<query_id>` – Delete a legal query

- GET    `/api/admin/activity-log` – User activity audit log
- GET    `/api/admin/usage-stats` – Usage statistics for features
- GET    `/api/admin/system/health` – Detailed system health
- POST   `/api/admin/sessions/cleanup` – Cleanup expired sessions
- GET    `/api/admin/health` – Admin blueprint health check

**Payment (`/api/payment`)**
- GET  `/api/payment/packages` – Retrieve available payment packages
- POST `/api/payment/create-order` – Create a new RazorPay order
- POST `/api/payment/verify` – Verify a completed payment
- POST `/api/payment/webhook` – Webhook endpoint for RazorPay

**Monitoring (`/api/monitoring`)**
- GET  `/api/monitoring/health` – Database hybrid health status
- GET  `/api/monitoring/backup-sync/status` – Backup sync status
- POST `/api/monitoring/backup-sync/manual` – Trigger manual backup sync
- GET  `/api/monitoring/performance` – Performance metrics for databases
- GET  `/api/monitoring/configuration` – Current DB configuration
- POST `/api/monitoring/test-hybrid` – Test hybrid operations

**Core & Health**
- GET `/health` (or `/`) – Basic health check (level=basic/full/detailed via query param)

### 8.2 Authentication & Request Details

- **AuthService Endpoints** (`/api/auth/*`)
  • No bearer token required for login and create-user. Accepts JSON body with credentials.
  • Stores session token in `httpOnly` secure cookie (`user_session_token` or `admin_session_token`).

- **User & Admin Endpoints** (`/api/admin/*`, `/api/user/*` if added)
  • Requires authentication via cookie or `Authorization: Bearer <token>` header.
  • Admin routes require `admin_session_token`; user routes require `user_session_token`.
  • Requests should include JSON bodies or query parameters as documented.

- **Payment & Monitoring** (`/api/payment/*`, `/api/monitoring/*`)
  • Require valid authenticated user (must send `user_session_token` cookie or bearer token).

### 8.3 Common Response Format

All endpoints return JSON in the following structure:
```json
{
  "success": true | false,
  "message": "Optional human-readable message",
  "data": { ... } | [ ... ],     // Present on success
  "error": "Error description", // Present on failure
  "timestamp": "ISO8601 timestamp"
}
```
- **Success** responses include `data` or other documented fields.
- **Failure** responses include `error` and appropriate HTTP status code.

---

## 9. Performance, Monitoring & Analytics

- **Code Splitting & Lazy Loading**: Use dynamic imports to split bundles by route and enable faster initial load.
- **Performance Budgets**: Establish size and load time budgets; monitor via Lighthouse or WebPageTest.
- **Real User Monitoring (RUM)**: Integrate tools like New Relic Browser or Google Analytics to capture frontend performance metrics.
- **Error Reporting**: Use Sentry or LogRocket to capture runtime exceptions, unhandled promise rejections, and user interactions leading to errors.
- **Logging & Metrics**: Emit custom metrics (API latency, user flow completion rates) and front-end logs for dashboard monitoring.

## 10. Testing & QA

- **Unit Testing**: Write Jest + React Testing Library tests for components, services, and utils.
- **Integration Tests**: Test critical flows (login, resume upload/view) with Cypress or Playwright.
- **Visual Regression**: Use Chromatic or Percy to detect unintended UI changes.
- **Accessibility (a11y)**: Enforce WCAG 2.1 AA using axe-core integration and CI checks.
- **Continuous Testing**: Integrate tests into GitHub Actions to run on every PR and report coverage.

## 11. Security & Compliance

- **Authentication**: Secure JWT handling, token refresh, and secure storage (httpOnly cookies or secure localStorage patterns).
- **Authorization**: Protect routes via role-based access control (RBAC) on the client and server.
- **Input Sanitization**: Sanitize user inputs to prevent XSS, SQL injection, and other attacks.
- **CSP & Security Headers**: Configure Content Security Policy, X-Frame-Options, HSTS in hosting environment.
- **Data Privacy**: Comply with GDPR/CCPA: consent banner, data export, and delete requests.

## 12. Deployment & CI/CD

- **Branch Strategy**: Use `main` for production, `develop` for staging, feature branches for work.
- **CI Pipeline**: GitHub Actions workflows to lint, test, build, and deploy on merge to `main`/`develop`.
- **Hosting**: Deploy to Vercel/Netlify or AWS S3 + CloudFront; use CDNs for static assets.
- **Environment Management**: Securely inject env vars via hosting dashboard; use `.env.local` for local dev.
- **Versioning**: Automate semantic versioning and release notes with actions (semantic-release).

---

## 13. Next Steps & Pending Tasks

- Complete precise request/response schemas for remaining admin endpoints (users CRUD, legal queries, activity-log, usage-stats) to ensure alignment with backend implementations.
- Add user-side API contracts, including request and response schemas for `/api/user/my-resumes`, public resume analysis endpoints, and any additional user routes.
- Verify consistency of all field names and data structures (`has_analysis`, `analysis_result`, `file_url`, etc.) between spec and backend code.
- Conduct a comprehensive review of the spec against the codebase and update sections 5.3 (User Management) and 6.2 (My Resumes) with exact payload definitions.

*This specification provides a foundational blueprint. Components and pages can be iterated based on UX feedback, branding guidelines, and feature priorities.*
