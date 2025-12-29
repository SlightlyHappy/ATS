# **App Name**: HR Intel Pro

## Core Features:

- Authentication System: Email/password login via /api/auth/login, User registration with trial credits (100 free), JWT token management with auto-refresh, Password reset functionality
- AI Resume Analysis Dashboard: Upload interface for PDF/DOCX resumes via /api/upload, 4-Agent AI Analysis display, Real-time analysis progress tracking, Batch processing for multiple resumes via /api/analyze/batch
- Resume Database & Management: Comprehensive resume library with search/filter, Individual resume analysis view with PDF preview, Scoring breakdown (0-100 scale per agent), Analysis history and comparison tools, Export capabilities for analysis reports
- HR Legal RAG Consultation: AI-powered legal query interface via /api/hr-legal/query, Indian labor law compliance guidance, Query history and favorites, Confidence scoring and source attribution, Real-time legal recommendations
- Credit Management System: Credit balance display (trial + premium credits), Processing tier visualization, Payment integration with RazorPay, Credit usage analytics and forecasting
- Admin Authentication: Separate admin login via /api/auth/admin-login, Enhanced security with session management, Role-based access control
- Executive Dashboard: System KPIs: Total users (1,250+), resumes processed (5,420+), Revenue metrics and MRR tracking, Real-time system health monitoring, User activity analytics with geographic distribution
- User Management Hub: Complete CRUD operations via /api/admin/users, Credit management and trial limit controls, User behavior analytics and lead scoring, Bulk operations and user communication tools
- Resume Database Administration: System-wide resume database via /api/admin/resumes, Batch processing management and queue monitoring, AI analysis performance metrics, Failed analysis retry mechanisms
- RAG System Testing Interface: HR Legal model testing console via /api/admin/hr-legal/query, Query performance analytics and optimization, Legal knowledge base management, A/B testing for prompt strategies
- Sales Intelligence & Analytics: Lead conversion tracking and predictions, Revenue forecasting with multiple scenarios, Customer lifecycle analytics and churn prevention, Pricing optimization recommendations
- Insights Summarizer: Use an LLM tool to summarise and present key strengths and weaknesses extracted by the 4-agent AI analysis system, and turn those into actionable recommendations.

## Style Guidelines:

- Primary Brand: Deep Indigo (#1E293B) - Trust, intelligence
- Secondary: Royal Blue (#3B82F6) - Technology, reliability
- Success: Emerald (#10B981) - Positive outcomes
- Warning: Amber (#F59E0B) - Alerts, attention
- Danger: Red (#EF4444) - Critical issues
- Background: Slate Gray (#F8FAFC) - Clean, professional
- Accent: Gold (#FFD700) - Premium features, CTAs
- Headlines: 'Inter' - Clean, modern sans-serif
- Body Text: 'Inter' - Excellent readability
- Monospace: 'JetBrains Mono' - Code, technical data
- Cards: Clean shadows, rounded corners (8px)
- Buttons: Modern gradient effects for premium features
- Data Tables: Advanced filtering, sorting, pagination
- Charts: Interactive analytics with drill-down capabilities
- Icons: Lucide React for consistent iconography